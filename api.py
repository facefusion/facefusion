# Setup
# pip install Flask
# pip install waitress

# Run Dev
# .\venv\Scripts\python.exe .\api.py --host 0.0.0.0 --port 9777 headless-run --log-level=info --execution-device-id 0 --execution-providers cuda --video-memory-strategy tolerant

# Run Prod
# .\venv\Scripts\python.exe .\api.py --host 127.0.0.1 --port 18001 headless-run --log-level=info --execution-device-id 0 --execution-providers cuda --video-memory-strategy tolerant
# .\venv\Scripts\python.exe .\api.py --host 127.0.0.1 --port 18002 headless-run --log-level=info --execution-device-id 1 --execution-providers cuda --video-memory-strategy tolerant
# .\venv\Scripts\python.exe .\api.py --host 127.0.0.1 --port 18003 headless-run --log-level=info --execution-device-id 2 --execution-providers cuda --video-memory-strategy tolerant
# .\venv\Scripts\python.exe .\api.py --host 127.0.0.1 --port 18004 headless-run --log-level=info --execution-device-id 3 --execution-providers cuda --video-memory-strategy tolerant

import signal
import os
import tempfile
import argparse
from threading import Lock
from flask import Flask, request
from waitress import serve
from facefusion import logger, state_manager
from facefusion.args import apply_args
from facefusion.program import create_program
from facefusion.program_helper import validate_args
from facefusion.exit_helper import graceful_exit, hard_exit
from facefusion.core import (
    common_pre_check,
    conditional_process,
    pre_check,
    processors_pre_check,
)
from facefusion.vision import detect_image_resolution, pack_resolution

app = Flask(__name__)

mutex = Lock()
temp_dir = os.path.join(app.root_path, "temp")
global_models = [
    "hyperswap_1a_256",
    "hyperswap_1b_256",
    "hyperswap_1c_256",
    "inswapper_128",
    "inswapper_128_fp16",
    "blendswap_256",
    "ghost_1_256",
    "ghost_2_256",
    "ghost_3_256",
    "hififace_unofficial_256",
    "simswap_256",
    "uniface_256",
]
global_detector_models = ["yolo_face", "retinaface", "scrfd", "many"]
global_restore_models = [
    "codeformer",
    "gfpgan_1.4",
    "gpen_bfr_256",
    "gpen_bfr_512",
    "gpen_bfr_1024",
    "gpen_bfr_2048",
    "restoreformer_plus_plus",
]
global_upscale_models = [
    "real_esrgan_x2",
    "real_esrgan_x2_fp16",
    "real_esrgan_x4",
    "real_esrgan_x4_fp16",
    "real_esrgan_x8",
    "real_esrgan_x8_fp16",
    "real_hatgan_x4",
    "real_web_photo_x4",
    "realistic_rescaler_x4",
    "span_kendata_x4",
    "ultra_sharp_x4",
]


