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
from io import BytesIO
import facefusion.globals
from facefusion import core
from tkinter.filedialog import askdirectory
from tkinter import filedialog, font, Toplevel, messagebox, PhotoImage, Tk, Canvas, Scrollbar, Frame, Label, Button
from facefusion.processors.frame import globals as frame_processors_globals, choices as frame_processors_choices
from facefusion.uis.components import about, frame_processors, frame_processors_options, execution, execution_thread_count, execution_queue_count, memory, temp_frame, output_options, common_options, source, target, output, preview, trim_frame, face_analyser, face_selector, face_masker

def pre_check() -> bool:
	return True

def pre_render() -> bool:
	return True

####Globals and toggles
program_root = os.getenv('MYAPP_ROOT', os.getcwd())

user_dir = "QueueItUp"
working_dir = os.path.normpath(os.path.join(program_root, user_dir))
media_cache_dir = os.path.normpath(os.path.join(working_dir, "mediacache"))
jobs_queue_file = os.path.normpath(os.path.join(working_dir, "jobs_queue.json"))

print("Working Directory:", working_dir)
print("Media Cache Directory:", media_cache_dir)
print("Jobs Queue File:", jobs_queue_file)
 
debugging = True
system_logs= False
history_logs= True
keep_completed_jobs = True
ADD_JOB_BUTTON = gradio.Button("Add Job ", variant="primary")
RUN_JOBS_BUTTON = gradio.Button("Run Jobs", variant="primary")
STATUS_WINDOW = gradio.Textbox(label="Job Status")
EDIT_JOB_BUTTON = gradio.Button("Edit Jobs")
#status_priority = {'editing': 0, 'pending': 1, 'failed': 2, 'executing': 3, 'completed': 4}
create_and_verify_json = 0
JOB_IS_RUNNING = 0
JOB_IS_EXECUTING = 0
PENDING_JOBS_COUNT = 0
CURRENT_JOB_NUMBER = 0
    # ANSI Color Codes     
RED = '\033[91m'     #use this  
GREEN = '\033[92m'     #use this  
YELLOW = '\033[93m'     #use this  
BLUE = '\033[94m'     #use this  
ENDC = '\033[0m'       #use this    Resets color to default

def get_values_from_globals(state_name):
    state_dict = {}
    modules = [facefusion.globals, frame_processors_globals]  # List of modules to extract values from

    for module in modules:
        for attr in dir(module):
            if not attr.startswith("__"):
                value = getattr(module, attr)
                try:
                    json.dumps(value)  # Check if the value is JSON serializable
                    state_dict[attr] = value  # Store or update the value in the dictionary
                except TypeError:
                    continue  # Skip values that are not JSON serializable

    # Optional debugging to write state to file
    if debugging:
        with open(os.path.join(working_dir, f"{state_name}.txt"), "w") as file:
            for key, val in state_dict.items():
                file.write(f"{key}: {val}\n")
        print(f"{state_name}.txt created")

    return state_dict

# Use the function to grab default values
default_values = get_values_from_globals("default_values")

