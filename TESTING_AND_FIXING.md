# Testing and Fixing

Triage of media/workflow bugs found on `v4`. Each one was reproduced on `v4` (working tree) and on `origin/master` (72470819).

Every suggested diff below was applied to a scratch copy of v4 and checked three ways:
- the CLI or python repro passes
- the new test fails on unpatched v4 and passes on the patched copy
- flake8 is clean

No file in the repo was changed except this document.

Scratch locations, all under `/tmp/claude-1000/-home-henry-PycharmProjects-facefusion/28a37a6c-09fe-4ba4-b2cd-568c77adfbbe/scratchpad/regress/`:
- repro scripts, logs, outputs: `media/`
- `media/run.sh v4|master|patched <name> <args>` runs the CLI with a private TMPDIR. On master it uses `headless-run`, because `run` launches the UI there.
- patched v4 copy: `patched/`
- combined diffs: `code.diff`, `tests.diff`

Test media:
- `target-2s-audio.mp4`: 50 frames, 2.0s aac, moov at end
- `target-4s-audio.mp4`: 100 frames, 3.79s audio
- `target-2s-faststart.mp4`: faststart copy of `target-2s-audio.mp4`


## Labels

Scope (where to fix):
- **[master+v4]**: pre-existing. Fix on master, merge forward into v4. Port by hand: v4 renamed `frame_number` to `frame_index`, uses `temp_helper(temp_path, output_path)` and `--reference-frame-index`.
- **[v4-regression]**: works on master, broken on v4. Fix on v4.
- **[v4-only]**: the feature does not exist on master. Fix on v4.
- **[master-only]**: none found.

Priority:
- **P0 critical**: default path produces wrong output silently.
- **P1 high**: common path or API produces wrong or empty output.
- **P2 medium**: non-default mode broken, or a latent wrong result.
- **P3 low**: edge case, bad input, or performance only.


## Summary

### v4-only (fix on v4)

Includes the two v4 regressions, which work on master and are broken on v4.

| # | Scope | Priority | Module | Bug | Fix validated |
|---|-------|----------|--------|-----|---------------|
| 5 | v4-only | P1 high | ffmpeg.py + apis/asset_helper.py | sanitize_video fails on moov-at-end MP4/MOV; real-world uploads crash with 500 (see 24) | yes |
| 24 | v4-only | P1 high | asset_store.create_asset / ffprobe.extract_video_metadata + extract_audio_metadata | moov-at-end mp4, mov and m4a uploads crash with 500 (`float('N/A')`) | no, suggestion only |
| 1 | v4-regression | P0 critical | workflows/to_video.py | memory strategy (default) drops original audio | yes |
| 2 | v4-regression | P1 high | workflows/to_video.py | disk strategy trim truncates audio | yes (same diff as 1) |
| 16 | v4-only | P1 high | apis/endpoints/stream.py | dead /stream websocket stays in store, crashes the session sweeper | no, suggestion only |
| 3 | v4-only | P2 medium | ffmpeg.spawn_frames | audio-to-image trim start yields truncated video | yes |
| 11 | v4-only | P2 medium | ffmpeg.replace_audio | audio-to-image trim: audio track not offset (lip desync) | no, suggestion only |
| 7 | v4-only | P2 medium | workflows/core.py | as-frames mode gets empty source audio/voice | yes |
| 19 | v4-only | P2 medium | workflows/as_frames.py | image-to-video:frames ignores output_video_scale (frames at processor resolution) | no, suggestion only |
| 15 | v4-only | P2 medium | codecs/aom_decoder.py | AV1 decode uses padded size, junk edges on non-multiple-of-8 frames | no, suggestion only |
| 17 | v4-only | P2 medium | codecs/vpx_encoder.py + apis/stream_video.py | VP8 resolution growth fails silently, config already overwritten | no, suggestion only |
| 21 | v4-only | P2 medium | store_creator.init_content | init() resets an existing session entry instead of being idempotent | no, suggestion only |
| 18 | v4-only | P3 low | rtc.py | create_sdp_offer / create_sdp_answer return '' instead of None | no, suggestion only |

### master+v4 (fix on master, merge into v4)

| # | Scope | Priority | Module | Bug | Fix validated |
|---|-------|----------|--------|-----|---------------|
| 4 | master+v4 | P1 high | ffmpeg.py (ffprobe cache) | stale cached temp video metadata across jobs | yes |
| 22 | master+v4 | P2 medium | download.conditional_download_hashes / _sources | failed download leaves the process in checking, later calls wait forever | no, suggestion only |
| 8 | master+v4 | P2 medium | ffmpeg.run_ffmpeg | returncode None outside processing state | yes |
| 12 | master+v4 | P2 medium | ffmpeg.log_debug | `--log-level debug` closes ffmpeg stdout, encoder detection crashes | no, suggestion only |
| 6 | master+v4 | P3 low | filesystem.move_file | missing output dir raises FileNotFoundError | yes |
| 10 | master+v4 | P3 low | video_manager.py | negative reference frame index desyncs reader | yes |
| 13 | master+v4 | P3 low | jobs/job_manager.init_jobs | jobs path that is a file raises NotADirectoryError | no, suggestion only |
| 14 | master+v4 | P3 low | ffmpeg.run_ffmpeg_with_progress | already stopped run leaves ffmpeg running | no, suggestion only |
| 20 | master+v4 | P3 low | core.conditional_process | mismatched --workflow-mode exits 1 without an error message | no, suggestion only |
| 23 | master+v4 | P3 low | curl_builder.run / download.conditional_download | HTTP error body (e.g. 404 "Not Found") is saved as the downloaded file | no, suggestion only |
| 9 | master+v4 | won't fix | workflows/core.py | voice_extractor runs without a processor needing it | by design |

Suggested order:
1. **[top bug, v4-only]**: bugs 5 and 24 together. Ordinary phone, camera and editor MP4/MOV/M4A files with the index at the end crash the upload API with a 500. Users report it, and it is reproduced with replicas of their files.
2. **[v4-regression]**: bugs 1 and 2. One diff; this should unblock default runs.
3. **[master+v4]**: bugs 4, 22, 8, 12, 6, 10, 13, 14, 20, 23 on master, then merge into v4.
4. **[v4-only]**: bugs 16, 3, 11, 7, 15, 17, 19, 21, 18.

