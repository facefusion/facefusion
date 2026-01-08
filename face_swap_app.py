#!/usr/bin/env python3
"""
Basit Yuz Degistirme Uygulamasi
Face Swap Application - Turkish Interface
"""

import os
import sys
import cv2
import gradio as gr
import numpy as np
from pathlib import Path

# FaceFusion modullerini ice aktar
os.environ['OMP_NUM_THREADS'] = '1'

# FaceFusion path ayarlari
sys.path.insert(0, os.path.dirname(__file__))

from facefusion import state_manager
from facefusion.face_analyser import get_one_face, get_many_faces
from facefusion.processors.modules.face_swapper.core import swap_face, pre_check, get_model_options
from facefusion.vision import read_static_image
from facefusion.download import conditional_download_hashes, conditional_download_sources


def initialize_facefusion():
    """FaceFusion'i baslatir ve gerekli modelleri yukler"""
    # Temel state manager ayarlari
    state_manager.init_item('face_detector_model', 'yoloface')
    state_manager.init_item('face_detector_size', '640x640')
    state_manager.init_item('face_detector_score', 0.5)
    state_manager.init_item('face_landmarker_model', '2dfan4')
    state_manager.init_item('face_landmarker_score', 0.5)
    state_manager.init_item('face_recognizer_model', 'arcface_inswapper')
    state_manager.init_item('face_swapper_model', 'inswapper_128')
    state_manager.init_item('face_swapper_pixel_boost', '128x128')
    state_manager.init_item('face_swapper_weight', 0.5)
    state_manager.init_item('face_mask_types', ['box'])
    state_manager.init_item('face_mask_blur', 0.3)
    state_manager.init_item('face_mask_padding', (0, 0, 0, 0))
    state_manager.init_item('face_mask_regions', [])
    state_manager.init_item('face_mask_areas', [])
    state_manager.init_item('source_paths', [])
    state_manager.init_item('target_path', None)
    state_manager.init_item('output_path', None)
    state_manager.init_item('video_memory_strategy', 'moderate')
    state_manager.init_item('execution_providers', ['cpu'])
    state_manager.init_item('execution_thread_count', 4)
    state_manager.init_item('temp_path', '.facefusion/temp')

    # Modelleri kontrol et ve yukle
    try:
        if not pre_check():
            return False, "Model dosyalari yuklenemiyor. Lutfen internet baglantinizi kontrol edin."
        return True, "Basariyla baslatildi!"
    except Exception as e:
        return False, f"Hata: {str(e)}"


def process_face_swap(source_image, target_image, swap_strength):
    """
    Yuz degistirme islemi yapar

    Args:
        source_image: Kaynak yuz resmi (bu yuz hedef resme uygulanacak)
        target_image: Hedef resim (yuzun degistirilecegi resim)
        swap_strength: Degistirme gucu (0-1 arasi)

    Returns:
        Islenmis resim veya hata mesaji
    """
    try:
        if source_image is None or target_image is None:
            return None, "Lutfen hem kaynak hem de hedef resim yukleyin!"

        # Guc ayarini guncelle
        state_manager.set_item('face_swapper_weight', float(swap_strength))

        # Kaynak resmi gecici dosyaya kaydet
        temp_source_path = ".facefusion/temp/source.jpg"
        os.makedirs(os.path.dirname(temp_source_path), exist_ok=True)
        cv2.imwrite(temp_source_path, cv2.cvtColor(source_image, cv2.COLOR_RGB2BGR))
        state_manager.set_item('source_paths', [temp_source_path])

        # Kaynak yuzu analiz et
        source_frame = read_static_image(temp_source_path)
        source_faces = get_many_faces([source_frame])
        source_face = get_one_face(source_faces)

        if source_face is None:
            return None, "Kaynak resimde yuz bulunamadi! Lutfen acik bir yuz resmi secin."

        # Hedef yuzu analiz et
        target_frame = target_image.copy()
        if len(target_frame.shape) == 3 and target_frame.shape[2] == 3:
            target_frame_bgr = cv2.cvtColor(target_frame, cv2.COLOR_RGB2BGR)
        else:
            target_frame_bgr = target_frame

        target_faces = get_many_faces([target_frame_bgr])
        target_face = get_one_face(target_faces)

        if target_face is None:
            return None, "Hedef resimde yuz bulunamadi! Lutfen acik bir yuz iceren resim secin."

        # Yuz degistirme islemi
        result_frame = swap_face(source_face, target_face, target_frame_bgr)

        # RGB'ye cevir
        result_rgb = cv2.cvtColor(result_frame.astype(np.uint8), cv2.COLOR_BGR2RGB)

        return result_rgb, "Yuz degistirme basarili!"

    except Exception as e:
        return None, f"Hata olustu: {str(e)}"


