# FrameStore Architecture Plan

Architecture change + simplification for `video_manager` frame reading. Not a cleanup — it replaces two competing frame caches and the single-cursor seek heuristics with one owner.

## Problem (today)

- **One reader per file, shared and lock-serialized.** Different access patterns fight over one cursor and force `kill + respawn` (seek thrash).
- **Two range-read mechanisms doing the same job:**
  - `read_video_chunk` (in `vision`) — `lru_cache(maxsize = 2)`, used by ~11 processors.
  - `read_video_reader_window` (in `video_manager`) — rolling `frame_set` + margin eviction, used by `select_video_frames`.
  - Their todos even argue with each other ("window read replaces the chunk cache" vs "restore the chunk_size approach").
- **Cache + eviction logic is inline** inside `read_video_reader_window`; the `[memory]` todo lives there.
- **`frame_set` is glued onto the reader handle** — state mixed into identity.

## Target architecture

- **Reader = dumb sequential decoder.** `{process, position}` (+ `file_path`, `metadata`). Plays forward, decodes on demand. No cache.
- **FrameStore = the single owner of decoded frames.** Keyed by `(source, frame_number)`, lives inside `video_manager`. Every consumer already routes through `video_manager` to get frames, so the store sits behind that same door.
- **Writer = self-describing sink.** Already done in the writer PR.

The store does the work a per-reader cache cannot:
- **Decode once, serve many** — overlapping windows reuse frames instead of each decoding.
- **Interest-based eviction** — a frame is dropped when no live window covers it (union of live ranges), replacing the crude `< frame_start - margin` trim.
- **One memory budget** — a single place that caps frames in RAM.

## Illustrative shape (not final)

```
# frame_store lives in video_manager, keyed by (source, frame_number)
read_frame_window(source, frame_start, frame_end)   # hits store, decodes misses via a reader
store_frame(source, frame_number, vision_frame)
evict_frames(source, live_ranges)                   # drop frames no live window covers
clear_frame_store()                                 # called from clear_video_pool
```

`read_video_chunk` and `read_video_reader_window` both collapse into `read_frame_window` — "give me frames `[a, b]`".

## What dies (the simplification)

- `read_video_chunk`'s `lru_cache` **and** `read_video_reader_window`'s `frame_set` → one store.
- inline eviction in `read_video_reader_window` → store policy.
- 11 processor `read_static_video_chunk.cache_clear()` lines → **deleted** (store clears via `clear_video_pool()`, which every processor already calls right next to it).
- the `skip 128` drain / `refresh` / `conditional_set_position` seek dance → shrinks; the store owns decode strategy.

## Scope / blast radius

- **Core store + window read** → `video_manager`-internal.
- **Chunk unification** → reaches ~11 processors, but only their teardown: the `cache_clear()` calls get removed, not rewired. Shallow and wide, mostly subtraction.
- **No deep processor changes.** Public read functions keep their signatures.

## Open decisions

- **id-key / multiple readers per file** — enables independent cursors (kills seek thrash). Only worth it if multiplicity is a real goal; adds pools + lifecycle sync (fights "avoid globals"). **Deferred** — decide before phase 3.
- **`position` stays on the reader** — it is the process cursor, inseparable from the process. Not moved.
- **Do not chase symmetric `{process, file_path, metadata}` reader** — a reader is a stateful cursor, a writer is a sink; the asymmetry is correct.
- **`image_to_video`'s `calculate_frame_look_ahead` (3 GB)** — a *different* concern (executor future buffer, not the reader cache). Folding it into the store budget is optional, separate.

## Pros / cons

**Pros**
- Decode once, share overlaps — less redundant decoding.
- One memory owner — predictable RAM, kills scattered budgets.
- Dumb readers — deletes the seek heuristics.
- Two caches become one — the chunk-vs-window todo dilemma disappears.
- Cache in one place — testable, one home for the memory todo.

**Cons**
- A subsystem, not a cleanup — real design cost.
- Eviction is easy to get wrong — evict too early = re-decode; never = leak.
- Concurrency moves into the store — it needs its own locking; it did not vanish.
- Multiplicity (if adopted) = more ffmpeg processes = more CPU/RAM.
- Over-engineering risk if overlaps/multiplicity are not actually needed.

## Phasing

1. **Writer PR** — done. Ship it.
2. **FrameStore (contained):** route `read_video_reader_window` + `read_video_chunk` through the store; delete the `lru_cache` and `frame_set`; fold store clear into `clear_video_pool`; delete the 11 `cache_clear()` lines.
3. **(optional) id-keyed multiple readers:** kill seek thrash; fold the look-ahead budget in. Needs the multiplicity decision first.

**Bottom line:** worth it because it is mostly subtraction — two caches and the seek heuristics collapse into one owner. The one real question is multiplicity (phase 3); phase 2 stands on its own.
