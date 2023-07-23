

import os
import pathlib
import shutil
import hashlib
import itertools
import functools
import logging
import time
from concurrent.futures import ThreadPoolExecutor

def setup_logger():
    logger = logging.getLogger("organize_files_logger")
    logger.setLevel(logging.DEBUG)

    # Create a file handler to log errors to a file
    file_handler = logging.FileHandler("organize_files_errors.log")
    file_handler.setLevel(logging.ERROR)

    # Create a stream handler to display progress messages on the console
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)

    # Create a formatter for the log messages
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger

def default_sorting_order(filename):
    # Provide a default sorting order based on the filename
    # You can customize this function to meet your specific requirements
    return filename

def calculate_file_hash(file_path):
    # Calculate a unique hash for the file content using hashlib
    block_size = 65536
    file_hash = hashlib.md5()
    with open(file_path, 'rb') as f:
        for block in iter(lambda: f.read(block_size), b''):
            file_hash.update(block)
    return file_hash.hexdigest()

def move_file(file, target_file_path):
    try:
        shutil.move(file, target_file_path)
    except Exception as e:
        logger = logging.getLogger("organize_files_logger")
        logger.error(f"Error moving {file.name}: {e}")
        print("Skipping file...")

def organize_files_by_format(folder_path, num_threads=None, sorting_order=None, skip_existing=True):
    logger = logging.getLogger("organize_files_logger")

    all_files = list(pathlib.Path(folder_path).iterdir())
    total_files = len(all_files)
    processed_files = 0

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        for file in all_files:
            if file.is_file():
                file_extension = file.suffix.lower()
                if not file_extension:
                    # Skip files without an extension
                    continue

                #format_folder = pathlib.Path(folder_path, file_extension)
                format_folder = pathlib.Path(folder_path, file_extension[1:]) # Slice the extension to remove the leading "."

                if not format_folder.exists():
                    format_folder.mkdir(parents=True)

                # Update the target_file_path to use the original filename instead of the hash
                target_file_path = format_folder / file.name

                # Use multithreading to move files concurrently
                executor.submit(move_file, file, target_file_path)

                processed_files += 1
                progress = (processed_files / total_files) * 100
                print(f"Progress: {progress:.2f}%   ", end='\r')

    print("\nFile moving complete!")

    # Optionally, sort files using Timsort (Python's default sorting algorithm)
    for format_folder in pathlib.Path(folder_path).glob('*'):
        if format_folder.is_dir():
            format_files = list(format_folder.iterdir())  # Convert to list before sorting

            if sorting_order is None:
                sorting_order_func = default_sorting_order
            else:
                sorting_order_func = lambda file: sorting_order(file.name)

            format_files = sorted(format_files, key=sorting_order_func)

            for file in format_files:
                new_filename = file.stem + file.suffix  # Keep the original filename without the index
                file.rename(format_folder / new_filename)

if __name__ == "__main__":
    folder_path = r"path_to_folder"
    num_threads = 4  # You can adjust the number of threads as per your machine's capabilities
    sorting_order = None  # You can specify a sorting function here if needed
    skip_existing = True  # Set this to False if you don't want to skip existing files

    # Set up the logging
    logger = setup_logger()

    try:
        start_time = time.time()
        organize_files_by_format(folder_path, num_threads=num_threads, sorting_order=sorting_order, skip_existing=skip_existing)
        end_time = time.time()
        print(f"Files organized successfully in {end_time - start_time:.2f} seconds.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")

