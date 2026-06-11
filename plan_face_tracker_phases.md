# Face Tracker — Phased Roadmap

Companion to `plan_face_tracker.md` (full design). This file tracks the phases,
their deliverables, acceptance criteria, and status.

Goal recap: assign a **persistent identity (track id) to each face across
frames** with a ByteTrack-style Kalman + IoU tracker. **Identity association,
not stabilization** — geometry that drives the warp is never rewritten. Default
**off**; zero behaviour change until enabled.

| Phase | Scope | Status |
|---|---|---|
| 1 | Tracker core (Kalman + IoU + association) + unit tests | ✅ done |
| 2 | Video `many` mode: sequential pre-pass + track-stable ordering | ⬜ planned |
| 3 | Hybrid IoU + embedding cost; `reference` gap-bridging | ⬜ planned |
| 4 | Stream integration (sequential read-loop association) | ⬜ planned |

---

## Phase 1 — Tracker core ✅

**Done.** Pure, self-contained, no pipeline wiring (nothing imports it yet).

Delivered:
- `facefusion/types.py` — `Measurement`, `Mean`, `Covariance`, `TrackState`
  aliases + `Track` namedtuple (`track_id`, `mean`, `covariance`, `state`,
  `hit_streak`, `time_since_update`).
- `facefusion/face_tracker.py` — de-classed ByteTrack:
  - Kalman as functions: `kalman_initiate`, `kalman_predict`, `kalman_project`,
    `kalman_update` (`MOTION_MATRIX` / `UPDATE_MATRIX` module constants).
  - `bounding_box_to_measurement` / `measurement_to_bounding_box`,
    `calculate_iou`, `iou_distance`.
  - `associate` (`scipy.optimize.linear_sum_assignment` + distance gate).
  - `update_tracks(detection_bounding_boxes, iou_threshold = 0.2, track_buffer = 30)`
    → stable `track_id` per detection in input order.
  - State `TRACK_STATE` / `TRACK_ID_COUNTER` mutated in place + `clear_tracks()`.
- `tests/test_face_tracker.py` — 8 pure-math tests (no models/downloads).

Acceptance (met):
- 8/8 pass, `flake8 facefusion/face_tracker.py tests/test_face_tracker.py` clean.
- Mutation-validated: removing prediction breaks the occlusion test; removing the
  distance gate breaks the reject test.
- CLAUDE.md: no classes / no global rebinds / no `else`·`continue`·`break`·`try`,
  typed, tabs/AllMan, one-line imports.

---

## Phase 2 — Video `many` mode ⬜

Wire the core into the video path **without** losing parallelism, by separating
tracking (sequential) from processing (parallel).

Scope:
- `facefusion/face_tracker.py` — add the frame store + helpers:
  - `TRACK_STORE : Dict[str, List[Tuple[int, BoundingBox]]]` keyed by
    `create_hash(vision_frame.tobytes())` (mirrors `face_store`).
  - `assign_frame_tracks(vision_frame, faces)` — pre-pass entry; pulls boxes off
    faces, `update_tracks`, stores `{hash: [(track_id, bounding_box)]}`.
  - `lookup_frame_tracks(vision_frame)` — O(1) retrieval; `clear_tracks()` also
    clears `TRACK_STORE`.
- `facefusion/workflows/image_to_video.py` (~line 80) — sequential
  `build_face_tracks(temp_frame_paths)` **before** the `ThreadPoolExecutor` loop
  (read in order → `get_many_faces` → `assign_frame_tracks`). Processing loop
  unchanged.
- `facefusion/face_selector.py` — `order_faces_by_track(target_vision_frame, target_faces)`:
  IoU-attach this frame's detections to stored `(track_id, box)`, order faces by
  **track id** (first-seen order still set by `face_selector_order`); lookup miss
  → current spatial sort (graceful fallback). Guard with `face_tracking` toggle.
- `facefusion/core.py` lifecycle — call `clear_tracks()` beside `clear_faces()`.
- Config surface: `face_tracking` toggle in state / `choices.py` / program args
  (default off; argparse `type`/`choices` per the security rule).

Acceptance:
- On a multi-face moving clip, count id flips (slot changes for the same person)
  with tracking on vs off → measurable reduction; document the number.
- Tracking off ⇒ byte-for-byte identical output to current `master`.
- New tests: `test_assign_frame_tracks`, `test_lookup_frame_tracks`,
  `test_order_faces_by_track_is_stable` (two faces swap spatial order, keep
  slots). Mutation-validate the ordering. `flake8` clean.

Risk: double detection (pre-pass + processing). Mitigate with cheapest pre-pass
detector settings; `TRACK_STORE` holds only ids+boxes (tiny memory, respects the
`dbf4346f` target-cache removal). Optional single-detection variant deferred.

---

## Phase 3 — Hybrid cost + `reference` ⬜

Make association robust to fast motion / appearance changes and extend continuity
to `reference` mode.

Scope:
- `facefusion/face_tracker.py` — blend cost = IoU distance ⊕ embedding distance
  (`1 - cosine` on `Face.embedding_norm`, already computed). IoU dominates;
  embedding breaks ties and survives motion blur where IoU is ambiguous. Extend
  `Track` with an `embedding` field; thread embeddings through
  `update_tracks` / `assign_frame_tracks`.
- `facefusion/face_selector.py` — `reference` mode: when the reference face's
  track id is known, follow that id through detection gaps even when
  `compare_faces()` would momentarily drop it.
- Config: `face_tracking_iou_threshold`, `face_tracking_embedding_distance`,
  `face_tracking_buffer` (range-validated args).

Acceptance:
- On a blur/profile-turn clip, `reference` mode holds the target through frames
  where pure-embedding matching drops it → measurable continuity gain.
- Tests: `test_update_tracks_hybrid_breaks_tie`,
  `test_reference_bridges_embedding_dropout`. Mutation-validated. `flake8` clean.

---

## Phase 4 — Streams ⬜

Bring the same association to the live pipeline, where no pre-pass is possible.

Scope:
- `facefusion/streamer.py` (~line 26) — sequential detect + `assign_frame_tracks`
  in the read loop, **before** `executor.submit`; processing stays parallel.
  `select_faces()` lookup path is identical to video.
- Bound `TRACK_STORE` growth for long-running streams (evict by frame age /
  ring-buffer of recent hashes).

Acceptance:
- Webcam/stream `many` mode keeps stable ids across movement; no unbounded memory
  growth over a long session.
- Tests for the eviction/bounding helper. `flake8` clean.

---

## Cross-cutting

- **Threading invariant**: tracking is always computed in frame order (pre-pass
  for video, read loop for streams); the parallel processing pass only *reads*
  precomputed assignments by frame hash. This is what lets us add tracking
  without forcing single-threaded execution.
- **Non-goals**: not smoothing; little value on single near-stationary
  talking-heads — value scales with motion + multiple faces + occlusion.
- **Validation discipline (every phase)**: mutate production, confirm a test
  catches it, revert; keep `flake8 facefusion tests` clean.
