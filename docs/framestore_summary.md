# FrameStore — Short Version

## Idea
One shared shelf of decoded frames inside `video_manager`, keyed by `(source, frame_number)`. Everyone asks it for frames; it decodes misses via a dumb reader and reuses the rest.

## Why
Today there are two frame caches doing the same job (`read_video_chunk` lru + `read_video_reader_window` frame_set), plus messy single-cursor seek rules. The store replaces all of it with one owner.

## What changes
- Readers become dumb forward decoders (no cache).
- `read_video_chunk` + `read_video_reader_window` → one range read.
- Cache, overlaps, and eviction live in the store.
- Store clears via `clear_video_pool()` → delete 11 processor `cache_clear()` lines.

## Scope
Mostly inside `video_manager`. The only outside touch is removing those 11 `cache_clear()` lines. Public read functions keep their signatures.

## Open question
Multiple readers per file (id key) — only if we want independent cursors to kill seek thrash. Deferred.

## Order
1. Writer PR — done.
2. FrameStore (contained).
3. Optional: multiple readers.

Full version: [framestore_architecture.md](framestore_architecture.md)
