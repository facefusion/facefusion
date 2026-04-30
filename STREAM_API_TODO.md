# Stream API TODO

## Approach

1. vibe code mass testing to get broad coverage fast
2. vibe code refactoring (naming, boilerplate extraction, validation)
3. hand craft production code (stream pipeline, encoder loop, IVF parsing)
4. hand craft testing — thin it out to essentials only

## Unit Tests

| Function | Rating | Assertions |
|---|---|---|
| `get_websocket_stream_mode` | essential | returns None for missing header, returns None for unknown protocol |
| `forward_rtc_frames` | essential | reads IVF header and forwards frame data, handles broken pipe |
| `run_encode_loop` | nice to have | drains deque and closes encoder |
| `receive_vision_frames` | skip | async generator, covered by integration tests |
| `submit_encoder_frame` | skip | thin glue between cv2 and subprocess stdin |
| `websocket_stream` | skip | routing only, covered by integration tests |
| `post_stream` | skip | covered by integration tests |

## Integration Tests

- [ ] test stream without session — expect rejection
- [ ] test stream with expired or invalid token
- [ ] test image stream without source selected
- [ ] test video stream without source selected
- [ ] test WHEP offer without active websocket stream
- [ ] test WHEP offer with malformed SDP body
- [ ] test WHEP offer with wrong content type
- [ ] test multiple WHEP viewers on same stream
- [ ] test websocket disconnect mid-stream triggers cleanup

## Naming

- [ ] rename `test_get_stream_mode` to `test_get_websocket_stream_mode` in `test_stream_helper.py` — does not match function name
- [ ] rename `make_scope` in `test_stream_helper.py` to `make_websocket_scope` — more descriptive
- [ ] `stream_helper.py` mixes pure helpers (`calculate_bitrate`) with async handlers (`handle_image_stream`) — consider splitting

## Dead Code

- [ ] `read_pipe_buffer` has a test but the test is disconnected from how it is actually used — the test reads from a closed pipe, production reads from a live subprocess stdout

## Refactor

- [ ] `handle_image_stream` and `handle_video_stream` share session setup boilerplate (subprotocol, access_token, session_id, source_paths, websocket accept) — extract common setup
- [ ] `forward_rtc_frames` assumes IVF container format with hardcoded header size 32 and frame header size 12 — document or make configurable
- [ ] `post_stream` does not validate content type is `application/sdp` before parsing body
- [ ] `calculate_bitrate` has a TODO about improving the calculation
- [ ] `handle_video_stream` has a hardcoded fallback `output_video_fps or 30` with a TODO to resolve from target video fps

## Violations

- `stream_helper.py:24` — comment on `calculate_bitrate` (no comments)
- `stream_helper.py:143` — comment on `output_video_fps` fallback (no comments)
- `test_stream_helper.py:30` — `test_get_stream_mode` does not match function name `get_websocket_stream_mode` (naming convention)

## Security

- `endpoints/stream.py:27` — `request.body().decode()` is not sanitized, raw user input forwarded to C library via RTC layer
