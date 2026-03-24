# Compiling libdatachannel

Prebuilt DLLs from OBS or pip lack VP8 support. We compile from source to get all codecs (H264, VP8, AV1, Opus).

## Source

```
git clone --depth 1 --recurse-submodules https://github.com/paullouisageneau/libdatachannel.git
cd libdatachannel
```

## Windows

Requirements: Visual Studio Build Tools 2019+ with C++ workload, cmake, ninja (available via conda).

```cmd
call "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvarsall.bat" x64
cmake -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DNO_WEBSOCKET=ON -DNO_EXAMPLES=ON -DNO_TESTS=ON -DUSE_NICE=OFF
cmake --build build --config Release
```

Output: `build/datachannel.dll`

Rename to: `windows-x64-openssl-h264-vp8-av1-opus-datachannel-<version>.dll`

Place in: `bin/`

## Linux

Requirements: gcc/g++, cmake, ninja-build, libssl-dev.

```bash
sudo apt install build-essential cmake ninja-build libssl-dev
cmake -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DNO_WEBSOCKET=ON -DNO_EXAMPLES=ON -DNO_TESTS=ON -DUSE_NICE=OFF
cmake --build build --config Release
```

Output: `build/libdatachannel.so`

Rename to: `linux-x64-openssl-h264-vp8-av1-opus-libdatachannel-<version>.so`

Install to: `/usr/local/lib/` or project `bin/`

If installed to a custom path, run `sudo ldconfig` or set `LD_LIBRARY_PATH`.

## macOS

Requirements: Xcode Command Line Tools, cmake, ninja.

```bash
xcode-select --install
brew install cmake ninja
cmake -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DNO_WEBSOCKET=ON -DNO_EXAMPLES=ON -DNO_TESTS=ON -DUSE_NICE=OFF
cmake --build build --config Release
```

For universal binary (arm64 + x86_64):

```bash
cmake -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DNO_WEBSOCKET=ON -DNO_EXAMPLES=ON -DNO_TESTS=ON -DUSE_NICE=OFF -DCMAKE_OSX_ARCHITECTURES="arm64;x86_64"
cmake --build build --config Release
```

Output: `build/libdatachannel.dylib`

Rename to: `macos-universal-openssl-h264-vp8-av1-opus-libdatachannel-<version>.dylib`

Install to: `/usr/local/lib/` or project `bin/`

## Naming convention

```
<os>-<arch>-<tls>-<codecs>-datachannel-<version>.<ext>
```

- os: `windows`, `linux`, `macos`
- arch: `x64`, `arm64`, `universal`
- tls: `openssl` (default), `gnutls`, `mbedtls`
- codecs: supported packetizers, e.g. `h264-vp8-av1-opus`
- version: libdatachannel version, e.g. `0.24.1`

## Verifying the build

```python
import ctypes
lib = ctypes.CDLL('path/to/datachannel.dll')
for fn in ['rtcSetH264Packetizer', 'rtcSetVP8Packetizer', 'rtcSetAV1Packetizer', 'rtcSetOpusPacketizer']:
    try:
        getattr(lib, fn)
        print(f'{fn}: OK')
    except AttributeError:
        print(f'{fn}: MISSING')
```

## CMake flags reference

| Flag | Default | Purpose |
|---|---|---|
| `NO_WEBSOCKET` | OFF | Disable WebSocket support (not needed) |
| `NO_MEDIA` | OFF | Disable media transport (must be OFF for codecs) |
| `NO_EXAMPLES` | OFF | Skip building examples |
| `NO_TESTS` | OFF | Skip building tests |
| `USE_NICE` | OFF | Use libnice instead of libjuice for ICE |
| `USE_GNUTLS` | OFF | Use GnuTLS instead of OpenSSL |
| `USE_MBEDTLS` | OFF | Use Mbed TLS instead of OpenSSL |

## Runtime dependencies

- **libopus**: Required for audio encoding. Install via `conda install -c conda-forge libopus` (Windows) or `apt install libopus-dev` (Linux) or `brew install opus` (macOS).
- **OpenSSL**: Usually bundled or system-provided. On Windows, conda provides it.
