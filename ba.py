#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FaceFusion batch runner + comparison + HTML report
- keeps only swapper / occluder / enhancer model axes
- outputs per-run images, a results HTML and a results.zip
"""

import subprocess, itertools, time, html, sys, platform, shutil, zipfile, traceback
from pathlib import Path
import cv2, numpy as np
from skimage.metrics import structural_similarity as ssim
from tqdm import tqdm
import psutil
import mediapipe as mp

# ----------------------------
# 用户可修改参数
# ----------------------------
source_paths = ["images/source3.jpg","images/source1.jpg","images/source2.jpg"]   # list of source image paths
target_path = "images/target.jpg"       # target image path
output_dir = Path("./out")              # where outputs and HTML will be written
html_file = output_dir / "results.html"
zip_file = Path("results.zip")

# Only keep swapper + occluder + enhancer
face_swapper_models = [
    "blendswap_256",
  "hyperswap_1a_256", "hyperswap_1b_256",
"inswapper_128"
]


face_occluder_models = ["xseg_3"]  # Face Occluder models (example)

# Face Enhancer models (example)
face_enhancer_models = ["gfpgan_1.4", "gpen_bfr_512", "restoreformer_plus_plus","codeformer"]

# Command used to call facefusion in headless mode.
# Adjust if your entrypoint is different (e.g., "python3" or other args).
FACEFUSION_CMD = ["python", "facefusion.py", "headless-run"]

# ----------------------------
# Prepare output dir
# ----------------------------
if output_dir.exists():
    shutil.rmtree(output_dir)
output_dir.mkdir(parents=True, exist_ok=True)

# ----------------------------
# 系统信息获取
# ----------------------------
def get_system_info():
    info = {}
    info["os"] = platform.platform()
    info["python"] = platform.python_version()
    info["cpu"] = platform.processor() or "Unknown CPU"
    info["cpu_cores"] = psutil.cpu_count(logical=False) or 0
    info["cpu_threads"] = psutil.cpu_count(logical=True) or 0
    mem = psutil.virtual_memory()
    info["mem_total"] = round(mem.total / (1024**3), 2)
    info["mem_used"]  = round(mem.used / (1024**3), 2)
    info["mem_free"]  = round(mem.available / (1024**3), 2)
    disk = shutil.disk_usage(".")
    info["disk_total"] = round(disk.total / (1024**3),2)
    info["disk_free"]  = round(disk.free / (1024**3),2)
    # Try to get NVIDIA GPU info; ignore if fails
    try:
        gpu_raw = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
            stderr=subprocess.STDOUT
        ).decode().strip().split("\n")
        gpus = []
        for line in gpu_raw:
            name, mem_total, driver = [x.strip() for x in line.split(",")]
            gpus.append({"name": name, "mem_total": mem_total, "driver": driver})
        info["gpus"] = gpus
    except Exception:
        info["gpus"] = []
    try:
        cuda_output = subprocess.check_output(["nvcc", "--version"], stderr=subprocess.STDOUT).decode()
        for line in cuda_output.split("\n"):
            if "release" in line:
                info["cuda"] = line.strip()
                break
        else:
            info["cuda"] = "Unknown"
    except Exception:
        info["cuda"] = "Not installed"
    return info

sysinfo = get_system_info()

# ----------------------------
# Helper: 复制文件（到 output_dir，保留原名）
# ----------------------------
def copy_if_exists(src_path: Path, dst_path: Path):
    if src_path.exists():
        shutil.copy(src_path, dst_path)
        return True
    else:
        print(f"[WARN] File not found: {src_path}", file=sys.stderr)
        return False

# copy sources and target to output dir (so HTML thumbnails can reference easily)
for p in source_paths:
    copy_if_exists(Path(p), output_dir / Path(p).name)
copy_if_exists(Path(target_path), output_dir / Path(target_path).name)

# ----------------------------
# Helper: Mediapipe face detection & letterbox
# ----------------------------
# Use mediapipe face_detection. model_selection=1 chooses full-range model for faces (0/1)
mp_face_detection = mp.solutions.face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.3)

def detect_face_box(img):
    """Return (x1,y1,x2,y2) in pixel coordinates, or None."""
    if img is None:
        return None
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    res = mp_face_detection.process(rgb)
    if not res.detections:
        return None
    d = res.detections[0]
    box = d.location_data.relative_bounding_box
    h,w = img.shape[:2]
    x1 = int(max(box.xmin * w, 0))
    y1 = int(max(box.ymin * h, 0))
    x2 = int(min((box.xmin + box.width) * w, w))
    y2 = int(min((box.ymin + box.height) * h, h))
    if x2 <= x1 or y2 <= y1:
        return None
    return (x1, y1, x2, y2)

def letterbox_image(img, target_w, target_h):
    """Resize image to fit into target size preserving aspect ratio and center it on black canvas."""
    if img is None:
        return None
    h,w = img.shape[:2]
    scale = min(target_w / w, target_h / h)
    new_w, new_h = int(w * scale), int(h * scale)
    resized = cv2.resize(img, (new_w, new_h))
    canvas = np.zeros((target_h, target_w, 3), dtype=np.uint8)
    top, left = (target_h - new_h) // 2, (target_w - new_w) // 2
    canvas[top:top+new_h, left:left+new_w] = resized
    return canvas

def compare_face_region(source_img, output_img, source_box=None):
    """
    Compare face region between source_img and output_img.
    Returns (ssim_val, psnr_val). If faces not detected, returns (0.0, 0.0).
    """
    if source_img is None or output_img is None:
        return 0.0, 0.0
    h, w = source_img.shape[:2]
    output_resize = letterbox_image(output_img, w, h)
    if output_resize is None:
        return 0.0, 0.0
    box_s = source_box if source_box else detect_face_box(source_img)
    box_o = detect_face_box(output_resize)
    if not box_s or not box_o:
        return 0.0, 0.0
    x1s, y1s, x2s, y2s = box_s
    x1o, y1o, x2o, y2o = box_o
    face_s = source_img[y1s:y2s, x1s:x2s]
    face_o = output_resize[y1o:y2o, x1o:x2o]
    if face_s.size == 0 or face_o.size == 0:
        return 0.0, 0.0
    # resize output face to match source face size
    try:
        face_o = cv2.resize(face_o, (face_s.shape[1], face_s.shape[0]))
    except Exception:
        return 0.0, 0.0
    face_s_gray = cv2.cvtColor(face_s, cv2.COLOR_BGR2GRAY)
    face_o_gray = cv2.cvtColor(face_o, cv2.COLOR_BGR2GRAY)
    dr = float(face_o_gray.max() - face_o_gray.min()) or 255.0
    try:
        ssim_val = ssim(face_s_gray, face_o_gray, data_range=dr)
    except Exception:
        ssim_val = 0.0
    try:
        psnr_val = cv2.PSNR(face_s, face_o)
    except Exception:
        psnr_val = 0.0
    return float(ssim_val), float(psnr_val)

# ----------------------------
# 参数组合 & 主循环
# ----------------------------
param_combinations = list(itertools.product(
    face_swapper_models,
    face_occluder_models,
    face_enhancer_models
))

# read source images and detect boxes once
source_imgs = []
for p in source_paths:
    img = cv2.imread(p)
    if img is None:
        print(f"[WARN] Could not read source image: {p}", file=sys.stderr)
    source_imgs.append(img)
source_boxes = [detect_face_box(img) for img in source_imgs]

results = []
total_runs = len(source_imgs) * len(param_combinations)
pbar = tqdm(total=total_runs, desc="FaceFusion runs")

for src_idx, sp_img in enumerate(source_imgs):
    sp_name = Path(source_paths[src_idx]).name
    sp_box = source_boxes[src_idx]
    for combo_idx, (swap, occ, en) in enumerate(param_combinations):
        output_file = output_dir / f"result_s{src_idx}_c{combo_idx}.jpg"
        cmd = FACEFUSION_CMD + [
            "-s", source_paths[src_idx],
            "-t", target_path,
            "-o", str(output_file),
            "--face-swapper-model", swap,
            "--face-occluder-model", occ,
            "--face-enhancer-model", en
        ]
        start = time.time()
        status = "fail"
        ssim_val = 0.0
        psnr_val = 0.0
        elapsed = 0.0
        try:
            # run facefusion
            subprocess.run(cmd, check=True)
            elapsed = time.time() - start
            status = "success"
            output_img = cv2.imread(str(output_file))
            if output_img is not None:
                ssim_val, psnr_val = compare_face_region(sp_img, output_img, sp_box)
        except subprocess.CalledProcessError as e:
            elapsed = time.time() - start
            print(f"[ERROR] subprocess failed (cmd): {' '.join(cmd)}", file=sys.stderr)
            print(e, file=sys.stderr)
        except Exception as e:
            elapsed = time.time() - start
            print("[ERROR] Exception during run:", file=sys.stderr)
            traceback.print_exc()
        results.append(dict(
            swap=swap, occ=occ, en=en,
            source=sp_name,
            output=output_file.name if output_file.exists() else "",
            time=round(elapsed, 2),
            status=status,
            ssim=round(ssim_val, 4),
            psnr=round(psnr_val, 2)
        ))
        pbar.update(1)
pbar.close()

# ----------------------------
# HTML 输出（已移除 detector/landmarker/parser）
# ----------------------------
# prepare tab ids for each source
tab_ids = [f"tab_{i}" for i in range(len(source_paths))]

sysinfo_html = f"""
<h3>System Information</h3>
<ul>
<li><b>OS:</b> {sysinfo['os']}</li>
<li><b>Python:</b> {sysinfo['python']}</li>
<li><b>CPU:</b> {sysinfo['cpu']} ({sysinfo['cpu_cores']} cores / {sysinfo['cpu_threads']} threads)</li>
<li><b>Memory:</b> {sysinfo['mem_total']} GB total, {sysinfo['mem_used']} GB used, {sysinfo['mem_free']} GB free</li>
<li><b>Disk:</b> {sysinfo['disk_total']} GB total, {sysinfo['disk_free']} GB free</li>
<li><b>CUDA:</b> {sysinfo['cuda']}</li>
"""

if sysinfo["gpus"]:
    sysinfo_html += "<li><b>GPUs:</b><ul>"
    for g in sysinfo["gpus"]:
        sysinfo_html += f"<li>{g['name']} — {g['mem_total']} — Driver {g['driver']}</li>"
    sysinfo_html += "</ul></li>"
else:
    sysinfo_html += "<li><b>GPUs:</b> No NVIDIA GPU detected</li>"
sysinfo_html += "</ul>"

html_content = f"""
<html>
<head>
<meta charset="utf-8"/>
<title>模型对比结果</title>
<style>
body{{font-family:Arial;}}
table{{border-collapse:collapse;width:100%;margin-bottom:10px;}}
th,td{{border:1px solid #ccc;padding:5px;text-align:center;}}
th{{background:#f2f2f2;cursor:pointer;}}
img.thumb{{width:120px;border:1px solid #888;}}
.lightbox{{position:fixed;left:0;top:0;width:100%;height:100%;background: rgba(0,0,0,0.8); display:none; align-items:center; justify-content:center;}}
.lightbox img{{max-width:90%;max-height:90%;}}
.tabbtns button{{padding:5px 10px;cursor:pointer;margin-right:2px;}}
.tabcontent{{display:none;}}
.highest{{background:#ffff88;}}
</style>
<script>
function showLightbox(src) {{
    document.getElementById("lightbox").style.display = "flex";
    document.getElementById("lightimg").src = src;
}}
function hideLightbox() {{
    document.getElementById("lightbox").style.display = "none";
}}
function openTab(id) {{
    let contents = document.getElementsByClassName('tabcontent');
    for (let c of contents) c.style.display = 'none';
    let el = document.getElementById(id);
    if (el) el.style.display = 'block';
}}
function sortTable(n, table_id) {{
    var table = document.getElementById(table_id);
    var rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
    switching = true;
    dir = "desc";
    while (switching) {{
        switching = false;
        rows = table.rows;
        for (i = 1; i < rows.length - 1; i++) {{
            shouldSwitch = false;
            x = rows[i].getElementsByTagName("TD")[n];
            y = rows[i+1].getElementsByTagName("TD")[n];
            let xv = parseFloat(x.innerHTML) || 0;
            let yv = parseFloat(y.innerHTML) || 0;
            if (dir == "asc" ? xv > yv : xv < yv) {{
                shouldSwitch = true;
                break;
            }}
        }}
        if (shouldSwitch) {{
            rows[i].parentNode.insertBefore(rows[i+1], rows[i]);
            switching = true;
            switchcount++;
        }} else if (switchcount == 0 && dir == "desc") {{
            dir = "asc";
            switching = true;
        }}
    }}
}}
</script>
</head>
<body>
<h2>FaceFusion Model Comparison</h2>
<div class="tabbtns">
<button onclick="openTab('summary')">Summary</button>
"""

# buttons for each source tab
for idx, p in enumerate(source_paths):
    html_content += f'<button onclick="openTab(\'{tab_ids[idx]}\')">{Path(p).name}</button>'

html_content += "</div>\n"
html_content += sysinfo_html

# per-source tabs
for src_idx, sp in enumerate(source_paths):
    sp_name = Path(sp).name
    tab_id = tab_ids[src_idx]
    sp_results = [r for r in results if r['source'] == sp_name]
    if not sp_results:
        continue
    max_ssim = max((r["ssim"] for r in sp_results), default=0)
    max_psnr = max((r["psnr"] for r in sp_results), default=0)
    html_content += f'<div id="{tab_id}" class="tabcontent">'
    html_content += f'<h3>{sp_name} Results</h3>'
    html_content += '<table id="table_' + tab_id + '"><thead><tr>'
    html_content += '<th>Swapper</th><th>Occluder</th><th>Enhancer</th>'
    html_content += '<th>Source</th><th>Target</th><th>Output</th>'
    html_content += '<th onclick="sortTable(6,\'table_' + tab_id + '\')">Time(s)</th>'
    html_content += '<th>Status</th>'
    html_content += '<th onclick="sortTable(8,\'table_' + tab_id + '\')">SSIM</th>'
    html_content += '<th onclick="sortTable(9,\'table_' + tab_id + '\')">PSNR</th>'
    html_content += '</tr></thead><tbody>'
    target_name = Path(target_path).name
    for r in sp_results:
        out_img_tag = (f'<img class="thumb" src="{html.escape(r["output"])}" onclick="showLightbox(\'{html.escape(r["output"])}\')">'
                       if r["output"] else "(no output)")
        html_content += '<tr>'
        html_content += f'<td>{html.escape(r["swap"])}</td>'
        html_content += f'<td>{html.escape(r["occ"])}</td>'
        html_content += f'<td>{html.escape(r["en"])}</td>'
        html_content += f'<td><img class="thumb" src="{html.escape(sp_name)}" onclick="showLightbox(\'{html.escape(sp_name)}\')"></td>'
        html_content += f'<td><img class="thumb" src="{html.escape(target_name)}" onclick="showLightbox(\'{html.escape(target_name)}\')"></td>'
        html_content += f'<td>{out_img_tag}</td>'
        html_content += f'<td>{r["time"]}</td>'
        html_content += f'<td>{r["status"]}</td>'
        ssim_class = 'highest' if r["ssim"] == max_ssim else ''
        psnr_class = 'highest' if r["psnr"] == max_psnr else ''
        html_content += f'<td class="{ssim_class}">{r["ssim"]}</td>'
        html_content += f'<td class="{psnr_class}">{r["psnr"]}</td>'
        html_content += '</tr>'
    html_content += '</tbody></table></div>'

# Summary tab
html_content += '<div id="summary" class="tabcontent">'
html_content += '<h3>Summary (Average per Model Combination)</h3>'

summary_data = {}
for r in results:
    # key is (swapper, occluder, enhancer)
    key = (r['swap'], r['occ'], r['en'])
    summary_data.setdefault(key, []).append((r['ssim'], r['psnr']))

# find best averages for highlighting
avg_ssim_all = 0.0
avg_psnr_all = 0.0
if summary_data:
    avg_ssim_all = max((sum(v[0] for v in vals)/len(vals) for vals in summary_data.values()), default=0)
    avg_psnr_all = max((sum(v[1] for v in vals)/len(vals) for vals in summary_data.values()), default=0)

html_content += '<table id="summary_table"><thead><tr>'
html_content += '<th>Swapper</th><th>Occluder</th><th>Enhancer</th>'
html_content += '<th onclick="sortTable(3,\'summary_table\')">Avg SSIM</th>'
html_content += '<th onclick="sortTable(4,\'summary_table\')">Avg PSNR</th></tr></thead><tbody>'
for key, vals in summary_data.items():
    avg_ssim = round(sum(v[0] for v in vals) / len(vals), 4)
    avg_psnr = round(sum(v[1] for v in vals) / len(vals), 2)
    ssim_class = 'highest' if avg_ssim == avg_ssim_all else ''
    psnr_class = 'highest' if avg_psnr == avg_psnr_all else ''
    swap, occ, en = key
    html_content += '<tr>'
    html_content += f'<td>{swap}</td><td>{occ}</td><td>{en}</td>'
    html_content += f'<td class="{ssim_class}">{avg_ssim}</td>'
    html_content += f'<td class="{psnr_class}">{avg_psnr}</td></tr>'
html_content += '</tbody></table></div>'

# Lightbox and default tab open
html_content += """
<div id="lightbox" class="lightbox" onclick="hideLightbox()">
<img id="lightimg">
</div>
<script>
"""
# choose default tab: first source if exists else summary
default_tab = tab_ids[0] if tab_ids else "summary"
html_content += f"openTab('{default_tab}');\n"
html_content += "</script></body></html>"

# write HTML to file
with open(html_file, "w", encoding="utf-8") as f:
    f.write(html_content)

# ----------------------------
# 打包 zip (包含 out folder contents)
# ----------------------------
with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zf:
    for file in output_dir.iterdir():
        # include files in root of zip
        zf.write(file, arcname=file.name)

print("\nDone!")
print("HTML saved at:", html_file)
print("Results zipped at:", zip_file)