Bugs 12 to 24 were added later, from the 95% coverage push and the xfail work. They have not gone through the patched-copy validation yet. 12, 13, 14 and 20 were reproduced on both trees with the same result. For 15 to 18, `git cat-file` and `git grep` on `origin/master` confirm that their files, and any aom, vpx, libdatachannel or websocket code, do not exist on master.

Test results on the scratch copies, run over test_ffmpeg, test_workflow, test_image_to_video, test_audio_to_image(_as_frames), test_filesystem, test_video_manager and test_temp_helper:

| Tree | Failed | Passed |
|------|--------|--------|
| v4 plus new tests | 9 (every new or extended test) | 71 |
| patched plus new tests | 1 | 79 |

The one patched failure is `test_merge_video`. It also fails on unpatched v4, because it loops over every locally available encoder.



## Expected-failure tests

Every bug with a deterministic reproduction has a test in the suite marked `@pytest.mark.xfail(strict = True, raises = <exception>, reason = 'TESTING_AND_FIXING.md #N')`. It asserts the correct behaviour, so the suite stays green while the bug exists.

- **When a fix lands, the test passes.** `strict = True` turns that XPASS into a failure, which is the signal to remove the marker.
- **If a fix fails some other way, the test fails visibly.** `raises` limits `xfail` to the exception the bug produces today. For example, the #5 fix changes the `sanitize_video` signature, so its test then fails with a `TypeError` and has to be updated.

| # | Test | Raises today |
|---|------|--------------|
| 1 | tests/test_image_to_video.py::test_process_memory_with_audio | AssertionError |
| 2 | tests/test_image_to_video.py::test_process_disk_with_trim_frame | AssertionError |
| 3 | tests/test_ffmpeg.py::test_spawn_frames_with_trim_frame_start | AssertionError |
| 4 | tests/test_ffmpeg.py::test_restore_audio_with_reused_output_path | AssertionError |
| 5 | tests/test_ffmpeg.py::test_sanitize_video_with_moov_at_end | AssertionError |
| 5, 24 | tests/test_api_assets.py::test_upload_assets_with_moov_at_end | ValueError |
| 6 | tests/test_filesystem.py::test_move_file_to_missing_directory | FileNotFoundError |
| 7 | tests/test_workflow.py::test_conditional_get_source_audio_frame_with_frames_mode | AssertionError |
| 8 | tests/test_ffmpeg.py::test_run_ffmpeg_without_processing | AssertionError |
| 10 | tests/test_video_manager.py::test_conditional_seek_video_reader_with_negative_frame_index | AssertionError |
| 21 | tests/test_store_creator.py::test_init_content_with_existing_content | AssertionError |
| 22 | tests/test_download.py::test_conditional_download_hashes_with_invalid_hash, test_conditional_download_sources_with_invalid_source | AssertionError |
| 23 | tests/test_download.py::test_conditional_download_with_missing_url | AssertionError |
| 24 | tests/test_api_assets.py::test_upload_assets_with_moov_at_end_audio | ValueError |

Checked against the patched copy (`regress/patched`):
- **#1, #2, #3, #4, #6, #7, #8, #10:** turn into XPASS(strict).
- **#5:** fails with a `TypeError` because of the signature change.
- **#21, #22, #23:** not patched there, so they stay xfail.

On the current tree the tests touched by this work report 86 passed and 12 xfailed; with #23 added, `test_download.py` has 3 xfailed.

`test_run_ffmpeg` used to assert `returncode is None` after `process_manager.end()`, which locked bug #8 in place. That assertion was removed in favour of the #8 test.

The tests for bugs 11 and 12–20 are still only written up in this document.

---

# Details


## 1. Memory strategy drops original audio
**[v4-regression] · P0 critical** · `facefusion/workflows/to_video.py`

### Evidence
- `run.sh v4 b1 -t target-2s-audio.mp4 --processors face_debugger`: ffmpeg logs `-to value smaller than -ss; aborting` and then "restoring audio skipped". The output has `video nb_frames=50` and **no audio stream**; exit=0.
- `run.sh master b1 ...` (same args): "restoring audio succeeded", audio 2.000s.
- `run.sh patched b1 ...`: "restoring audio succeeded", audio 2.02s.

### Cause
`merge_frames()` and `restore_audio()` clamp the trim with `restrict_trim_frame(len(temp_frame_paths), ...)`. The memory strategy writes no temp frames, so trim becomes (0, 0).

Introduced by `1b2fffd8 image to video as sequence` (blame on to_video.py lines 120-121 and 138-139). The commit is not on master.

### Suggested diff
Clamp against the media the trim refers to: the target video for image-to-video, and the source audio for audio-to-image.

```diff
--- facefusion/workflows/to_video.py
+++ facefusion/workflows/to_video.py
@@
-from typing import Deque
+from typing import Deque, Tuple
@@
 from facefusion import cli_progress, content_analyser, ffmpeg, logger, process_manager, state_manager, thread_helper, translator, video_manager
+from facefusion.audio import restrict_trim_audio_frame
 from facefusion.common_helper import get_first, get_middle
 from facefusion.filesystem import filter_audio_paths, is_video
-from facefusion.media_helper import restrict_trim_frame
 from facefusion.processors.core import get_processors_modules
-from facefusion.temp_helper import move_temp_file, resolve_temp_frame_paths
+from facefusion.temp_helper import move_temp_file
@@ def merge_frames() -> ErrorCode:
-	temp_frame_paths = resolve_temp_frame_paths(state_manager.get_temp_path(), state_manager.get_item('output_path'), state_manager.get_item('temp_frame_format'))
-	trim_frame_start, trim_frame_end = restrict_trim_frame(len(temp_frame_paths), state_manager.get_item('trim_frame_start'), state_manager.get_item('trim_frame_end'))
+	trim_frame_start, trim_frame_end = conditional_restrict_trim_frame()
@@ def restore_audio() -> ErrorCode:
-	temp_frame_paths = resolve_temp_frame_paths(state_manager.get_temp_path(), state_manager.get_item('output_path'), state_manager.get_item('temp_frame_format'))
-	trim_frame_start, trim_frame_end = restrict_trim_frame(len(temp_frame_paths), state_manager.get_item('trim_frame_start'), state_manager.get_item('trim_frame_end'))
+	trim_frame_start, trim_frame_end = conditional_restrict_trim_frame()
@@
+
+
+def conditional_restrict_trim_frame() -> Tuple[int, int]:
+	if state_manager.get_item('workflow_mode') == 'image-to-video':
+		return restrict_trim_video_frame(state_manager.get_item('target_path'), state_manager.get_item('trim_frame_start'), state_manager.get_item('trim_frame_end'))
+	source_audio_path = get_first(filter_audio_paths(state_manager.get_item('source_paths')))
+	return restrict_trim_audio_frame(source_audio_path, state_manager.get_item('output_audio_fps'), state_manager.get_item('trim_frame_start'), state_manager.get_item('trim_frame_end'))
```

