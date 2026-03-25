import os
import platform
import signal
import subprocess
import time

import httpx
from playwright.sync_api import sync_playwright

API_PORT : int = 8400
HTML_FILE : str = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_stream.html')
SOURCE_FILE : str = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.assets', 'examples', 'source.jpg')

if platform.system().lower() == 'windows':
	VIDEO_FILE : str = 'C:\\Users\\info\\Downloads\\face8k.mp4'
else:
	VIDEO_FILE : str = '/home/henry/Documents/examples/download.mp4'


def safe_print(text : str) -> None:
	try:
		print(text)
	except UnicodeEncodeError:
		print(text.encode('ascii', errors='replace').decode('ascii'))


def start_api() -> subprocess.Popen:
	env = os.environ.copy()
	python_cmd = 'python' if platform.system().lower() == 'windows' else 'python3'

	if platform.system().lower() != 'windows':
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
	if platform.system().lower() == 'windows':
		proc.terminate()
	else:
		proc.send_signal(signal.SIGTERM)

	try:
		proc.wait(timeout = 10)
	except subprocess.TimeoutExpired:
		proc.kill()
		proc.wait()

	time.sleep(1)


def kill_stale() -> None:
	ports = [ API_PORT ]

	if platform.system().lower() == 'windows':
		for port in ports:
			result = subprocess.run([ 'netstat', '-ano' ], capture_output = True, text = True)

			for line in result.stdout.splitlines():
				if ':' + str(port) + ' ' in line and ('LISTENING' in line or 'ESTABLISHED' in line):
					parts = line.split()
					pid = parts[-1]

					if pid.isdigit() and int(pid) > 0:
						subprocess.run([ 'taskkill', '/F', '/PID', pid ], stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
	else:
		for port in ports:
			subprocess.run([ 'fuser', '-k', str(port) + '/tcp' ], stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)

	time.sleep(2)


def test_rtc() -> dict:
	result = {'session': False, 'source': False, 'video': False, 'ws_open': False, 'stream_ready': False, 'playback': False, 'error': None}

	print('\n' + '=' * 60)
	print('TESTING: libdatachannel direct (RTC)')
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

			print('  video OK, starting stream...')

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

				try:
					frames_val = int(frames_stat) if frames_stat and frames_stat != '--' else 0
				except ValueError:
					frames_val = 0

				if frames_val > 0:
					result['playback'] = True
					print('  [' + str(i) + 's] frames=' + str(frames_val) + ' fps=' + fps_stat + ' rtc=' + rtc_stat)
					break

				print('  [' + str(i) + 's] ws=' + ws_stat + ' rtc=' + rtc_stat + ' frames=' + frames_stat)

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
	result = test_rtc()

	print('\n\n' + '=' * 60)
	print('RESULT')
	print('=' * 60)

	status = 'PASS' if result.get('playback') else 'FAIL'
	error = ' (' + result.get('error', '') + ')' if result.get('error') else ''
	flags = []

	if result.get('session'):
		flags.append('session')
	if result.get('ws_open'):
		flags.append('ws')
	if result.get('stream_ready'):
		flags.append('ready')
	if result.get('playback'):
		flags.append('playback')

	print('  ' + status + '  datachannel-direct  [' + ','.join(flags) + ']' + error)


if __name__ == '__main__':
	main()
