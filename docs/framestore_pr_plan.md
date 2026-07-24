# FrameStore — Implementation Plan (small PRs)

Branch: `feat/frame-store` off `next`. Each PR is small, independently green (pytest + flake8 + mypy), and mutation-verified (mutate the production line, confirm a test fails).

Guiding rule: **the store is a pure cache** — it holds frames, reports hits/misses, evicts. It never decodes. `video_manager` orchestrates: on a miss it decodes via a reader and stores the frame. This keeps `frame_store` ffmpeg-free and unit-testable in isolation.

---

## PR 1 — `frame_store` module (pure cache, unused)

**Goal:** land the store in isolation, no app behavior change.

**Changes**
- New `facefusion/frame_store.py`. Keyed by `source` (file_path for now), then `frame_number`.
- Functions: `get_frame_store`, `store_frame`, `read_frame_range`, `evict_frames`, `clear_frame_store`.
- `read_frame_range(source, start, end)` returns the cached frames in range; `evict_frames` drops frames outside the live range.
- Types in `types.py`: `FrameStore`, `FrameStoreSet`.

**Tests** — `tests/test_frame_store.py` (no ffmpeg, pure/fast)
- `test_store_frame` — stored frame is retrievable.
- `test_read_frame_range` — returns exactly the cached numbers in `[start, end]`, gaps reported/absent.
- `test_read_frame_range_overlap` — second overlapping range reuses already-stored frames (same object, no duplicate store).
- `test_evict_frames` — frames outside the live range are dropped, inside are kept.
- `test_clear_frame_store` — empties the store.

**Merge bar:** unit tests green + mutation-verified; module unused elsewhere.

---

## PR 2 — window read via the store; drop `frame_set` from the reader

**Goal:** `read_video_reader_window` uses `frame_store` instead of the reader's inline cache.

**Changes**
- `read_video_reader_window` becomes an orchestrator: ask the store for the range, decode misses via the reader, `store_frame`, return the range.
- Remove `frame_set` from `VideoReader` (types) and from `get_reader`/`refresh_video_reader`.
- `clear_video_pool` also calls `clear_frame_store`.

**Tests** — update `tests/test_video_manager.py`
- Keep `test_read_video_reader_window` (range correctness) and `test_evict_video_reader_buffer` (rewired to the store) — must stay green.
- Add `test_read_video_reader_window_reuse` — reading `[0,4]` then `[2,6]` decodes `2,3,4` only once (assert via frame identity / a decode spy).
- Strengthen assertions (Henry's note) — drop the `question if the assertions are good` todos on the tests reworked here.

**Merge bar:** `video_manager`-contained; green + mutation-verified.

---

## PR 3 — chunk read via the store; delete the lru cache + 11 `cache_clear()` lines

**Goal:** collapse the second cache into the store.

**Changes**
- `read_video_chunk` (vision) becomes a store range read (thin caller of the same primitive as the window read).
- Remove the `lru_cache` on `read_static_video_chunk`.
- Delete the 11 processor `read_static_video_chunk.cache_clear()` lines — the store clears via `clear_video_pool()`, which each processor already calls next to it.

**Tests**
- `tests/test_vision.py` chunk tests — chunk range correctness preserved; add a reuse assertion shared with the window path.
- Sanity: a processor teardown still clears frames (one integration assertion that the store is empty after `clear_video_pool`).

**Merge bar:** wide but shallow (deletions only in processors); full suite green.

---

## PR 4 — dumb readers, simplify the seek heuristics

**Goal:** now that the store owns caching, shrink the single-cursor seek dance.

**Changes**
- Simplify/retire `conditional_set_video_reader_position` skip-margin + `refresh` coupling where the store now covers reuse.
- Reader settles to `{process, file_path, metadata, position}`.

**Tests**
- Keep the process-identity proof test (forward-skip keeps the process, out-of-range refresh kills it → `returncode == -9`).
- Adjust for any retired functions; mutation-verify the remaining seek path.

**Merge bar:** `video_manager`-contained; green.

---

## PR 5 — (deferred) id-keyed multiple readers

**Goal:** multiple independent cursors per file → kill seek thrash for good.

**Decision required first:** do we actually want multiplicity? Adds id-keyed pools + lifecycle sync (fights "avoid globals"). Only do it if phase-4 seek behavior is still a real bottleneck.

**Tests:** two readers on one file advance independently; store overlap dedups across them.

---

## PR A — (independent, parallel) writer metadata fix

Not part of the store, but Henry's earlier review still stands and it can merge on its own.

**Changes**
- `VideoWriterMetadata` (`temp_video_fps`, `temp_video_resolution`, `output_video_resolution`, `output_video_fps`).
- `VideoWriter = {process, file_path, metadata: VideoWriterMetadata}`; drop the target-metadata (`ffprobe`) transfer.
- `get_writer(target_path, video_writer_metadata)`; update the one caller.

**Tests**
- `test_get_writer` — asserts `file_path` and `metadata` are stored (self-describing) + pooling identity.

**Merge bar:** green; independent of the store PRs.

---

## Order & sequencing
1. **PR 1** (store, isolated) — safest first.
2. **PR 2** (window) and **PR 3** (chunk) — after PR 1; sequence PR 2 → PR 3.
3. **PR 4** (dumb readers) — after 2 and 3.
4. **PR 5** — only if multiplicity is confirmed.
5. **PR A** (writer) — anytime, independent.

Each PR: never commit without request; run `flake8 facefusion tests`, `mypy facefusion.py install.py`, and `pytest` before marking done.