### Suggested test
`tests/test_image_to_video.py`. The existing `test_process` uses `target-240p.mp4`, which has **no audio**, so it could not catch this bug.

```diff
@@ def before_all() -> None:
 		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg',
+		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.mp3',
 		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-240p.mp4'
 	])
 
+	ffmpeg.run_ffmpeg(
+		ffmpeg_builder.chain(
+			ffmpeg_builder.set_input(get_test_example_file('source.mp3')),
+			ffmpeg_builder.set_input(get_test_example_file('target-240p.mp4')),
+			ffmpeg_builder.set_audio_sample_rate(48000),
+			ffmpeg_builder.set_output(get_test_example_file('target-240p-48khz.mp4'))
+		)
+	)
+
@@
+def test_process_restore_audio() -> None:
+	state_manager.set_item('target_path', get_test_example_file('target-240p-48khz.mp4'))
+	state_manager.set_item('trim_frame_start', 25)
+	state_manager.set_item('trim_frame_end', 75)
+
+	for workflow_strategy in [ 'disk', 'memory' ]:
+		state_manager.set_item('workflow_strategy', workflow_strategy)
+		state_manager.set_item('output_path', get_test_output_path('test-process-restore-audio-' + workflow_strategy + '.mp4'))
+
+		assert process(time()) == 0
+		assert probe_audio_entries(get_test_output_path('test-process-restore-audio-' + workflow_strategy + '.mp4'), [ 'duration' ]) == { 'duration': '2.000000' }
+
+	state_manager.set_item('target_path', get_test_example_file('target-240p.mp4'))
+	state_manager.set_item('trim_frame_start', 0)
+	state_manager.set_item('trim_frame_end', 10)
```

Also import `probe_audio_entries` from `facefusion.ffprobe`.

- v4: fails.
- patched: passes.
- This test covers bug 2 as well (the disk iteration).


## 2. Disk strategy trim truncates audio
**[v4-regression] · P1 high** · `facefusion/workflows/to_video.py`

### Evidence
- `run.sh v4 b2 -t target-4s-audio.mp4 --workflow-strategy disk --trim-frame-start 25 --trim-frame-end 75`: video 2.0s / 50 frames, **audio 1.023s**.
- master, same args: audio 2.000s.
- patched: audio 2.02s.
- Test b2m (memory strategy, same trim): v4 has no audio (bug 1); master and patched have 2.0s.

### Cause
The same clamp as bug 1: `restrict_trim_frame(50 temp frames, 25, 75)` gives (25, 50). Introduced by `1b2fffd8`.

### Suggested diff and test
The same as bug 1. `test_process_restore_audio` covers the disk strategy.


## 3. Audio-to-image trim start yields a truncated video
**[v4-only] · P2 medium** · `facefusion/ffmpeg.py` `spawn_frames`

### Evidence
- `run.sh v4 b3 -s source.mp3 -t source.jpg --workflow-mode audio-to-image:video --trim-frame-start 25 --trim-frame-end 75`: **26 frames / 1.04s**, where 50 are expected.
- patched (with bug 1 also fixed): 50 frames / 2.0s.
- Control runs: patched without a trim gives 95 frames / 3.8s, the full audio.
- master: n/a, there is no audio-to-image workflow.

### Cause
`spawn_frames` writes temp frames numbered from 1, but `merge_video` reads from `-start_number trim_frame_start`. The audio frame lookup in `conditional_get_source_audio_frame` also uses that temp frame number as an absolute index.

Introduced by `1b2fffd8`, `03bbc102`, `9bf9ee40`.

### Suggested diff
Number the spawned frames like `extract_frames` does.

```diff
--- facefusion/ffmpeg.py
+++ facefusion/ffmpeg.py
@@ def spawn_frames(...)
 		ffmpeg_builder.set_media_resolution(vision.pack_resolution(temp_video_resolution)),
+		ffmpeg_builder.set_start_number(trim_frame_start),
 		ffmpeg_builder.set_output(temp_frames_pattern)
```

### Suggested test
Add one assertion to `tests/test_ffmpeg.py` `test_spawn_frames`, inside the loop:

```diff
 		assert len(resolve_temp_frame_paths(state_manager.get_temp_path(), output_path, state_manager.get_item('temp_frame_format'))) == frame_total
+		assert min(resolve_temp_frame_set(state_manager.get_temp_path(), output_path, state_manager.get_item('temp_frame_format'))) == trim_frame_start
```

- v4: fails with `assert 1 == 0`.
- patched: passes.


## 11. Audio-to-image trim: audio track not offset
**[v4-only] · P2 medium** · `facefusion/ffmpeg.py` `replace_audio`

This is a new finding, made while validating bug 3.

### Evidence
The patched run b3 (trim 25-75, so frames and lip-sync audio cover source 1.0-3.0s) has an output audio track that cross-correlates best at a **source offset of 0.0s** (corr 0.43). The audio track therefore starts at 0s while the frames represent 1-3s, which desyncs lip sync.

### Cause
`restore_audio()` sends audio-to-image to `ffmpeg.replace_audio(source_audio_path, output_path)`, which does not apply the trim start to the audio input.

### Suggested diff
Not validated. Give `replace_audio` the trim and apply `ffmpeg_builder.select_media_range(trim_frame_start, trim_frame_end, output_audio_fps)` before `set_input(audio_path)`, the way `restore_audio` does for the target. Only audio-to-image should pass a trim; image-to-video replace_audio keeps the full source audio.

### Suggested test
In `test_audio_to_image.py`, run with trim 25-75 and compare the output audio with `source.mp3` trimmed at 1.0s, by duration and first-chunk samples.


## 7. As-frames mode gets empty source audio/voice
**[v4-only] · P2 medium** · `facefusion/workflows/core.py`

### Evidence
`media/b7.py` (source.mp3, frame 10):

| Mode | v4 | patched |
|------|----|---------|
| `image-to-video` | non-zero `True` | `True` |
| `image-to-video:frames` | `False` (lip_syncer gets silence) | `True` |

master: n/a, there is no `image-to-video:frames` mode.

