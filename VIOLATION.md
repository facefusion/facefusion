# Naming Convention Violations

## Variables using `xxx_frame` instead of `xxx_vision_frame`

- `source_frame_resize` → `source_vision_frame_resize` in `facefusion/vision.py:290`
- `target_frame_resize` → `target_vision_frame_resize` in `facefusion/vision.py:291`

## Variables using `xxx_mask` instead of `xxx_vision_mask`

### box_mask → box_vision_mask

- `facefusion/face_masker.py:192`
- `facefusion/processors/modules/face_debugger/core.py:131`
- `facefusion/processors/modules/expression_restorer/core.py:158`
- `facefusion/processors/modules/age_modifier/core.py:179,205`
- `facefusion/processors/modules/face_enhancer/core.py:346`
- `facefusion/processors/modules/face_editor/core.py:208`
- `facefusion/processors/modules/deep_swapper/core.py:331`
- `facefusion/processors/modules/face_swapper/core.py:591`
- `facefusion/processors/modules/lip_syncer/core.py:189`

### occlusion_mask → occlusion_vision_mask

- `facefusion/face_masker.py:221,222`
- `facefusion/processors/modules/face_debugger/core.py:135`
- `facefusion/processors/modules/expression_restorer/core.py:165`
- `facefusion/processors/modules/age_modifier/core.py:186,212,214`
- `facefusion/processors/modules/face_enhancer/core.py:353`
- `facefusion/processors/modules/deep_swapper/core.py:338`
- `facefusion/processors/modules/face_swapper/core.py:595`
- `facefusion/processors/modules/lip_syncer/core.py:184`

### area_mask → area_vision_mask

- `facefusion/face_masker.py:235,237`
- `facefusion/processors/modules/face_debugger/core.py:140`
- `facefusion/processors/modules/deep_swapper/core.py:350`
- `facefusion/processors/modules/face_swapper/core.py:608`
- `facefusion/processors/modules/lip_syncer/core.py:197`

### region_mask → region_vision_mask

- `facefusion/face_masker.py:250,252,253`
- `facefusion/processors/modules/face_debugger/core.py:144`
- `facefusion/processors/modules/deep_swapper/core.py:354`
- `facefusion/processors/modules/face_swapper/core.py:612`

### crop_mask → crop_vision_mask

- `facefusion/processors/modules/face_debugger/core.py:147,148,149`
- `facefusion/processors/modules/expression_restorer/core.py:172,173`
- `facefusion/processors/modules/age_modifier/core.py:197,224,225`
- `facefusion/processors/modules/face_enhancer/core.py:360,361`
- `facefusion/processors/modules/deep_swapper/core.py:357,405,406,407,408`
- `facefusion/processors/modules/face_swapper/core.py:615,616`
- `facefusion/processors/modules/lip_syncer/core.py:206,207`

### temp_mask → temp_vision_mask

- `facefusion/face_masker.py:216,217,218`
