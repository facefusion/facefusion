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