### Cause
`conditional_get_source_audio_frame` and `conditional_get_source_voice_frame` only cover `audio-to-image:*` and `image-to-video`. Introduced by `1b2fffd8` and extended in `9bf9ee40`.

### Suggested diff
Apply the same change in both functions.

```diff
-	if state_manager.get_item('workflow_mode') in [ 'audio-to-image:frames', 'audio-to-image:video', 'image-to-video' ]:
+	if state_manager.get_item('workflow_mode') in [ 'audio-to-image:frames', 'audio-to-image:video', 'image-to-video', 'image-to-video:frames' ]:
@@
-		if state_manager.get_item('workflow_mode') == 'image-to-video':
+		if state_manager.get_item('workflow_mode') in [ 'image-to-video', 'image-to-video:frames' ]:
```

### Suggested test
`tests/test_workflow.py` `test_conditional_get_source_audio_frame`, after the trim_frame_start 5 block:

```diff
+	state_manager.set_item('workflow_mode', 'image-to-video:frames')
+
+	assert numpy.array_equal(conditional_get_source_audio_frame(10), get_audio_frame(get_test_example_file('source.mp3'), 25, 5)) is True
+
+	state_manager.set_item('workflow_mode', 'image-to-video')
+
```

- v4: fails.
- patched: passes.
- A matching voice-frame assertion needs the kim_vocal model, so it fits the existing voice test setup.


## 5. sanitize_video fails on moov-at-end MP4 over pipe:0
**[v4-only] · P1 high, top bug (API uploads of plain ffmpeg/camera MP4s; fix together with 24)** · `facefusion/ffmpeg.py`, `facefusion/apis/asset_helper.py`

### Evidence
- `media/b5.py`, non-faststart `target-2s-audio.mp4`:
  - strict returns `False`
  - moderate returns `True` but writes a **262-byte file with no streams**. ffmpeg exits 0 after `partial file` / `Error during demuxing`.
- Faststart copy: both strategies work.
- patched (`media/b5_patched.py`): all four combinations return `True` with 50 frames.
- Realistic uploads: `tests/test_api_assets.py` `before_all` builds `target-240p-moov-end.mp4`. It is HEVC with AAC audio, 16s and 4.3 MB, with a 28-byte `ftyp` and `mdat` before a 17.7 KB `moov`. It also builds a `.mov` remux of it, whose `mdat` content starts at offset 36. Through `POST /assets`, both crash with **500** in both strategies; the details are under bug 24.
- The control `target-240p-faststart.mp4` is H.264 with AAC, 22s and 11.7 MB, with `moov` at offset 40. It uploads with 201 (`test_upload_assets_with_faststart`).
- Only a small video-only file (191 KB, stream copy) failed gracefully with 415.
- master: n/a, there is no `sanitize_video`.

### Cause
The mp4 demuxer must seek back to `mdat` after reading `moov`, and pipe:0 is not seekable. Files smaller than ffmpeg's input buffer (about 64 KB) still work.

The existing test hid this in two ways:
- its fixture `target-240p-h265-metadata.mp4` is written with `set_faststart('mp4')`
- that fixture is only 65 KB

Introduced by `5fa08845 FFmpeg powered sanitization, Chunk based upload write`.

### Suggested diff
Spool the upload to disk and give ffmpeg a seekable path.

```diff
--- facefusion/ffmpeg.py
+++ facefusion/ffmpeg.py
-def sanitize_video(file : BinaryIO, asset_path : str, security_strategy : ApiSecurityStrategy) -> bool:
+def sanitize_video(upload_path : str, asset_path : str, security_strategy : ApiSecurityStrategy) -> bool:
 	if security_strategy == 'strict':
 		available_video_encoders = get_static_available_encoder_set().get('video')
 		commands = ffmpeg_builder.chain(
-			ffmpeg_builder.set_input('pipe:0'),
+			ffmpeg_builder.set_input(upload_path),
@@
-		return run_ffmpeg_with_pipe(commands, file).returncode == 0
+		return run_ffmpeg(commands).returncode == 0
 
 	commands = ffmpeg_builder.chain(
-		ffmpeg_builder.set_input('pipe:0'),
+		ffmpeg_builder.set_input(upload_path),
@@
-	return run_ffmpeg_with_pipe(commands, file).returncode == 0
+	return run_ffmpeg(commands).returncode == 0
--- facefusion/apis/asset_helper.py
+++ facefusion/apis/asset_helper.py
+import shutil
@@
-from facefusion.filesystem import create_directory, get_file_extension, get_file_format, is_audio, is_image, is_video
+from facefusion.filesystem import create_directory, get_file_extension, get_file_format, is_audio, is_image, is_video, remove_file
@@
-		if media_type == 'video' and await asyncio.to_thread(ffmpeg.sanitize_video, upload_file.file, asset_path, api_security_strategy):
-			asset_paths.append(asset_path)
+		if media_type == 'video':
+			upload_path = os.path.join(temp_path, asset_file_name + '-upload' + file_extension)
+
+			with open(upload_path, 'wb') as upload_buffer:
+				shutil.copyfileobj(upload_file.file, upload_buffer)
+
+			if await asyncio.to_thread(ffmpeg.sanitize_video, upload_path, asset_path, api_security_strategy):
+				asset_paths.append(asset_path)
+
+			remove_file(upload_path)
```

Two notes on this diff:
- `run_ffmpeg` waits only while processing. That works here because `save_asset_files` calls `process_manager.start()` first. Bug 8 makes this robust in any case.
- Audio has the same pipe limit for containers with the index at the end (m4a/mp4 audio). Consider the same spooling for `sanitize_audio`. That case was not tested.

### Suggested test
`tests/test_ffmpeg.py` `test_sanitize_video`:
- pass paths instead of file objects
- add the existing moov-at-end fixture `target-240p-16khz.mp4` (171 KB, built in before_all without faststart)

