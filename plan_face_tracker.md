# Face Tracker — Implementation Plan

## Goal

Assign a **persistent identity (track id) to each face across video/stream
frames** using a **ByteTrack-style Kalman + IoU tracker**, so that the same
physical person keeps the same slot frame-to-frame. This is **identity
association / tracking** — explicitly **NOT a stabilizer / smoother**. We do not
touch the geometry that drives the warp (`bounding_box`, `landmark_set`); we only
decide *which detection is whom*.

## Why — the gap this fills

`facefusion/face_selector.py:select_faces()` treats **every frame
independently**. There is no link between a face in frame N and frame N-1:

- **`many` mode** (`face_selector.py:16`) re-orders faces every frame via
  `sort_faces_by_order()` (spatial: left-right / large-small / …). When two
  people cross, or detector order flickers, the spatial slot a face occupies
  changes → each processor's `for target_face in target_faces` loop
  (`face_swapper/core.py:777`) applies the **wrong source to the wrong person**
  for those frames → visible swap-flicker.
- **`reference` mode** matches by **embedding distance only**
  (`compare_faces()`, `calculate_face_distance()` → `1 - cosine`). It has no
  continuity, so it drops the target on motion blur / profile turns / brief
  occlusion, and can latch onto a look-alike.

A Kalman+IoU tracker provides a **stable track id** that:
1. fixes `many`-mode slot assignment (each track keeps its index), and
2. **bridges short detection gaps** (flicker / occlusion) so a target is not
   lost or re-assigned for a few frames.

## Use cases (where it earns its keep)

| Scenario | Benefit |
|---|---|
| `many` mode, multiple people moving / crossing | stable source→person mapping, no swap-flicker |
| 1–2 frame detector dropouts (flicker) | predicted box holds the target, swap does not blink off |
| short occlusion with a *moving* subject | re-associates the same id on reappearance |
| `reference` mode robustness | hybrid IoU + embedding survives blur where pure-embedding fails |

## Non-goals (be honest about scope)

- **Not** jitter smoothing — that is the One Euro work (`plan_face_stabilizer.md`),
  a separate concern. The tracker never rewrites `bounding_box` / `landmark_set`
  used for warping; it only orders/labels faces.
- **Single talking-head footage gains little** — when the face barely moves, the
  existing per-frame selection already matches it (measured: all 21 sample clips
  in `~/Videos/samples` have near-stationary faces). Tracking value scales with
  motion + multiple faces + occlusion. Default **off**, zero behaviour change.

## Hard constraints from `.claude/CLAUDE.md`

- **No classes** — ByteTrack ships `KalmanFilter`/`STrack` as classes. Re-express
  as pure functions + explicit state (a `Track` namedtuple, like `Face`).
- **Avoid globals** — cross-frame state uses one module-level store with a
  `clear_*()` reset, mirroring `face_store.FACE_STORE` (`face_store.py:8`).
- **No `re`, no nested `def`, no `else` where an exact `if` works, no
  `continue`/`break`, avoid `try`, no `!=`/`is not None` in asserts.**
- **Always type; speaking singular `TypeAlias`; AllMan; one-line imports.**
- `scipy` is already a dependency (`audio.py:5`) → use `scipy.linalg` (Kalman)
  and `scipy.optimize.linear_sum_assignment` (assignment). `numpy` everywhere.

## Architecture — the key decision

The processing pass is **parallel and out-of-order** (`image_to_video.py:81`
`ThreadPoolExecutor` + `as_completed`). A causal tracker **cannot** run inside
`select_faces()` there. Instead of forcing single-thread (the stabilizer's
fallback), decouple tracking from processing:

```
        ┌─ SEQUENTIAL pre-pass (frame order) ─────────────┐
target  │ detect → kalman+IoU track → assign track_id     │   builds
frames ─┤ store {track_id, bounding_box} keyed by         │── TRACK_STORE
        │ create_hash(frame.tobytes())                    │   (boxes+ids only)
        └─────────────────────────────────────────────────┘
                              │
        ┌─ PARALLEL pass (unchanged, out-of-order) ───────┐
        │ select_faces() hashes target_vision_frame,      │   stable
        │ looks up TRACK_STORE, IoU-attaches track_id to   │── ordering /
        │ this frame's detections, orders by track_id      │   assignment
        └─────────────────────────────────────────────────┘
```

