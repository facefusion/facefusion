#!/bin/bash

# Function to get the target directory or file from the command line arguments
get_target() {
  for arg in "$@"; do
    if [[ $arg == --target_dir=* ]] || [[ $arg == -td=* ]] || [[ $arg == --target=* ]] || [[ $arg == -t=* ]]; then
      echo "${arg#*=}"
      return
    fi
  done
}

# Function to get the source directory or file from the command line arguments
get_source() {
  for arg in "$@"; do
    if [[ $arg == --source_dir=* ]] || [[ $arg == -sd=* ]] || [[ $arg == --source=* ]] || [[ $arg == -s=* ]]; then
      source="${arg#*=}"
      # If the source is a directory, get all files in the directory
      if [ -d "$source" ]; then
        echo $(get_sources_from_source_dir "$source")
      fi
      return
    fi
  done
}

# Function to get all files from a source directory
get_sources_from_source_dir() {
  files=$(find "$1" -type f)
  new_source=""
  for file in $files; do
    new_source+="--source=$file "
  done
  echo "$new_source"
}

# Get the source and target from the command line arguments
source=$(get_source "$@")
target=$(get_target "$@")

# Replace the source value in the command line arguments for each source file in the directory
for ((i = 0; i < $#; i++)); do
  if [[ ${!i} == --source_dir=* ]] || [[ ${!i} == -sd=* ]]; then
    set -- "${@:1:i-1}" "$source" "${@:i+1}"
    break
  fi
done

# If the target is a directory, process each files in the directory
if [ -d "$target" ]; then
  nb_files=$(find "$target" -mindepth 1 -type f -print | wc -l)
  k=0

  # For each target files, run script with the new arguments
  for file in $(find "$target" -mindepth 1 -type f -print); do

  	# Replace the "target_dir" argument value in the command line arguments by "target" and current file
    for ((i = 0; i < $#; i++)); do
      if [[ ${!i} == --target_dir=* ]] || [[ ${!i} == -td=* ]] || [[ ${!i} == --target=* ]] || [[ ${!i} == -t=* ]]; then
        set -- "${@:1:i-1}" "--target=$file" "${@:i+1}"
        break
      fi
    done
    k=$((k+1))

    echo ""
    echo "Process for target $file ($k / $nb_files)"
    echo ""
    echo "New args: "
    echo "$@"

    # Execute
    python run.py $@
  done
else
  # If the target is a single file, run the script with the new arguments
  echo ""
  echo "Process for target $target (1 / 1)"
  echo ""
  echo "New args: "
  echo "$@"

  # Execute
  python run.py $@
fi
