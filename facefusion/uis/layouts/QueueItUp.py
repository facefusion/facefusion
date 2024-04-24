import multiprocessing
import gradio
import os
import re
import sys
import time
import json
import shutil
import logging
import tkinter
import datetime
import threading
import subprocess
import configparser
from math import ceil
from io import BytesIO
from filelock import Timeout, FileLock
import facefusion.globals
from facefusion import core
from tkinter import filedialog, font, Toplevel, messagebox, PhotoImage, Tk, Canvas, Scrollbar, Frame, Label, Button
from facefusion.uis.components import about, frame_processors, frame_processors_options, execution, execution_thread_count, execution_queue_count, memory, temp_frame, output_options, common_options, source, target, output, preview, trim_frame, face_analyser, face_selector, face_masker




def pre_check() -> bool:
	return True

def pre_render() -> bool:
	return True

####Globals and toggles
user_dir = "QueueItUp"  #Using quotes like this user_dir = "C:\AI\queuedir" 
working_dir = os.path.normpath(user_dir)
media_cache_dir = os.path.join(working_dir, "mediacache")
jobs_queue_file = os.path.join(working_dir, "jobs_queue.json")
running_job_file = os.path.join(working_dir, "run_job.json")
debugging = False
system_logs= False
keep_completed_jobs = False
ADD_JOB_BUTTON = gradio.Button("Add Job ", variant="primary")
RUN_JOBS_BUTTON = gradio.Button("Run Jobs", variant="primary")
STATUS_WINDOW = gradio.Textbox(label="Job Status")
EDIT_JOB_BUTTON = gradio.Button("Edit Jobs")
create_and_verify_json = 0
total_pending_jobs = 0
pending_jobs_count = 0
total_jobs = total_pending_jobs
job_is_running = False
    # ANSI Color Codes     
RED = '\033[91m'     #use this  
GREEN = '\033[92m'     #use this  
YELLOW = '\033[93m'     #use this  
BLUE = '\033[94m'     #use this  
ENDC = '\033[0m'       #use this    Resets color to default



def startup_init_checks_and_cleanup():
    print(f"Welcome Back To FaceFusion Queueing Addon\n\n")
    print(f"Checking Status\n\n")
    # Create directories if they do not exist
    if not os.path.exists(working_dir):
        os.makedirs(working_dir)
    if not os.path.exists(media_cache_dir):
        os.makedirs(media_cache_dir)
    print(f"Checking media_cache_dir\n\n")

    create_and_verify_json(jobs_queue_file)
    print(f"Checking jobs_queue_file\n\n")
    create_and_verify_json(running_job_file)
    print(f"Checking running_job_file\n\n")
    # Setup initial jobs using the utility functions

    check_for_completed_failed_or_aborted_jobs()
    # Optionally, perform additional setup or logging here
    print(f"Setup completed. Your Queue is Ready.")
    print_existing_jobs()
    return

