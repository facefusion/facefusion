Beta Updates
============


Changes on the `v4` development branch up to `7d042f69` since the `v4-beta` tag:

- MP4, MOV and M4A uploads with the `moov` atom at the end are rejected with `415`
- uploads whose content does not match their extension are rejected with `415`
- uploads keep the first video and the first audio stream only
- `strict` re-encodes videos with the encoder of the upload format, WebM uploads are no longer rejected
- `strict` re-encodes videos with the preset of `--output-video-preset` instead of `ultrafast`
- image to video keeps the original audio with the default `memory` workflow strategy, the output had no audio before
- image to video keeps the full audio when trimming with the `disk` workflow strategy, the audio was cut or missing before
- closing a session no longer fails when a `/stream` client disconnected while a frame was being processed
- a missing model download is no longer saved as an error page and no longer leaves the server stuck in checking
- cancelling a job no longer leaves ffmpeg running when the cancel arrives between two processing steps
- starting with `--log-level debug` no longer crashes the encoder detection
- type checking passes with mypy 2.4, the beta fails on `facefusion/ffmpeg.py` with an incompatible assignment
- a session is limited to one stream, metrics and ping websocket, a second connection of the same kind is rejected
- capturing asset frames and faces runs off the event loop, so a heavy capture no longer blocks other sessions while it decodes
- image uploads with a resolution above `4096` are rejected with `400`, which prevents decompression bombs
- video uploads with a resolution above `4096` are rejected with `400`, the check that guarded images now guards videos as well
- an upload is limited to `32` files, further files are rejected
- `/stream` ignores frames with a resolution above `4096` instead of decoding them
- capturing asset frames and faces returns a `multipart/mixed` stream with one part per frame instead of a single concatenated image, which avoids building one large image
- the API bounds the number of concurrent requests and the websocket message size and queue, which avoids an overload from too many requests at once
- Python `3.13` is required, the beta started with `3.10`
- a queued job can be canceled via `PATCH /jobs/{job_id}?action=cancel` and all queued jobs via `PATCH /jobs?action=cancel`, the job moves back to `drafted` and a running step stops its ffmpeg
- a session lives `5` minutes instead of `10`
- `DELETE /session` responds `409` while the session is busy with a stream, a running job, an upload or a capture
- `DELETE /session` always closes the session, when its files cannot be removed it responds `206` instead of responding `404` and keeping the session open
- reading video frames from several requests at once no longer starts duplicate ffmpeg processes
- metrics report AMD graphic devices on Windows with `directml` via ADLX and fall back to NVIDIA, AMD devices via `migraphx` are only detected on Linux
- concurrent uploads, captures and downloads of a session are tracked one by one, the session stays busy until the last one finishes and closing it cancels all of them, before the first one to finish marked the session idle
- `DELETE /session` responds `409` while the session is busy with a download as well
- CUDA and TensorRT always use the `EXHAUSTIVE` cuDNN convolution search, GeForce GTX 16xx cards no longer fall back to `DEFAULT`
- detecting graphic devices is serialized, so concurrent metrics no longer break the AMD and NVIDIA device detection
- `--api-host` defaults to `localhost` instead of `127.0.0.1`
- CORS is disabled by default, `--cors-origins` or `cors_origins` in the `[cors]` section of `facefusion.ini` allows the listed origins with the methods `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, the headers `Authorization`, `Content-Type` and exposes `Location`, the beta allows any origin, method and header
