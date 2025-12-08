import gradio as gr

from facefusion import state_manager
from facefusion.uis.components import (
    face_selector,
    instant_runner,
    job_manager,
    job_runner,
    output,
    preview,
    preview_options,
    source,
    target,
    ui_workflow,
)


def preload_defaults():
    # Processor defaults (required)
    state_manager.set_item("processors", ["face_swapper"])

    # Face swapper defaults
    state_manager.set_item("face_swapper_model", "inswapper_128")
    state_manager.set_item("face_swapper_pixel_boost", "128x128")
    state_manager.set_item("face_swapper_weight", 0.90)

    # Mask defaults
    state_manager.set_item("face_mask_types", ["box", "occlusion"])

    # Preview
    state_manager.set_item("preview_mode", "default")
    state_manager.set_item("preview_resolution", "1024x1024")

    # Face selector
    state_manager.set_item("face_selector_mode", "reference")
    state_manager.set_item("reference_face_position", 0)
    state_manager.set_item("reference_frame_number", 0)
    state_manager.set_item("reference_face_distance", 0.33)


def pre_check():
    return True


def render():
    preload_defaults()

    with gr.Blocks() as layout:

        with gr.Row():

            # ---------------------------------
            # LEFT PANEL: source + target
            # ---------------------------------
            with gr.Column(scale=4):
                source.render()
                target.render()

            # ---------------------------------
            # MIDDLE PANEL: output + job systems
            # ---------------------------------
            with gr.Column(scale=4):
                output.render()  # Output path + output preview
                ui_workflow.render()  # Workflow dropdown
                instant_runner.render()  # START & CLEAR
                job_runner.render()  # Job Runner panel
                job_manager.render()  # Job Manager

            # ---------------------------------
            # RIGHT PANEL: preview & face selector
            # ---------------------------------
            with gr.Column(scale=8):
                preview.render()
                preview_options.render()
                face_selector.render()

    return layout


def listen():
    # Input handlers
    source.listen()
    target.listen()

    # 🔥 OUTPUT HARUS SEBELUM PREVIEW — agar video muncul
    output.listen()

    # Preview updates
    preview.listen()
    preview_options.listen()

    # Face selector (setelah preview options)
    face_selector.listen()

    # Workflow + process runners
    instant_runner.listen()
    job_runner.listen()
    job_manager.listen()


def run(ui):
    ui.launch(
        favicon_path="facefusion.ico",
        server_name="0.0.0.0",
        server_port=7860,
        inbrowser=False,
    )
