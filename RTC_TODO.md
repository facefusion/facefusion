# RTC TODO

## Approach

1. vibe code mass testing to get broad coverage fast
2. vibe code refactoring (naming, dead code, restructure)
3. hand craft production code (libdatachannel, peer management, SDP)
4. hand craft testing — thin it out to essentials only

## Unit Tests

| Function | Rating | Assertions |
|---|---|---|
| `create_peer_connection` | essential | returns valid peer connection id |
| `add_audio_track` | essential | returns valid track id |
| `add_video_track` | essential | returns valid track id |
| `negotiate_sdp` | essential | returns sdp answer from valid offer, returns None on timeout |
| `delete_peers` | essential | clears peer list |
| `create_rtc_stream` | essential | initializes empty peer list |
| `destroy_rtc_stream` | essential | cleans up peers, handles missing session |
| `add_rtc_viewer` | nice to have | returns None for unknown session |
| `resolve_binary_file` | skip | covered implicitly by `create_static_rtc_library` |
| `handle_whep_offer` | skip | thin wrapper, covered by integration tests |
| `send_to_peers` | skip | needs open tracks, covered by integration tests |
| `send_rtc_frame` | skip | thin delegation to `send_to_peers` |

## Integration Tests

- [ ] test full SDP offer/answer roundtrip between two peer connections
- [ ] test `send_to_peers` delivers frame data to a connected peer
- [ ] test peer cleanup after `delete_peers` prevents further sends
- [ ] test `add_rtc_viewer` followed by `send_rtc_frame` end-to-end
- [ ] test multiple viewers receive frames from same stream
- [ ] test viewer disconnect does not break remaining peers

## Dead Code

- [ ] remove `is_peer_connected` from `rtc.py`, never called
- [ ] remove `pre_check` from `rtc.py`, never called
- [ ] remove `get_rtc_stream` from `rtc_store.py`, never called
- [ ] remove `RtcOfferSet` from `types.py`, never used

## Naming

- [ ] rename `rtc_bindings.py` to `libdatachannel.py` — owns C library loading, struct definitions, ctypes registration
- [ ] rename `RTC_CONFIGURATION` to a proper class definition
- [ ] rename `RTC_PACKETIZER_INIT` to a proper class definition
- [ ] rename `init_ctypes` to something more specific like `register_argtypes`

## Unused Library Config

- [ ] `create_peer_connection` exposes 14 params but production only uses `disable_auto_negotiation`, `enable_ice_udp_mux`, `force_media_transport` — reduce to what is needed
- [ ] `RTC_PACKETIZER_INIT` defines `nalSeparator`, `obuPacketization`, `playoutDelayId`, `playoutDelayMin`, `playoutDelayMax`, `sequenceNumber`, `timestamp` — none are set outside the struct definition, they are H264/AV1 specific and unused for VP8/Opus
- [ ] `rtcSetLocalDescription` is used in tests but not registered in `rtc_bindings.py`

## Refactor

- [ ] extract shared media description builder from `rtc.py` and `tests/stream_helper.py` (see TODO in `tests/stream_helper.py`)
- [ ] replace `type()` calls for ctypes structs in `rtc_bindings.py` with proper class definitions
- [ ] move `resolve_binary_file`, `create_static_download_set`, `create_static_rtc_library` from `rtc.py` into `libdatachannel.py` — library init belongs with the bindings, `rtc.py` just consumes it
- [ ] move `rtc_store.py` state into a proper store pattern consistent with other `*_store.py` files
- [ ] replace `time.sleep` polling loops in `negotiate_sdp` and `create_sdp_offer` (test helper) with `rtcSetGatheringStateChangeCallback` — signal a `threading.Event` on ICE gathering complete, then `event.wait(timeout=5)` instead of spinning
- [ ] `create_static_download_set` has hardcoded linux URLs with a TODO to use dynamic `binary_name`

## Violations

- `rtc.py:25` — comment on `create_static_download_set` (no comments)
- `rtc.py:34` — comment on hash url (no comments)
- `rtc.py:42` — comment on source url (no comments)
- `rtc.py:205` — `send_to_peers` returns None explicitly on a void function (redundant)
- `rtc_bindings.py:3,23` — `type()` to create structs is a class workaround (no classes, but these should be plain structs)
- `tests/stream_helper.py:45` — `sdp` temp variable before return (no need for temporary variable in simple cases)

## Security

- `rtc.py:157` — `negotiate_sdp` passes unsanitized `sdp_offer` string directly to C library, no SDP format validation before hitting native code
