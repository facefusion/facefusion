import subprocess
import itertools
import time
import csv
from pathlib import Path
import cv2
from skimage.metrics import structural_similarity as ssim
import numpy as np

# ==== 输入输出 ====
source_paths = ["images/source1.jpg", "images/source2.jpg", "images/source3.jpg"]
target_path = "images/target.jpg"
output_dir = Path("./out")
output_dir.mkdir(exist_ok=True)

# ==== 参数列表 ====
face_swapper_models = [
    "blendswap_256", "ghost_1_256", "ghost_2_256", "ghost_3_256",
    "hififace_unofficial_256", "hyperswap_1a_256", "hyperswap_1b_256",
    "hyperswap_1c_256", "inswapper_128", "inswapper_128_fp16",
    "simswap_256", "simswap_unofficial_512", "uniface_256"
]

face_detector_models = ["many", "retinaface", "scrfd"]
face_landmarker_models = ["many", "2dfan4", "peppa_wutz"]
face_parser_models = ["bisenet_resnet_18", "bisenet_resnet_34"]
face_occluder_models = ["xseg_1", "xseg_2", "xseg_3"]

# ==== 生成参数组合 ====
param_combinations = list(itertools.product(
    face_swapper_models,
    face_detector_models,
    face_landmarker_models,
    face_parser_models,
    face_occluder_models
))

# ==== 输出 CSV 和 HTML ====
csv_file = output_dir / "facefusion_results.csv"
html_file = output_dir / "facefusion_results.html"

# 读取目标图像
target_img = cv2.imread(target_path)
if target_img is None:
    raise FileNotFoundError(f"Target image not found: {target_path}")
target_gray = cv2.cvtColor(target_img, cv2.COLOR_BGR2GRAY)

html_rows = []

with open(csv_file, mode="w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "face_swapper_model", "detector_model", "landmarker_model", "parser_model", "occluder_model",
        "output_file", "time_sec", "status", "SSIM", "PSNR"
    ])

    for idx, (swap_model, det_model, land_model, parser_model, occluder_model) in enumerate(param_combinations):
        output_file = output_dir / f"result_{idx}.jpg"
        cmd = [
            "python", "facefusion.py", "headless-run",
            "-s", *source_paths,
            "-t", target_path,
            "-o", str(output_file),
            "--face-swapper-model", swap_model,
            "--face-detector-model", det_model,
            "--face-landmarker-model", land_model,
            "--face-parser-model", parser_model,
            "--face-occluder-model", occluder_model
        ]
        print(f"[{idx+1}/{len(param_combinations)}] Running: {cmd}")

        start_time = time.time()
        try:
            subprocess.run(cmd, check=True)
            elapsed = time.time() - start_time
            status = "success"

            # ==== 计算 SSIM 和 PSNR ====
            output_img = cv2.imread(str(output_file))
            if output_img is not None:
                output_gray = cv2.cvtColor(output_img, cv2.COLOR_BGR2GRAY)
                ssim_val = ssim(target_gray, output_gray, data_range=output_gray.max() - output_gray.min())
                psnr_val = cv2.PSNR(target_img, output_img)
            else:
                ssim_val = 0
                psnr_val = 0

        except subprocess.CalledProcessError:
            elapsed = time.time() - start_time
            status = "fail"
            ssim_val = 0
            psnr_val = 0

        # 写入 CSV
        writer.writerow([swap_model, det_model, land_model, parser_model, occluder_model,
                         output_file.name, round(elapsed, 2), status, round(ssim_val, 4), round(psnr_val, 2)])
        f.flush()

        # ==== HTML 记录 ====
        html_rows.append(f"""
        <tr>
            <td>{swap_model}</td>
            <td>{det_model}</td>
            <td>{land_model}</td>
            <td>{parser_model}</td>
            <td>{occluder_model}</td>
            <td><img src="{output_file.name}" width="200"></td>
            <td>{round(elapsed,2)}</td>
            <td>{status}</td>
            <td>{round(ssim_val,4)}</td>
            <td>{round(psnr_val,2)}</td>
        </tr>
        """)

# ==== 写 HTML 文件 ====
html_content = f"""
<html>
<head>
    <title>FaceFusion Parameter Comparison</title>
    <style>
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ccc; padding: 5px; text-align: center; }}
        th {{ background-color: #eee; }}
        img {{ border: 1px solid #aaa; }}
    </style>
</head>
<body>
<h2>FaceFusion Parameter Comparison</h2>
<table>
<tr>
<th>Swapper</th><th>Detector</th><th>Landmarker</th><th>Parser</th><th>Occluder</th>
<th>Output</th><th>Time(s)</th><th>Status</th><th>SSIM</th><th>PSNR</th>
</tr>
{''.join(html_rows)}
</table>
</body>
</html>
"""

with open(html_file, "w") as f:
    f.write(html_content)

print(f"All tests done. CSV saved in {csv_file}, HTML saved in {html_file}")
