import multiprocessing
import gradio
import os
import re
import sys
import ast
import uuid
import time
import math
import json
import tempfile
import shutil
import socket
import shlex
import logging
import tkinter as tk
import platform
import threading
import subprocess
import configparser
from tkinter.filedialog import askdirectory
from tkinter import filedialog, Text, font, Toplevel, messagebox, PhotoImage, Tk, Canvas, Scrollbar, Frame, Label, Button
from io import BytesIO
import facefusion.globals
from facefusion import core
import facefusion.core as core
from facefusion.uis.components import about, frame_processors, frame_processors_options, execution, execution_thread_count, execution_queue_count, memory, temp_frame, output_options, common_options, source, target, output, preview, trim_frame, face_analyser, face_selector, face_masker


def pre_check() -> bool:
    return True

def pre_render() -> bool:
    return True


def render() -> gradio.Blocks:
    global ADD_JOB_BUTTON, RUN_JOBS_BUTTON, status_window
    with gradio.Blocks() as layout:
        with gradio.Row():
            with gradio.Column(scale = 2):
                with gradio.Blocks():
                    about.render()
                with gradio.Blocks():
                    frame_processors.render()
                with gradio.Blocks():
                    frame_processors_options.render()
                with gradio.Blocks():
                    execution.render()
                    execution_thread_count.render()
                    execution_queue_count.render()
                with gradio.Blocks():
                    memory.render()
                with gradio.Blocks():
                    temp_frame.render()
                with gradio.Blocks():
                    output_options.render()
            with gradio.Column(scale = 2):
                with gradio.Blocks():
                    source.render()
                with gradio.Blocks():
                    target.render()
                with gradio.Blocks():
                    output.render()
                # with gradio.Blocks():
                    # status_window.render()
                with gradio.Blocks():
                    ADD_JOB_BUTTON.render()
                with gradio.Blocks():
                    RUN_JOBS_BUTTON.render()
                with gradio.Blocks():
                    EDIT_JOB_BUTTON.render()
            with gradio.Column(scale = 3):
                with gradio.Blocks():
                    preview.render()
                with gradio.Blocks():
                    trim_frame.render()
                with gradio.Blocks():
                    face_selector.render()
                with gradio.Blocks():
                    face_masker.render()
                with gradio.Blocks():
                    face_analyser.render()
                with gradio.Blocks():
                    common_options.render()
    return layout

    

def listen() -> None:
    global EDIT_JOB_BUTTON, status_window
    ADD_JOB_BUTTON.click(assemble_queue)
    RUN_JOBS_BUTTON.click(execute_jobs)
    EDIT_JOB_BUTTON.click(edit_queue)
    # status_window.change(custom_print, inputs=[], outputs=[status_window])
    frame_processors.listen()
    frame_processors_options.listen()
    execution.listen()
    execution_thread_count.listen()
    execution_queue_count.listen()
    memory.listen()
    temp_frame.listen()
    output_options.listen()
    source.listen()
    target.listen()
    output.listen()
    preview.listen()
    trim_frame.listen()
    face_selector.listen()
    face_masker.listen()
    face_analyser.listen()
    common_options.listen()

def get_default_values_from_ini():
    #only needed for Sd-webui version Reads and parses default values from the ini file.
    default_values = {}
    with open(os.path.join(base_dir, "default_values.ini"), "r") as file:
        for line in file:
            key, val = line.strip().split(": ", 1)
            if val == "None":
                parsed_val = None
            else:
                # Parsing logic directly within this function
                if val.startswith('[') and val.endswith(']'):
                    parsed_val = val[1:-1].split(', ')
                elif val.startswith('(') and val.endswith(')'):
                    parsed_val = tuple(val[1:-1].split(', '))
                else:
                    try:
                        parsed_val = int(val)
                    except ValueError:
                        try:
                            parsed_val = float(val)
                        except ValueError:
                            parsed_val = val
            default_values[key] = parsed_val
    with open(os.path.join(working_dir, f"default_values.txt"), "w") as file:
        for key, val in default_values.items():
            file.write(f"{key}: {val}\n")
    return default_values

def assemble_queue():
    global RUN_JOBS_BUTTON, ADD_JOB_BUTTON, jobs_queue_file, jobs, default_values, current_values
    # default_values are already initialized, do not call for new default except if sd-webui version
    if automatic1111:
        default_values = get_default_values_from_ini()

    current_values = get_values_from_globals('current_values')

    differences = {}
    keys_to_skip = ["source_paths", "target_path", "output_path", "ui_layouts", "face_recognizer_model"]
    if "frame-processors" in current_values:
        frame_processors = current_values["frame-processors"]
        if "face-enhancer" not in frame_processors:
            keys_to_skip.append("face-enhancer-model")
        if "frame-enhancer" not in frame_processors:
            keys_to_skip.append("frame-enhancer-model")
        if "face-swapper" not in frame_processors:
            keys_to_skip.append("face_swapper_model")
    # Compare current_values against default_values and record only changed current values
    for key, current_value in current_values.items():
        if key in keys_to_skip:
            continue  # Skip these keys
        default_value = default_values.get(key)
        if current_value != default_value:
            if current_value is None:
                continue
            formatted_value = current_value
            if isinstance(current_value, list):
                formatted_value = ' '.join(map(str, current_value))
            elif isinstance(current_value, tuple):
                formatted_value = ' '.join(map(str, current_value))
            differences[key] = formatted_value

    source_paths = current_values.get("source_paths", [])
    target_path = current_values.get("target_path", "")
    output_path = current_values.get("output_path", "")

    while True:
        if JOB_IS_RUNNING:
            if JOB_IS_EXECUTING:
                debug_print("Job is executing.")
                break
            else:
                debug_print("Job is running but not executing. Stuck in loop.\n")
                time.sleep(1)
        else:
            debug_print("Job is not running.")
            break
    oldeditjob = None
    found_editing = False
    jobs = load_jobs(jobs_queue_file)

    for job in jobs:
        if job['status'] == 'editing':
            oldeditjob = job.copy()  
            found_editing = True
            break

    cache_source_paths = copy_to_media_cache(source_paths)
    source_basenames = [os.path.basename(path) for path in cache_source_paths] if isinstance(cache_source_paths, list) else os.path.basename(cache_source_paths)
    debug_print(f"{GREEN}Source file{ENDC} copied to Media Cache folder: {GREEN}{source_basenames}{ENDC}\n\n")
    cache_target_path = copy_to_media_cache(target_path)
    debug_print(f"{GREEN}Target file{ENDC} copied to Media Cache folder: {GREEN}{os.path.basename(cache_target_path)}{ENDC}\n\n")

    # Construct the arguments string
    arguments = " ".join(f"--{key.replace('_', '-')} {value}" for key, value in differences.items() if value)
    if debugging:
        with open(os.path.join(working_dir, "arguments.txt"), "w") as file:
            file.write(json.dumps(arguments) + "\n")
    job_args = f"{arguments}"
    debug_print(f"{GREEN}Target file{ENDC} copied to Media Cache folder: {GREEN}{os.path.basename(cache_target_path)}{ENDC}\n\n")

    if isinstance(cache_source_paths, str):
        cache_source_paths = [cache_source_paths]

    new_job = {
        "job_args": job_args,
        "status": "pending",
        "headless": "--headless",
        "frame_processors": current_values['frame_processors'],
        "sourcecache": (cache_source_paths),
        "targetcache": (cache_target_path),
        "output_path": (output_path),
    }
    if debugging:
        with open(os.path.join(working_dir, f"job_args.txt"), "w") as file:
            for key, val in current_values.items():
                file.write(f"{key}: {val}\n")

    if found_editing:
        if not (oldeditjob['sourcecache'] == new_job['sourcecache'] or oldeditjob['sourcecache'] == new_job['targetcache']):
            check_if_needed(oldeditjob, 'source')
        if not (oldeditjob['targetcache'] == new_job['sourcecache'] or oldeditjob['targetcache'] == new_job['targetcache']):
            check_if_needed(oldeditjob, 'target')

        job.update(new_job)
        save_jobs(jobs_queue_file, jobs)
        custom_print(f"{GREEN}You have successfully returned the Edited job back to the job Queue, it is now a Pending Job {ENDC}")

    if not found_editing:
        jobs.append(new_job)
        save_jobs(jobs_queue_file, jobs)
    
    if edit_queue_window > 0:
        print("edit queue windows is open")
        count_existing_jobs()
        edit_queue.refresh_frame_listbox()

    count_existing_jobs()
    if JOB_IS_RUNNING:
        custom_print(f"{BLUE}job # {CURRENT_JOB_NUMBER + PENDING_JOBS_COUNT + 1} was added {ENDC}\n\n")
    else:
        custom_print(f"{BLUE}Your Job was Added to the queue,{ENDC} there are a total of {GREEN}#{PENDING_JOBS_COUNT} Job(s){ENDC} in the queue,  Add More Jobs, Edit the Queue,\n\n or Click Run Queue to Execute all the queued jobs\n\n")