Why this works:
- The pre-pass is **sequential by construction** → correct in-order tracking,
  **without** giving up parallelism in the expensive processing pass.
- Keyed by **frame content hash** (same mechanism as `face_store`), so
  `select_faces()` needs **no new argument** — it already holds
  `target_vision_frame` and can hash it.
- `TRACK_STORE` holds only `{hash: [(track_id, bounding_box)]}` (ints + 4 floats)
  → tiny memory, unlike caching full target `Face`s (which `dbf4346f` removed for
  memory reasons).
- Detection runs twice (pre-pass + processing). Acceptable: detection is fast on
  TensorRT, the same-frame IoU re-attach is near-perfect (same detector), and we
  keep both correctness and parallelism. (Single-detection variant noted under
  Risks.)

For **streams** there is no pre-pass: insert the sequential detect+track step in
the streamer read loop (`streamer.py`, before `executor.submit`), writing the
same `TRACK_STORE` keyed by hash. Processing stays parallel.

## §1 New module `facefusion/face_tracker.py`

Kalman re-expressed as functions; state is plain `numpy` arrays.

```python
Mean       : TypeAlias = NDArray[Any]   # (8,)  [cx, cy, aspect, h, vx, vy, va, vh]
Covariance : TypeAlias = NDArray[Any]   # (8, 8)
Track      = namedtuple('Track', [ 'track_id', 'mean', 'covariance', 'state', 'hit_streak', 'time_since_update', 'embedding' ])
TrackStore : TypeAlias = Dict[str, List[Tuple[int, BoundingBox]]]

TRACK_STORE : TrackStore = {}
TRACK_STATE : List[Track] = []          # active tracks during the pre-pass only
TRACK_ID_COUNTER : List[int] = [ 0 ]    # list-wrapped to avoid a bare global rebind

def kalman_initiate(measurement : Measurement) -> Tuple[Mean, Covariance]: ...
def kalman_predict(mean : Mean, covariance : Covariance) -> Tuple[Mean, Covariance]: ...
def kalman_update(mean : Mean, covariance : Covariance, measurement : Measurement) -> Tuple[Mean, Covariance]: ...

def iou_distance(track_boxes : List[BoundingBox], detection_boxes : List[BoundingBox]) -> NDArray[Any]: ...
def associate(cost_matrix : NDArray[Any], threshold : float) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
	# scipy.optimize.linear_sum_assignment, gated by threshold

def update_tracks(bounding_boxes : List[BoundingBox], scores : List[Score], embeddings : List[Embedding]) -> List[int]:
	# 1. kalman_predict every active track
	# 2. cost = blend of iou_distance and (1 - cosine on embedding_norm)   <-- hybrid
	# 3. associate; kalman_update matched; spawn new tracks; age unmatched
	# 4. drop tracks with time_since_update > track_buffer
	# returns a track_id per input box, in input order

def assign_frame_tracks(vision_frame : VisionFrame, faces : List[Face]) -> None:
	# pre-pass entry: pull boxes/scores/embeddings off faces, update_tracks, store keyed by hash
	TRACK_STORE[create_hash(vision_frame.tobytes())] = list(zip(track_ids, bounding_boxes))

def lookup_frame_tracks(vision_frame : VisionFrame) -> Optional[List[Tuple[int, BoundingBox]]]:
	return TRACK_STORE.get(create_hash(vision_frame.tobytes()))

def clear_tracks() -> None:
	TRACK_STORE.clear()
	TRACK_STATE.clear()
	TRACK_ID_COUNTER[0] = 0
```

Notes:
- **Hybrid cost** (IoU ⊕ embedding) is the facefusion-specific edge over vanilla
  ByteTrack — embeddings already exist on `Face.embedding_norm`, so combining
  position continuity with appearance is cheap and far more robust than either
  alone. IoU weight dominates; embedding breaks ties / survives fast motion.
- `state` ∈ `tracked` / `lost` mirrors ByteTrack; `track_buffer` frames kept
  before removal.
- Port the math verbatim from the validated ByteTrack kalman (velocity converges
  to true within ~1 px/frame — measured), just de-classed.

## §2 Integration in `facefusion/face_selector.py`

Add a track-aware ordering used **only when tracking is enabled** (else current
behaviour, untouched):

```python
def select_faces(reference_vision_frame, source_vision_frames, target_vision_frame) -> List[Face]:
	...
	if state_manager.get_item('face_tracking'):
		target_faces = order_faces_by_track(target_vision_frame, target_faces)
	...
```