def create_ui():
    """Gradio arayuzunu olusturur"""

    with gr.Blocks(title="Yuz Degistirme Uygulamasi", theme=gr.themes.Soft()) as app:
        gr.Markdown("""
        # 🎭 Yuz Degistirme Uygulamasi
        ### Face Swap Application

        Bu uygulama ile bir resimdeki yuzu baska bir resme aktarabilirsiniz.
        """)

        # Baslangic durumu
        init_status = gr.State({"initialized": False})

        with gr.Row():
            with gr.Column():
                gr.Markdown("### 📸 Kaynak Resim (Bu yuz kullanilacak)")
                source_input = gr.Image(
                    label="Kaynak Yuzu Yukleyin",
                    type="numpy",
                    height=300
                )
                gr.Markdown("*Acik ve net bir yuz resmi secin*")

            with gr.Column():
                gr.Markdown("### 🎯 Hedef Resim (Yuz degistirilecek)")
                target_input = gr.Image(
                    label="Hedef Resmi Yukleyin",
                    type="numpy",
                    height=300
                )
                gr.Markdown("*Yuzu degistirilecek resim*")

        with gr.Row():
            swap_strength = gr.Slider(
                minimum=0.0,
                maximum=1.0,
                value=0.5,
                step=0.05,
                label="Degistirme Gucu / Swap Strength",
                info="0 = Tamamen kaynak yuz, 1 = Karma (varsayilan: 0.5)"
            )

        with gr.Row():
            process_btn = gr.Button("🔄 Yuz Degistir / Swap Face", variant="primary", size="lg")
            clear_btn = gr.Button("🗑️ Temizle / Clear", variant="secondary")

        with gr.Row():
            status_text = gr.Textbox(
                label="Durum / Status",
                value="Hazir. Resimlerinizi yukleyin.",
                interactive=False
            )

        gr.Markdown("---")

        with gr.Row():
            output_image = gr.Image(
                label="✨ Sonuc / Result",
                type="numpy",
                height=400
            )

        gr.Markdown("""
        ---
        ### 📖 Kullanim Kilavuzu / How to Use
        1. **Kaynak Resim**: Kullanmak istediginiz yuzu iceren resmi yukleyin
        2. **Hedef Resim**: Yuzun degistirilecegi resmi yukleyin
        3. **Degistirme Gucu**: Karisim oranini ayarlayin (0.5 onerilir)
        4. **Yuz Degistir**: Butona tiklayarak islemi baslatın

        ### ⚠️ Onemli Notlar
        - Her iki resimde de acik ve net yuzler olmalidir
        - En iyi sonuc icin benzer acilardaki yuz resimleri kullanin
        - Isleme suresi resim boyutuna bagli olarak degisebilir

        ### 🔧 Powered by FaceFusion
        """)

        # Event handlers
        def process_with_init(source, target, strength, init_state):
            # Ilk kullanimda initialize et
            if not init_state["initialized"]:
                success, msg = initialize_facefusion()
                if not success:
                    return None, f"Baslangic hatasi: {msg}", init_state
                init_state["initialized"] = True

            result, status = process_face_swap(source, target, strength)
            return result, status, init_state

        def clear_all():
            return None, None, None, "Temizlendi. Yeni resimler yukleyebilirsiniz.", {"initialized": init_status.value["initialized"]}

        process_btn.click(
            fn=process_with_init,
            inputs=[source_input, target_input, swap_strength, init_status],
            outputs=[output_image, status_text, init_status]
        )

        clear_btn.click(
            fn=clear_all,
            inputs=[],
            outputs=[source_input, target_input, output_image, status_text, init_status]
        )

    return app


if __name__ == "__main__":
    print("=" * 60)
    print("  YUZ DEGISTIRME UYGULAMASI BASLATILIYOR")
    print("  FACE SWAP APPLICATION STARTING")
    print("=" * 60)
    print("\nFaceFusion modulleri yukleniyor...")
    print("Loading FaceFusion modules...")

    # Uygulamayi olustur ve baslat
    app = create_ui()

    print("\n" + "=" * 60)
    print("  UYGULAMA HAZIR!")
    print("  APPLICATION READY!")
    print("=" * 60)
    print("\nTarayicinizda acilacak sayfada yuz degistirme islemlerinizi yapabilirsiniz.")
    print("You can perform face swap operations in the browser window that opens.")
    print("\nUygulamayi durdurmak icin Ctrl+C tuslayin.")
    print("Press Ctrl+C to stop the application.")
    print("=" * 60 + "\n")

    # Uygulamayi baslat
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        quiet=False
    )
