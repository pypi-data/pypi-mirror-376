import shutil
import pickle
import json
import os

def read_json(filename):
    """
    Read data from a JSON file and return it as a Python object.

    Args:
        filename (str): The name of the JSON file to read from.

    Returns:
        Any: The data read from the JSON file, as a Python object.
    """
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"File '{filename}' not found.")
        return None
    except json.JSONDecodeError:
        print(f"Invalid JSON format in file '{filename}'.")
        return None

def write_json(data, filename):
    """
    Write data to a JSON file.

    Args:
        data (Any): The data to write to the JSON file.
        filename (str): The name of the JSON file to write to.

    Returns:
        None
    """
    try:
        with open(filename, 'w') as f:
            json.dump(data, f)
    except IOError:
        print(f"Error writing to file '{filename}'.")


## Removed split_video_to_mp4: required OpenCV (cv2)

def get_output_dir(directory):
    """
    Takes the output directory created by split_video_to_mp4 and returns the sorted list of files.

    Parameters:
        directory (string): The path to the directory containing the split clips.

    Returns:
        list: the sorted files in the directory.
    """
    files = os.listdir(directory)
    files.sort(key=lambda x: int(x.split(".")[0]))
    return list(map(lambda x: os.path.join(directory, x), files))

## Removed Pillow/OpenCV helpers and add_noise: required PIL and cv2

def pickle_read(file):
    """
    Reads the content from a pickle file.
    """
    with open(file, 'rb') as f:
        data = pickle.load(f)
    return data

def pickle_write(data, file_name):
    """
    Writes data (first argument) to a pickle file (second argument).
    """
    with open(file_name, 'wb') as file:
        pickle.dump(data, file)

pkl_read  = pickle_read
pkl_write = pickle_write

def json_read(file):
    """
    Reads the content from a JSON file.
    """
    with open(file, 'r') as f:
        data = json.load(f)
    return data

def json_write(data, file_name):
    """
    Writes data (first argument) to a JSON file (second argument).
    """
    with open(file_name, 'w') as file:
        json.dump(data, file, indent=4)

def jsonl_read(file):
    """
    Reads the content from a JSONL file.
    """
    data = []
    with open(file, 'r') as f:
        for line in f:
            data.append(json.loads(line))
    return data

def jsonl_write(data, file_name):
    """
    Writes data (first argument, a list of dictionaries/objects) to a JSONL file (second argument).
    """
    with open(file_name, 'w') as file:
        for item in data:
            json.dump(item, file)
            file.write('\n')
