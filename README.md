FaceFusion Version 2.0 FREEDOM DONT BE EVIL
==========

Thanks to [FaceFusion](https://github.com/facefusion/facefusion)

# WARNING DONT BE EVIL !

READ : 

[windows 1](https://docs.facefusion.io/installation/platform/windows)

[windows 2](https://docs.facefusion.io/installation/environment/windows)

[windows 3](https://docs.facefusion.io/installation/accelerator/cuda)


# ---------------- NO NEED INSTALL

[Manual Download For WIn](https://download.pytorch.org/whl/cu118/torch-2.1.0%2Bcu118-cp310-cp310-win_amd64.whl#sha256=eb512249df3083bce7bd3d89d9d1289fa82fe807e714a02b754e66971d358da3)

[Manual Download For Linux](https://download.pytorch.org/whl/cu118/torch-2.1.0%2Bcu118-cp310-cp310-linux_x86_64.whl#sha256=a81b554184492005543ddc32e96469f9369d778dedd195d73bda9bed407d6589)

# ---------------- NO NEED INSTALL

```sh
git clone https://github.com/EKI-INDRADI/facefusion_rnd_20231129_freedom_dont_be_evil.git
cd facefusion_rnd_20231129_freedom_dont_be_evil
py -3.10 -m venv venv
cd venv\Scripts

activate
cd ..
cd ..

pip install -r requirements.txt
pip install onnxruntime-gpu


# ---------------- NO NEED INSTALL
pip uninstall torch

# Manual Download For WIn https://download.pytorch.org/whl/cu118/torch-2.1.0%2Bcu118-cp310-cp310-win_amd64.whl#sha256=eb512249df3083bce7bd3d89d9d1289fa82fe807e714a02b754e66971d358da3
pip install torch-2.1.0+cu118-cp310-cp310-win_amd64.whl

# Manual Download For Linux https://download.pytorch.org/whl/cu118/torch-2.1.0%2Bcu118-cp310-cp310-linux_x86_64.whl#sha256=a81b554184492005543ddc32e96469f9369d778dedd195d73bda9bed407d6589
pip install torch-2.1.0+cu118-cp310-cp310-linux_x86_64.whl


# ---------------- NO NEED INSTALL

python run.py

```

Documentation V2.6.0
-------------

> Next generation face swapper and enhancer. V.2.6.0

[![Build Status](https://img.shields.io/github/actions/workflow/status/facefusion/facefusion/ci.yml.svg?branch=master)](https://github.com/facefusion/facefusion/actions?query=workflow:ci)
![License](https://img.shields.io/badge/license-MIT-green)


Preview
-------

![Preview](https://raw.githubusercontent.com/facefusion/facefusion/master/.github/preview.png?sanitize=true)


Installation
------------

Be aware, the [installation](https://docs.facefusion.io/installation) needs technical skills and is not recommended for beginners. In case you are not comfortable using a terminal, our [Windows Installer](https://buymeacoffee.com/henryruhs/e/251939) can have you up and running in minutes.


Usage
-----

Run the command:

```
python run.py [options]

options:
  -h, --help                                                                                                                                                                            show this help message and exit
  -c CONFIG_PATH, --config CONFIG_PATH                                                                                                                                                  choose the config file to override defaults
  -s SOURCE_PATHS, --source SOURCE_PATHS                                                                                                                                                choose single or multiple source images or audios
  -t TARGET_PATH, --target TARGET_PATH                                                                                                                                                  choose single target image or video
  -o OUTPUT_PATH, --output OUTPUT_PATH                                                                                                                                                  specify the output file or directory
  -v, --version                                                                                                                                                                         show program's version number and exit

misc:
  --force-download                                                                                                                                                                      force automate downloads and exit
  --skip-download                                                                                                                                                                       omit automate downloads and remote lookups
  --headless                                                                                                                                                                            run the program without a user interface
  --log-level {error,warn,info,debug}                                                                                                                                                   adjust the message severity displayed in the terminal

execution:
  --execution-device-id EXECUTION_DEVICE_ID                                                                                                                                             specify the device used for processing
  --execution-providers EXECUTION_PROVIDERS [EXECUTION_PROVIDERS ...]                                                                                                                   accelerate the model inference using different providers (choices: cpu, ...)
  --execution-thread-count [1-128]                                                                                                                                                      specify the amount of parallel threads while processing
  --execution-queue-count [1-32]                                                                                                                                                        specify the amount of frames each thread is processing

memory:
  --video-memory-strategy {strict,moderate,tolerant}                                                                                                                                    balance fast frame processing and low VRAM usage
  --system-memory-limit [0-128]                                                                                                                                                         limit the available RAM that can be used while processing

face analyser:
  --face-analyser-order {left-right,right-left,top-bottom,bottom-top,small-large,large-small,best-worst,worst-best}                                                                     specify the order in which the face analyser detects faces
  --face-analyser-age {child,teen,adult,senior}                                                                                                                                         filter the detected faces based on their age
  --face-analyser-gender {female,male}                                                                                                                                                  filter the detected faces based on their gender
  --face-detector-model {many,retinaface,scrfd,yoloface,yunet}                                                                                                                          choose the model responsible for detecting the face
  --face-detector-size FACE_DETECTOR_SIZE                                                                                                                                               specify the size of the frame provided to the face detector
  --face-detector-score [0.0-0.95]                                                                                                                                                      filter the detected faces base on the confidence score
  --face-landmarker-score [0.0-0.95]                                                                                                                                                    filter the detected landmarks base on the confidence score

face selector:
  --face-selector-mode {many,one,reference}                                                                                                                                             use reference based tracking or simple matching
  --reference-face-position REFERENCE_FACE_POSITION                                                                                                                                     specify the position used to create the reference face
  --reference-face-distance [0.0-1.45]                                                                                                                                                  specify the desired similarity between the reference face and target face
  --reference-frame-number REFERENCE_FRAME_NUMBER                                                                                                                                       specify the frame used to create the reference face

face mask:
  --face-mask-types FACE_MASK_TYPES [FACE_MASK_TYPES ...]                                                                                                                               mix and match different face mask types (choices: box, occlusion, region)
  --face-mask-blur [0.0-0.95]                                                                                                                                                           specify the degree of blur applied the box mask
  --face-mask-padding FACE_MASK_PADDING [FACE_MASK_PADDING ...]                                                                                                                         apply top, right, bottom and left padding to the box mask
  --face-mask-regions FACE_MASK_REGIONS [FACE_MASK_REGIONS ...]                                                                                                                         choose the facial features used for the region mask (choices: skin, left-eyebrow, right-eyebrow, left-eye, right-eye, glasses, nose, mouth, upper-lip, lower-lip)

frame extraction:
  --trim-frame-start TRIM_FRAME_START                                                                                                                                                   specify the the start frame of the target video
  --trim-frame-end TRIM_FRAME_END                                                                                                                                                       specify the the end frame of the target video
  --temp-frame-format {bmp,jpg,png}                                                                                                                                                     specify the temporary resources format
  --keep-temp                                                                                                                                                                           keep the temporary resources after processing

output creation:
  --output-image-quality [0-100]                                                                                                                                                        specify the image quality which translates to the compression factor
  --output-image-resolution OUTPUT_IMAGE_RESOLUTION                                                                                                                                     specify the image output resolution based on the target image
  --output-video-encoder {libx264,libx265,libvpx-vp9,h264_nvenc,hevc_nvenc,h264_amf,hevc_amf}                                                                                           specify the encoder use for the video compression
  --output-video-preset {ultrafast,superfast,veryfast,faster,fast,medium,slow,slower,veryslow}                                                                                          balance fast video processing and video file size
  --output-video-quality [0-100]                                                                                                                                                        specify the video quality which translates to the compression factor
  --output-video-resolution OUTPUT_VIDEO_RESOLUTION                                                                                                                                     specify the video output resolution based on the target video
  --output-video-fps OUTPUT_VIDEO_FPS                                                                                                                                                   specify the video output fps based on the target video
  --skip-audio                                                                                                                                                                          omit the audio from the target video

frame processors:
  --frame-processors FRAME_PROCESSORS [FRAME_PROCESSORS ...]                                                                                                                            load a single or multiple frame processors. (choices: face_debugger, face_enhancer, face_swapper, frame_colorizer, frame_enhancer, lip_syncer, ...)
  --face-debugger-items FACE_DEBUGGER_ITEMS [FACE_DEBUGGER_ITEMS ...]                                                                                                                   load a single or multiple frame processors (choices: bounding-box, face-landmark-5, face-landmark-5/68, face-landmark-68, face-landmark-68/5, face-mask, face-detector-score, face-landmarker-score, age, gender)
  --face-enhancer-model {codeformer,gfpgan_1.2,gfpgan_1.3,gfpgan_1.4,gpen_bfr_256,gpen_bfr_512,gpen_bfr_1024,gpen_bfr_2048,restoreformer_plus_plus}                                     choose the model responsible for enhancing the face
  --face-enhancer-blend [0-100]                                                                                                                                                         blend the enhanced into the previous face
  --face-swapper-model {blendswap_256,inswapper_128,inswapper_128_fp16,simswap_256,simswap_512_unofficial,uniface_256}                                                                  choose the model responsible for swapping the face
  --frame-colorizer-model {ddcolor,ddcolor_artistic,deoldify,deoldify_artistic,deoldify_stable}                                                                                         choose the model responsible for colorizing the frame
  --frame-colorizer-blend [0-100]                                                                                                                                                       blend the colorized into the previous frame
  --frame-colorizer-size {192x192,256x256,384x384,512x512}                                                                                                                              specify the size of the frame provided to the frame colorizer
  --frame-enhancer-model {clear_reality_x4,lsdir_x4,nomos8k_sc_x4,real_esrgan_x2,real_esrgan_x2_fp16,real_esrgan_x4,real_esrgan_x4_fp16,real_hatgan_x4,span_kendata_x4,ultra_sharp_x4}  choose the model responsible for enhancing the frame
  --frame-enhancer-blend [0-100]                                                                                                                                                        blend the enhanced into the previous frame
  --lip-syncer-model {wav2lip_gan}                                                                                                                                                      choose the model responsible for syncing the lips

uis:
  --open-browser                                                                                                                                                                        open the browser once the program is ready
  --ui-layouts UI_LAYOUTS [UI_LAYOUTS ...]                                                                                                                                              launch a single or multiple UI layouts (choices: benchmark, default, webcam, ...)
```


Documentation
-------------

Read the [documentation](https://docs.facefusion.io) for a deep dive.




---

Documentation V2.4.1
-------------

Read the [documentation](https://docs.facefusion.io) for a deep dive.

> Next generation face swapper and enhancer. V2.4.1

[![Build Status](https://img.shields.io/github/actions/workflow/status/facefusion/facefusion/ci.yml.svg?branch=master)](https://github.com/facefusion/facefusion/actions?query=workflow:ci)
![License](https://img.shields.io/badge/license-MIT-green)


Preview
-------

![Preview](https://raw.githubusercontent.com/facefusion/facefusion/master/.github/preview.png?sanitize=true)


Installation
------------

Be aware, the installation needs technical skills and is not for beginners. Please do not open platform and installation related issues on GitHub. We have a very helpful [Discord](https://join.facefusion.io) community that will guide you to complete the installation.

Get started with the [installation](https://docs.facefusion.io/installation) guide.


Usage
-----

Run the command:

```
python run.py [options]

options:
  -h, --help                                                                                                             show this help message and exit
  -s SOURCE_PATHS, --source SOURCE_PATHS                                                                                 choose single or multiple source images or audios
  -t TARGET_PATH, --target TARGET_PATH                                                                                   choose single target image or video
  -o OUTPUT_PATH, --output OUTPUT_PATH                                                                                   specify the output file or directory
  -v, --version                                                                                                          show program's version number and exit

misc:
  --skip-download                                                                                                        omit automate downloads and remote lookups
  --headless                                                                                                             run the program without a user interface
  --log-level {error,warn,info,debug}                                                                                    adjust the message severity displayed in the terminal

execution:
  --execution-providers EXECUTION_PROVIDERS [EXECUTION_PROVIDERS ...]                                                    accelerate the model inference using different providers (choices: cpu, ...)
  --execution-thread-count [1-128]                                                                                       specify the amount of parallel threads while processing
  --execution-queue-count [1-32]                                                                                         specify the amount of frames each thread is processing

memory:
  --video-memory-strategy {strict,moderate,tolerant}                                                                     balance fast frame processing and low vram usage
  --system-memory-limit [0-128]                                                                                          limit the available ram that can be used while processing

face analyser:
  --face-analyser-order {left-right,right-left,top-bottom,bottom-top,small-large,large-small,best-worst,worst-best}      specify the order in which the face analyser detects faces.
  --face-analyser-age {child,teen,adult,senior}                                                                          filter the detected faces based on their age
  --face-analyser-gender {female,male}                                                                                   filter the detected faces based on their gender
  --face-detector-model {many,retinaface,scrfd,yoloface,yunet}                                                           choose the model responsible for detecting the face
  --face-detector-size FACE_DETECTOR_SIZE                                                                                specify the size of the frame provided to the face detector
  --face-detector-score [0.0-1.0]                                                                                        filter the detected faces base on the confidence score
  --face-landmarker-score [0.0-1.0]                                                                                      filter the detected landmarks base on the confidence score

face selector:
  --face-selector-mode {many,one,reference}                                                                              use reference based tracking or simple matching
  --reference-face-position REFERENCE_FACE_POSITION                                                                      specify the position used to create the reference face
  --reference-face-distance [0.0-1.5]                                                                                    specify the desired similarity between the reference face and target face
  --reference-frame-number REFERENCE_FRAME_NUMBER                                                                        specify the frame used to create the reference face

face mask:
  --face-mask-types FACE_MASK_TYPES [FACE_MASK_TYPES ...]                                                                mix and match different face mask types (choices: box, occlusion, region)
  --face-mask-blur [0.0-1.0]                                                                                             specify the degree of blur applied the box mask
  --face-mask-padding FACE_MASK_PADDING [FACE_MASK_PADDING ...]                                                          apply top, right, bottom and left padding to the box mask
  --face-mask-regions FACE_MASK_REGIONS [FACE_MASK_REGIONS ...]                                                          choose the facial features used for the region mask (choices: skin, left-eyebrow, right-eyebrow, left-eye, right-eye, eye-glasses, nose, mouth, upper-lip, lower-lip)

frame extraction:
  --trim-frame-start TRIM_FRAME_START                                                                                    specify the the start frame of the target video
  --trim-frame-end TRIM_FRAME_END                                                                                        specify the the end frame of the target video
  --temp-frame-format {bmp,jpg,png}                                                                                      specify the temporary resources format
  --keep-temp                                                                                                            keep the temporary resources after processing

output creation:
  --output-image-quality [0-100]                                                                                         specify the image quality which translates to the compression factor
  --output-image-resolution OUTPUT_IMAGE_RESOLUTION                                                                      specify the image output resolution based on the target image
  --output-video-encoder {libx264,libx265,libvpx-vp9,h264_nvenc,hevc_nvenc,h264_amf,hevc_amf}                            specify the encoder use for the video compression
  --output-video-preset {ultrafast,superfast,veryfast,faster,fast,medium,slow,slower,veryslow}                           balance fast video processing and video file size
  --output-video-quality [0-100]                                                                                         specify the video quality which translates to the compression factor
  --output-video-resolution OUTPUT_VIDEO_RESOLUTION                                                                      specify the video output resolution based on the target video
  --output-video-fps OUTPUT_VIDEO_FPS                                                                                    specify the video output fps based on the target video
  --skip-audio                                                                                                           omit the audio from the target video

frame processors:
  --frame-processors FRAME_PROCESSORS [FRAME_PROCESSORS ...]                                                             load a single or multiple frame processors. (choices: face_debugger, face_enhancer, face_swapper, frame_enhancer, lip_syncer, ...)
  --face-debugger-items FACE_DEBUGGER_ITEMS [FACE_DEBUGGER_ITEMS ...]                                                    load a single or multiple frame processors (choices: bounding-box, face-landmark-5, face-landmark-5/68, face-landmark-68, face-mask, face-detector-score, face-landmarker-score, age, gender)
  --face-enhancer-model {codeformer,gfpgan_1.2,gfpgan_1.3,gfpgan_1.4,gpen_bfr_256,gpen_bfr_512,restoreformer_plus_plus}  choose the model responsible for enhancing the face
  --face-enhancer-blend [0-100]                                                                                          blend the enhanced into the previous face
  --face-swapper-model {blendswap_256,inswapper_128,inswapper_128_fp16,simswap_256,simswap_512_unofficial,uniface_256}   choose the model responsible for swapping the face
  --frame-enhancer-model {lsdir_x4,nomos8k_sc_x4,real_esrgan_x4,real_esrgan_x4_fp16,span_kendata_x4}                     choose the model responsible for enhancing the frame
  --frame-enhancer-blend [0-100]                                                                                         blend the enhanced into the previous frame
  --lip-syncer-model {wav2lip_gan}                                                                                       choose the model responsible for syncing the lips

uis:
  --ui-layouts UI_LAYOUTS [UI_LAYOUTS ...]                                                                               launch a single or multiple UI layouts (choices: benchmark, default, webcam, ...)
```

---

Documentation V2
-------------

Read the [documentation](https://docs.facefusion.io) for a deep dive.

> Next generation face swapper and enhancer. V2

[![Build Status](https://img.shields.io/github/actions/workflow/status/facefusion/facefusion/ci.yml.svg?branch=master)](https://github.com/facefusion/facefusion/actions?query=workflow:ci)
![License](https://img.shields.io/badge/license-MIT-green)


Preview
-------

![Preview](https://raw.githubusercontent.com/facefusion/facefusion/master/.github/preview.png?sanitize=true)


Installation
------------

Be aware, the installation needs technical skills and is not for beginners. Please do not open platform and installation related issues on GitHub. We have a very helpful [Discord](https://join.facefusion.io) community that will guide you to complete the installation.

Get started with the [installation](https://docs.facefusion.io/installation) guide.


Usage
-----

Run the command:

```
python run.py [options]

options:
  -h, --help                                                                                                         show this help message and exit
  -s SOURCE_PATH, --source SOURCE_PATH                                                                               select a source image
  -t TARGET_PATH, --target TARGET_PATH                                                                               select a target image or video
  -o OUTPUT_PATH, --output OUTPUT_PATH                                                                               specify the output file or directory
  -v, --version                                                                                                      show program's version number and exit

misc:
  --skip-download                                                                                                    omit automate downloads and lookups
  --headless                                                                                                         run the program in headless mode

execution:
  --execution-providers {cpu} [{cpu} ...]                                                                            choose from the available execution providers
  --execution-thread-count [1-128]                                                                                   specify the number of execution threads
  --execution-queue-count [1-32]                                                                                     specify the number of execution queries
  --max-memory [0-128]                                                                                               specify the maximum amount of ram to be used (in gb)

face analyser:
  --face-analyser-order {left-right,right-left,top-bottom,bottom-top,small-large,large-small,best-worst,worst-best}  specify the order used for the face analyser
  --face-analyser-age {child,teen,adult,senior}                                                                      specify the age used for the face analyser
  --face-analyser-gender {male,female}                                                                               specify the gender used for the face analyser
  --face-detector-model {retinaface,yunet}                                                                           specify the model used for the face detector
  --face-detector-size {160x160,320x320,480x480,512x512,640x640,768x768,960x960,1024x1024}                           specify the size threshold used for the face detector
  --face-detector-score [0.0-1.0]                                                                                    specify the score threshold used for the face detector

face selector:
  --face-selector-mode {reference,one,many}                                                                          specify the mode for the face selector
  --reference-face-position REFERENCE_FACE_POSITION                                                                  specify the position of the reference face
  --reference-face-distance [0.0-1.5]                                                                                specify the distance between the reference face and the target face
  --reference-frame-number REFERENCE_FRAME_NUMBER                                                                    specify the number of the reference frame

face mask:
  --face-mask-blur [0.0-1.0]                                                                                         specify the blur amount for face mask
  --face-mask-padding FACE_MASK_PADDING [FACE_MASK_PADDING ...]                                                      specify the face mask padding (top, right, bottom, left) in percent

frame extraction:
  --trim-frame-start TRIM_FRAME_START                                                                                specify the start frame for extraction
  --trim-frame-end TRIM_FRAME_END                                                                                    specify the end frame for extraction
  --temp-frame-format {jpg,png}                                                                                      specify the image format used for frame extraction
  --temp-frame-quality [0-100]                                                                                       specify the image quality used for frame extraction
  --keep-temp                                                                                                        retain temporary frames after processing

output creation:
  --output-image-quality [0-100]                                                                                     specify the quality used for the output image
  --output-video-encoder {libx264,libx265,libvpx-vp9,h264_nvenc,hevc_nvenc}                                          specify the encoder used for the output video
  --output-video-quality [0-100]                                                                                     specify the quality used for the output video
  --keep-fps                                                                                                         preserve the frames per second (fps) of the target
  --skip-audio                                                                                                       omit audio from the target

frame processors:
  --frame-processors FRAME_PROCESSORS [FRAME_PROCESSORS ...]                                                         choose from the available frame processors (choices: face_debugger, face_enhancer, face_swapper, frame_enhancer, ...)
  --face-debugger-items {bbox,kps,face-mask,score} [{bbox,kps,face-mask,score} ...]                                  specify the face debugger items
  --face-enhancer-model {codeformer,gfpgan_1.2,gfpgan_1.3,gfpgan_1.4,gpen_bfr_256,gpen_bfr_512,restoreformer}        choose the model for the frame processor
  --face-enhancer-blend [0-100]                                                                                      specify the blend factor for the frame processor
  --face-swapper-model {blendface_256,inswapper_128,inswapper_128_fp16,simswap_256,simswap_512_unofficial}           choose the model for the frame processor
  --frame-enhancer-model {real_esrgan_x2plus,real_esrgan_x4plus,real_esrnet_x4plus}                                  choose the model for the frame processor
  --frame-enhancer-blend [0-100]                                                                                     specify the blend factor for the frame processor

uis:
  --ui-layouts UI_LAYOUTS [UI_LAYOUTS ...]                                                                           choose from the available ui layouts (choices: benchmark, webcam, default, ...)
```


Documentation
-------------

Read the [documentation](https://docs.facefusion.io) for a deep dive.