def create_and_verify_json(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as json_file:  # Use a different variable name
                json.load(json_file)
            #print(f"JSON file '{file_path}' exists and is valid.\n\n")
        except json.JSONDecodeError:
            backup_path = file_path + ".bak"
            shutil.copy(file_path, backup_path)
            print(f"Backup of corrupt JSON file saved as '{backup_path}'. Please check it for salvageable data.\n\n")
            with open(file_path, "w") as json_file:
                json.dump([], json_file)
            print(f"Original JSON file '{file_path}' was corrupt and has been reset to an empty list.\n\n")
    else:
        with open(file_path, "w") as json_file:
            json.dump([], json_file)
        print(f"JSON file '{file_path}' did not exist and has been created.")
file_locks = {}


def load_jobs(file_path):
    with open(file_path, 'r') as file:
        jobs = json.load(file)
    def sort_key(job):
        status_priority = {'pending': 0, 'failed': 1, 'executing': 2, 'completed': 3}
        return status_priority.get(job['status'], 4)
    return sorted(jobs, key=sort_key)

def save_jobs(file_path, jobs):
    with open(file_path, 'w') as file:
        json.dump(jobs, file, indent=4, separators=(',', ': '))

# jobs = load_jobs(jobs_queue_file)
# run_job = load_jobs(running_job_file)

def count_existing_jobs():
    global total_pending_jobs, pending_jobs_count, job_is_running  
    # Load jobs from JSON files directly using global paths
    jobs = load_jobs(jobs_queue_file)
    print(f"load_jobs jobs_queue_file\n\n")
    # Count pending jobs in jobs queue
    pending_jobs_count = len([job for job in jobs if job['status'] == 'pending'])

    # Corrected if statement syntax
    if job_is_running:  # Assumes job_is_running is a Boolean
        pending_runs_count = 1
    else:
        pending_runs_count = 0

    # Update global total_pending_jobs
    total_pending_jobs = pending_jobs_count + pending_runs_count



def print_existing_jobs():
    global total_pending_jobs, job_is_running  # Use the global variable

    count_existing_jobs()  # This now updates total_pending_jobs
    if job_is_running:
        STATUS_WINDOW.value = f"There is {total_pending_jobs} job(s) being Processed - Click Add Job to Queue more Jobs"
    else:
        if total_pending_jobs > 0:
            STATUS_WINDOW.value = f"There is {total_pending_jobs} job(s) in the queue - Click Run Queue to Execute Them, or continue adding more jobs to the queue"
        else:
            STATUS_WINDOW.value = f"There is 0 job(s) in the queue - Click Add Job instead of Start"
    print(STATUS_WINDOW.value + "\n\n")
    return STATUS_WINDOW.value

def check_for_completed_failed_or_aborted_jobs():
    # Update counts before checking
    count_existing_jobs()
    jobs = load_jobs(jobs_queue_file)
    print(f"check for failed or aborted jobs_queue_file\n\n")

    runs = load_jobs(running_job_file)
    print(f"check of abort jobs_queue_file\n\n")
    # Extend jobs with those that have 'pending' or 'executing' status
    jobs.extend([job for job in runs if job['status'] in ('executing')])

    # Now, remove those jobs from runs
    runs = [job for job in runs if job['status'] not in ('executing')]
    # Change the status of 'executing' jobs to 'pending' in jobs list
    for job in jobs:
        if job['status'] == 'executing':
            job['status'] = 'pending'
            print(f"A probable crash or aborted job execution was detected from your last use.... checking on status of unfinished jobs..\n\n")
            print(f"the incomplete job will be moved back to the pending jobs queue - Total jobs queued = {total_pending_jobs}\n\n")

    if not keep_completed_jobs:
        jobs = [job for job in jobs if job['status'] != 'completed']


    # Save updated lists back to their respective JSON files
    save_jobs(jobs_queue_file, jobs)
    print(f"save after check abour jobs_queue_file\n\n")
    save_jobs(running_job_file, runs)
    print(f"save after check abour running_job_file\n\n")

##################################
startup_init_checks_and_cleanup()     
##################################

def job_history(command):
    if system_logs:
        today = datetime.date.today().strftime("%Y-%m-%d")
        file_path = os.path.join(working_dir, "job_history.txt")

        try:
            with open(file_path, "r") as history_file:
                lines = history_file.readlines()
                last_date_line = next((line for line in reversed(lines) if line.strip() and line.strip().split(" ")[0].count('-') == 2), "")
            last_date = last_date_line.split(" ")[0] if last_date_line else ""

            with open(file_path, "a") as history_file:
                if today > last_date:
                    history_file.write(f"\n{today}\n")
                history_file.write(f"{command}\n")
        except (FileNotFoundError, IndexError):
            with open(file_path, "a") as history_file:
                history_file.write(f"\n{command}\n")
                print(f"Job command line added to history: {command}\n\n")

def copy_to_media_cache(file_path):
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    os.makedirs(media_cache_dir, exist_ok=True)
    base_name, ext = os.path.splitext(file_name)
    counter = 0

    while True:
        new_name = f"{base_name}_{counter}{ext}" if counter > 0 else file_name
        cache_path = os.path.join(media_cache_dir, new_name)
        if not os.path.exists(cache_path):
            shutil.copy(file_path, cache_path)
            return new_name
        else:
            cache_size = os.path.getsize(cache_path)
            if file_size == cache_size:
                return new_name  # If size matches, assume it's the same file
        counter += 1

def check_for_unneeded_media_cache():
    # List all files in the media cache directory
    cache_files = os.listdir(media_cache_dir)
    jobs = load_jobs(jobs_queue_file)
    
    # Create a set to store all needed filenames from the jobs
    needed_files = set()
    for job in jobs:
        if job['status'] in {'pending', 'failed'}:
            # Extract basename and add to needed_files
            source_basename = os.path.basename(job['sourcecache'])
            target_basename = os.path.basename(job['targetcache'])
            needed_files.add(source_basename)
            needed_files.add(target_basename)

    # Delete files that are not needed
    for cache_file in cache_files:
        if cache_file not in needed_files:
            os.remove(os.path.join(media_cache_dir, cache_file))
            print(f"Deleted unneeded file: {cache_file}")


def check_if_needed_cachefile(job, source_or_target, json):
    jobs = load_jobs(json)
    relevant_statuses = {'pending', 'failed'}

    # Collect all files and their usage counts
    file_usage_counts = {}
    for other_job in jobs:
        for key in ['sourcecache', 'targetcache']:
            file_path = os.path.normpath(other_job[key])
            if other_job['status'] in relevant_statuses:
                if file_path in file_usage_counts:
                    file_usage_counts[file_path] += 1
                else:
                    file_usage_counts[file_path] = 1

    def check_and_delete_files(cache_file):
        file_path = os.path.normpath(job[cache_file])
        if file_usage_counts.get(file_path, 0) <= 1:  # Only this job uses it, or it's the last reference
            if os.path.exists(file_path):  # Check if the file actually exists
                try:
                    os.remove(file_path)
                    print(f"Successfully deleted {cache_file}: {os.path.basename(file_path)}\n\n")
                except Exception as e:
                    print(f"Failed to delete {cache_file} ({file_path}): {e}\n\n")
            else:
                print(f"No need to delete {cache_file} ({os.path.basename(file_path)}) as it does not exist.\n\n")
        else:
            print(f"Did not delete {cache_file} ({os.path.basename(file_path)}) as it's needed by another job.\n\n")
            # Decrement the count since we're keeping the file
            if file_path in file_usage_counts:
                file_usage_counts[file_path] -= 1

    if source_or_target == 'both':
        check_and_delete_files('sourcecache')
        check_and_delete_files('targetcache')
    elif source_or_target == 'source':
        check_and_delete_files('sourcecache')
    elif source_or_target == 'target':
        check_and_delete_files('targetcache')

def render() -> gradio.Blocks:
    global ADD_JOB_BUTTON, RUN_JOBS_BUTTON, STATUS_WINDOW
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
                with gradio.Blocks():
                    STATUS_WINDOW.render()
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
    global STATUS_WINDOW, EDIT_JOB_BUTTON 
    ADD_JOB_BUTTON.click(prepqueuejob, outputs=STATUS_WINDOW)
    RUN_JOBS_BUTTON.click(run_queue, outputs=STATUS_WINDOW)
    EDIT_JOB_BUTTON.click(edit_queue)
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


def get_values_from_globals(state_name):
    state_dict = {}
    for attr in dir(facefusion.globals):
        if not attr.startswith("__"):
            value = getattr(facefusion.globals, attr)
            try:
                json.dumps(value)
                state_dict[attr] = value
            except TypeError:
                continue
    if debugging:
        with open(os.path.join(working_dir, f"{state_name}.txt"), "w") as file:
            for key, val in state_dict.items():
                file.write(f"{key}: {val}\n")  # Writing each key-value pair on a new line
                print(f"{state_name}.txt created")

    return state_dict

default_values = get_values_from_globals("default_values")

def prepqueuejob():
    global total_pending_jobs, RUN_JOBS_BUTTON, ADD_JOB_BUTTON, job_is_running
    assemble_queue()
    if job_is_running:
        count_existing_jobs()
        message = f"job # {total_pending_jobs} was added  - and is line to be Processed - Click Add Job to Queue more Jobs"
        print (message)
        return message
    else:
        count_existing_jobs()
        message = f"job # {total_pending_jobs} was added to the queue - Click Run Queue to Execute queued jobs, or continue adding more jobs to the queue"
        print (message)
        return message
def assemble_queue():
    global jobs_queue, total_jobs, total_pending_jobs, media_cache_dir
    media_cache_dir = os.path.join(working_dir, "mediacache")
    current_values = get_values_from_globals('current_values')
    differences = {}

    # Define renaming rules
    renaming_rules = {
        "CUDAExecutionProvider": "cuda",
        "CPUExecutionProvider": "cpu",
        "CoreMLExecutionProvider": "coreml",
        "TensorrtExecutionProvider": "tensorrt",
        "arcface_inswapper": "inswapper",
        "arcface_blendswap": "blendswap_256",
        "arcface_simswap": "simswap_256",
        "arcface_uniface": "uniface_256"
    }

    # Compare current_values against default_values and record only changed current values
    for key, current_value in current_values.items():
        if key in ["source_paths", "target_path", "output_path", "ui_layouts"]:
            continue  # Skip these keys

        default_value = default_values.get(key)
        if default_value is None or current_value != default_value:
            if current_value is None:
                continue  # Skip if the resulting value would be None

            # Format the output based on type
            formatted_value = current_value
            if isinstance(current_value, list):
                # Apply renaming to each value in the list, if applicable, and format as space-separated string
                formatted_value = ' '.join(renaming_rules.get(item, str(item)) for item in current_value)
            elif isinstance(current_value, tuple):
                # Convert tuple to space-separated string without parentheses
                formatted_value = ' '.join(map(str, current_value))

            differences[key] = formatted_value

    if debugging:
        with open(os.path.join(working_dir, "temp_diff.txt"), "w") as file:
            for key, value in differences.items():
                file.write(f"--{key.replace('_', '-')} {value}\n")


    # Extract the first source path, assuming source_paths is always a list
    #prepairing for multiple sources code  the argument would look like this if 3 files were selected -s image1.jpg -s image2.png -s audio.mp3
    source_path = current_values.get("source_paths", [""])[0]   #no support for multiple sources, feel free to patch if you want that feature
    target_path = current_values.get("target_path", "")
    output_path = current_values.get("output_path", "")

    source_cache = copy_to_media_cache(source_path)
    print(f"Source file copied to Mediacache folder: {source_cache}\n\n")
    
    target_cache = copy_to_media_cache(target_path)
    print(f"Target file copied to Mediacache folder: {target_cache}\n\n")
        
    cache_source_path = os.path.join(media_cache_dir, source_cache)
    cache_target_path = os.path.join(media_cache_dir, target_cache)
    
    
    # Construct the additional arguments string
    additional_args = " ".join(f"--{key.replace('_', '-')} {value}" for key, value in differences.items() if value)
    if debugging:
        with open(os.path.join(working_dir, "additional_args.txt"), "w") as file:
            file.write(json.dumps(additional_args) + "\n")
    batch_command = f"python run.py -s \"{cache_source_path}\" -t \"{cache_target_path}\" -o \"{output_path}\" --headless"
    batch_command += f" {additional_args}"
    # Load the existing jobs using the defined function
    jobs = load_jobs(jobs_queue_file)

    # Create a new job and add it to the job queue
    new_job = {
        "command": batch_command,
        "status": "pending",
        "sourcecache": (cache_source_path),
        "targetcache": (cache_target_path)
    }

    # Check for any jobs with a status 'editing' and replace it with the new job
    found_editing = False
    for job in jobs:
        if job['status'] == 'editing':
            job.update(new_job)
            found_editing = True
            break

    # If no 'editing' job was found, append the new job to the queue
    if not found_editing:
        jobs.append(new_job)

    # Save the updated job queue back to the JSON file using the defined function
    save_jobs(jobs_queue_file, jobs)
    # Clean up batch_command for logging
    cleaned_batch_command = batch_command.replace('\\\\', '\\').replace('"', '')

    # Save job to job history file, Update the queue status text and count existing jobs and total jobs sent for processing
    job_history(cleaned_batch_command)
    count_existing_jobs()
    print_existing_jobs()


def run_queue():
    global total_pending_jobs, STATUS_WINDOW, job_is_running
    # Count the total number of jobs and pending jobs
    count_existing_jobs()

    # Check if there are pending jobs and the execution thread has not started
    if total_pending_jobs > 0 and not job_is_running:
        job_is_running = True  # Set the lock before starting the job execution
        message = f"Executing Jobs - There are {total_pending_jobs} job(s) in the Queue\n\n"
        print(message)
        execute_jobs()
        job_is_running = False  # Reset the lock after finishing the job execution
        return message
    elif total_pending_jobs > 0 and job_is_running:
        message = f"a Jobs are already executing, with {total_pending_jobs-1} more job(s) waiting to be processed.\n\n"
        print(message)
        return message
    else:
        message = f"Whoops!!!, There are {total_pending_jobs} job(s) queued. Please add to the queue before pressing Run Queue.\n\n"
        print(message)
        return message

def execute_jobs():
    global total_pending_jobs, job_is_running
    count_existing_jobs()
    current_job_number = 0
    # Set the execution lock to True to indicate the function is running
    job_is_running = True
    # Section 2: Transfer 1 pending jobs from jobs to run_job
    jobs = load_jobs(jobs_queue_file)
    run_job = load_jobs(running_job_file)
    # Find the first pending job
    first_pending_job = next((job for job in jobs if job['status'] == 'pending'), None)
    if first_pending_job:
        # Add it to the run_job list with status 'pending'
        run_job.append(first_pending_job)
        save_jobs(running_job_file, run_job)  

        # Remove the first pending job from jobs by keeping jobs that are not the first_pending_job
        jobs = [job for job in jobs if job != first_pending_job]

        # Change status to 'executing' and add it back to the jobs
        first_pending_job['status'] = 'executing'
        jobs.append(first_pending_job)

        # Save the updated main jobs queue back to the jobs_queue_file
        save_jobs(jobs_queue_file, jobs)

        # Clear first_pending_job after everything is saved
        first_pending_job = None

    # Reset the jobs if necessary (depending on additional context or requirements)
    jobs = []
    while True:
        run_job = load_jobs(running_job_file)
        # Section 3: Check if there are pending jobs
        total_pending_jobs_queue = len([job for job in run_job if job['status'] == 'pending'])
        if total_pending_jobs_queue == 0:
            print(f"All {current_job_number} Jobs have been proccesed, No pending jobs remaining.")
            break

        # Section 4: Process the first and only pending job in the running_job_file
        current_run_job = None
    # Since running_job_file will only have one job with a status of 'pending',
        # directly access this job without the need for a loop.
        if run_job and run_job[0]['status'] == 'pending':
            # Directly take the first job assuming it is the pending one
            current_run_job = run_job[0]
            current_run_job['status'] = 'executing'  # Update the status in current_run_job
            run_job[0]['status'] = 'executing'  # Ensure the list is also updated

        # Save the changes to the running_job_file
        save_jobs(running_job_file, run_job)
        # Optionally clear run_job if necessary, though this might depend on your broader use case
        run_job = []

        # Assuming current_job_number tracks the number of jobs processed or similar
        current_job_number += 1


        print(f"Starting Job {current_job_number}, with {total_pending_jobs-1} jobs remaining: {os.path.basename(current_run_job['sourcecache'])} -> {os.path.basename(current_run_job['targetcache'])}\n\n")

        command_for_printing = current_run_job['command'].replace('\\\\', '\\')
        print(f"Executing Job #{current_job_number} - {command_for_printing}\n\n")
        
        process = subprocess.Popen(
            command_for_printing, 
            shell=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            text=True, 
            bufsize=1
        )
        previous_line_was_progress = False
        while True:
            line = process.stdout.readline()
            if not line:
                break
            if line.startswith("Processing:") or line.startswith("Analysing:"):
                print(f"Job {current_job_number} - {line.strip()[:100]}", end='\r', flush=True)
                previous_line_was_progress = True
            else:
                if previous_line_was_progress:
                    print("\n\n", end='', flush=True)
                    previous_line_was_progress = False
                print(line, end='')

        return_code = process.wait()

        # List of error phrases to watch for
        error_phrases = [
            "FFMpeg is not installed",
            "Extracting frames failed",
            "Temporary frames not found",
            "Merging video failed",
            "Processing to image failed",
            "Processing to video failed",
            "Select a image for source path",
            "Select a audio for source path",
            "Select a video for target path",
            "Select a image or video for target path",
            "Select a file or directory for output path",
            "No source face detected",
            "could not be loaded"
        ]

        # Collect all output for checking against error phrases
        output_log = process.communicate()[0] if process.stdout else ""

        if return_code == 0 and not any(phrase in output_log for phrase in error_phrases):
            current_run_job['status'] = 'completed'
            print(f"Job #{current_job_number} completed successfully.")
        else:
            print(f"Job #{current_job_number} failed. Please check validity of {job['sourcecache']} and {job['targetcache']}.")
            current_run_job['status'] = 'failed'



        run_job = load_jobs(running_job_file)
        for i, job in enumerate(run_job):
            if job['status'] == 'executing':
                del run_job[i]  # Remove it from run_job
                save_jobs(running_job_file, run_job)
                run_job = []  # Clearing the list if needed, though might be redundant after deletion
                break

        # Section 6: Append executed job back to the job queue
        jobs = load_jobs(jobs_queue_file)
        jobs.append(current_run_job)
        save_jobs(jobs_queue_file, jobs)
        jobs = []  # Resetting jobs after saving, ensure this is intended

        # Reset current_run_job to None, indicating it's no longer holding a job
        current_run_job = None
        

        # Find the first pending job
        jobs = load_jobs(jobs_queue_file)
        first_pending_job = next((job for job in jobs if job['status'] == 'pending'), None)
        if first_pending_job:
            # Add it to the run_job list
            run_job.append(first_pending_job)
            # Remove the first pending job from jobs by keeping jobs that are not the first_pending_job
            jobs = [job for job in jobs if job != first_pending_job]
        # Save updated lists back to their respective JSON files
        save_jobs(running_job_file, run_job)
        save_jobs(jobs_queue_file, jobs)
        jobs = []
        first_pending_job = None
    job_is_running = False
    check_for_completed_failed_or_aborted_jobs()
    check_for_unneeded_media_cache()
# Keep references to images to prevent garbage collection
image_references = {}

def edit_queue():
    global root, frame
    EDIT_JOB_BUTTON = gradio.Button("Edit Queue")
    jobs = load_jobs(jobs_queue_file)  # Load jobs when the program starts
    root = tkinter.Tk()
    root.geometry('725x800')
    root.title("Edit Queued Jobs")
    root.lift()
    root.attributes('-topmost', True)
    root.after_idle(root.attributes, '-topmost', False)
    scrollbar = Scrollbar(root)
    scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
    canvas = tkinter.Canvas(root, scrollregion=(0, 0, 0, 7000))
    canvas.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True)
    frame = Frame(canvas)
    canvas.create_window((0, 0), window=frame, anchor='nw')

    close_button = tkinter.Button(root, text="Close Window", command=root.destroy)
    close_button.pack(pady=5)

    # # Adding additional buttons as requested
    # all_jobs_button = tkinter.Button(root, text="All Jobs", command=lambda: update_job_listbox(jobs))
    # all_jobs_button.pack(pady=5)

    # jobs_pending_button = tkinter.Button(root, text="Jobs Pending", command=lambda: update_job_listbox('pending'))
    # jobs_pending_button.pack(pady=5)

    # jobs_failed_button = tkinter.Button(root, text="Jobs Failed", command=lambda: update_job_listbox('failed'))
    # jobs_failed_button.pack(pady=5)

    # jobs_executing_button = tkinter.Button(root, text="Jobs Executing", command=lambda: update_job_listbox('executing'))
    # jobs_executing_button.pack(pady=5)

    canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(int(-1*(event.delta/120)), "units"))


    
    def close_window():
        root.destroy()
        save_jobs(jobs_queue_file, jobs)

    def reload_in_ui_to_edit(job):
        # Confirmation dialog before editing the job
        response = messagebox.askyesno("Confirm Edit", "THIS WILL REMOVE THIS PENDING JOB FROM THE QUEUE, AND LOAD IT INTO FACEFUSION WEBUI FOR EDITING, WHEN DONE EDITING CLICK START TO RUN IT OR ADD JOB TO REQUEUE IT. ARE YOU SURE YOU WANT TO EDIT THIS JOB", icon='warning')
        if not response:
            # If user clicks 'No', save the jobs and update the listbox, then exit the function
            save_jobs(jobs_queue_file, jobs)
            update_job_listbox()
            return

        # Replace '--headless' with '--ui-layouts QueueItUp' in the command string
        headless_index = job['command'].find('--headless')
        if headless_index != -1:
            job['command'] = job['command'][:headless_index] + job['command'][headless_index + len('--headless'):]

        # Change status to 'editing'
        job['status'] = 'editing'
        save_jobs(jobs_queue_file, jobs)
        update_job_listbox()
        top = Toplevel()
        top.title("Please Wait")
        message_label = tkinter.Label(top, text="Please wait while the job loads back into FaceFusion...", padx=20, pady=20)
        message_label.pack()

        subprocess.Popen(job['command'])
        
        # top.after(1000, close_window)
        # Show a message box and keep it for 5 seconds


        # Center the Toplevel window on the screen
        top.update_idletasks()
        x = (top.winfo_screenwidth() // 2) - (top.winfo_reqwidth() // 2)
        y = (top.winfo_screenheight() // 2) - (top.winfo_reqheight() // 2)
        top.geometry("+{}+{}".format(x, y))
        top.after(7000, top.destroy)
        # Execute the command using subprocess and handle the output


        # Schedule the close window function and the Toplevel destruction





    def delete_job(job, source_or_target):
        job['status'] = ('deleting')
        # Call the new function to handle cache file checks and deletion
        source_or_target='both'
        check_if_needed_cachefile(job, 'both', jobs_queue_file)
        # Remove the job from the list and save the changes
        jobs.remove(job)
        save_jobs(jobs_queue_file, jobs)
        update_job_listbox()

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

    def create_thumbnail(parent, job, source_or_target, size=(100, 100)):
        file_path = job[source_or_target + 'cache']
        if not os.path.exists(file_path):
            # Create a button as a placeholder for non-existing files that allows updating the file
            button = Button(parent, text="File not found\nClick to update", bg='white', fg='black',
                            command=lambda ft=source_or_target: select_file(parent, job, ft))
            button.pack(pady=2, fill='x', expand=True)
            return button

        try:
            if file_path.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
                # Create a thumbnail for video files
                cmd = [
                    'ffmpeg', '-i', file_path,
                    '-ss', '00:00:01',  # Take a snapshot at the 1-second mark
                    '-vframes', '1',    # Only take one frame (the snapshot)
                    '-vf', f'scale={size[0]}:{size[1]}',  # Scale the image to the given size
                    '-f', 'image2pipe', '-c:v', 'png', 'pipe:1'
                ]
                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                image_data = BytesIO(result.stdout)
                photo_image = PhotoImage(data=image_data.read())
            else:
                # Create a thumbnail for image files
                # Use FFmpeg to ensure uniform handling of image resizing and maintain aspect ratio
                cmd = [
                    'ffmpeg', '-i', file_path,
                    '-vf', f'scale={size[0]}:{size[1]}',  # Scale the image to the given size
                    '-f', 'image2pipe', '-c:v', 'png', 'pipe:1'
                ]
                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                image_data = BytesIO(result.stdout)
                photo_image = PhotoImage(data=image_data.read())
            # Create a button to display the thumbnail
            button = Button(parent, image=photo_image, command=lambda ft=source_or_target: select_file(parent, job, ft))
            button.image = photo_image  # keep a reference!
            button.pack(side='left', padx=5)
            return button
        except Exception as e:
            print(f"Error creating thumbnail for {file_path}: {e}")
            return None

    def select_file(parent, job, source_or_target):
        # Determine the allowed file types based on the source_or_target and current file extension
        file_types = []
        if source_or_target == 'source':
            file_types = [('Image files', '*.jpg *.jpeg *.png')]
        elif source_or_target == 'target':
            # Get current extension
            current_extension = job['targetcache'].lower().rsplit('.', 1)[-1]
            if current_extension in ['jpg', 'jpeg', 'png']:
                file_types = [('Image files', '*.jpg *.jpeg *.png')]
            elif current_extension in ['mp4', 'mov', 'avi', 'mkv']:
                file_types = [('Video files', '*.mp4 *.avi *.mov *.mkv')]

        # Open file dialog with the appropriate filters
        selected_path = filedialog.askopenfilename(title=f"Select {source_or_target.capitalize()} File", filetypes=file_types)
        if selected_path:
            check_if_needed_cachefile(job, source_or_target, jobs_queue_file)
            path = selected_path  # Ensure path uses correct separators
            update_command(job, source_or_target, path)

            job['status'] = 'pending'
            save_jobs(jobs_queue_file, jobs)  # Save the updated jobs to the JSON file
            update_job_listbox()  # Refresh the job list to show the new thumbnail or placeholder

    def update_command(job, source_or_target, path):

        cache_name = copy_to_media_cache(path)

        # Replace backslashes with double backslashes for regex compatibility
        cache_path = os.path.join(media_cache_dir, cache_name)
        cache_path_escaped = cache_path.replace("\\", "\\\\")
        pattern = {
            'source': r'(-s\s+)"[^"]+"',
            'target': r'(-t\s+)"[^"]+"',
            'output': r'(-o\s+)"[^"]+"'
        }
        job['command'] = re.sub(pattern[source_or_target], r'\1"' + cache_path_escaped + '"', job['command'])


        if source_or_target in ['source', 'target']:
            cache_key = f'{source_or_target}cache'
            job[cache_key] = cache_path
        save_jobs(jobs_queue_file, jobs)
        update_job_listbox()        
    def update_job_listbox():
        global image_references
    # # def update_job_listbox(status_filter=None):
        # # global image_references, frame, jobs_queue_file
        # jobs = load_jobs(jobs_queue_file)  # Reload the jobs from file every time the function is called

        image_references.clear()
        for widget in frame.winfo_children():
            widget.destroy()

        # # # Validate the status_filter and filter jobs accordingly
        # # filtered_jobs = [job for job in jobs if job['status'] == status_filter] if isinstance(status_filter, str) else jobs
        for index, job in enumerate(jobs):
 #      for index, job in enumerate(filtered_jobs):
            # Retrieve the original job index in jobs for direct updates
            # original_index = jobs.index(job)

            source_thumb_exists = os.path.exists(job['sourcecache'])
            target_thumb_exists = os.path.exists(job['targetcache'])
            # bg_color = 'red' if not source_thumb_exists or not target_thumb_exists else 'SystemButtonFace'

            # if job['status'] == 'failed':
                # bg_color = 'red'
            # elif job['status'] == 'pending':
                # bg_color = 'SystemButtonFace'
            # elif job['status'] == 'executing':
                # bg_color = 'black'
            # elif job['status'] == 'completed':
                # bg_color = 'grey'
            if job['status'] == 'failed':
                bg_color = 'red'
            if job['status'] == 'pending':
                bg_color = 'SystemButtonFace'
            if job['status'] == 'executing':
                bg_color = 'black'
            if not source_thumb_exists or not target_thumb_exists:
               bg_color = 'red'
            if job['status'] == 'completed':
                bg_color = 'grey'
            if job['status'] == 'editing':
                bg_color = 'green'

            # Create job frame with updated background color
            job_frame = tkinter.Frame(frame, borderwidth=2, relief='groove', background=bg_color)
            job_frame.pack(fill='x', expand=True, padx=5, pady=5)
            # Add other buttons and labels as before...
            # Delete button
            delete_button = tkinter.Button(job_frame, text="Delete", command=lambda j=job: delete_job(j, 'both'))
            delete_button.pack(side='left', padx=2)
            # Create or update thumbnail for source
            source_button = create_thumbnail(job_frame, job, 'source')
            source_button.pack(side='left', padx=10)
            # Define a bold font
            bold_font = font.Font(family="Helvetica", size=10, weight="bold")
            # Arrow label and status with multiline string and bold font
            arrow_label = Label(job_frame, text=f"{job['status']}\n-->", font=bold_font)
            arrow_label.pack(side='left', padx=5)
            # Create or update thumbnail for target
            target_button = create_thumbnail(job_frame, job, 'target')
            target_button.pack(side='left', padx=10)
            # Replace the command label with a button
            custom_font = font.Font(family="Helvetica", size=18, weight="bold")
            command_button = tkinter.Button(job_frame, text="UN-Queue It Up\nedit the job parameters", font=bold_font, wraplength=400, justify='left')
            command_button.pack(side='left', padx=10, fill='x', expand=True)
            command_button.bind("<Button-1>", lambda event: reload_in_ui_to_edit(job))  # Bind left mouse click to edit_command
            # Move frame for the move buttons
            move_frame = tkinter.Frame(job_frame)
            move_frame.pack(side='left', fill='y', padx=5)
            # Move up button
            move_up_button = tkinter.Button(move_frame, text="Top", command=lambda idx=index: move_job_to_top(idx))
            move_up_button.pack(side='top', fill='x')
            move_up_button = tkinter.Button(move_frame, text="Up", command=lambda idx=index: move_job_up(idx))
            move_up_button.pack(side='top', fill='x')
            # Move down button
            move_down_button = tkinter.Button(move_frame, text="Down", command=lambda idx=index: move_job_down(idx))
            move_down_button.pack(side='top', fill='x')
            # Move bottom button
            move_bottom_button = tkinter.Button(move_frame, text="Bottom", command=lambda idx=index: move_job_to_bottom(idx))
            move_bottom_button.pack(side='top', fill='x')
    root.after(1000, update_job_listbox)  # Optionally refresh listbox every 1000 milliseconds if needed
    root.mainloop()
    if __name__ == '__main__':
        edit_queue()

def run(ui : gradio.Blocks) -> None:
	concurrency_count = min(8, multiprocessing.cpu_count())
	ui.queue(concurrency_count = concurrency_count).launch(show_api = True, inbrowser = True, quiet = False)