@app.route("/face_swap", methods=["post"])
def swap_face():
    try:
        processors = request.form.get("processors", "face_swapper").split(",")
        model = request.form.get("model", "hyperswap_1c_256")
        pixel_boost = request.form.get("pixel_boost", "256x256")
        selector_mode = request.form.get("selector_mode", "one")
        detector_model = request.form.get("detector_model", "yolo_face")
        restore_model = request.form.get("restore_model", "gfpgan_1.4")
        restore_visibility = float(request.form.get("restore_visibility", "0.8"))
        upscale_model = request.form.get("upscale_model", "span_kendata_x4")
        upscale_visibility = float(request.form.get("upscale_visibility", "0.8"))

        if model not in global_models:
            print(f"invalid model: {model}")
            return {"error": f"invalid model: {model}"}, 400
        if detector_model not in global_detector_models:
            print(f"invalid detector_model: {detector_model}")
            return {"error": f"invalid detector_model: {detector_model}"}, 400
        if restore_model != "" and restore_model not in global_restore_models:
            print(f"invalid restore_model: {restore_model}")
            return {"error": f"invalid restore_model: {restore_model}"}, 400
        if upscale_model != "" and upscale_model not in global_upscale_models:
            print(f"invalid upscale_model: {upscale_model}")
            return {"error": f"invalid upscale_model: {upscale_model}"}, 400

        if not (0 <= restore_visibility <= 1):
            print(f"invalid restore_visibility: {restore_visibility}")
            return {"error": f"invalid restore_visibility: {restore_visibility}"}, 400
        if not (0 <= upscale_visibility <= 1):
            print(f"invalid upscale_visibility: {upscale_visibility}")
            return {"error": f"invalid upscale_visibility: {upscale_visibility}"}, 400

        source = request.files.get("source", None)
        target = request.files.get("target", None)

        if not (source and target):
            print("source or target required")
            return {"error": "source or target required"}, 400

        with mutex:

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=f'.{source.filename.split(".")[-1]}',
                dir=temp_dir,
            ) as temp_source:
                source.save(temp_source)
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=f'.{target.filename.split(".")[-1]}',
                dir=temp_dir,
            ) as temp_target:
                target.save(temp_target)
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=f'.o.{target.filename.split(".")[-1]}',
                dir=temp_dir,
            ) as temp_output:
                pass

            state_manager.set_item("processors", processors)
            state_manager.set_item("face_swapper_model", model)
            state_manager.set_item("face_swapper_pixel_boost", pixel_boost)
            state_manager.set_item("face_selector_mode", selector_mode)
            state_manager.set_item("face_detector_model", detector_model)
            state_manager.set_item("face_enhancer_model", restore_model)
            state_manager.set_item("face_enhancer_blend", int(restore_visibility * 100))
            state_manager.set_item("frame_enhancer_model", upscale_model)
            state_manager.set_item(
                "frame_enhancer_blend", int(upscale_visibility * 100)
            )
            state_manager.set_item("source_paths", [temp_source.name])
            state_manager.set_item("target_path", temp_target.name)
            state_manager.set_item("output_path", temp_output.name)
            state_manager.set_item(
                "face_debugger_items",
                [
                    "face-landmark-5/68",
                    "face-mask",
                    "bounding-box",
                    "age",
                    "gender",
                    "race",
                    "face-detector-score",
                ],
            )
            state_manager.set_item("output_image_quality", 95)

            output_image_resolution = detect_image_resolution(temp_target.name)
            state_manager.set_item(
                "output_image_resolution", pack_resolution(output_image_resolution)
            )

            result = conditional_process()
            if result != 0:
                print(f"process error: {result}")
                return {"error": f"process error: {result}"}, 500

            with open(temp_output.name, "rb") as f:
                output_stream = f.read()

            ext = temp_output.name.split(".")[-1].lower()
            content_type = {
                "jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "png": "image/png",
                "webp": "image/webp",
            }.get(ext, "application/octet-stream")

            return output_stream, 200, {"Content-Type": content_type}
    except Exception as e:
        print(f"exception: {e}")
        return {"error": f"exception: {e}"}, 500
    finally:
        try:
            if "temp_source" in locals():
                os.unlink(temp_source.name)
            if "temp_target" in locals():
                os.unlink(temp_target.name)
            if "temp_output" in locals():
                os.unlink(temp_output.name)
        except OSError:
            pass


if __name__ == "__main__":
    os.makedirs(temp_dir, exist_ok=True)
    signal.signal(signal.SIGINT, lambda signal_number, frame: graceful_exit(0))
    program = create_program()
    if validate_args(program):
        args = vars(program.parse_args())
        apply_args(args, state_manager.init_item)
        logger.init(state_manager.get_item("log_level"))
        if not pre_check():
            hard_exit(2)
        if not common_pre_check() or not processors_pre_check():
            hard_exit(2)
        logger.info(f"Server running at http://{args['host']}:{args['port']}", __name__)
        serve(app, host=args["host"], port=args["port"], threads=16)
    else:
        hard_exit(2)
