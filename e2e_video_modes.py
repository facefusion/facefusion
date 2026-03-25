import os
import platform
import signal
import subprocess
import sys
import time

import httpx
from playwright.sync_api import sync_playwright

API_PORT : int = 8400
HTML_FILE : str = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_stream.html')
SOURCE_FILE : str = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.assets', 'examples', 'source.jpg')

def is_windows() -> bool:
	return platform.system().lower() == 'windows'

def is_macos() -> bool:
	return platform.system().lower() == 'darwin'

if is_windows():
	VIDEO_FILE : str = 'C:\\Users\\info\\Downloads\\face8k.mp4'
elif is_macos():
	VIDEO_FILE : str = '/Users/henry/Downloads/copy_face_instant.mp4'
else:
	VIDEO_FILE : str = '/home/henry/Documents/examples/download.mp4'


def safe_print(text : str) -> None:
	try:
		print(text)
	except UnicodeEncodeError:
		print(text.encode('ascii', errors='replace').decode('ascii'))

_ALL_MODES =\
[
	'whip-mediamtx',
	'whip-python',
	'whip-datachannel',
	'ws-fmp4',
	'datachannel-direct',
	'datachannel-relay-py',
	'ws-mjpeg'
]

MODES = [ m for m in _ALL_MODES if not (is_macos() and m == 'whip-mediamtx') ]


def start_api() -> subprocess.Popen:
	env = os.environ.copy()
	python_cmd = 'python' if is_windows() else 'python3'

	if not is_windows() and not is_macos():
		env['LD_LIBRARY_PATH'] = '/home/henry/local/lib:' + env.get('LD_LIBRARY_PATH', '')

	proc = subprocess.Popen(
		[ python_cmd, 'facefusion.py', 'api', '--api-port', str(API_PORT), '--execution-providers', 'cpu' ],
		env = env,
		stdout = subprocess.PIPE,
		stderr = subprocess.PIPE
	)
	return proc


def wait_for_api(timeout : int = 60) -> bool:
	for i in range(timeout):
		time.sleep(1)

		try:
			r = httpx.get('http://localhost:' + str(API_PORT) + '/capabilities', timeout = 2)

			if r.status_code == 200:
				return True
		except Exception:
			pass

		if i % 10 == 9:
			print('  [' + str(i + 1) + 's] still waiting for API...')

	return False


def stop_api(proc : subprocess.Popen) -> None:
	if is_windows():
		proc.terminate()
	else:
		proc.send_signal(signal.SIGTERM)

	try:
		proc.wait(timeout = 10)
	except subprocess.TimeoutExpired:
		proc.kill()
		proc.wait()

	time.sleep(1)


def kill_port_windows(port : int) -> None:
	result = subprocess.run(
		[ 'netstat', '-ano' ],
		capture_output = True, text = True
	)

	for line in result.stdout.splitlines():
		if ':' + str(port) + ' ' in line and ('LISTENING' in line or 'ESTABLISHED' in line):
			parts = line.split()
			pid = parts[-1]

			if pid.isdigit() and int(pid) > 0:
				subprocess.run([ 'taskkill', '/F', '/PID', pid ], stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)


def kill_port_macos(port : int) -> None:
	pids = set()

	for proto in [ 'tcp', 'udp' ]:
		result = subprocess.run(
			[ 'lsof', '-ti', proto + ':' + str(port) ],
			capture_output = True, text = True
		)

		for pid in result.stdout.split():
			if pid.isdigit():
				pids.add(pid)

	for pid in pids:
		subprocess.run([ 'kill', '-9', pid ], stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)


