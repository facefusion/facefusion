# app.py
import os
import traceback
import uuid
from io import BytesIO
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

# ---- 引入 facefusion ----
from facefusion import state_manager, logger
from facefusion.args import apply_args
from facefusion.jobs import job_manager, job_store
from facefusion.setup_args import setup_args
from facefusion.core import process_headless_v2


# =============== FastAPI ===============
app = FastAPI(title="FaceFusion API")

# 创建临时目录
TEMP_DIR = Path("./temp")
TEMP_DIR.mkdir(exist_ok=True)


# -------- 启动初始化 --------
@app.on_event("startup")
def startup():
    print("🔥 Initializing facefusion ...")

    job_keys = ['config_path', 'temp_path', 'jobs_path', 'execution_device_id', 'execution_providers', 'execution_thread_count', 'execution_queue_count', 'download_providers', 'video_memory_strategy', 'system_memory_limit', 'log_level']
    step_keys = ['source_paths', 'target_path', 'output_path', 'face_detector_model', 'face_detector_angles', 'face_detector_size', 'face_detector_score', 'face_landmarker_model', 'face_landmarker_score', 'face_selector_mode', 'face_selector_order', 'face_selector_gender', 'face_selector_race', 'face_selector_age_start', 'face_selector_age_end', 'reference_face_position', 'reference_face_distance', 'reference_frame_number', 'face_occluder_model', 'face_parser_model', 'face_mask_types', 'face_mask_areas', 'face_mask_regions', 'face_mask_blur', 'face_mask_padding', 'trim_frame_start', 'trim_frame_end', 'temp_frame_format', 'keep_temp', 'output_image_quality', 'output_image_resolution', 'output_audio_encoder', 'output_audio_quality', 'output_audio_volume', 'output_video_encoder', 'output_video_preset', 'output_video_quality', 'output_video_resolution', 'output_video_fps', 'processors', 'age_modifier_model', 'age_modifier_direction', 'deep_swapper_model', 'deep_swapper_morph', 'expression_restorer_model', 'expression_restorer_factor', 'face_debugger_items', 'face_editor_model', 'face_editor_eyebrow_direction', 'face_editor_eye_gaze_horizontal', 'face_editor_eye_gaze_vertical', 'face_editor_eye_open_ratio', 'face_editor_lip_open_ratio', 'face_editor_mouth_grim', 'face_editor_mouth_pout', 'face_editor_mouth_purse', 'face_editor_mouth_smile', 'face_editor_mouth_position_horizontal', 'face_editor_mouth_position_vertical', 'face_editor_head_pitch', 'face_editor_head_yaw', 'face_editor_head_roll', 'face_enhancer_model', 'face_enhancer_blend', 'face_enhancer_weight', 'face_swapper_model', 'face_swapper_pixel_boost', 'frame_colorizer_model', 'frame_colorizer_blend', 'frame_colorizer_size', 'frame_enhancer_model', 'frame_enhancer_blend', 'lip_syncer_model', 'lip_syncer_weight']

    try:
        job_store.register_job_keys(job_keys)
        job_store.register_step_keys(step_keys)
    except:
        pass

    defaults = setup_args()
    try:
        apply_args(defaults, state_manager.init_item)
    except:
        pass

    try:
        logger.init(state_manager.get_item("log_level"))
    except:
        logger.init("info")

    try:
        job_manager.init_jobs(state_manager.get_item("jobs_path"))
    except:
        default_path = os.path.abspath("./jobs")
        os.makedirs(default_path, exist_ok=True)
        state_manager.init_item("jobs_path", default_path)
        job_manager.init_jobs(default_path)

    print("✅ FaceFusion Initialized!")


# -------- 执行接口（文件上传版） --------
@app.post("/run")
async def run_facefusion(
    source_file: UploadFile = File(..., description="源图片（人脸）"),
    target_file: UploadFile = File(..., description="目标图片（要换脸的对象）"),
    options: Optional[str] = None
):
    """
    上传源图片和目标图片，返回换脸后的图片
    """
    # 验证文件类型
    allowed_image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
    
    source_ext = os.path.splitext(source_file.filename)[1].lower()
    target_ext = os.path.splitext(target_file.filename)[1].lower()
    
    if source_ext not in allowed_image_extensions:
        raise HTTPException(400, f"源图片格式不支持，请使用: {', '.join(allowed_image_extensions)}")
    
    if target_ext not in allowed_image_extensions:
        raise HTTPException(400, f"目标图片格式不支持，请使用: {', '.join(allowed_image_extensions)}")
    
    # 生成唯一文件名
    source_filename = f"source_{uuid.uuid4().hex}{source_ext}"
    target_filename = f"target_{uuid.uuid4().hex}{target_ext}"
    output_filename = f"output_{uuid.uuid4().hex}{target_ext}"
    
    source_path = TEMP_DIR / source_filename
    target_path = TEMP_DIR / target_filename
    output_path = TEMP_DIR / output_filename
    
    # 保存上传的文件
    try:
        source_content = await source_file.read()
        target_content = await target_file.read()
        
        with open(source_path, "wb") as f:
            f.write(source_content)
        with open(target_path, "wb") as f:
            f.write(target_content)
    except Exception as e:
        raise HTTPException(500, f"保存文件失败: {str(e)}")
    
    # 解析选项
    option_dict = {}
    if options:
        try:
            import json
            option_dict = json.loads(options)
        except:
            pass
    
    # 准备参数
    args = setup_args()
    args["command"] = "headless-run"
    args["source_paths"] = [str(source_path)]
    args["target_path"] = str(target_path)
    args["output_path"] = str(output_path)
    
    # 应用用户选项
    for k, v in option_dict.items():
        if k in args:  # 只覆盖存在的参数
            args[k] = v
    
    try:
        # 初始化并执行
        apply_args(args, state_manager.init_item)
        result = process_headless_v2(args)
        
        # 检查输出文件是否存在
        if not os.path.exists(output_path):
            # 清理临时文件
            try:
                source_path.unlink(missing_ok=True)
                target_path.unlink(missing_ok=True)
            except:
                pass
            
            return JSONResponse(
                status_code=500,
                content={
                    "ok": False,
                    "error": "换脸失败，输出文件未生成",
                    "detail": str(result)
                }
            )
        
        # 读取输出文件
        with open(output_path, "rb") as f:
            output_content = f.read()
        
        # 清理临时文件
        try:
            source_path.unlink(missing_ok=True)
            target_path.unlink(missing_ok=True)
            output_path.unlink(missing_ok=True)
        except:
            pass
        
        # 返回图片
        return StreamingResponse(
            BytesIO(output_content),
            media_type=f"image/{target_ext[1:].lower() if target_ext[1:] != 'jpg' else 'jpeg'}",
            headers={
                "Content-Disposition": f"attachment; filename=facefusion_result{target_ext}"
            }
        )
        
    except Exception as e:
        # 清理临时文件
        try:
            source_path.unlink(missing_ok=True)
            target_path.unlink(missing_ok=True)
            output_path.unlink(missing_ok=True)
        except:
            pass
        
        tb = traceback.format_exc()
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": f"换脸处理失败: {str(e)}",
                "traceback": tb
            }
        )


# -------- 健康检查 --------
@app.get("/health")
def health():
    return {"status": "ok", "service": "facefusion-api"}


# -------- 主入口 --------
if __name__ == "__main__":
    print("🚀 Starting FaceFusion API on 0.0.0.0:6006 ...")
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=6006,
        reload=False
    )