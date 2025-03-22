import os
import re

def replace_in_file(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
        try:
            content = file.read()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return False
    
    # Replace 'weyfusion' with 'weyfusion' (preserving case)
    modified_content = re.sub(r'weyfusion', 'weyfusion', content, flags=re.IGNORECASE)
    modified_content = re.sub(r'weyfusion', 'WeyFusion', modified_content)
    modified_content = re.sub(r'weyfusion', 'WEYFUSION', modified_content)
    
    if content != modified_content:
        with open(file_path, 'w', encoding='utf-8') as file:
            try:
                file.write(modified_content)
                print(f"Updated: {file_path}")
                return True
            except Exception as e:
                print(f"Error writing to {file_path}: {e}")
                return False
    return False

def process_directory(directory):
    file_extensions = ['.py', '.md', '.ini', '.yml', '.txt', '.flake8', '.ini']
    changes_count = 0
    
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            _, extension = os.path.splitext(file_path)
            
            if extension.lower() in file_extensions or file in ['.flake8', '.editorconfig']:
                if replace_in_file(file_path):
                    changes_count += 1
    
    return changes_count

if __name__ == '__main__':
    base_directory = '.'
    changes = process_directory(base_directory)
    print(f"Replaced 'weyfusion' with 'weyfusion' in {changes} files.") 