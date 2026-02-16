import json  
from pathlib import Path  
from filename_checker import full_list_name_filter  
import os  
  
# Configuration variables  
INPUT_PATH = "input.txt"  
INPUT_PATH2 = "input2.txt"  
OUTPUT_PATH = "output.txt"  
OUTPUT_PATH2 = "output2.txt"  
  
DEFAULT_CHUNK_SIZE = 1200  
DEFAULT_CHUNK_OVERLAP = 100  
DEFAULT_SPLITTER = "RecursiveCharacterTextSplitter"  
DEFAULT_LOADER = "FileLoader"  
IMAGE_BASED_LOADER = "DoclingFileLoader"  
IMAGE_BASED_CHUNK_SIZE = 500  
LARGE_DOCUMENT_CHUNK_SIZE = 2000  
  
def retrieve_special_document(name_list: list[str]) -> list[str]:  
    """  
    Allows user to select special documents by index from a list.  
    Args:  
        name_list (list[str]): List of file names.  
    Returns:  
        list[str]: List of selected file names.  
    """  
    special_document_list = []  
    print("Available documents:")  
    for i, name in enumerate(name_list):  
        print(f"{i}: {name}")  
    while True:  
        try:  
            idx = int(input("Input the related index, or enter -1 to finish: "))  
            if idx == -1:  
                break  
            if 0 <= idx < len(name_list):  
                special_document_list.append(name_list[idx])  
            else:  
                print("Index out of range.")  
        except ValueError:  
            print("Please input integers only.")  
    return special_document_list  
  
def file_name_to_loader_json(name_list: list[str]) -> list[dict]:  
    """  
    Creates loader JSON entries based on filtered name list and user input.  
    Args:  
        name_list (list[str]): List of filtered file names.  
    Returns:  
        list[dict]: List of loader config dictionaries.  
    """  
    folder_name = input("Please input your folder name: ")  
    special_doc_img = []  
    special_doc_large = []  
  
    try:  
        image_bool = int(input("Any image based document? If yes, enter 1. Else enter 2.\n"))  
        if image_bool == 1:  
            special_doc_img = retrieve_special_document(name_list)  
    except ValueError:  
        print("Invalid input. Skipping image based selection.")  
  
    try:  
        large_doc_bool = int(input("Any large document? If yes, enter 1. Else enter 2.\n"))  
        if large_doc_bool == 1:  
            special_doc_large = retrieve_special_document(name_list)  
    except ValueError:  
        print("Invalid input. Skipping large document selection.")  
  
    loader_list = []  
    for name in name_list:  
        json_curr = {}  
        curr_chunk_size = DEFAULT_CHUNK_SIZE  
        curr_chunk_overlap = DEFAULT_CHUNK_OVERLAP  
        curr_splitter = DEFAULT_SPLITTER  
        curr_loader = DEFAULT_LOADER  
  
        # Adjust settings based on special doc selection  
        if name in special_doc_img and name not in special_doc_large:  
            curr_loader = IMAGE_BASED_LOADER  
            curr_chunk_size = IMAGE_BASED_CHUNK_SIZE  
        elif name not in special_doc_img and name in special_doc_large:  
            curr_chunk_size = LARGE_DOCUMENT_CHUNK_SIZE  
        elif name in special_doc_img and name in special_doc_large:  
            curr_loader = IMAGE_BASED_LOADER  
  
        base_name = Path(name).stem  
        json_curr['loader'] = curr_loader  
        json_curr['args'] = {'path': f"{folder_name}/{name}", 'start_page_num': 1}  
        json_curr['splitter'] = curr_splitter  
        json_curr['splitter_args'] = {'chunk_size': curr_chunk_size, 'chunk_overlap': curr_chunk_overlap}  
        json_curr['metadata'] = {'title': base_name}  
        loader_list.append(json_curr)  
    return loader_list  
  
def main():  
    """  
    Main function to read settings, filter file names, and generate config JSON.  
    """  
    data_final = {}  
  
    # Read vector space settings  
    input_file = Path(INPUT_PATH)  
    if not input_file.exists():  
        print(f"Error: The file '{INPUT_PATH}' was not found.")  
        return  
  
    try:  
        with input_file.open('r', encoding='utf-8') as file:  
            loaded_data = json.load(file)  
            print("Loaded settings:", loaded_data)  
            data_final['settings'] = loaded_data.get('settings', {})  
            data_final['common_args'] = {}  
    except json.JSONDecodeError as e:  
        print(f"Failed to decode JSON: {e}")  
        return  
    except Exception as e:  
        print(f"An error occurred while reading '{INPUT_PATH}': {e}")  
        return  
  
    # Retrieve filtered name list  
    filtered_name_list = full_list_name_filter(INPUT_PATH2, OUTPUT_PATH2)  
    if not filtered_name_list:  
        print("No filtered names found.")  
        return  
  
    # Build loader JSON  
    loaders = file_name_to_loader_json(filtered_name_list)  
    data_final['loaders'] = loaders  
  
    # Write output config JSON  
    output_file = Path(OUTPUT_PATH)  
    try:  
        with output_file.open('w', encoding='utf-8') as file:  
            json.dump(data_final, file, indent=4)  
        print(f"Config written to {OUTPUT_PATH}")  
    except Exception as e:  
        print(f"An error occurred while writing: {e}")  
  
    # Optional: Print the config for verification  
    try:  
        with output_file.open('r', encoding='utf-8') as file:  
            print("\nConfig preview:")  
            data = json.load(file)  
            print(json.dumps(data, indent=4))  
    except Exception as e:  
        print(f"An error occurred while reading: {e}")  
  
if __name__ == "__main__":  
    main()  