```diff
-	with open(file_path, 'rb') as file:
-		assert sanitize_video(file, output_paths[0], 'strict') is True
-		...
+	assert sanitize_video(file_path, output_paths[0], 'strict') is True
+	assert probe_video_entries(output_paths[0], [ 'codec_name' ]).get('codec_name') == 'h264'
+	assert probe_video_entries(output_paths[0], [ 'nb_frames' ]).get('nb_frames') == '270'
+	assert probe_title_tag(output_paths[0]) == {}
+
+	assert sanitize_video(file_path, output_paths[1], 'moderate') is True
+	assert probe_video_entries(output_paths[1], [ 'codec_name' ]).get('codec_name') == 'hevc'
+	assert probe_video_entries(output_paths[1], [ 'nb_frames' ]).get('nb_frames') == '270'
+	assert probe_title_tag(output_paths[1]) == {}
+
+	file_path = get_test_example_file('target-240p-16khz.mp4')
+
+	for security_strategy in [ 'strict', 'moderate' ]:
+		output_path = get_test_output_path('test-sanitize-video-moov-end-' + security_strategy + '.mp4')
+
+		assert sanitize_video(file_path, output_path, security_strategy) is True
+		assert probe_video_entries(output_path, [ 'nb_frames' ]).get('nb_frames') == '270'
```

- v4, in the file-object form with the moov-end fixture: fails.
- patched: passes.
- Also add a non-faststart video upload to the API asset tests (`tests/test_api_assets.py`). Not run here.


## 4. Stale cached metadata of the temp video
**[master+v4] · P1 high (multi-job processes: API, job runner)** · `facefusion/ffmpeg.py`

### Evidence
`media/b4_v4.py` and `media/b4_master.py`: one process, same output path, trims (0, 25) then (25, 100). Expected frames for the second job: 75.

| Tree | Second job |
|------|------------|
| v4 | **25 frames / 1.0s** |
| master | **25 frames / 1.0s** |
| patched | 75 frames / 3.0s |

### Cause
`restore_audio` and `replace_audio` take `temp_video_duration` from `vision.detect_video_duration`, which reads the `lru_cache`d `extract_static_video_metadata` keyed by path. The temp file is rewritten between jobs at the same path. The temp path key is the target name on master and the output name on v4.

### Suggested diff
Temp files are mutable, so probe them uncached. Apply the same change in both `restore_audio` and `replace_audio`.

```diff
-	temp_video_duration = vision.detect_video_duration(temp_video_path)
+	temp_video_duration = ffprobe.extract_video_metadata(temp_video_path).get('duration')
```

On master, port this as the same line in `restore_audio` and `replace_audio`.

### Suggested test
`tests/test_ffmpeg.py` `test_restore_audio`: rerun into the same `test-restore-audio.mp4` with a different trim.

```diff
 	clear_temp_directory(state_manager.get_temp_path(), output_path)
+	create_temp_directory(state_manager.get_temp_path(), output_path)
+	extract_frames(target_path, output_path, (426, 226), 25.0, 50, 150)
+	merge_video(target_path, output_path, 25.0, 25.0, (426, 226), 50, 150)
+
+	assert restore_audio(target_path, output_path, 50, 150) is True
+	assert extract_video_metadata(output_path).get('frame_total') == 100
+
+	clear_temp_directory(state_manager.get_temp_path(), output_path)
```

- v4: fails with `assert 50 == 100`.
- patched: passes.


## 8. run_ffmpeg returns returncode None outside the processing state
**[master+v4] · P2 medium (latent false failures)** · `facefusion/ffmpeg.py`

### Evidence
`media/b8.py`:

| State | v4 and master | patched |
|-------|---------------|---------|
| processing | returncode `0` | `0` |
| after `process_manager.end()` | `None` | `0` |

### Cause
`run_ffmpeg` only waits inside `while process_manager.is_processing()`. Once `prepare_image` (or anything else) has called `end()`, every later helper returns while ffmpeg is still running.

### Suggested diff
```diff
 	if process_manager.is_stopping():
 		process.terminate()
 
+	process.wait()
 	return process
```

Also consider dropping the redundant `process_manager.end()` in `to_image.prepare_image`, since the workflow loop already ends the process on error.

### Suggested test
New `test_run_ffmpeg` in `tests/test_ffmpeg.py`, placed in ffmpeg.py method order after `test_get_available_encoder_set`.

```python
def test_run_ffmpeg() -> None:
	commands = ffmpeg_builder.chain(
		ffmpeg_builder.set_input(get_test_example_file('source.mp3')),
		ffmpeg_builder.force_output(get_test_output_path('test-run-ffmpeg.wav'))
	)
	process_manager.end()

	assert ffmpeg.run_ffmpeg(commands).returncode == 0

	process_manager.start()
```

- v4: fails with `assert None == 0`. Because the assertion fails before `start()` runs again, the rest of the module cascades into failures on v4.
- patched: passes.


## 6. Missing output directory raises instead of returning an error code
**[master+v4] · P3 low** · `facefusion/filesystem.py`

### Evidence
- CLI (b6): blocked by pre_check on both trees ("specify the output image or video within a directory!", exit=1).
- `media/b6.py` (direct `to_video.restore_audio()`): v4 and master both raise `FileNotFoundError`. patched returns `0`, and `finalize_video` then reports error 1.

### Cause
`move_temp_file` calls `move_file`, which calls `shutil.move` into a directory that does not exist. Reachable when the directory disappears mid-run, or through a caller that skips pre_check.

### Suggested diff
```diff
 def move_file(file_path : str, move_path : str) -> bool:
-	if is_file(file_path):
+	if is_file(file_path) and is_directory(os.path.dirname(os.path.abspath(move_path))):
```

### Suggested test
`tests/test_filesystem.py` `test_move_file`:

```diff
 	assert move_file(file_path, output_path) is False
+	assert move_file(output_path, get_test_output_path('invalid/test-move-file-moved.jpg')) is False
+	assert is_file(output_path) is True
```

- v4: fails with `FileNotFoundError`.
- patched: passes.


## 10. Negative reference frame index desyncs the shared reader
**[master+v4] · P3 low (bad input)** · `facefusion/video_manager.py`

### Evidence
`media/b10.py`: `read_video_frame(path, -5)` then `read_video_frame(path, 10)`.

| Tree | Second read returns |
|------|---------------------|
| v4 | **about frame 15** (offset +5) |
| master | **about frame 15** (offset +5) |
| patched | frame 10 |

### Cause
The arg is `type = int` with no lower bound (`--reference-frame-index` on v4, `--reference-frame-number` on master). `conditional_seek_video_reader` only clamps the upper bound. ffmpeg `-ss -0.2` starts at 0, while the reader records frame -5. On v4 the option was only renamed, in `161aec62`.

### Suggested diff
Clamp at the reader, which protects every caller. Optionally also bound the CLI/API arg at 0.

```diff
-	frame_index = min(frame_total - 1, frame_index)
+	frame_index = max(0, min(frame_total - 1, frame_index))
```

