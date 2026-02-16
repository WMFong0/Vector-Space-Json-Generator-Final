import re  
from pathlib import Path  
  
def filter_name(original_name: str) -> str | None:  
    """  
    Filters the given file name to only allow alphanumeric characters, hyphens, and underscores.  
    Replaces any illegal character with an underscore.  
    Args:  
        original_name (str): The original file name (without extension).  
    Returns:  
        str: The filtered file name, or None if the input is empty.  
    """  
    if not original_name:  
        return None  
  
    # Replace any character not allowed with '_'  
    filtered = re.sub(r'[^a-zA-Z0-9\-_]', '_', original_name)  
    # Report illegal characters  
    illegal_chars = set(re.findall(r'[^a-zA-Z0-9\-_]', original_name))  
    for char in illegal_chars:  
        if char == ' ':  
            print("Error! Space is not allowed")  
        else:  
            print(f"Error! '{char}' is not allowed")  
    return filtered  
  
def full_list_name_filter(  
        input_path: str = "input2.txt",  
        output_path: str = "output.txt"  
    ) -> list[str]:  
    """  
    Filters all file names in the input file and writes the filtered names to the output file.  
    Returns the filtered name list.  
    Args:  
        input_path (str): Path to the input file.  
        output_path (str): Path to the output file.  
    Returns:  
        list[str]: List of filtered file names (with extensions).  
    """  
    filtered_name_list = []  
    input_file = Path(input_path)  
    output_file = Path(output_path)  
  
    if not input_file.exists():  
        print(f"Error: The file '{input_path}' was not found.")  
        return []  
  
    try:  
        with input_file.open('r', encoding='utf-8') as infile:  
            for line in infile:  
                line = line.strip()  
                if not line:  
                    continue  
                base_name, extension = Path(line).stem, Path(line).suffix  
                filtered_name = filter_name(base_name)  
                if filtered_name:  
                    filtered_name_with_ext = filtered_name + extension  
                    filtered_name_list.append(filtered_name_with_ext)  
    except Exception as e:  
        print(f"An error occurred while reading: {e}")  
        return []  
  
    try:  
        with output_file.open('w', encoding='utf-8') as outfile:  
            for name in filtered_name_list:  
                outfile.write(f"{name}\n")  
        print(f"Output written to {output_path}")  
    except Exception as e:  
        print(f"An error occurred while writing: {e}")  
  
    return filtered_name_list  
  
def main():  
    """  
    Main prompt for user interaction.  
    Allows user to filter names manually or via file input.  
    """  
    print("input 1 for manual name input\ninput 2 for file input.")  
    while True:  
        try:  
            choice = int(input("Your selection: "))  
            if choice in (1, 2):  
                break  
            print("Invalid input. Please input 1 or 2.")  
        except ValueError:  
            print("Invalid input. Please input 1 or 2.")  
  
    if choice == 1:  
        while True:  
            user_input = input("Please input your file name (or empty to quit): ")  
            if not user_input:  
                break  
            filtered_name = filter_name(user_input)  
            print(f"Fixed name: {filtered_name}")  
    elif choice == 2:  
        filtered_name_list = full_list_name_filter()  
        print("Filtered names:", filtered_name_list)  
  
if __name__ == "__main__":  
    main()  