def kill_stale() -> None:
	ports = [ API_PORT, 8889, 8189, 9997, 8890, 8891, 8892 ]

	if is_windows():
		for port in ports:
			kill_port_windows(port)
	elif is_macos():
		for port in ports:
			kill_port_macos(port)
	else:
		subprocess.run([ 'fuser', '-k', str(API_PORT) + '/tcp' ], stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
		subprocess.run([ 'fuser', '-k', '8889/tcp' ], stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
		subprocess.run([ 'fuser', '-k', '8189/udp' ], stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
		subprocess.run([ 'fuser', '-k', '9997/tcp' ], stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
		subprocess.run([ 'fuser', '-k', '8890/tcp' ], stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
		subprocess.run([ 'fuser', '-k', '8891/tcp' ], stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
		subprocess.run([ 'fuser', '-k', '8892/tcp' ], stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)

	time.sleep(2)


def test_mode(mode : str) -> dict:
	result = {'mode': mode, 'session': False, 'source': False, 'video': False, 'ws_open': False, 'stream_ready': False, 'playback': False, 'error': None}

	print('\n' + '=' * 60)
	print('TESTING: ' + mode)
	print('=' * 60)

	kill_stale()
	api_proc = start_api()
	print('  starting API...')

	if not wait_for_api():
		result['error'] = 'API failed to start'
		stop_api(api_proc)
		return result

	print('  API ready')

	try:
		with sync_playwright() as pw:
			browser = pw.chromium.launch(
				headless = False,
				channel = 'chrome',
				args = [ '--autoplay-policy=no-user-gesture-required', '--allow-file-access-from-files' ]
			)
			page = browser.new_page(viewport = { 'width': 1920, 'height': 1080 })

			logs = []
			page.on('console', lambda msg: logs.append(msg.text))
			page.goto('file://' + HTML_FILE)

			page.fill('#serverUrl', 'http://localhost:' + str(API_PORT))
			page.click('text=Connect')
			print('  waiting for session...')

			for _ in range(15):
				time.sleep(1)
				log_text = page.locator('#log').text_content()

				if 'session ok' in log_text:
					result['session'] = True
					break

			if not result.get('session'):
				result['error'] = 'session failed'
				print('  FAIL: no session')
				browser.close()
				stop_api(api_proc)
				return result

			print('  session OK, uploading source...')
			page.locator('#sourceFile').set_input_files(SOURCE_FILE)

			for _ in range(10):
				time.sleep(1)
				log_text = page.locator('#log').text_content()

				if 'source face set' in log_text:
					result['source'] = True
					break

			if not result.get('source'):
				result['error'] = 'source upload failed'
				print('  FAIL: source upload')
				browser.close()
				stop_api(api_proc)
				return result

			print('  source OK, loading video...')
			page.locator('#videoFile').set_input_files(VIDEO_FILE)

			for i in range(15):
				time.sleep(1)
				log_text = page.locator('#log').text_content()

				if 'video file' in log_text:
					time.sleep(2)
					result['video'] = True
					break

			if not result.get('video'):
				log_text = page.locator('#log').text_content()
				result['error'] = 'video load failed: ' + log_text[-200:]
				print('  FAIL: video load')
				browser.close()
				stop_api(api_proc)
				return result

			print('  video OK, selecting mode: ' + mode)
			page.select_option('#streamMode', mode)
			time.sleep(0.5)

			print('  starting stream...')

			for _ in range(10):
				time.sleep(1)

				try:
					if page.locator('#btnPlay').is_enabled(timeout = 1000):
						break
				except Exception:
					pass

			page.locator('#btnPlay').click(timeout = 5000)

			for i in range(10):
				time.sleep(1)
				log_text = page.locator('#log').text_content()

				if 'websocket open' in log_text:
					result['ws_open'] = True
					break

			if not result.get('ws_open'):
				result['error'] = 'websocket failed to open'
				log_text = page.locator('#log').text_content()
				print('  FAIL: ws not open')
				print('  LOG: ' + log_text[-300:])
				browser.close()
				stop_api(api_proc)
				return result

			print('  ws open, waiting for playback...')

			for i in range(45):
				time.sleep(1)
				log_text = page.locator('#log').text_content()
				ws_stat = page.locator('#statWs').text_content()
				rtc_stat = page.locator('#statRtc').text_content()
				frames_stat = page.locator('#statFrames').text_content()
				fps_stat = page.locator('#statFps').text_content()

				if 'stream ready' in log_text or 'WHEP' in log_text:
					result['stream_ready'] = True

				if mode == 'ws-mjpeg':
					result['stream_ready'] = True

					try:
						has_img = page.evaluate('!!document.getElementById("outputVideo")._mjpegImg && !!document.getElementById("outputVideo")._mjpegImg.src')

						if has_img:
							result['playback'] = True
							print('  [' + str(i) + 's] MJPEG receiving frames')
							break
					except Exception:
						pass

				if mode == 'ws-fmp4':
					if 'MSE source buffer ready' in log_text:
						result['stream_ready'] = True

					try:
						mse_info = page.evaluate('''() => {
							var v = document.getElementById("outputVideo");
							var ms = v._mediaSource || window.mediaSource;
							var buf = (v.buffered && v.buffered.length > 0) ? v.buffered.end(0) : 0;
							return { time: v.currentTime, buffered: buf, readyState: v.readyState, networkState: v.networkState };
						}''')
						buffered = mse_info.get('buffered', 0)

						if buffered > 0 or mse_info.get('time', 0) > 0:
							result['playback'] = True
							print('  [' + str(i) + 's] MSE buffered=' + str(round(buffered, 2)) + ' time=' + str(round(mse_info.get('time', 0), 2)))
							break

						if i % 5 == 0:
							print('  [' + str(i) + 's] MSE: ' + str(mse_info))
					except Exception:
						pass
				else:
					try:
						frames_val = int(frames_stat) if frames_stat and frames_stat != '--' else 0
					except ValueError:
						frames_val = 0

					if frames_val > 0:
						result['playback'] = True
						print('  [' + str(i) + 's] frames=' + str(frames_val) + ' fps=' + fps_stat + ' rtc=' + rtc_stat)
						break

				try:
					rtc_stats = page.evaluate('''() => {
						if (!window.pc) return '';
						return pc.getStats().then(stats => {
							var r = '';
							stats.forEach(report => {
								if (report.type === 'inbound-rtp' && report.kind === 'video') {
									r = 'pkts=' + (report.packetsReceived||0) + ' bytes=' + (report.bytesReceived||0) + ' lost=' + (report.packetsLost||0) + ' dropped=' + (report.framesDropped||0) + ' dec=' + (report.decoderImplementation||'?') + ' kf=' + (report.keyFramesDecoded||0) + ' nacks=' + (report.nackCount||0) + ' plis=' + (report.pliCount||0);
								}
							});
							return r;
						});
					}''')
				except Exception:
					rtc_stats = ''
				print('  [' + str(i) + 's] ws=' + ws_stat + ' rtc=' + rtc_stat + ' frames=' + frames_stat + ' ' + str(rtc_stats))

			if not result.get('playback'):
				log_text = page.locator('#log').text_content()
				result['error'] = 'no playback after 45s'
				safe_print('  FAIL: no playback')
				safe_print('  LOG (last 500): ' + log_text[-500:])

				for line in logs[-20:]:
					safe_print('  [console] ' + line)

			browser.close()

	except Exception as exception:
		result['error'] = str(exception)
		safe_print('  EXCEPTION: ' + str(exception))

	stderr_out = ''

	try:
		stop_api(api_proc)
		stderr_out = api_proc.stderr.read().decode('utf-8', errors='ignore')[-5000:]
	except Exception:
		pass

	if stderr_out.strip():
		safe_print('  API stderr: ' + stderr_out)

	return result


def main() -> None:
	modes_to_test = MODES

	if len(sys.argv) > 1:
		modes_to_test = sys.argv[1:]

	results = []

	for mode in modes_to_test:
		result = test_mode(mode)
		results.append(result)

	print('\n\n' + '=' * 60)
	print('SUMMARY')
	print('=' * 60)

	for r in results:
		status = 'PASS' if r.get('playback') else 'FAIL'
		error = ' (' + r.get('error', '') + ')' if r.get('error') else ''
		flags = []

		if r.get('session'):
			flags.append('session')
		if r.get('ws_open'):
			flags.append('ws')
		if r.get('stream_ready'):
			flags.append('ready')
		if r.get('playback'):
			flags.append('playback')

		print('  ' + status + '  ' + r.get('mode') + '  [' + ','.join(flags) + ']' + error)


if __name__ == '__main__':
	main()