### Suggested test
`tests/test_video_manager.py` `test_conditional_seek_video_reader`, before the 1000 case:

```diff
+	conditional_seek_video_reader(video_reader, -5)
+
+	assert video_reader.get('frame_index') == 0
+	assert numpy.array_equal(read_video_frame(video_reader), video_frames.get(0)) is True
+
 	conditional_seek_video_reader(video_reader, 1000)
```

- v4: fails.
- patched: passes.


## 9. voice_extractor runs without a processor needing it
**[master+v4] · won't fix (by design)** · `facefusion/workflows/core.py`

### Evidence
With face_debugger only, `kim_vocal_2` loads in all three runs:
- master `image-to-video -s source.jpg source.mp3` (b9)
- v4 `image-to-video` with the same sources (b9i2v)
- v4 `audio-to-image:video` (b9)

### Decision
`voice_extractor` is a common module of every processor. The earlier choice (2026-09-13, master) was to declare it in every processor's `get_common_modules()`; a workflow-level gate in `workflows/core.py` was rejected. v4 already lists `voice_extractor` in all 11 processors.

No change; this entry is listed only for completeness.


---

# Added from the 95% coverage push

These entries have not been through the patched-copy validation. The suggested diffs are a starting point.

Repro scripts are in `regress/new/`.


## 16. Dead /stream websocket stays in the store and crashes the session sweeper
**[v4-only] · P1 high** · `facefusion/apis/endpoints/stream.py`

### Evidence
The coverage agent for apis reproduced it and then removed the test, because the crash takes down the sweeper thread during the test run.

What happens:
1. A send to the client fails, and `process_image` raises.
2. `websocket_store.delete_websocket` never runs, so the dead websocket stays in the store.
3. When the session expires, the sweeper calls `websocket_store.destroy`, which raises `RunFinishedError` on the closed websocket.
4. The sweeper thread dies, so sessions stop expiring.

### Cause
```python
await websocket.accept(subprotocol = subprotocol)
websocket_store.set_websocket(websocket)
await process_image(websocket)
websocket_store.delete_websocket(websocket)
```
The delete only runs on the success path.

### Suggested diff
The project avoids `try` blocks, so there are two options:
- Make `websocket_store.destroy` skip websockets whose `client_state` is not `CONNECTED`, so a stale entry cannot raise.
- Or wrap the call in `try`/`finally` so `delete_websocket` always runs.

The first keeps to the code style and also protects against any other path that leaves a stale entry.

### Suggested test
`tests/test_api_stream.py`: open `/stream`, make the send fail, then expire the session. Assert that the websocket store for the session is empty and that the sweeper thread is still alive.


## 12. `--log-level debug` closes ffmpeg stdout and encoder detection crashes
**[master+v4] · P2 medium** · `facefusion/ffmpeg.py`

### Evidence
`regress/new/b12.py` calls `get_available_encoder_set()` with `log_level = debug`:

| Tree | Result |
|------|--------|
| v4 | `ValueError: readline of closed file` |
| master | `ValueError: readline of closed file` |

On v4 this reaches the asset sanitizing path (for example `api --log-level debug`) while the encoder cache is still cold.

The same thing happens in `concat_video`: it calls `process.communicate()` on the process that `run_ffmpeg` returns. In debug mode `log_debug` has already called `communicate()` and closed the pipes, so this second call reads nothing. The fix below covers both callers.

### Cause
`run_ffmpeg` calls `log_debug(process)`, and `log_debug` calls `process.communicate()`. That reads stdout to the end and closes it. Any caller that reads `process.stdout` afterwards, like `get_available_encoder_set`, then fails.

### Suggested diff
`log_debug` should read only stderr and leave stdout to the caller.
```diff
 def log_debug(process : subprocess.Popen[Buffer]) -> None:
-	_, stderr = process.communicate()
-	errors = stderr.decode().splitlines()
+	errors = process.stderr.read().decode().splitlines()
```
Check for a pipe deadlock on commands with large stdout. If that is a risk, move the `log_debug` call after the caller has drained stdout.

### Suggested test
`tests/test_ffmpeg.py` `test_get_available_encoder_set`: set `log_level` to `debug`, call it, and assert that `libx264` is in the `video` list. Reset the log level afterwards.


## 15. AV1 decode uses the padded frame size
**[v4-only] · P2 medium** · `facefusion/codecs/aom_decoder.py`

### Evidence
A 426x226 frame decodes as 432x232, with junk pixels at the right and bottom edges.

### Cause
```python
frame_width = ctypes.c_uint.from_address(address + 28).value & ~1
frame_height = ctypes.c_uint.from_address(address + 32).value & ~1
```
Offsets 28 and 32 hold the aligned (padded) size of `aom_image_t`. The display size `d_w` and `d_h` is at offsets 40 and 44.

### Suggested diff
```diff
-				frame_width = ctypes.c_uint.from_address(address + 28).value & ~1
-				frame_height = ctypes.c_uint.from_address(address + 32).value & ~1
+				frame_width = ctypes.c_uint.from_address(address + 40).value & ~1
+				frame_height = ctypes.c_uint.from_address(address + 44).value & ~1
```
Check that `collect` still reads rows with the correct stride, which stays the padded width.

### Suggested test
`tests/test_codec_aom_decoder.py`: encode a 426x226 frame, decode it, and assert that the resolution is `(426, 226)` and that the decoded frame is close to the input.


## 17. VP8 resolution growth fails silently
**[v4-only] · P2 medium** · `facefusion/codecs/vpx_encoder.py`, `facefusion/apis/stream_video.py`

### Evidence
Found by the apis coverage agent: `vpx_encoder.update_resolution` returns False once the resolution grows past the size the encoder was created with.

### Cause
- `update_resolution` writes the new width and height into the config with `struct.pack_into` before calling `vpx_codec_enc_config_set`. On failure, the config already holds the new size.
- `run_video_encode_loop` ignores the return value and sets `temp_resolution` anyway, so it never tries again.

### Suggested diff
- In `run_video_encode_loop`, only take the new `temp_resolution` when `update_video_encoder_resolution` returns True. When it returns False, destroy the encoder and create a new one at the new size.
- In `update_resolution`, restore the previous width and height when `vpx_codec_enc_config_set` fails.

### Suggested test
`tests/test_codec_vpx_encoder.py`: create a vp8 encoder at 320x240. Assert that `update_resolution` to 640x480 either returns True, or returns False and leaves the config at 320x240. Then assert that encoding a 640x480 frame through the loop produces a non-empty buffer.


