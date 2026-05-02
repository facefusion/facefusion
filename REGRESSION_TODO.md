# Regression TODO

## WHEP SDP negotiation blocks the async event loop

`negotiate_sdp` polls with `time.sleep(0.05)` in a loop for up to 5 seconds. Calling it directly from the async handler freezes all requests and WebSocket traffic.

Before:

```python
async def post_stream(request : Request) -> Response:
	sdp_answer = rtc_store.add_rtc_viewer(session_id, sdp_offer)
```

After:

```python
async def post_stream(request : Request) -> Response:
	event_loop = asyncio.get_running_loop()
	sdp_answer = await event_loop.run_in_executor(None, rtc_store.add_rtc_viewer, session_id, sdp_offer)
```

## Stream data uses magic byte sniffing instead of channel metadata

The WebSocket received both vision frames and PCM audio as binary messages. The old code checked for JPEG magic bytes (`\xff\xd8`) to distinguish them. This is wrong because it only supports JPEG, breaks when audio happens to start with `0xff 0xd8`, and fails silently for PNG or other image formats.

Before:

```python
JPEG_MAGIC : bytes = b'\xff\xd8'

if data[:2] == JPEG_MAGIC:
	vision_frame = cv2.imdecode(numpy.frombuffer(data, numpy.uint8), cv2.IMREAD_COLOR)

if data[:2] != JPEG_MAGIC:
	rtc_store.send_rtc_audio(session_id, data)
```

After:

```python
if data[0] == ord('v'):
	vision_frame = cv2.imdecode(numpy.frombuffer(data[1:], numpy.uint8), cv2.IMREAD_COLOR)

if data[0] == ord('a'):
	rtc_store.send_rtc_audio(session_id, data[1:])
```

The client prepends a single byte (`v` or `a`) to each message. The server reads the first byte to route the payload — format-agnostic and explicit.

Before (client):

```javascript
ws.send(buf);
ws.send(pcm.buffer);
```

After (client):

```javascript
var prefixed = new Uint8Array(buf.byteLength + 1);
prefixed[0] = 118; // 'v'
prefixed.set(new Uint8Array(buf), 1);
ws.send(prefixed.buffer);

var prefixed = new Uint8Array(pcm.buffer.byteLength + 1);
prefixed[0] = 97; // 'a'
prefixed.set(new Uint8Array(pcm.buffer), 1);
ws.send(prefixed.buffer);
```

## SDP negotiation polls with sleep loop instead of using callbacks

`negotiate_sdp` polls `rtcGetLocalDescription` every 50ms for up to 5 seconds. This wastes CPU and adds latency because the answer might be ready after 5ms but we sleep the full 50ms. libdatachannel provides `rtcSetLocalDescriptionCallback` which fires exactly when the SDP answer is ready.

Before:

```python
def negotiate_sdp(peer_connection : int, sdp_offer : str) -> Optional[str]:
	rtc_library.rtcSetRemoteDescription(peer_connection, sdp_offer.encode('utf-8'), b'offer')
	buffer_size = 16384
	buffer_string = ctypes.create_string_buffer(buffer_size)
	wait_limit = time.monotonic() + 5

	while time.monotonic() < wait_limit:
		if rtc_library.rtcGetLocalDescription(peer_connection, buffer_string, buffer_size) > 0:
			return buffer_string.value.decode()
		time.sleep(0.05)

	return None
```

After:

```python
def negotiate_sdp(peer_connection : int, sdp_offer : str) -> Optional[str]:
	rtc_library.rtcSetRemoteDescription(peer_connection, sdp_offer.encode('utf-8'), b'offer')
	result = threading.Event()
	sdp_holder = [None]

	@ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p)
	def on_description(pc, sdp, sdp_type, user_ptr):
		sdp_holder[0] = sdp.decode()
		result.set()

	rtc_library.rtcSetLocalDescriptionCallback(peer_connection, on_description)
	result.wait(timeout = 5)
	return sdp_holder[0]
```

Uses a `threading.Event` to block until the callback fires — no polling, no wasted sleep cycles, instant response.

## No connection state tracking per peer

`send_to_peers` calls `rtcIsOpen` on the video track for every frame, every peer. There is no way to detect when a peer disconnects or fails — dead peers stay in the list until the stream is destroyed. The poc branch used `rtcSetStateChangeCallback` to track a `connected` flag per viewer and auto-clean dead connections.

Before:

```python
def send_to_peers(peers, data):
	for rtc_peer in peers:
		video_track_id = rtc_peer.get('video_track')

		if video_track_id and rtc_library.rtcIsOpen(video_track_id):
			rtc_library.rtcSetTrackRtpTimestamp(video_track_id, timestamp)
			rtc_library.rtcSendMessage(video_track_id, data_buffer, data_total)
```

After:

