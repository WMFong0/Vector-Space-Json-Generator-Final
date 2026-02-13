import json
import filename_checker
import os

input_path = "input.txt" # Original Vector Store Setting (To keep settings)
input_path2 = "input2.txt" # File names to be inserted into Vector Store
output_path = "output.txt" # Vector Space JSON
output_path2 = "output2.txt" # Formatted Names Output

data_final = {}

default_chunk_size = 1200
default_chunk_overlap = 100
default_splitter = "RecursiveCharacterTextSplitter"
default_loader = "FileLoader"

image_based_loader = "DoclingFileLoader"
image_based_chunk_size = 500

large_document_chunk_size = 2000

def retrieve_special_document():
    special_document_list = []
    special_document_index = -1
    for i, name in enumerate(name_list):
        print(i + ". " + name)
    while special_document_index != -1:
        try:
            print("Input the related index, or enter -1 to finish. \n" + f"Current image based document list: {special_document_list}\n" + "Index:")
            special_document_index = int(input(""))
            if special_document_index == -1:
                break
            else:
                curr_special_document = name_list[special_document_index]
                special_document_list.append(curr_special_document)
        except IndexError:
            print("Please input numbers inside the range")
        except ValueError:
            print("Please input integers Only")
    return special_document_list

def file_name_to_loader_json(name_list):
    folder_name = input("Please input your folder name: ")
    special_doc_img = []
    special_doc_large = []
    
    image_bool: int = int(input("Any image based document? If yes, enter 1. Else enter 2."))
    if image_bool == 1:
        # Let user select the image
        special_doc_img = retrieve_special_document()
        
    large_doc_bool: int = int(input("Any large document? If yes, enter 1. Else enter 2."))
    if large_doc_bool == 1:
        # Let user select the image
        special_doc_large = retrieve_special_document()
    
        
    loader_list = []
    for name in name_list:
        json_curr = {}
        curr_chunk_size = default_chunk_size
        curr_chunk_overlap = default_chunk_overlap
        curr_splitter = default_splitter
        curr_loader = default_loader
        if name in special_doc_img and name not in special_doc_large:
            curr_loader = image_based_loader
            curr_chunk_size = image_based_chunk_size
        elif name not in special_doc_img and name in special_doc_large:
            curr_chunk_size = large_document_chunk_size
        elif name in special_doc_img and name in special_doc_large:
            curr_loader = image_based_loader
        
        
        base_name = os.path.splitext(name)[0]
        json_curr['loader'] = curr_loader
        json_curr['args'] = {'path': f"{folder_name}/{name}", 'start_page_num': 1}
        json_curr['splitter'] = curr_splitter
        json_curr['splitter_args'] = {'chunk_size': curr_chunk_size, 'chunk_overlap': curr_chunk_overlap}
        json_curr['metadata'] = {'title' : base_name}
        loader_list.append(json_curr)
    return loader_list
    
def main():
    try:
        with open(input_path, 'r') as file:
            loaded_data = json.load(file)
            print(loaded_data)
            print(type(loaded_data))
            data_final['settings'] = loaded_data['settings']
            data_final['common_args'] = {}
            print("\n" , data_final['settings'])
    except FileNotFoundError:
        print(f"Error: The file '{input_path}' was not found.")
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON: {e}")

    # Retrieve Full Filtered name list
    filtered_name_list = filename_checker.full_list_name_filter(input_path = "input2.txt", output_path= "output2.txt")
    
    # Trim the json file
    loaders = file_name_to_loader_json(filtered_name_list)
    data_final['loaders'] = loaders
    
    
    print(data_final)
    
    # Write the output file with the 
    try:
        with open(output_path, 'w') as file:
            json.dump(data_final, file, indent=4)
    except Exception as e:
        print(f"An error occurred while writing: {e}")
    
    try:
        with open(output_path, 'r') as file:
            print("\n")
            data = json.load(file)
            print(data)
    except Exception as e:
        print(f"An error occurred while reading: {e}")
    return

if __name__ == "__main__":
    name_list: list = ["I_am_gay.pdf", "I_am_gay2.pdf"]
    file_name_to_loader_json(name_list)