## 13. A jobs path that is a file raises NotADirectoryError
**[master+v4] · P3 low** · `facefusion/jobs/job_manager.py`

### Evidence
`regress/new/b13.py` calls `init_jobs` with a path to an existing file:

| Tree | Result |
|------|--------|
| v4 | raises `NotADirectoryError` |
| master | raises `NotADirectoryError` |

The `hard_exit(1)` branches in `core.py` that expect `init_jobs` to return False only work when a status directory, not the jobs path itself, is blocked by a file.

### Cause
`create_directory(os.path.join(jobs_path, job_status))` only checks whether the leaf path is a file. `os.makedirs` then fails on the parent, which is a file.

### Suggested diff
```diff
 def create_directory(directory_path : str) -> bool:
-	if directory_path and not is_file(directory_path):
+	if directory_path and not is_file(directory_path) and not is_file(os.path.dirname(directory_path)):
```
A more thorough option is to walk all parents, or to bail out in `init_jobs` when `is_file(jobs_path)`.

### Suggested test
`tests/test_job_manager.py` `test_init_jobs`: create a file, pass its path as `jobs_path`, and assert that `init_jobs` returns False.


## 14. An already stopped run leaves ffmpeg running
**[master+v4] · P3 low** · `facefusion/ffmpeg.py`

### Evidence
`regress/new/b14.py` calls `process_manager.stop()`, then runs a 30s realtime `testsrc` through `run_ffmpeg_with_progress`:

| Tree | ffmpeg still running 2s after return |
|------|--------------------------------------|
| v4 | yes |
| master | yes |

### Cause
`run_ffmpeg_with_progress` only handles stopping inside `while process_manager.is_processing()`. When it is called after the process has already been stopped, the loop never runs and the function returns with ffmpeg still running. `run_ffmpeg` has the extra `if process_manager.is_stopping(): process.terminate()` after the loop; this function does not.

### Suggested diff
```diff
 		except subprocess.TimeoutExpired:
 			continue
 		return process
 
+	if process_manager.is_stopping():
+		process.terminate()
+
 	return process
```

### Suggested test
`tests/test_ffmpeg.py`: call `process_manager.stop()`, then run a long `testsrc` command through `run_ffmpeg_with_progress`. Assert that `process.wait(timeout = 5)` returns, meaning ffmpeg was terminated. Call `process_manager.end()` afterwards.


## 18. create_sdp_offer / create_sdp_answer never return None
**[v4-only] · P3 low** · `facefusion/rtc.py`

### Evidence
Found by the apis coverage agent. On failure, `rtcGetLocalDescription` returns a negative error code, which is truthy. The functions then return `''` instead of None, so `rtc.py` lines 28 and 40 can never run.

### Cause
```python
if datachannel_library.rtcGetLocalDescription(peer_connection, sdp_buffer, 8192):
```

### Suggested diff
```diff
-	if datachannel_library.rtcGetLocalDescription(peer_connection, sdp_buffer, 8192):
+	if datachannel_library.rtcGetLocalDescription(peer_connection, sdp_buffer, 8192) > 0:
```
Apply the same change in both functions.

### Suggested test
`tests/test_rtc.py`: call `create_sdp_offer` with a peer connection that has already been closed, and assert that it returns None.


## 19. image-to-video:frames ignores output_video_scale
**[v4-only] · P2 medium** · `facefusion/workflows/as_frames.py`

### Evidence
Found by the processor coverage agent with `frame_enhancer` on `target-240p.mp4`:

