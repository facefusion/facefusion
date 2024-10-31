from typing import List, Optional, Tuple

from facefusion import process_manager, state_manager, wording
import gradio as gr
import psutil
import subprocess
import platform
import pandas as pd
import matplotlib.pyplot as plt

TOTAL_RAM_SLIDER: Optional[gr.Slider] = None 
CHARTIFACE: Optional[gr.Interface] = None
CHART_CLEAR_BUTTON: Optional[gr.Button] = None
CHART_REFRESH_BUTTON: Optional[gr.Button] = None

def get_ram_info():  
    ram = psutil.virtual_memory()  
    total_ram = round(ram.total / (1024 ** 3), 2)  # Convert bytes to GB  
    available_ram = round(ram.free / (1024 ** 3), 2)  # Convert bytes to GB  
    return total_ram, available_ram  

def get_vram_info():
    vram_info = []
    
    try:
        if platform.system() == "Windows":
            # Get GPU details
            command = "wmic path win32_VideoController get name, adapterram"
            output = subprocess.check_output(command, shell=True).decode().strip().split("\n")[1:]
            for line in output:
                if line.strip():
                    parts = line.split()
                    gpu_name = " ".join(parts[:-1])
                    total_vram = int(parts[-1]) / (1024 ** 2)  # Convert bytes to GB
                    # Get current VRAM usage using nvidia-smi
                    usage_command = "nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits"
                    current_usage = subprocess.check_output(usage_command, shell=True).decode().strip().split("\n")[0]
                    used_vram = int(current_usage)  # Used VRAM in MB
                    vram_info.append((gpu_name, total_vram, used_vram / 1024))  # Convert to GB
        
        elif platform.system() == "Linux":
            # Get GPU names and total VRAM using nvidia-smi
            command = "nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits"
            output = subprocess.check_output(command, shell=True).decode().strip().split("\n")
            for line in output:
                if line.strip():
                    parts = line.split(", ")
                    gpu_name = parts[0]
                    total_vram = int(parts[1])  # Total VRAM in MB
                    # Get current VRAM usage
                    usage_command = "nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits"
                    current_usage = subprocess.check_output(usage_command, shell=True).decode().strip().split("\n")[0]
                    used_vram = int(current_usage)  # Used VRAM in MB
                    vram_info.append((gpu_name, total_vram / 1024, used_vram / 1024))  # Convert to GB

        else:
            print("Unsupported OS")
            return []

        return vram_info

    except Exception as e:
        print(f"An error occurred: {e}")
        return []

def plot_vram_chart():
    vram_info = get_vram_info()
    total_ram, available_ram = get_ram_info()  
    vram_info.append(("RAM", total_ram, available_ram))
    print(vram_info)

    gpu_names = [gpu[0] for gpu in vram_info]
    used_vram = [gpu[2] for gpu in vram_info]
    total_vram = [gpu[1] for gpu in vram_info]

    # Create a bar chart using matplotlib
    plt.figure(figsize=(10, 5))
    bars = plt.bar(gpu_names, used_vram, label='Used VRAM', color='blue')
    plt.bar(gpu_names, [total - used for total, used in zip(total_vram, used_vram)], 
            bottom=used_vram, label='Free VRAM', color='orange')
    
    plt.ylabel('VRAM (GB)')
    plt.title('VRAM Usage')
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Save the plot to a file
    plt.savefig("vram_usage.png")
    plt.close()

    return "vram_usage.png"

def render() -> None:  
    global TOTAL_RAM_SLIDER
    global CHARTIFACE
    global CHART_REFRESH_BUTTON
    global CHART_CLEAR_BUTTON

    total_ram, available_ram = get_ram_info()  
    TOTAL_RAM_SLIDER = gr.Slider(  
        label="USED RAM SIZE ",  
        info=f"TOTAL RAM SIZE {total_ram} GB",
        value=round(total_ram - available_ram, 2),  
        step=0.1,  
        minimum=0,  
        maximum=total_ram  
    )  

    vram_info = get_vram_info()  

    if vram_info:
        vram_info.append(("RAM", total_ram, available_ram))
    else:
        print("No VRAM information available.")
        vram_info.append(("RAM", total_ram, available_ram))

    # Create the Gradio Blocks interface
    with gr.Blocks() as CHARTIFACE:
        # Custom CSS to hide buttons
        gr.Markdown(
            """
            <style>
                .gr-button { display: none; }
            </style>
            """
        )
        
        # Button to generate the plot
        btn = gr.Button("RAM, VRAM USAGE", variant='primary', size='sm')
        img = gr.Image(type="filepath")

        initial_image = plot_vram_chart()
        img.value = initial_image

        # Set the button action
        btn.click(fn=plot_vram_chart, outputs=img)

def listen() -> None: 
    pass