def run_job_args(current_run_job):
    global CURRENT_JOB_NUMBER

    if isinstance(current_run_job['sourcecache'], list):
        arg_source_paths = ' '.join(f'-s "{p}"' for p in current_run_job['sourcecache'])
    else:
        arg_source_paths = f"-s \"{current_run_job['sourcecache']}\""
        
    arg_target_path = f"-t \"{current_run_job['targetcache']}\""
    arg_output_path = f"-o \"{current_run_job['output_path']}\""

    simulated_args = f"{arg_source_paths} {arg_target_path} {arg_output_path} {current_run_job['headless']} {current_run_job['job_args']}"
    simulated_cmd = simulated_args.replace('\\\\', '\\')
    ui_layouts = 'ui_layouts'
    setattr(facefusion.globals, ui_layouts, ['QueueItUp'])

    if automatic1111:
        process = subprocess.Popen(
            f"{venv_python} {base_dir}\\run2.py {simulated_cmd}",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1  # Line-buffered
        )
    else:
        process = subprocess.Popen(
            f"python run.py {simulated_cmd}",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1  # Line-buffered
        )

    stdout_lines = []
    stderr_lines = []

    def handle_output(stream, lines, is_stdout):
        previous_line_was_progress = False
        while True:
            line = stream.readline()
            if line == '' and process.poll() is not None:
                break
            if line:
                lines.append(line)
                label = f"{BLUE}job# {CURRENT_JOB_NUMBER}{ENDC}"
                if line.startswith("Processing:") or line.startswith("Analysing:"):
                    print(f"\r{label} - {GREEN}{line.strip()[:100]}{ENDC}", end='', flush=True)
                    previous_line_was_progress = True
                else:
                    if previous_line_was_progress:
                        print()  # Move to the next line before printing a new non-progress message
                        previous_line_was_progress = False
                    if "error" in line.lower() or "failed" in line.lower():
                        print(f"{label}: {RED}{line.strip()}{ENDC}")
                    else:
                        print(f"{label}: {YELLOW}{line.strip()}{ENDC}")


    stdout_thread = threading.Thread(target=handle_output, args=(process.stdout, stdout_lines, True))
    stderr_thread = threading.Thread(target=handle_output, args=(process.stderr, stderr_lines, False))

    stdout_thread.start()
    stderr_thread.start()

    stdout_thread.join()
    stderr_thread.join()

    return_code = process.poll()

    stdout = ''.join(stdout_lines)
    stderr = ''.join(stderr_lines)

    # Check for errors in the output
    if "error" in stdout.lower() or "error" in stderr.lower() or "failed" in stdout.lower() or "failed" in stderr.lower():
        current_run_job['status'] = 'failed'
        return_code = 1
    elif return_code == 0:
        current_run_job['status'] = 'completed'
    else:
        current_run_job['status'] = 'failed'

    return return_code
def execute_jobs():
    global JOB_IS_RUNNING, JOB_IS_EXECUTING,CURRENT_JOB_NUMBER,jobs_queue_file, jobs
    count_existing_jobs()
    if not PENDING_JOBS_COUNT + JOB_IS_RUNNING > 0:
        custom_print(f"Whoops!!!, There are {PENDING_JOBS_COUNT} Job(s) queued.  Add a job to the queue before pressing Run Queue.\n\n")
        return

    if PENDING_JOBS_COUNT + JOB_IS_RUNNING > 0 and JOB_IS_RUNNING:
        custom_print(f"Whoops a Jobs is already executing, with {PENDING_JOBS_COUNT} more job(s) waiting to be processed.\n\n You don't want more then one job running at the same time your GPU cant handle that,\n\nYou just need to click add job if jobs are already running, and thie job will be placed in line for execution. you can edit the job order with Edit Queue button\n\n")
        return
        
    jobs = load_jobs(jobs_queue_file)
    JOB_IS_RUNNING = 1
    CURRENT_JOB_NUMBER = 0
    # current_run_job = {}
    first_pending_job = next((job for job in jobs if job['status'] == 'pending'), None)
    jobs = [job for job in jobs if job != first_pending_job]
    # Change status to 'executing' and add it back to the jobs
    first_pending_job['status'] = 'executing'
    jobs.append(first_pending_job)
    save_jobs(jobs_queue_file, jobs)

    while True:
        if not first_pending_job['status'] == 'executing':
            break
        current_run_job = first_pending_job
        current_run_job['headless'] = '--headless'
        count_existing_jobs()
        JOB_IS_EXECUTING = 1
        CURRENT_JOB_NUMBER += 1
        custom_print(f"{BLUE}Starting Job #{GREEN} {CURRENT_JOB_NUMBER}{ENDC}\n\n")
        printjobtype = current_run_job['frame_processors']
        custom_print(f"{BLUE}Executing Job # {CURRENT_JOB_NUMBER} of {CURRENT_JOB_NUMBER + PENDING_JOBS_COUNT}  {ENDC}\n\n")

        if isinstance(current_run_job['sourcecache'], list):
            source_basenames = [os.path.basename(path) for path in current_run_job['sourcecache']]
        else:
            source_basenames = os.path.basename(current_run_job['sourcecache'])

        custom_print(f"{BLUE}Job #{CURRENT_JOB_NUMBER} will be doing {YELLOW}{printjobtype}{ENDC} - with source {GREEN}{source_basenames}{ENDC} to -> target {GREEN}{os.path.basename(current_run_job['targetcache'])}{ENDC}\n\n")

