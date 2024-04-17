#!/usr/bin/env python3

import gradio as gr
from modules import script_callbacks

import facefusion.globals
from facefusion import logger
from facefusion.core import apply_args, get_argument_parser, pre_check
from facefusion.processors.frame.modules import (
    face_debugger,
    face_enhancer,
    face_swapper,
    frame_enhancer,
    frame_colorizer,
    lip_syncer,
)
from facefusion.uis.layouts import default


def on_ui_tabs():
    apply_args(get_argument_parser())
    logger.init(facefusion.globals.log_level)

    if not pre_check():
        return

    if (
        not face_debugger.pre_check()
        or not face_enhancer.pre_check()
        or not face_swapper.pre_check()
        or not frame_colorizer.pre_check()
        or not frame_enhancer.pre_check()
        or not lip_syncer.pre_check()
    ):
        return

    if not default.pre_check():
        return

    with gr.Blocks() as block:
        if default.pre_render():
            default.render()
            default.listen()

        return ((block, "FaceFusion", "facefusion"),)


script_callbacks.on_ui_tabs(on_ui_tabs)