- `order_faces_by_track()` reads `lookup_frame_tracks()`, IoU-attaches each
  current detection to a stored `(track_id, box)`, then orders faces by **track
  id** while letting `face_selector_order` decide the order a track **first**
  appears (so a new person slots in predictably, existing people keep their
  slot).
- `reference` mode: if the reference's track id is known, follow that track id
  through gaps even when `compare_faces()` would momentarily drop it.
- When the lookup misses (no pre-pass / cache eviction), fall back to the
  current spatial sort — graceful degradation, never a hard failure.

## §3 Pipeline insertion points

| File | Change |
|---|---|
| `facefusion/workflows/image_to_video.py:~80` | before the `ThreadPoolExecutor` loop, sequential `build_face_tracks(temp_frame_paths)` (read in order → `get_many_faces` → `assign_frame_tracks`) |
| `facefusion/workflows/image_to_image.py` (multi), other video workflows | same pre-pass guard |
| `facefusion/streamer.py:~26` | sequential detect+`assign_frame_tracks` at read, before `executor.submit` |
| `facefusion/face_selector.py` | `order_faces_by_track()` + `reference` gap-bridge (§2) |
| `facefusion/core.py` / run lifecycle | `clear_tracks()` alongside existing `clear_faces()` |
| `facefusion/uis/components/preview.py:273` | preview is single-frame → tracking is a no-op (lookup miss → spatial fallback); document, no change |

## §4 Config / args surface

State + `choices.py` + program args (argparse needs `type`/`choices` per the
security rule):

| Item | Type | Default | Meaning |
|---|---|---|---|
| `face_tracking` | bool flag | off | master toggle (separate enable, not a param on existing calls) |
| `face_tracking_iou_threshold` | float (range-validated) | 0.2 | min IoU to associate |
| `face_tracking_embedding_distance` | float (range-validated) | 0.5 | hybrid appearance gate |
| `face_tracking_buffer` | int (range-validated) | 30 | frames a lost track survives |

Default off ⇒ existing pipelines are byte-for-byte unchanged.

## §5 Testing — `tests/test_face_tracker.py`

Order: fixtures (`before_all`, `before_each`), helpers, then test methods in
source order. Reuse the synthetic harnesses already built under
`~/Documents/Github/byte-track` (occlusion / flicker generators):

- `test_kalman_predict` — constant-velocity input ⇒ predicted advance ≈ true
  (port the convergence probe: `est_vx ≈ 9` for true 9).
- `test_iou_distance`, `test_associate` — known overlaps ⇒ expected matches.
- `test_update_tracks_keeps_id_through_occlusion` — moving box, 8-frame gap ⇒
  same id before/after.
- `test_update_tracks_new_id_on_lost_overlap` — frozen-equivalent control.
- `test_update_tracks_flicker_low_lag` — 1–2 frame gaps ⇒ id stable.
- `test_order_faces_by_track_is_stable` — two faces swapping spatial order keep
  their track slots.
- **Mutation validation** (per CLAUDE.md): break association (force IoU=0) and
  confirm `test_*_keeps_id` fails; revert.
- `flake8 facefusion tests` clean.

## §6 Phases

1. **Tracker core** — `face_tracker.py` (kalman fns, IoU, associate,
   `update_tracks`) + unit tests. No pipeline wiring. Pure, fully testable.
2. **Video `many` mode** — pre-pass in `image_to_video.py`,
   `order_faces_by_track()`, `clear_tracks()` lifecycle. Measure swap-reduction
   on a multi-face moving clip (count id flips vs baseline).
3. **Hybrid + `reference`** — embedding-blended cost, reference gap-bridging.
4. **Streams** — sequential read-loop association in `streamer.py`.

## §7 Risks & trade-offs

- **Double detection** (pre-pass + processing). Mitigation: cheapest detector
  settings in the pre-pass; or optional single-detection mode that stores full
  `Face`s in `TRACK_STORE` (reverts the `dbf4346f` memory saving — offer as a
  flag, not default).
- **Hash-keyed lookup misses** on re-encoded/altered frames ⇒ spatial fallback;
  never fatal.
- **Talking-head footage**: little to no gain (see Non-goals) — keep default off
  and document when to enable.
- **Detector order at spawn**: first-seen ordering still uses
  `face_selector_order`; only continuity is added, so existing UX is preserved.