########
        run_job_args(current_run_job)
########


        if current_run_job['status'] == 'completed':
            custom_print(f"{BLUE}Job # {CURRENT_JOB_NUMBER} {GREEN} completed successfully {BLUE}{PENDING_JOBS_COUNT} jobs remaining, pausing 1 second before starting next job{ENDC}\n")
        else:
            source_basenames = [os.path.basename(path) for path in current_run_job['sourcecache']] if isinstance(current_run_job['sourcecache'], list) else [os.path.basename(current_run_job['sourcecache'])]
            custom_print(f"{BLUE}Job # {CURRENT_JOB_NUMBER} {RED} failed. Please check the validity of {source_basenames} and {RED}{os.path.basename(current_run_job['targetcache'])}.{BLUE}{PENDING_JOBS_COUNT} jobs remaining, pausing 5 seconds before starting next job{ENDC}\n")

        JOB_IS_EXECUTING = 0  # Reset the job execution flag
        time.sleep(1)
        jobs = load_jobs(jobs_queue_file)
        jobs = [job for job in jobs if job['status'] != 'executing']
        jobs.append(current_run_job)
        save_jobs(jobs_queue_file, jobs)
 
        # Reset current_run_job to None, indicating it's no longer holding a job
        current_run_job = None
        # Find the first pending job
        jobs = load_jobs(jobs_queue_file)
        
        first_pending_job = next((job for job in jobs if job['status'] == 'pending'), None)
        
        if first_pending_job:
            jobs = [job for job in jobs if job != first_pending_job]
            current_run_job = first_pending_job.copy()
            current_run_job['status'] = 'executing'
            jobs.append(current_run_job)
            first_pending_job = current_run_job
            
            save_jobs(jobs_queue_file, jobs)
        else:#no more pending jobs
            custom_print(f"{BLUE}a total of {CURRENT_JOB_NUMBER} Jobs have completed processing,{ENDC}...... {GREEN}the Queue is now empty, {BLUE}Feel Free to QueueItUp some more..{ENDC}")
            current_run_job = None
            first_pending_job = None
            break
    JOB_IS_RUNNING = 0
    save_jobs(jobs_queue_file, jobs)
    check_for_unneeded_media_cache()