```python
@ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_int, ctypes.c_void_p)
def on_state_change(pc, state, user_ptr):
	if state == 4:  # RTC_FAILED
		mark_peer_disconnected(pc)
	if state == 5:  # RTC_CLOSED
		mark_peer_disconnected(pc)

def handle_whep_offer(peers, sdp_offer):
	peer_connection = create_peer_connection()
	rtc_library.rtcSetStateChangeCallback(peer_connection, on_state_change)
```

Avoids calling `rtcIsOpen` on every frame and allows removing dead peers immediately when the connection drops.

## SDP line endings break Firefox

SDP media descriptions used `os.linesep` which produces `\n` on Linux. RFC 4566 requires `\r\n` — Firefox rejected the SDP entirely while Chrome was lenient.

Before:

```python
media_description = b'm=video 9 UDP/TLS/RTP/SAVPF 96' + os.linesep.encode() + b'a=rtpmap:96 VP8/90000' + os.linesep.encode()
```

After:

```python
media_description = ('m=video 9 UDP/TLS/RTP/SAVPF 96\r\na=rtpmap:96 VP8/90000\r\na=sendonly\r\na=mid:0\r\na=rtcp-mux\r\n').encode()
```

## SDP payload types are hardcoded instead of negotiated

Payload types were hardcoded (VP8 PT 96, Opus PT 111). Chrome happens to use these, but Firefox offers VP8 PT 120 and Opus PT 109. The server answered with payload types Firefox never offered, so Firefox couldn't decode the RTP packets.

Before:

```python
def handle_whep_offer(peers, sdp_offer):
	peer_connection = create_peer_connection()
	audio_track = add_audio_track(peer_connection)
	video_track = add_video_track(peer_connection)
```

After:

```python
def extract_payload_type(sdp_offer, media_type, codec_name, fallback):
	current_media = None

	for line in sdp_offer.splitlines():
		if line.startswith('m=' + media_type):
			current_media = media_type
		if line.startswith('m=') and not line.startswith('m=' + media_type):
			current_media = None
		if current_media == media_type and line.startswith('a=rtpmap:') and codec_name in line:
			return int(line.split(':')[1].split(' ')[0])

	return fallback

def handle_whep_offer(peers, sdp_offer):
	video_payload_type = extract_payload_type(sdp_offer, 'video', 'VP8/90000', 96)
	audio_payload_type = extract_payload_type(sdp_offer, 'audio', 'opus/48000', 111)
	peer_connection = create_peer_connection()
	audio_track = add_audio_track(peer_connection, payload_type = audio_payload_type)
	video_track = add_video_track(peer_connection, payload_type = video_payload_type)
```

## Worker threads bypass API context and skip inference

`process_vision_frame` runs in a `ThreadPoolExecutor` where `detect_app_context()` walks the call stack and finds no `facefusion/apis/` frame — so it reads from the empty `cli` state and returns frames without face swap.

Before:

```python
future = executor.submit(process_vision_frame, capture_frame)
```

After:

```python
def process_stream_frame(capture_frame : VisionFrame) -> VisionFrame:
	return process_vision_frame(capture_frame)

future = executor.submit(process_stream_frame, capture_frame)
```

The wrapper lives in `facefusion/apis/stream_helper.py`, so `detect_app_context()` finds it on the call stack and resolves to `api`.

## Frame processing lacks a deque for fluent streaming

Without a deque, processed frames are sent one at a time — if inference is slower than the capture rate, frames queue up in futures and the output stutters. A `deque` buffers completed frames so the encoder can drain them smoothly while inference continues in parallel.

Before:

```python
while not stop_event.is_set():
	capture_frame = latest_frame_holder[0]
	output_vision_frame = process_stream_frame(capture_frame)
	encoder.stdin.write(output_vision_frame.tobytes())
```

After:

```python
output_deque : deque[VisionFrame] = deque()

with ThreadPoolExecutor(max_workers = state_manager.get_item('execution_thread_count')) as executor:
	futures = []

	while not stop_event.is_set():
		if capture_frame is not None and len(futures) < 4:
			future = executor.submit(process_stream_frame, capture_frame)
			futures.append(future)

		for future_done in [ future for future in futures if future.done() ]:
			output_deque.append(future_done.result())
			futures.remove(future_done)

		while output_deque:
			temp_vision_frame = output_deque.popleft()
			encoder.stdin.write(temp_vision_frame.tobytes())
```

Consider reusing `multi_process_capture` from `streamer.py` — it has the same ThreadPoolExecutor + deque pattern. If it accepted a frame iterator instead of `cv2.VideoCapture`, both pipelines could share the same processing loop.

## Binary files belong in `.binaries/` at project root

The libdatachannel shared library downloads to `.binaries/` in the project root. This is not an asset — binary dependencies are platform-specific build artifacts and must stay separate from `.assets/`.

```python
'path': resolve_relative_path('../.binaries/' + binary_name)
```
