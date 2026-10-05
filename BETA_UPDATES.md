Beta Updates
============


Changes on the `v4` development branch since the `v4-beta` tag:

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