def edit_queue():
    global root, frame, output_text, edit_queue_window, default_values, jobs_queue_file, jobs, job, image_references, thumbnail_dir, working_dir, PENDING_JOBS_COUNT, pending_jobs_var

    root = tk.Tk()
    jobs = load_jobs(jobs_queue_file)
    PENDING_JOBS_COUNT = count_existing_jobs()

    root.geometry('1200x800')
    root.title("Edit Queued Jobs")
    root.lift()
    root.attributes('-topmost', True)
    root.after_idle(root.attributes, '-topmost', False)

    scrollbar = Scrollbar(root)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    canvas = tk.Canvas(root)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    canvas.config(yscrollcommand=scrollbar.set)
    scrollbar.config(command=canvas.yview)

    frame = tk.Frame(canvas)
    canvas.create_window((0, 0), window=frame, anchor='nw')
    canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(int(-1*(event.delta/120)), "units"))

    custom_font = font.Font(family="Helvetica", size=12, weight="bold")
    bold_font = font.Font(family="Helvetica", size=12, weight="bold")

    pending_jobs_var = tk.StringVar()
    pending_jobs_var.set(f"Delete {PENDING_JOBS_COUNT} Pending Jobs")

    close_button = tk.Button(root, text="Close Window", command=root.destroy, font=custom_font)
    close_button.pack(pady=5)

    refresh_button = tk.Button(root, text="Refresh View", command=lambda: refresh_buttonclick(), font=custom_font)
    refresh_button.pack(pady=5)

    pending_jobs_button = tk.Button(root, textvariable=pending_jobs_var, command=lambda: delete_pending_jobs(), font=custom_font)
    pending_jobs_button.pack(pady=5)

    missing_jobs_button = tk.Button(root, text="Delete Missing ", command=lambda: delete_missing_media_jobs(), font=custom_font)
    missing_jobs_button.pack(pady=5)

    archived_jobs_button = tk.Button(root, text="Delete archived ", command=lambda: delete_archived_jobs(), font=custom_font)
    archived_jobs_button.pack(pady=5)

    failed_jobs_button = tk.Button(root, text="Delete Failed", command=lambda: delete_failed_jobs(), font=custom_font)
    failed_jobs_button.pack(pady=5)

    completed_jobs_button = tk.Button(root, text="Delete Completed", command=lambda: delete_completed_jobs(), font=custom_font)
    completed_jobs_button.pack(pady=5)

    def refresh_buttonclick():
        count_existing_jobs()
        update_job_listbox()
        refresh_frame_listbox()

    def refresh_frame_listbox():
        global jobs
        status_priority = {'editing': 0, 'executing': 1, 'pending': 2, 'failed': 3, 'missing': 4, 'completed': 5, 'archived': 6}
        jobs = load_jobs(jobs_queue_file)
        jobs.sort(key=lambda x: status_priority.get(x['status'], 6))
        save_jobs(jobs_queue_file, jobs)
        update_job_listbox()

    def close_window():
        save_jobs(jobs_queue_file, jobs)
        root.destroy


    def delete_pending_jobs():
        jobs = load_jobs(jobs_queue_file)
        jobs = [job for job in jobs if job['status'] != 'pending']
        save_jobs(jobs_queue_file, jobs)
        refresh_frame_listbox()
        
    def delete_completed_jobs():
        jobs = load_jobs(jobs_queue_file)
        jobs = [job for job in jobs if job['status'] != 'completed']
        save_jobs(jobs_queue_file, jobs)
        refresh_frame_listbox()

    def delete_failed_jobs():
        jobs = load_jobs(jobs_queue_file)
        jobs = [job for job in jobs if job['status'] != 'failed']        
        save_jobs(jobs_queue_file, jobs)
        refresh_frame_listbox()

        
    def delete_missing_media_jobs(): 
        jobs = load_jobs(jobs_queue_file)
        jobs = [job for job in jobs if job['status'] != 'missing']
        save_jobs(jobs_queue_file, jobs)
        refresh_frame_listbox()

    def archive_job(job):
        job['status'] = 'archived'
        save_jobs(jobs_queue_file, jobs) 
        refresh_frame_listbox()

    def delete_archived_jobs(): 
        jobs = load_jobs(jobs_queue_file)
        for job in jobs:
            if job['status'] == 'archived':
                check_if_needed(job, 'both')
        jobs = [job for job in jobs if job['status'] != 'archived']
        save_jobs(jobs_queue_file, jobs)
        refresh_frame_listbox()

    def reload_job_in_facefusion_edit(job):
        sourcecache_path = job.get('sourcecache')
        targetcache_path = job.get('targetcache')

        if isinstance(sourcecache_path, list):
            missing_files = [path for path in sourcecache_path if not os.path.exists(path)]
            if missing_files:
                messagebox.showerror("Error", f"Cannot edit job. The following source files do not exist: {', '.join(os.path.basename(path) for path in missing_files)}")
                return
        else:
            if not os.path.exists(sourcecache_path):
                messagebox.showerror("Error", f"Cannot edit job. The source file '{os.path.basename(sourcecache_path)}' does not exist.")
                return

        if not os.path.exists(targetcache_path):
            messagebox.showerror("Error", f"Cannot edit job. The target file '{os.path.basename(targetcache_path)}' does not exist.")
            return

        response = messagebox.askyesno("Confirm Edit", "THIS WILL REMOVE THIS PENDING JOB FROM THE QUEUE, AND LOAD IT INTO FACEFUSION WEBUI FOR EDITING, WHEN DONE EDITING CLICK START TO RUN IT OR ADD JOB TO REQUEUE IT. ARE YOU SURE YOU WANT TO EDIT THIS JOB", icon='warning')
        if not response:
            return
        job['headless'] = '--ui-layouts QueueItUp'
        job['status'] = 'editing'
        save_jobs(jobs_queue_file, jobs)
        top = Toplevel()
        top.title("Please Wait")
        message_label = tk.Label(top, text="Please wait while the job loads back into FaceFusion...", padx=20, pady=20)
        message_label.pack()
        top.after(1000, close_window)
        top.after(2000, top.destroy)
        custom_print(f"{GREEN} PLEASE WAIT WHILE THE Jobs IS RELOADED IN FACEFUSION{ENDC}...... {YELLOW}THIS WILL CREATE AN ADDITIONAL PYTHON PROCESS AND YOU SHOULD CONSIDER RESTARTING FACEFUSION AFTER DOING THIS MOR THEN 3 TIMES{ENDC}")

        root.destroy()
        run_job_args(job)

    def output_path_job(job):
        selected_path = filedialog.askdirectory(title="Select A New Output Path for this Job")
        ###old error selected_path = askdirectory(title="Select A New Output Path for this Job")

        if selected_path:
            formatted_path = selected_path.replace('/', '\\')  
            job['output_path'] = formatted_path
            update_paths(job, formatted_path, 'output')
        save_jobs(jobs_queue_file, jobs)  
        update_job_listbox()  
        refresh_frame_listbox()

    def delete_job(job):
        job['status'] = ('deleting')
        source_or_target='both'
        check_if_needed(job, 'both')
        jobs.remove(job)
        save_jobs(jobs_queue_file, jobs)
        update_job_listbox()  
        refresh_frame_listbox()

    def move_job_up(index):
        if index > 0:
            jobs.insert(index - 1, jobs.pop(index))
            save_jobs(jobs_queue_file, jobs)
            update_job_listbox()

    def move_job_down(index):
        if index < len(jobs) - 1:
            jobs.insert(index + 1, jobs.pop(index))
            save_jobs(jobs_queue_file, jobs)
            update_job_listbox()

    def move_job_to_top(index):
        if index > 0:
            jobs.insert(0, jobs.pop(index))
            save_jobs(jobs_queue_file, jobs)
            update_job_listbox()

    def move_job_to_bottom(index):
        if index < len(jobs) - 1:
            jobs.append(jobs.pop(index))
            save_jobs(jobs_queue_file, jobs)
            update_job_listbox()

    def edit_job_arguments_text(job):
        global default_values
        job_args = job.get('job_args', '')
        preprocessed_defaults = preprocess_execution_providers(default_values)

        edit_arg_window = tk.Toplevel()
        edit_arg_window.title("Edit Job Arguments")
        edit_arg_window.geometry("1050x500")

        canvas = tk.Canvas(edit_arg_window)
        scrollable_frame = tk.Frame(canvas)

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.pack(side="left", fill="both", expand=True)

        entries = {}
        checkboxes = {}
        row = 0
        col = 0

        args_pattern = r'(--[\w-]+)\s+((?:.(?! --))+.)'
        iter_args = re.finditer(args_pattern, job_args)
        job_args_dict = {}
        for match in iter_args:
            arg, value = match.groups()
            value = ' '.join(value.split())  # Normalize spaces
            job_args_dict[arg] = value
        skip_keys = ['--source-paths', '--target-path', '--output-path', '--ui-layouts']

        for arg, default_value in default_values.items():
            cli_arg = '--' + arg.replace('_', '-')
            if cli_arg in skip_keys:
                continue  # Skip the creation of GUI elements for these keys

            formatted_default_value = format_cli_value(default_value)
            current_value = job_args_dict.get(cli_arg, formatted_default_value)
            is_checked = cli_arg in job_args_dict
            
            var = tk.BooleanVar(value=is_checked)
            chk = tk.Checkbutton(scrollable_frame, text=cli_arg, variable=var)
            chk.grid(row=row, column=col*3, padx=5, pady=2, sticky="w")

            entry = tk.Entry(scrollable_frame)
            entry.insert(0, str(current_value if current_value else default_value))
            entry.grid(row=row, column=col*3+1, padx=5, pady=2, sticky="w")
            entry.config(state='normal' if is_checked else 'disabled')

            entries[cli_arg] = entry
            checkboxes[cli_arg] = var

            var.trace_add("write", lambda *args, var=var, entry=entry, value=current_value: update_entry(var, entry, value))

            row += 1
            if row >= 16:
                row = 0
                col += 1

        def update_entry(var, entry, value):
            if var.get():
                entry.config(state=tk.NORMAL)
                entry.delete(0, tk.END)
                entry.insert(0, value)
            else:
                entry.config(state=tk.DISABLED)
                entry.delete(0, tk.END)

        def save_changes():
            new_job_args = []
            for arg, var in checkboxes.items():
                if var.get():
                    entry_text = entries[arg].get().strip()
                    if entry_text:
                        new_job_args.append(f"{arg} {entry_text}")

            job['job_args'] = ' '.join(new_job_args)
            debug_print("Updated Job Args:", job['job_args'])
            save_jobs(jobs_queue_file, jobs)
            edit_arg_window.destroy()

        ok_button = tk.Button(edit_arg_window, text="OK", command=save_changes)
        ok_button.pack(pady=5, padx=5, side=tk.RIGHT)

        cancel_button = tk.Button(edit_arg_window, text="Cancel", command=edit_arg_window.destroy)
        cancel_button.pack(pady=5, padx=5, side=tk.RIGHT)

        scrollable_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        edit_arg_window.mainloop()

    def batch_job(job):
        file_types = []
        target_filetype = None
        source_or_target = None


        if isinstance(job['sourcecache'], str):
            job['sourcecache'] = [job['sourcecache']]
        current_extension = job['targetcache'].lower().rsplit('.', 1)[-1]
        if current_extension in ['jpg', 'jpeg', 'png']:
            target_filetype = 'Image'
        elif current_extension in ['mp4', 'mov', 'avi', 'mkv']:
            target_filetype = 'Video'

        def on_use_source():
            nonlocal source_or_target
            source_or_target = 'target'
            dialog.destroy()
            open_file_dialog()

        def on_use_target():
            nonlocal source_or_target
            source_or_target = 'source'
            if any(ext in src.lower() for ext in ['.mp3', '.wav', '.aac'] for src in job['sourcecache']):
                messagebox.showinfo("BatchItUp Error", "Sorry, BatchItUp cannot clone lipsync jobs yet.")
                dialog.destroy()
                return

            if len(job['sourcecache']) > 1:
                source_filenames = [os.path.basename(src) for src in job['sourcecache']]
                proceed = messagebox.askyesno(
                    "BatchItUp Multiple Faces",
                    f"Your current source contains multiple faces ({', '.join(source_filenames)}). BatchItUp cannot create multiple target {target_filetype} jobs while still maintaining multiple source faces. "
                    f"If you click 'Yes' to proceed, you will get 1 target {target_filetype} for each source face you select in the next file dialog, but you can use the edit queue window "
                    f"to add more source faces to each job created after BatchItUp has created them. Do you want to proceed?"
                )
                if not proceed:
                    dialog.destroy()
                    return
            dialog.destroy()
            open_file_dialog()

        def open_file_dialog():
            selected_paths = []
            if source_or_target == 'source':
                selected_paths = filedialog.askopenfilenames(
                    title="Select Multiple targets for BatchItUp to make multiple cloned jobs using each File",
                    filetypes=[('Image files', '*.jpg *.jpeg *.png')]
                )
            elif source_or_target == 'target':
                file_types = [('Image files', '*.jpg *.jpeg *.png')] if target_filetype == 'Image' else [('Video files', '*.mp4 *.avi *.mov *.mkv')]
                selected_paths = filedialog.askopenfilenames(
                    title="Select Multiple sources for BatchItUp to make multiple cloned jobs using each File",
                    filetypes=file_types
                )
            if selected_paths:
                for path in selected_paths:
                    add_new_job = job.copy()  # Copy the existing job to preserve other attributes
                    path = copy_to_media_cache(path)
                    add_new_job[source_or_target + 'cache'] = path
                    debug_print(f"{YELLOW}{source_or_target} - {GREEN}{add_new_job[source_or_target + 'cache']}{YELLOW} copied to temp media cache dir{ENDC}")
                    jobs.append(add_new_job)
                save_jobs(jobs_queue_file, jobs)
                update_job_listbox()

        dialog = tk.Toplevel()
        dialog.withdraw()

        source_filenames = [os.path.basename(src) for src in job['sourcecache']]
        message = (
            f"Welcome to the BatchItUp feature. Here you can add multiple batch jobs with just a few clicks.\n\n"
            f"Click the 'Use Source' button to select as many target {target_filetype}s as you like and BatchItUp will create a job for each {target_filetype} "
            f"using {', '.join(source_filenames)} as the source image(s), OR you can Click 'Use Target' to select as many Source Images as you like and BatchItUp will "
            f"create a job for each source image using {os.path.basename(job['targetcache'])} as the target {target_filetype}."
        )

        dialog.deiconify()
        dialog.geometry("500x300")
        dialog.title("BatchItUp")

        label = tk.Label(dialog, text=message, wraplength=450, justify="left")
        label.pack(pady=20)

        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=10)

        use_source_button = tk.Button(button_frame, text="Use Source", command=on_use_source)
        use_source_button.pack(side="left", padx=10)

        use_target_button = tk.Button(button_frame, text="Use Target", command=on_use_target)
        use_target_button.pack(side="left", padx=10)

        dialog.mainloop()

    def select_job_file(parent, job, source_or_target):
        file_types = []
        if source_or_target == 'source':
            file_types = [('source files', '*.jpg *.jpeg *.png *.mp3 *.wav *.aac')]
        elif source_or_target == 'target':
            current_extension = job['targetcache'].lower().rsplit('.', 1)[-1]
            if current_extension in ['jpg', 'jpeg', 'png']:
                file_types = [('Image files', '*.jpg *.jpeg *.png')]
            elif current_extension in ['mp4', 'mov', 'avi', 'mkv']:
                file_types = [('Video files', '*.mp4 *.avi *.mov *.mkv')]

        if source_or_target == 'source':
            selected_paths = filedialog.askopenfilenames(title=f"Select {source_or_target.capitalize()} File(s)", filetypes=file_types)
        else:
            selected_path = filedialog.askopenfilename(title=f"Select {source_or_target.capitalize()} File", filetypes=file_types)
            selected_paths = [selected_path] if selected_path else []

        if selected_paths:
            check_if_needed(job, source_or_target)
            update_paths(job, selected_paths, source_or_target)
            if isinstance(job['sourcecache'], list):
                source_cache_exists = all(os.path.exists(cache) for cache in job['sourcecache'])
            else:
                source_cache_exists = os.path.exists(job['sourcecache'])
            
            if source_cache_exists and os.path.exists(job['targetcache']):
                job['status'] = 'pending'
            else:
                job['status'] = 'missing'

            save_jobs(jobs_queue_file, jobs)
            update_job_listbox()
            
    def create_job_thumbnail(parent, job, source_or_target):
        job_id = job['id']

        # Clear the existing image reference for this specific job to force update
        if job_id in image_references:
            del image_references[job_id]

        file_paths = job[source_or_target + 'cache']
        file_paths = file_paths if isinstance(file_paths, list) else [file_paths]

        for file_path in file_paths:
            if not os.path.exists(file_path):
                button = Button(parent, text=f"File not found:\n\n {os.path.basename(file_path)}\nClick to update", bg='white', fg='black',
                                command=lambda: select_job_file(parent, job, source_or_target))
                button.pack(pady=2, fill='x', expand=False)
                return button

        if not os.path.exists(thumbnail_dir):
            os.makedirs(thumbnail_dir)

        num_images = len(file_paths)
        grid_size = math.ceil(math.sqrt(num_images))
        thumb_size = 200 // grid_size

        thumbnail_files = []
        for idx, file_path in enumerate(file_paths):
            thumbnail_path = os.path.join(thumbnail_dir, f"{source_or_target}_thumb_{job_id}_{idx}.png")
            if file_path.lower().endswith(('.mp3', '.wav', '.aac', '.flac')):
                audio_icon_path = os.path.join(working_dir, 'audioicon.png')
                cmd = [
                    'ffmpeg', '-i', audio_icon_path,
                    '-vf', f'scale={thumb_size}:{thumb_size}',
                    '-vframes', '1',
                    '-y', thumbnail_path
                ]
            else:
                cmd = [
                    'ffmpeg', '-i', file_path,
                    '-vf', f'scale={thumb_size}:{thumb_size}',
                    '-vframes', '1',
                    '-y', thumbnail_path
                ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            thumbnail_files.append(thumbnail_path)

        list_file_path = os.path.join(thumbnail_dir, f'{job_id}_input_list.txt')
        with open(list_file_path, 'w') as file:
            for thumb in thumbnail_files:
                file.write(f"file '{thumb}'\n")

        grid_path = os.path.join(thumbnail_dir, f"{source_or_target}_grid_{job_id}.png")
        grid_cmd = [
            'ffmpeg',
            '-loglevel', 'error',
            '-f', 'concat', '-safe', '0', '-i', list_file_path,
            '-filter_complex', f'tile={grid_size}x{grid_size}:padding=2',
            '-y', grid_path
        ]
        grid_result = subprocess.run(grid_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if grid_result.returncode != 0:
            print(f"Error creating grid: {grid_result.stderr.decode()}")
            return None

        try:
            with open(grid_path, 'rb') as f:
                grid_image_data = BytesIO(f.read())
            grid_photo_image = PhotoImage(data=grid_image_data.read())
            button = Button(parent, image=grid_photo_image, command=lambda ft=source_or_target: select_job_file(parent, job, ft))
            button.image = grid_photo_image
            button.pack(side='left', padx=5)
            image_references[job_id] = button
        except Exception as e:
            print(f"Failed to open grid image: {e}")

        # Clean up thumbnail directory
        for file in thumbnail_files:
            if os.path.exists(file):
                os.remove(file)
        if os.path.exists(list_file_path):
            os.remove(list_file_path)
        if os.path.exists(grid_path):
            os.remove(grid_path)

        return button


    def update_paths(job, path, source_or_target):
        job_id = id(job)
        if job_id in image_references:
            del image_references[job_id]
        if source_or_target == 'source':
            cache_path = copy_to_media_cache(path)
            if not isinstance(cache_path, list):
                cache_path = [cache_path]
            cache_key = 'sourcecache'
            job[cache_key] = cache_path


        if source_or_target == 'target':
            cache_path = copy_to_media_cache(path)
            cache_key = 'targetcache'
            job[cache_key] = cache_path
            copy_to_media_cache(path)

            
        if source_or_target == 'output':
            cache_key = 'output_path'
            cache_path = job['output_path']
        job[cache_key] = cache_path
        save_jobs(jobs_queue_file, jobs)
        update_job_listbox()

    def update_job_listbox():
        global image_references, frame
        update_counters()

        try:
            if frame.winfo_exists():
                count_existing_jobs()
                for widget in frame.winfo_children():
                    widget.destroy()

                for index, job in enumerate(jobs):
                    source_cache_path = job['sourcecache'] if isinstance(job['sourcecache'], list) else [job['sourcecache']]
                    source_thumb_exists = all(os.path.exists(os.path.normpath(source)) for source in source_cache_path)
                    target_cache_path = job['targetcache'] if isinstance(job['targetcache'], str) else job['targetcache'][0]
                    target_thumb_exists = os.path.exists(os.path.normpath(target_cache_path))
                    bg_color = 'SystemButtonFace'
                    if job['status'] == 'failed':
                        bg_color = 'red'
                    if job['status'] == 'executing':
                        bg_color = 'black'
                    if job['status'] == 'completed':
                        bg_color = 'grey'
                    if job['status'] == 'editing':
                        bg_color = 'green'
                    if job['status'] == 'pending':
                        bg_color = 'SystemButtonFace'
                    if not source_thumb_exists or not target_thumb_exists:
                        bg_color = 'red'
                    if job['status'] == 'archived':
                        bg_color = 'brown'
                    job_frame = tk.Frame(frame, borderwidth=2, relief='groove', background=bg_color)
                    job_frame.pack(fill='x', expand=True, padx=5, pady=5)
                    move_job_frame = tk.Frame(job_frame)
                    move_job_frame.pack(side='left', fill='x', padx=5)
                    move_top_button = tk.Button(move_job_frame, text="   Top   ", command=lambda idx=index: move_job_to_top(idx))
                    move_top_button.pack(side='top', fill='y')
                    move_up_button = tk.Button(move_job_frame, text="   Up   ", command=lambda idx=index: move_job_up(idx))
                    move_up_button.pack(side='top', fill='y')
                    move_down_button = tk.Button(move_job_frame, text=" Down ", command=lambda idx=index: move_job_down(idx))
                    move_down_button.pack(side='top', fill='y')
                    move_bottom_button = tk.Button(move_job_frame, text="Bottom", command=lambda idx=index: move_job_to_bottom(idx))
                    move_bottom_button.pack(side='top', fill='y')
                    
                    source_frame = tk.Frame(job_frame)
                    source_frame.pack(side='left', fill='x', padx=5)
                    source_button = create_job_thumbnail(job_frame, job, source_or_target='source')
                    if source_button:
                        source_button.pack(side='left', padx=5)
                    else:
                        print("Failed to create source button.")

                    action_frame = tk.Frame(job_frame)
                    action_frame.pack(side='left', fill='x', padx=5)

                    arrow_label = tk.Label(action_frame, text=f"{job['status']}\n\u27A1", font=bold_font)
                    arrow_label.pack(side='top', padx=5)

                    output_path_button = tk.Button(action_frame, text="Output Path", command=lambda j=job: output_path_job(j))
                    output_path_button.pack(side='top', padx=2)
                    
                    delete_button = tk.Button(action_frame, text=" Delete ", command=lambda j=job: delete_job(j))
                    delete_button.pack(side='top', padx=2)
                    
                    archive_button = tk.Button(action_frame, text="Archive", command=lambda j=job: archive_job(j))
                    archive_button.pack(side='top', padx=2)
                    
                    batch_button = tk.Button(action_frame, text="BatchItUp", command=lambda j=job: batch_job(j))
                    batch_button.pack(side='top', padx=2)
                    
                    target_frame = tk.Frame(job_frame)
                    target_frame.pack(side='left', fill='x', padx=5)
                    target_button = create_job_thumbnail(job_frame, job, source_or_target='target')
                    if target_button:
                        target_button.pack(side='left', padx=5)
                    else:
                        print("Failed to create target button.")
                
                    argument_frame = tk.Frame(job_frame)
                    argument_frame.pack(side='left', fill='x', padx=5)

                    facefusion_button = tk.Button(argument_frame, text=f"UN-Queue It Up", font=bold_font, justify='center')
                    facefusion_button.pack(side='top', padx=5, fill='x', expand=False)
                    facefusion_button.bind("<Button-1>", lambda event, j=job: reload_job_in_facefusion_edit(j))

                    argument_button = tk.Button(argument_frame, text=f"EDIT JOB ARGUMENTS", wraplength=325, justify='center')
                    argument_button.pack(side='bottom', padx=5, fill='x', expand=False)
                    argument_button.bind("<Button-1>", lambda event, j=job: edit_job_arguments_text(j))
                
                frame.update_idletasks()
                canvas.config(scrollregion=canvas.bbox("all"))

        except tk.TclError as e:
            pass
            
    # edit_queue.update_job_listbox = update_job_listbox
    edit_queue.refresh_frame_listbox = refresh_frame_listbox
    edit_queue_window += 1
    # root.after(1000, update_job_listbox)
    root.after(1000, refresh_frame_listbox)
    root.mainloop()
    edit_queue_window = 0
    if __name__ == '__main__':
        edit_queue()
    # update_job_listbox()

def count_existing_jobs():
    global PENDING_JOBS_COUNT
    jobs = load_jobs(jobs_queue_file)
    PENDING_JOBS_COUNT = len([job for job in jobs if job['status'] in ['pending']])
    return PENDING_JOBS_COUNT

def update_counters():
    global root, pending_jobs_var
    if pending_jobs_var:
        root.after(0, lambda: pending_jobs_var.set(f"Delete {PENDING_JOBS_COUNT} Pending Jobs"))

def get_values_from_globals(state_name):
    state_dict = {}
    
    from facefusion.processors.frame import globals as frame_processors_globals, choices as frame_processors_choices

    modules = [facefusion.globals, frame_processors_globals]  

    for module in modules:
        for attr in dir(module):
            if not attr.startswith("__"):
                value = getattr(module, attr)
                try:
                    json.dumps(value)  # Check if the value is JSON serializable
                    state_dict[attr] = value  # Store or update the value in the dictionary
                except TypeError:
                    continue  # Skip values that are not JSON serializable

    state_dict = preprocess_execution_providers(state_dict)
    if debugging:
        with open(os.path.join(working_dir, f"{state_name}.txt"), "w") as file:
            for key, val in state_dict.items():
                file.write(f"{key}: {val}\n")
        debug_print(f"{state_name}.txt created")
    return state_dict

def debug_print (*msgs):
    if debugging:
        custom_print(*msgs)



def custom_print(*msgs):
    # Join all arguments into a single message string
    message = " ".join(str(msg) for msg in msgs)

    # ANSI Color Codes
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'

    # Mapping of ANSI codes to tkinter text widget tags
    ansi_to_tag = {
        RED: 'red',
        GREEN: 'green',
        YELLOW: 'yellow',
        BLUE: 'blue',
        ENDC: 'end'
    }

    print(message)  # Print to terminal with ANSI coloring




def create_and_verify_json(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as json_file:  
                json.load(json_file)
        except json.JSONDecodeError:
            backup_path = file_path + ".bak"
            shutil.copy(file_path, backup_path)
            debug_print(f"Backup of corrupt JSON file saved as '{backup_path}'. Please check it for salvageable data.\n\n")
            with open(file_path, "w") as json_file:
                json.dump([], json_file)
            debug_print(f"Original JSON file '{file_path}' was corrupt and has been reset to an empty list.\n\n")
    else:
        with open(file_path, "w") as json_file:
            json.dump([], json_file)
        debug_print(f"JSON file '{file_path}' did not exist and has been created.")

def load_jobs(file_path):
    with open(file_path, 'r') as file:
        jobs = json.load(file)
    return jobs

def load_jobs(file_path):
    with open(file_path, 'r') as file:
        jobs = json.load(file)
    for job in jobs:
        if 'id' not in job:
            job['id'] = str(uuid.uuid4())
    return jobs


def save_jobs(file_path, jobs):
    with open(file_path, 'w') as file:
        json.dump(jobs, file, indent=4)
      

def format_cli_value(value):
    if isinstance(value, list) or isinstance(value, tuple):
        return ' '.join(map(str, value))  # Convert list or tuple to space-separated string
    if value is None:
        return 'None'
    return str(value)

def print_existing_jobs():

    count_existing_jobs()
    if JOB_IS_RUNNING:
        message = f"There is {PENDING_JOBS_COUNT + JOB_IS_RUNNING} job(s) being Processed - Click Add Job to Queue more Jobs"
    else:
        if PENDING_JOBS_COUNT > 0:
            message = f"There is {PENDING_JOBS_COUNT + JOB_IS_RUNNING} job(s) in the queue - Click Run Queue to Execute Them, or continue adding more jobs to the queue"
        else:
            message = f"There is 0 job(s) in the queue - Click Add Job instead of Start"
    custom_print(message + "\n\n")
    

def check_for_completed_failed_or_aborted_jobs():
    count_existing_jobs()
    jobs = load_jobs(jobs_queue_file)
    for job in jobs:
        if job['status'] == 'executing':
            job['status'] = 'pending'
            custom_print(f"{RED}A probable crash or aborted job execution was detected from your last use.... checking on status of unfinished jobs..{ENDC}\n\n")
            if isinstance(job['sourcecache'], list):
                source_basenames = [os.path.basename(path) for path in job['sourcecache']]
            else:
                source_basenames = os.path.basename(job['sourcecache'])

                custom_print(f"{GREEN}A job {GREEN}{source_basenames}{ENDC} to -> {GREEN}{os.path.basename(job['targetcache'])} was found that terminated early it will be moved back to the pending jobs queue - you have a Total of {PENDING_JOBS_COUNT + JOB_IS_RUNNING} in the Queue\n\n")
            save_jobs(jobs_queue_file, jobs)
    if not keep_completed_jobs:
        jobs = [job for job in jobs if job['status'] != 'completed']
        save_jobs(jobs_queue_file, jobs)
        custom_print(f"{BLUE}All completed jobs have been removed, if you would like to keep completed jobs change the setting to True{ENDC}\n\n")

def sanitize_filename(filename):
    valid_chars = "-_.()abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    sanitized = ''.join(c if c in valid_chars else '_' for c in filename)
    return sanitized

def copy_to_media_cache(file_paths):
    if isinstance(file_paths, str):
        file_paths = [file_paths]  # Convert single file path to list
    cached_paths = []
    for file_path in file_paths:
        file_name = os.path.basename(file_path)
        sanitized_name = sanitize_filename(file_name)  # Sanitize the filename
        file_size = os.path.getsize(file_path)
        base_name, ext = os.path.splitext(sanitized_name)
        counter = 0
        while True:
            new_name = f"{base_name}_{counter}{ext}" if counter > 0 else sanitized_name
            cache_path = os.path.join(media_cache_dir, new_name)
            if not os.path.exists(cache_path):
                shutil.copy(file_path, cache_path)
                cached_paths.append(cache_path)
                break
            else:
                cache_size = os.path.getsize(cache_path)
                if file_size == cache_size:
                    cached_paths.append(cache_path)  # If size matches, assume it's the same file
                    break
            counter += 1

    # Ensure target_path is treated as a single path
    if isinstance(cached_paths, list) and len(cached_paths) == 1:
        return cached_paths[0]  # Return the single path
    else:
        return cached_paths  # Return the list of paths
def check_for_unneeded_media_cache():
    # List all files in the media cache directory
    cache_files = os.listdir(media_cache_dir)
    jobs = load_jobs(jobs_queue_file)
    # Create a set to store all needed filenames from the jobs
    needed_files = set()
    for job in jobs:
        if job['status'] in {'pending', 'failed', 'missing', 'editing', 'executing'}:
            # Now handle sourcecache as a list
            for source_cache_path in job['sourcecache']:
                source_basename = os.path.basename(source_cache_path)
                needed_files.add(source_basename)
            target_basename = os.path.basename(job['targetcache'])
            needed_files.add(target_basename)
    # Delete files that are not needed
    for cache_file in cache_files:
        if cache_file not in needed_files:
            os.remove(os.path.join(media_cache_dir, cache_file))
            debug_print(f"{GREEN}Deleted unneeded file: {cache_file}{ENDC}")

def check_if_needed(job, source_or_target):
    with open(jobs_queue_file, 'r') as file:
        jobs = json.load(file)

    relevant_statuses = {'pending', 'executing', 'failed', 'missing', 'editing', 'archived'}
    file_usage_counts = {}

    # Create an index list for all jobs with relevant statuses and count file paths
    for other_job in jobs:
        if other_job['status'] in relevant_statuses:
            for key in ['sourcecache', 'targetcache']:
                paths = other_job[key] if isinstance(other_job[key], list) else [other_job[key]]
                for path in paths:
                    normalized_path = os.path.normpath(path)
                    file_usage_counts[normalized_path] = file_usage_counts.get(normalized_path, 0) + 1

    # Check and handle sourcecache paths
    if source_or_target in ['both', 'source']:
        source_cache_paths = job['sourcecache'] if isinstance(job['sourcecache'], list) else [job['sourcecache']]
        for source_cache_path in source_cache_paths:
            normalized_source_path = os.path.normpath(source_cache_path)
            file_use_count = file_usage_counts.get(normalized_source_path, 0)
            if file_use_count < 2:
                if os.path.exists(normalized_source_path):
                    try:
                        os.remove(normalized_source_path)
                        action_message = f"Successfully deleted the file: {GREEN}{os.path.basename(normalized_source_path)}{ENDC} as it is no longer needed by any other jobs"
                    except Exception as e:
                        action_message = f"{RED}Failed to delete {YELLOW}{os.path.basename(normalized_source_path)}{ENDC}: {e}"
                else:
                    action_message = f"{BLUE}No need to delete the file: {GREEN}{os.path.basename(normalized_source_path)}{ENDC} as it does not exist."
            else:
                action_message = f"{BLUE}Did not delete the file: {GREEN}{os.path.basename(normalized_source_path)}{ENDC} as it's needed by another job."
            debug_print(f"{action_message}\n\n")

    # Check and handle targetcache path
    if source_or_target in ['both', 'target']:
        target_cache_path = job['targetcache']
        if isinstance(target_cache_path, list):
            target_cache_path = target_cache_path[0]  # Assuming the first element if it's erroneously a list
        normalized_target_path = os.path.normpath(target_cache_path)
        if file_usage_counts.get(normalized_target_path, 0) < 2:
            if os.path.exists(normalized_target_path):
                try:
                    os.remove(normalized_target_path)
                    debug_print(f"Successfully deleted the file: {GREEN}{os.path.basename(normalized_target_path)}{ENDC} as it is no longer needed by any other jobs\n\n")
                except Exception as e:
                    debug_print(f"{RED}Failed to delete {YELLOW}{os.path.basename(normalized_target_path)}{ENDC}: {e}\n\n")
            else:
                debug_print(f"{BLUE}No need to delete the file: {GREEN}{os.path.basename(normalized_target_path)}{ENDC} as it does not exist.\n\n")
        else:
            debug_print(f"{BLUE}Did not delete the file: {GREEN}{os.path.basename(normalized_target_path)}{ENDC} as it's needed by another job.\n\n")

def preprocess_execution_providers(data):
    new_data = data.copy()
    for key, value in new_data.items():
        if key == "execution_providers":
            new_providers = []
            for provider in value:
                if provider == "CUDAExecutionProvider":
                    new_providers.append('cuda')
                elif provider == "CPUExecutionProvider":
                    new_providers.append('cpu')
                elif provider == "CoreMLExecutionProvider":
                    new_providers.append('coreml')
                # Assuming you don't want to keep original values that don't match, skip the else clause
            new_data[key] = new_providers  # Replace the old list with the new one
    return new_data
    
##################################
#startup_init_checks_and_cleanup     
##################################
#Globals and toggles
script_root = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(script_root)))

# Appending 'QueueItUp' to the adjusted base directory
user_dir = "QueueItUp"
working_dir = os.path.normpath(os.path.join(base_dir, user_dir))
media_cache_dir = os.path.normpath(os.path.join(working_dir, "mediacache"))
thumbnail_dir = os.path.normpath(os.path.join(working_dir, "thumbnails"))
jobs_queue_file = os.path.normpath(os.path.join(working_dir, "jobs_queue.json"))
debugging = True
keep_completed_jobs = False
ADD_JOB_BUTTON = gradio.Button("Add Job ", variant="primary")
RUN_JOBS_BUTTON = gradio.Button("Run Jobs", variant="primary")
EDIT_JOB_BUTTON = gradio.Button("Edit Jobs")
#status_priority = {'editing': 0, 'pending': 1, 'failed': 2, 'executing': 3, 'completed': 4}
JOB_IS_RUNNING = 0
JOB_IS_EXECUTING = 0
PENDING_JOBS_COUNT = 0
CURRENT_JOB_NUMBER = 0
edit_queue_window = 0
root = None
pending_jobs_var = None
PENDING_JOBS_COUNT = 0
image_references = {}
default_values = {}
#code to determin if running inside atutomatic1111
automatic1111 = os.path.isfile(os.path.join(base_dir, "flavor.txt")) and "automatic1111" in open(os.path.join(base_dir, "flavor.txt")).readline().strip()
if automatic1111:
    print("automatic1111")
    from facefusion import core2
    import facefusion.core2 as core2
if automatic1111: venv_python = os.path.normpath(os.path.join(os.path.dirname(os.path.dirname(base_dir)), 'venv', 'scripts', 'python.exe'))
if automatic1111: debug_print("Venv Python Path:", venv_python)
if not automatic1111: default_values = get_values_from_globals("default_values")
    # ANSI Color Codes     
RED = '\033[91m'     #use this  
GREEN = '\033[92m'     #use this  
YELLOW = '\033[93m'     #use this  
BLUE = '\033[94m'     #use this  
ENDC = '\033[0m'       #use this    Resets color to default
debug_print("Base Directory:", base_dir)
debug_print("Working Directory:", working_dir)
debug_print("Media Cache Directory:", media_cache_dir)
debug_print("Jobs Queue File:", jobs_queue_file)
debug_print(f"{BLUE}Welcome Back To FaceFusion Queueing Addon\n\n")
debug_print(f"Checking Status{ENDC}\n\n")
if not os.path.exists(working_dir):
    os.makedirs(working_dir)
if not os.path.exists(media_cache_dir):
    os.makedirs(media_cache_dir)
create_and_verify_json(jobs_queue_file)
check_for_completed_failed_or_aborted_jobs()
debug_print(f"{GREEN}STATUS CHECK COMPLETED. {BLUE}You are now ready to QUEUE IT UP!{ENDC}")
print_existing_jobs()

def run(ui: gradio.Blocks) -> None:
    global server
    concurrency_count = min(8, multiprocessing.cpu_count())
    ui.queue(concurrency_count=concurrency_count).launch(show_api=False, inbrowser=True, quiet=False)