def create_and_verify_json(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as json_file:  
                json.load(json_file)
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
def load_jobs(file_path):
    with open(file_path, 'r') as file:
        jobs = json.load(file)
    return (jobs)

def save_jobs(file_path, jobs):
    with open(file_path, 'w') as file:
        json.dump(jobs, file, indent=4, separators=(',', ': '))

def count_existing_jobs():
    global PENDING_JOBS_COUNT
    jobs = load_jobs(jobs_queue_file)
    PENDING_JOBS_COUNT = len([job for job in jobs if job['status'] in ['pending', 'editing']])


    return PENDING_JOBS_COUNT

def print_existing_jobs():
    global STATUS_WINDOW

    count_existing_jobs()
    if JOB_IS_RUNNING:
        STATUS_WINDOW.value = f"There is {PENDING_JOBS_COUNT + JOB_IS_RUNNING} job(s) being Processed - Click Add Job to Queue more Jobs"
    else:
        if PENDING_JOBS_COUNT > 0:
            STATUS_WINDOW.value = f"There is {PENDING_JOBS_COUNT + JOB_IS_RUNNING} job(s) in the queue - Click Run Queue to Execute Them, or continue adding more jobs to the queue"
        else:
            STATUS_WINDOW.value = f"There is 0 job(s) in the queue - Click Add Job instead of Start"
    print(STATUS_WINDOW.value + "\n\n")
    return STATUS_WINDOW.value

def check_for_completed_failed_or_aborted_jobs():
    # Update counts before checking
    count_existing_jobs()
    jobs = load_jobs(jobs_queue_file)
    for job in jobs:
        if job['status'] == 'executing':
            job['status'] = 'pending'
            print(f"{RED}A probable crash or aborted job execution was detected from your last use.... checking on status of unfinished jobs..{ENDC}\n\n")
            print(f"{GREEN}A job {GREEN}{os.path.basename(job['sourcecache'])}{ENDC} to -> {GREEN}{os.path.basename(job['targetcache'])} was found that terminated early it will be moved back to the pending jobs queue - you have a Total of {PENDING_JOBS_COUNT + JOB_IS_RUNNING} in the Queue\n\n")
            save_jobs(jobs_queue_file, jobs)
    if not keep_completed_jobs:
        jobs = [job for job in jobs if job['status'] != 'completed']
        save_jobs(jobs_queue_file, jobs)
        print(f"{BLUE}All completed jobs have been removed, if you would like to keep completed jobs change the setting to True{ENDC}\n\n")
    
def startup_init_checks_and_cleanup():
    print(f"{BLUE}Welcome Back To FaceFusion Queueing Addon\n\n")
    print(f"Checking Status{ENDC}\n\n")
    # Create directories if they do not exist
    if not os.path.exists(working_dir):
        os.makedirs(working_dir)
    if not os.path.exists(media_cache_dir):
        os.makedirs(media_cache_dir)

    create_and_verify_json(jobs_queue_file)
    check_for_completed_failed_or_aborted_jobs()
    # Optionally, perform additional setup or logging here
    print(f"{GREEN}STATUS CHECK COMPLETED. {BLUE}You are now ready to QUEUE IT UP!{ENDC}")

    print_existing_jobs()
    return
##################################
startup_init_checks_and_cleanup()     
##################################

def job_history(text, command):
    if history_logs:
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
                history_file.write(f"{text} - {command}\n")
        except (FileNotFoundError, IndexError):
            with open(file_path, "a") as history_file:
                history_file.write(f"\n{command}\n")
                print(f"command line added to history: {command}\n\n")

def copy_to_media_cache(file_path):
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    base_name, ext = os.path.splitext(file_name)
    counter = 0

    while True:
        new_name = f"{base_name}_{counter}{ext}" if counter > 0 else file_name
        cache_path = os.path.join(media_cache_dir, new_name)
        if not os.path.exists(cache_path):
            shutil.copy(file_path, cache_path)
            return cache_path
        else:
            cache_size = os.path.getsize(cache_path)
            if file_size == cache_size:
                return cache_path  # If size matches, assume it's the same file
        counter += 1

def check_for_unneeded_media_cache():
    # List all files in the media cache directory
    cache_files = os.listdir(media_cache_dir)
    jobs = load_jobs(jobs_queue_file)
    
    # Create a set to store all needed filenames from the jobs
    needed_files = set()
    for job in jobs:
        if job['status'] in {'pending', 'failed', 'missing', 'editing', 'executing'}:
            # Extract basename and add to needed_files
            source_basename = os.path.basename(job['sourcecache'])
            target_basename = os.path.basename(job['targetcache'])
            needed_files.add(source_basename)
            needed_files.add(target_basename)

    # Delete files that are not needed
    for cache_file in cache_files:
        if cache_file not in needed_files:
            os.remove(os.path.join(media_cache_dir, cache_file))
            print(f"{GREEN}Deleted unneeded file: {cache_file}{ENDC}")


def check_if_needed_cachefile(job, source_or_target, json):
    jobs = load_jobs(json)
    relevant_statuses = {'pending', 'failed', 'missing', 'editing', 'executing'}
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
                    print(f"Successfully deleted the file:{GREEN} {os.path.basename(file_path)}{ENDC} as it is no longer needed by any other jobs\n\n")
                except Exception as e:
                    print(f"{RED}Failed to delete {YELLOW} ({file_path}):{ENDC} {e}\n\n")
            else:
                print(f"{BLUE}No need to delete the file:{GREEN} ({os.path.basename(file_path)}) as it does not exist.{ENDC}\n\n")
        else:
            print(f"{BLUE}Did not delete the file: {GREEN}({os.path.basename(file_path)}) as it's needed by another job.{ENDC}\n\n")
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
    ADD_JOB_BUTTON.click(assemble_queue, outputs=STATUS_WINDOW)
    RUN_JOBS_BUTTON.click(execute_jobs, outputs=STATUS_WINDOW)
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


def assemble_queue():
    global RUN_JOBS_BUTTON, ADD_JOB_BUTTON, STATUS_WINDOW
    #default_values are already initialized, do not call for new default values
    current_values = get_values_from_globals('current_values')
    differences = {}


    dicts = [current_values, default_values]  # Ensure these are defined or passed to this function appropriately

    for d in dicts:
        if "execution_providers" in d:
            if d["execution_providers"] == ["CUDAExecutionProvider"]:
                d["execution_providers"] = 'cuda'
            elif d["execution_providers"] == ["CPUExecutionProvider"]:
                d["execution_providers"] = 'cpu'
            elif d["execution_providers"] == ["CoreMLExecutionProvider"]:
                d["execution_providers"] = 'coreml'


            
    # Skip these keys
    keys_to_skip = ["source_paths", "target_path", "output_path", "ui_layouts", "face_recognizer_model"]

    # Check if "frame-processors" includes "face-enhancer" or "frame-enhancer"
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
        if default_value is None or current_value != default_value:
            if current_value is None:
                continue  # Skip if the resulting value would be None

            # Format the output based on type
            formatted_value = current_value
            if isinstance(current_value, list):
                # Convert list to space-separated string
                formatted_value = ' '.join(map(str, current_value))
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

    while True:
        if JOB_IS_RUNNING:
            if JOB_IS_EXECUTING:
                print("Job is executing.")
                break  # Exit the loop if the job is executing
            else:
                print("Job is running but not executing. Stuck in loop.\n")
                time.sleep(1)  # Wait for 1 second to reduce CPU usage, continue checking
        else:
            print("Job is not running.")
            break  # Exit the loop if the job is not running

    oldeditjob = None
   
    # Check for any jobs with a status 'editing' and replace it with the new job
    found_editing = False
    jobs = load_jobs(jobs_queue_file)

    for job in jobs:
        if job['status'] == 'editing':
            # Copy the job's data to oldeditjob
            oldeditjob = job.copy()  # Use copy to ensure oldeditjob is a separate dictionary
            found_editing = True
            break

    cache_source_path = copy_to_media_cache(source_path)
    print(f"{GREEN}Source file{ENDC} copied to Media Cache folder: {GREEN}{os.path.basename(cache_source_path)}{ENDC}\n\n")
    cache_target_path = copy_to_media_cache(target_path)
    print(f"{GREEN}Target file{ENDC} copied to Media Cache folder: {GREEN}{os.path.basename(cache_target_path)}{ENDC}\n\n")
    

    # Construct the additional arguments string
    additional_args = " ".join(f"--{key.replace('_', '-')} {value}" for key, value in differences.items() if value)
    if debugging:
        with open(os.path.join(working_dir, "additional_args.txt"), "w") as file:
            file.write(json.dumps(additional_args) + "\n")
    batch_command = f"python run.py -s \"{cache_source_path}\" -t \"{cache_target_path}\" -o \"{output_path}\" --headless"
    batch_command += f" {additional_args}"

    new_job = {
        "command": batch_command,
        "status": "pending",
        "sourcecache": (cache_source_path),
        "targetcache": (cache_target_path)
    }

    if found_editing:  
        job.update(new_job)
        save_jobs(jobs_queue_file, jobs)
        if not (oldeditjob['sourcecache'] == new_job['sourcecache'] or oldeditjob['sourcecache'] == new_job['targetcache']):
            check_if_needed_cachefile(oldeditjob, 'source', jobs_queue_file)

        if not (oldeditjob['targetcache'] == new_job['sourcecache'] or oldeditjob['targetcache'] == new_job['targetcache']):
            check_if_needed_cachefile(oldeditjob, 'target', jobs_queue_file)

    if not found_editing:
        jobs.append(new_job)
        save_jobs(jobs_queue_file, jobs)

    # Clean up batch_command for logging
    cleaned_batch_command = batch_command.replace('\\\\', '\\').replace('"', '')

    job_history('Job Added', cleaned_batch_command)
    print ("job added to history log")
    count_existing_jobs()


    if JOB_IS_RUNNING:
        message = f"{BLUE}job # {CURRENT_JOB_NUMBER + PENDING_JOBS_COUNT} was added {ENDC} - and is in line to be Processed - Click Add Job to Queue more Jobs"
        message2 = f"job # {CURRENT_JOB_NUMBER + PENDING_JOBS_COUNT} was added - and is in line to be Processed - Click Add Job to Queue more Jobs"
        print (message)
        return message2
    else:
        message = f"{BLUE}Your Job was Added to the queue,{ENDC} there are a total of {GREEN}#{PENDING_JOBS_COUNT} Job(s){ENDC} in the queue,  Add More Jobs, Edit the Queue, or Click Run Queue to Execute all the queued jobs"
        message2 = f"Your Job was Added to the queue, there are a total of #{PENDING_JOBS_COUNT} Job(s) in the queue,  Add More Jobs, Edit the Queue, or Click Run Queue to Execute all the queued jobs"
        print(message)
        return message2

def execute_jobs():
    global JOB_IS_RUNNING, JOB_IS_EXECUTING,CURRENT_JOB_NUMBER
    count_existing_jobs()
    if not PENDING_JOBS_COUNT + JOB_IS_RUNNING > 0:
        message = f"Whoops!!!, There are {PENDING_JOBS_COUNT} Job(s) queued.  Add a job to the queue before pressing Run Queue.\n\n"
        print(message)
        return message    
    if PENDING_JOBS_COUNT + JOB_IS_RUNNING > 0 and JOB_IS_RUNNING:
        message = f"Whoops a Jobs is already executing, with {PENDING_JOBS_COUNT} more job(s) waiting to be processed.\n\n You don't want more then one job running at the same time your GPU cant handle that,\n\nYou just need to click add job if jobs are already running, and thie job will be placed in line for execution. you can edit the job order with Edit Queue button\n\n"
        print(message)
        return(message)
    jobs = load_jobs(jobs_queue_file)
    JOB_IS_RUNNING = 1
    CURRENT_JOB_NUMBER = 0
    current_run_job = {}
    first_pending_job = next((job for job in jobs if job['status'] == 'pending'), None)
    # Remove the first pending job from jobs by keeping jobs that are not the first_pending_job
    jobs = [job for job in jobs if job != first_pending_job]
    # Change status to 'executing' and add it back to the jobs
    first_pending_job['status'] = 'executing'
    jobs.append(first_pending_job)
    save_jobs(jobs_queue_file, jobs)

    # Reset the jobs if necessary (depending on additional context or requirements)
    while True:
        if not first_pending_job['status'] == 'executing':
            break
        current_run_job = first_pending_job
        JOB_IS_EXECUTING = 1
        CURRENT_JOB_NUMBER += 1
        print(f"{PENDING_JOBS_COUNT-1} jobs remaining:{ENDC}\n\n\n\n")
        print(f"{BLUE}Starting Job #{GREEN} {CURRENT_JOB_NUMBER}{ENDC}\n\n")
        command_for_running = current_run_job['command'].replace('\\\\', '\\')
        print(f"{BLUE}Executing Job # {CURRENT_JOB_NUMBER} of {CURRENT_JOB_NUMBER + PENDING_JOBS_COUNT}  {ENDC} - {YELLOW}{command_for_running}\n\n")
        
        print(f"Job #{CURRENT_JOB_NUMBER} will be SWAPPING - {GREEN}{os.path.basename(current_run_job['sourcecache'])}{ENDC} to -> {GREEN}{os.path.basename(current_run_job['targetcache'])}{ENDC}\n\n")

        job_history('Executing', command_for_running)
        
        # Set up the subprocess to directly output everything to the terminal
        process = subprocess.Popen(
            command_for_running,
            shell=True,
            stdout=None,  # Default, outputs directly to the terminal
            stderr=None,  # Default, outputs directly to the terminal
            text=True
        )
        # Continuously check if the process has finished
        while True:
            if process.poll() is not None:  # Check if the process has terminated
                break  # Exit the loop if the process is done
            time.sleep(0.1)  # Sleep for a short interval to avoid busy waiting

        return_code = process.poll()  # Get the exit code after the loop

        JOB_IS_EXECUTING = 0  # Reset the job execution flag

        if return_code == 0:
            current_run_job['status'] = 'completed'
            print(f"{BLUE}Job {CURRENT_JOB_NUMBER} completed successfully.{ENDC}\n")
        else:
            current_run_job['status'] = 'failed'
            print(f"{RED}Job {CURRENT_JOB_NUMBER} failed.{ENDC} Please check the validity of {RED}{os.path.basename(current_run_job['sourcecache'])}{ENDC} and {RED}{os.path.basename(current_run_job['targetcache'])}.{ENDC}")
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
            print(f"{BLUE}a total of {CURRENT_JOB_NUMBER} Jobs have completed processing,{ENDC}...... {GREEN}the Queue is now empty, {BLUE}Feel Free to QueueItUp some more..{ENDC}")
            current_run_job = None
            first_pending_job = None
            break
    JOB_IS_RUNNING = 0
    save_jobs(jobs_queue_file, jobs)
    check_for_unneeded_media_cache()
image_references = {}

def edit_queue():
    global root, frame
    EDIT_JOB_BUTTON = gradio.Button("Edit Queue")
    
    jobs = load_jobs(jobs_queue_file)  # Load jobs when the program starts
    root = tkinter.Tk()
    root.geometry('1200x800')
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
    canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(int(-1*(event.delta/120)), "units"))
    custom_font = font.Font(family="Helvetica", size=12, weight="bold")
    bold_font = font.Font(family="Helvetica", size=12, weight="bold")
    
    close_button = tkinter.Button(root, text="Close Window", command=root.destroy, font=custom_font)
    close_button.pack(pady=5)

    refresh_button = tkinter.Button(root, text="Refresh View", command=lambda: refresh_frame_listbox(), font=custom_font)
    refresh_button.pack(pady=5)

    run_jobs_button = tkinter.Button(root, text=f"RUN {PENDING_JOBS_COUNT} JOBS", command=lambda: check_and_run_jobs(), font=custom_font)
    run_jobs_button.pack(pady=5)


    pending_jobs_button = tkinter.Button(root, text=f"Delete {PENDING_JOBS_COUNT} Pending Jobs", command=lambda: delete_pending_jobs, font=custom_font)
    pending_jobs_button.pack(pady=5)
    
    missing_jobs_button = tkinter.Button(root, text="Delete Missing ", command=lambda: delete_missing_media_jobs, font=custom_font)
    missing_jobs_button.pack(pady=5)

    failed_jobs_button = tkinter.Button(root, text="Delete Failed", command=lambda: delete_failed_jobs, font=custom_font)
    failed_jobs_button.pack(pady=5)

    completed_jobs_button = tkinter.Button(root, text="Delete Completed", command=lambda: delete_completed_jobs, font=custom_font)
    completed_jobs_button.pack(pady=5)



    def refresh_frame_listbox():
        #global jobs # Ensure we are modifying the global list
        status_priority = {'editing': 0, 'executing': 1, 'pending': 2, 'failed': 3, 'missing': 4, 'completed': 5, 'archived': 6}
        jobs = load_jobs(jobs_queue_file)

        # First, sort the entire list by status priority
        jobs.sort(key=lambda x: status_priority.get(x['status'], 6))

        # Save the newly sorted list back to the file
        save_jobs(jobs_queue_file, jobs)
        root.destroy()
        edit_queue()
        
    def close_window():
        root.destroy()
        save_jobs(jobs_queue_file, jobs)

    def check_and_run_jobs():
        root.destroy()
        save_jobs(jobs_queue_file, jobs)
        execute_jobs()    
  
    def delete_pending_jobs():
        jobs = load_jobs(jobs_queue_file)
        jobs = [job for job in jobs if job['status'] != 'pending']
        refresh_frame_listbox()


    def delete_completed_jobs():
        jobs = load_jobs(jobs_queue_file)
        jobs = [job for job in jobs if job['status'] != 'completed']
        refresh_frame_listbox()

    
    def delete_failed_jobs():
        jobs = load_jobs(jobs_queue_file)
        jobs = [job for job in jobs if job['status'] != 'failed']
        refresh_frame_listbox()

        
    def delete_missing_media_jobs(): 
        jobs = load_jobs(jobs_queue_file)
        jobs = [job for job in jobs if job['status'] != 'missing']
        refresh_frame_listbox()

    def update_job_listbox():
        global image_references
        bg_color = 'SystemButtonFace'
        count_existing_jobs()
        image_references.clear()
        for widget in frame.winfo_children():
            widget.destroy()
        for index, job in enumerate(jobs):
            source_thumb_exists = os.path.exists(job['sourcecache'])
            target_thumb_exists = os.path.exists(job['targetcache'])
            if job['status'] == 'failed':
                bg_color = 'red'
            if job['status'] == 'pending':
                bg_color = 'SystemButtonFace'
            if not source_thumb_exists or not target_thumb_exists:
               bg_color = 'red'
            if job['status'] == 'executing':
                bg_color = 'black'
            if job['status'] == 'completed':
                bg_color = 'grey'
            if job['status'] == 'editing':
                bg_color = 'green'
            if job['status'] == 'archived':
                bg_color = 'brown'

            # Create job frame with updated background color
            job_frame = tkinter.Frame(frame, borderwidth=2, relief='groove', background=bg_color)
            job_frame.pack(fill='x', expand=True, padx=5, pady=5)
            

            # Move job frame for the move buttons
            move_job_frame = tkinter.Frame(job_frame)
            move_job_frame.pack(side='left', fill='x', padx=5)
            # Move up button
            move_top_button = tkinter.Button(move_job_frame, text="   Top   ", command=lambda idx=index: move_job_to_top(idx))
            move_top_button.pack(side='top', fill='y')
            move_up_button = tkinter.Button(move_job_frame, text="   Up   ", command=lambda idx=index: move_job_up(idx))
            move_up_button.pack(side='top', fill='y')
            # Move down button
            move_down_button = tkinter.Button(move_job_frame, text=" Down ", command=lambda idx=index: move_job_down(idx))
            move_down_button.pack(side='top', fill='y')
            # Move bottom button
            move_bottom_button = tkinter.Button(move_job_frame, text="Bottom", command=lambda idx=index: move_job_to_bottom(idx))
            move_bottom_button.pack(side='top', fill='y')
            
            source_frame = tkinter.Frame(job_frame)
            source_frame.pack(side='left', fill='x', padx=5)
            source_button = create_job_thumbnail(job_frame, job, 'source')
            source_button.pack(side='left', padx=5)

            # Frame to hold the arrow label and archive button
            action_archive_frame = tkinter.Frame(job_frame)
            action_archive_frame.pack(side='left', fill='x', padx=5)
            

            arrow_label = Label(action_archive_frame, text=f"{job['status']}\n\u27A1", font=bold_font)
            arrow_label.pack(side='top', padx=5)
            
            output_path_button = tkinter.Button(action_archive_frame, text="Output Path", command=lambda j=job: output_path_job(j))
            output_path_button.pack(side='top', padx=2)
                        
            delete_button = tkinter.Button(action_archive_frame, text=" Delete ", command=lambda j=job: delete_job(j, 'both'))
            delete_button.pack(side='top', padx=2)
            archive_button = tkinter.Button(action_archive_frame, text="Archive",command=lambda j=job: archive_job(j, 'both'))
            archive_button.pack(side='top', padx=2)

            target_frame = tkinter.Frame(job_frame)
            target_frame.pack(side='left', fill='x', padx=5)
            target_button = create_job_thumbnail(job_frame, job, 'target')
            target_button.pack(side='left', padx=5)

            # frame for the Command Arguments
            argument_frame = tkinter.Frame(job_frame)
            argument_frame.pack(side='left', fill='x', padx=5)

            custom_font = font.Font(family="Helvetica", size=12, weight="bold")
            facefusion_button = tkinter.Button(argument_frame, text=f"UN-Queue It Up\n\n --EDIT ARGUMENTS", font=bold_font, justify='center')
            facefusion_button.pack(side='top', padx=5, fill='x', expand=False)
            facefusion_button.bind("<Button-1>", lambda event, j=job: reload_job_in_facefusion_edit(j))


            custom_font = font.Font(family="Helvetica", size=10, weight="bold")
            argument_button = tkinter.Button(argument_frame, text=f" {job['command']} ", wraplength=325, justify='center')
            argument_button.pack(side='bottom', padx=5, fill='x', expand=False)
            argument_button.bind("<Button-2>", lambda event, j=job: edit_arguments_text(j))
            

    def archive_job(job, source_or_target):

        # Update the job status to 'archived'
        job['status'] = 'archived'
        source_or_target='both'
        check_if_needed_cachefile(job, 'both', jobs_queue_file)
        save_jobs(jobs_queue_file, jobs)  # Save the updated list of active jobs
        # Refresh the job list to show the updated list
        update_job_listbox()
    
      

    def reload_job_in_facefusion_edit(job):
        # Check if sourcecache and targetcache files exist
        sourcecache_path = job.get('sourcecache')
        targetcache_path = job.get('targetcache')
        if not os.path.exists(sourcecache_path):
            messagebox.showerror("Error", f"Cannot edit job. The source file '{os.path.basename(sourcecache_path)}' does not exist.")
            return
        if not os.path.exists(targetcache_path):
            messagebox.showerror("Error", f"Cannot edit job. The target file '{os.path.basename(targetcache_path)}' does not exist.")
            return

        # Check if source and target paths in command section match sourcecache and targetcache values
        command = job.get('command', '')
        source_start_index = command.find('-s "') + len('-s "')
        source_end_index = command.find('"', source_start_index)
        source_path = command[source_start_index:source_end_index]

        target_start_index = command.find('-t "') + len('-t "')
        target_end_index = command.find('"', target_start_index)
        target_path = command[target_start_index:target_end_index]

        errors = []
        if source_path != sourcecache_path:
            errors.append(f"The source file specified in the command does not match the selected source file '{os.path.basename(sourcecache_path)}'.")
        if target_path != targetcache_path:
            errors.append(f"The target file specified in the command does not match the selected target file '{os.path.basename(targetcache_path)}'.")

        if len(errors) == 2:
            messagebox.showerror("Error", f"Cannot edit job. {errors[0]} {errors[1]}")
        elif len(errors) == 1:
            messagebox.showerror("Error", f"Cannot edit job. {errors[0]}")
        else:
            # Confirmation dialog before editing the job
            response = messagebox.askyesno("Confirm Edit", "THIS WILL REMOVE THIS PENDING JOB FROM THE QUEUE, AND LOAD IT INTO FACEFUSION WEBUI FOR EDITING, WHEN DONE EDITING CLICK START TO RUN IT OR ADD JOB TO REQUEUE IT. ARE YOU SURE YOU WANT TO EDIT THIS JOB", icon='warning')
            if not response:
                # If user clicks 'No', save the jobs and update the listbox, then exit the function
                save_jobs(jobs_queue_file, jobs)
                update_job_listbox()
                return
            headless_index = job['command'].find('--headless')
            if headless_index != -1:
                job['command'] = job['command'][:headless_index] + job['command'][headless_index + len('--headless'):]
            job['status'] = 'editing'
            save_jobs(jobs_queue_file, jobs)
            update_job_listbox()
            print (job['status'])

            top = Toplevel()
            top.title("Please Wait")
            message_label = tkinter.Label(top, text="Please wait while the job loads back into FaceFusion...", padx=20, pady=20)
            message_label.pack()
            print (job['status'])
            print (job['command'])
            
            subprocess.Popen(job['command'])
            top.after(1000, close_window)
            top.update_idletasks()
            x = (top.winfo_screenwidth() // 2) - (top.winfo_reqwidth() // 2)
            y = (top.winfo_screenheight() // 2) - (top.winfo_reqheight() // 2)
            top.geometry("+{}+{}".format(x, y))
            top.after(7000, top.destroy)


    

    def output_path_job(job):
        # Open a dialog to select a directory
        selected_path = askdirectory(title="Select A New Output Path for this Job")
        if selected_path:
            formatted_path = selected_path.replace('/', '\\')  # Replace single forward slashes with backslashes
        #        if not formatted_path.endswith('\\'):
        #    formatted_path += '\\'  # Add a trailing backslash only if it's not already there

        # Find and replace the output path in the command
        parts = job['command'].split(' -o ')  # Split the command at '-o'
        before_o = parts[0]
        after_o = parts[1].split(' ', 1)  # Split to isolate the old output path and the rest of the command
        rest_of_command = after_o[1] if len(after_o) > 1 else ''  # Handle case where '-o' is the last argument

        # Rebuild the command with the new output path
        job['command'] = f'{before_o} -o "{formatted_path}" {rest_of_command}'
        save_jobs(jobs_queue_file, jobs)  # Save the updated jobs to the JSON file
        update_job_listbox()  # Refresh the job list to show the new thumbnail or placeholder





    def delete_job(job, source_or_target):
        job['status'] = ('deleting')
        source_or_target='both'
        check_if_needed_cachefile(job, 'both', jobs_queue_file)
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

    def create_job_thumbnail(parent, job, source_or_target, size=(200, 200)):
        file_path = job[source_or_target + 'cache']
        if not os.path.exists(file_path):
            if not job['status'] == 'failed':
                if job['status'] == 'pending':
                    job['status'] = 'missing'
            # Create a button as a placeholder for non-existing files that allows updating the file
            button = Button(parent, text=f"{source_or_target} file missing\n{os.path.basename(file_path)}\n Click to update", wraplength=100,  bg='white', fg='black',
                            command=lambda ft=source_or_target: select_job_file(parent, job, ft))
            button.pack(pady=2, fill='y', expand=True)
            save_jobs(jobs_queue_file, jobs)
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
            button = Button(parent, image=photo_image, command=lambda ft=source_or_target: select_job_file(parent, job, ft))
            button.image = photo_image  # keep a reference!
            button.pack(side='left', padx=5)
            return button
        except Exception as e:
            print(f"{RED}Error creating thumbnail for {file_path}:{ENDC} {e}")
            return None

    def select_job_file(parent, job, source_or_target):
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
            update_job_command(job, source_or_target, path)

            job['status'] = 'pending' # fix should be changed to pending if both cache files exist otherwise staus ‘missing’
            save_jobs(jobs_queue_file, jobs)  
            update_job_listbox()  

    def update_job_command(job, source_or_target, path):
        cache_name = copy_to_media_cache(path)

        cache_path = os.path.join(media_cache_dir, cache_name)
        cache_path_escaped = cache_path.replace("\\", "\\\\")

        pattern = {
            'source': r'(-s\s+)".+?"',
            'target': r'(-t\s+)".+?"'
        }

        # Update job command
        if source_or_target in pattern:
            old_path_pattern = pattern[source_or_target]
            new_command = re.sub(old_path_pattern, rf'\1"{cache_path_escaped}"', job['command'])
            job['command'] = new_command
            # Update cache information in job
            cache_key = f'{source_or_target}cache'
            job[cache_key] = cache_path

        save_jobs(jobs_queue_file, jobs)
        update_job_listbox()       
            

    root.after(1000, update_job_listbox())  # Optionally refresh listbox every 1000 milliseconds if needed
    root.mainloop()
    if __name__ == '__main__':
        edit_queue()

def run(ui : gradio.Blocks) -> None:
	concurrency_count = min(8, multiprocessing.cpu_count())
	ui.queue(concurrency_count = concurrency_count).launch(show_api = False, inbrowser = True, quiet = False)