| Mode | Output resolution |
|------|-------------------|
| `image-to-video` | 426x226 |
| `image-to-video:frames` | 1704x904 (the processor's own 4x resolution) |

Master has no frames mode.

### Cause
In `image-to-video`, scaling to the output resolution happens in `ffmpeg.merge_video`, which gets `conditional_scale_resolution()`. In `image-to-video:frames`, `copy_temp_frames` copies the processed temp frames into `output_path` unchanged. Any processor that changes the frame size, like `frame_enhancer`, therefore decides the output size, and `--output-video-scale` has no effect.

### Suggested diff
Before copying, resize each temp frame to `conditional_scale_resolution()` when the sizes differ. This is the same approach `process_memory_frame` uses in `to_video.py`. Alternatively, do the scaling as an ffmpeg step when finalizing the frames.

### Suggested test
`tests/test_image_to_video_as_frames.py`: run with `frame_enhancer` and `output_video_scale` 1.0. Assert that every output frame is 426x226, the same as `image-to-video` produces.


## 20. Mismatched --workflow-mode exits 1 without an error message
**[master+v4] · P3 low (bad input)** · `facefusion/core.py`

### Evidence
`--workflow-mode image-to-image` with a video target (`target-240p.mp4`), processor `face_debugger`:

| Tree | Command | Exit | Last log line |
|------|---------|------|---------------|
| v4 | `run` | 1 | `[FACEFUSION.CORE] processing step 1 of 1` |
| master | `headless-run` | 1 | `[FACEFUSION.CORE] processing step 1 of 1` |

Logs are in `regress/new/b20-v4.log` and `regress/new/b20-master.log`. The run never reaches the processors' own checks, so a source that doesn't fit the mode (for example face_swapper's "choose an image for the source") is never reported either.

### Cause
`conditional_process` only runs the workflow when `workflow_mode == detect_workflow_mode()`. Otherwise it falls through to `return 2` without logging anything. The code is the same on both trees.

### Suggested diff
Log an error on the mismatch path, naming the requested mode and the detected one, with a new translator key such as `workflow_mode_mismatch`. Optionally, validate the combination in `pre_check` so the error appears before the job starts.

### Suggested test
`tests/test_core.py`: run the CLI with `--workflow-mode image-to-image` and a video target. Assert exit code 1 and that stderr contains the new error message.


## 21. init() resets an existing session entry
**[v4-only] · P2 medium** · `facefusion/store_creator.py`

### Evidence
`tests/test_store_creator.py::test_init_content_with_existing_content`: after `init_content(store, 'session-a')`, change the entry, then call `init_content` again. The entry is back to the template.

### Cause
```python
def init_content(store : Store, session_id : SessionId) -> None:
	store['content_set'][session_id] = deepcopy(store.get('__init__'))
```
The agreed store contract (2026-09-12) is:
- `init()` creates the entry only when it is missing.
- `clear()` forces the template.

v4 has no `reset_content`, so `init()` and `clear()` behave the same. A second `process_manager.init()` on a running session turns `processing` into `pending`, and `is_process_stopping()` reads that as "stop". A second `rtc_store.init()` drops a live peer without deleting it.

### Suggested diff
```diff
 def init_content(store : Store, session_id : SessionId) -> None:
-	store['content_set'][session_id] = deepcopy(store.get('__init__'))
+	if not has_content(store, session_id):
+		store['content_set'][session_id] = deepcopy(store.get('__init__'))
+
+
+def reset_content(store : Store, session_id : SessionId) -> None:
+	store['content_set'][session_id] = deepcopy(store.get('__init__'))
```
The store modules' `clear()` then calls `reset_content`. Fixtures that reset with `init()` need to switch to `clear()`.


## 22. A failed download leaves the process in "checking"
**[master+v4] · P2 medium** · `facefusion/download.py`

### Evidence
`regress/runtime/bug3.py` gives the same result on both trees:
- `conditional_download_hashes` returns False with `checking = True`.
- `conditional_download_sources` returns False with `checking = True`.
- `get_inference_pool` is still blocked after 3s.

On master the process state is global, so the whole process hangs. On v4 only that session hangs, which matters for the API.

### Cause
Both functions call `process_manager.check()` at the start, but `process_manager.end()` only on success:
```python
if not invalid_hash_paths:
	process_manager.end()
return not invalid_hash_paths
```

### Suggested diff
```diff
-	if not invalid_hash_paths:
-		process_manager.end()
+	process_manager.end()
 	return not invalid_hash_paths
```
Make the same change in `conditional_download_sources`.

### Tests
`tests/test_download.py::test_conditional_download_hashes_with_invalid_hash` and `test_conditional_download_sources_with_invalid_source`.


## 23. HTTP error body is saved as the downloaded file
**[master+v4] · P3 low** · `facefusion/curl_builder.py`, `facefusion/download.py`

### Evidence
- `examples-3.0.0/target-240p.jpg` does not exist on the assets release. `conditional_download` saved the 404 body as a 9-byte file containing `Not Found`.
- A test `before_all` that listed this URL broke `test_copy_image`, `test_finalize_image` and three `test_workflow` tests whenever `test_ffmpeg.py` ran before the modules that generate the file with ffmpeg. The fixture now generates the file with ffmpeg too.
- `curl_builder.run` is the same on master.

### Cause
`curl_builder.run` does not pass `--fail`, so curl writes the error page to `--output`. `get_static_download_size` returns the error page's Content-Length (9). The size check then counts the download as complete.

Model downloads are protected, because their `.hash` validation fails and the file is removed. Anything downloaded without a hash is not.

### Suggested diff
```diff
-	return [ shutil.which('curl'), '--user-agent', user_agent, '--location', '--silent', '--ssl-no-revoke' ] + commands
+	return [ shutil.which('curl'), '--user-agent', user_agent, '--location', '--silent', '--fail', '--ssl-no-revoke' ] + commands
```
Also consider having `get_static_download_size` return 0 for non-2xx responses.

### Test
`tests/test_download.py::test_conditional_download_with_missing_url`.


## 24. Uploads with the index at the end crash with 500
**[v4-only] · P1 high, top bug (fix together with 5)** · `facefusion/apis/asset_store.py`, `facefusion/ffprobe.py`, `facefusion/ffmpeg.py` (`sanitize_video`, `sanitize_audio`)

### Evidence
Through the API in-process, `POST /assets`. The fixtures are built in `tests/test_api_assets.py` `before_all`:

| Upload | Layout | strict | moderate |
|--------|--------|--------|----------|
| `target-240p-faststart.mp4` (H.264 + AAC, 11.7 MB) | `moov` first | 201 | 201 |
| `target-240p-moov-end.mp4` (HEVC + AAC, 4.3 MB) | `mdat`, then `moov` at the end | **500** | **500** |
| `target-240p-moov-end.mov` (remux of the mp4) | `mdat` content at offset 36, then `moov` at the end | **500** | **500** |
| `source-moov-end.m4a` (AAC, 170 KB) | `mdat`, then `moov` at the end | **500** | **500** |

Piping the moov-at-end mp4 or mov into ffmpeg (`-i pipe:0`) logs `partial file`, exits **0**, and writes a file whose `format=duration` is `N/A`.

Traceback, video:
```
facefusion/apis/endpoints/assets.py:107  upload_assets -> asset_store.create_asset(asset_type, asset_path)
facefusion/apis/asset_store.py:72        create_asset -> extract_video_metadata(asset_path)
facefusion/ffprobe.py:102                ValueError: could not convert string to float: 'N/A'
```
Traceback, audio:
```
facefusion/apis/asset_store.py:42        create_asset -> extract_audio_metadata(asset_path)
facefusion/ffprobe.py:75                 ValueError: could not convert string to float: 'N/A'
```

### Cause
Two problems combine:
1. **Bug 5.** `sanitize_video` and `sanitize_audio` read the upload through `pipe:0`, and with the index at the end ffmpeg cannot seek back. ffmpeg still exits 0, so the sanitizer returns True and leaves a broken asset.
2. **Unguarded parsing.** `extract_video_metadata` and `extract_audio_metadata` convert ffprobe entries without checking them. `create_asset` therefore raises instead of returning None, which would give a 415. The exception middleware does not handle `ValueError`, so the client gets a 500. The same unguarded conversions exist on master, but there they are only reached with local files.

### Suggested fix
- Write the upload to a temp file and pass ffmpeg the path, as in bug 5. This makes these uploads work.
- Make the metadata readers return None when an entry is missing or `N/A`, and have `create_asset` return None. Any other broken asset then gives a graceful 415 instead of a 500.
- Optionally, have the sanitizers check the output (for example a non-empty duration) instead of trusting ffmpeg's exit code.

### Tests
- `tests/test_api_assets.py::test_upload_assets_with_moov_at_end` (mp4 and mov, both strategies; strict xfail, `raises = ValueError`)
- `tests/test_api_assets.py::test_upload_assets_with_moov_at_end_audio` (m4a, both strategies; strict xfail, `raises = ValueError`)
- Control: `tests/test_api_assets.py::test_upload_assets_with_faststart` (passes)

If only the crash is guarded, both xfail tests fail with an `AssertionError` (415), so `raises` keeps them from staying hidden. Once spooling lands, they pass.
