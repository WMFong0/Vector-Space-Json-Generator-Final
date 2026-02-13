import os

def filter_name(original_name):
    Past_Error = ""
    final_string = ""
    
    if original_name != "":
        for user_input_char in original_name:
            # Acceptable Character
            if ('a' <= user_input_char <= 'z' or 
                'A' <= user_input_char <= 'Z' or 
                '0' <= user_input_char <= '9' or 
                user_input_char == '-' or 
                user_input_char == '_'):
                final_string += user_input_char
                
            else:
                if user_input_char == '\n':
                    # Skip newline characters
                    continue
                
                # Only output error that has not been introduced
                if user_input_char in Past_Error:
                    final_string += '_'
                    continue
                
                Past_Error += user_input_char
                # Output Not accepted Character
                if user_input_char == " ":
                    print("Error! Space is not allowed")
                else: 
                    print(f"Error! {user_input_char} is not allowed")
                
                # Skip ) character (don't add anything to final_string)
                if user_input_char == ")":
                    continue
                    
                # Replace other special char with _
                final_string += '_'
        
        return final_string
    return None

def full_list_name_filter(input_path = "input2.txt", output_path = 'output.txt'): #Name of your input file

    filtered_name_list = []
    
    try:
        with open(input_path, 'r') as file:  # Read permission
            for line in file:
                if line.strip() == "" or line == '\n':
                    continue
                
                # Remove trailing newline before processing
                line = line.rstrip('\n')
                base_name, extension = os.path.splitext(line)
                
                filtered_name = filter_name(base_name)
                if filtered_name is not None:
                    filtered_name_with_extension = filtered_name + extension
                    filtered_name_list.append(filtered_name_with_extension)
    except FileNotFoundError:
        print(f"Error: The file '{input_path}' was not found.")
        return
    except Exception as e:
        print(f"An error occurred while reading: {e}")
        return
    
    
            
    try:
        with open(output_path, 'w') as file:  # Write permission
            for name in filtered_name_list:
                file.write(f"{name}\n")
        print(f"Output written to {output_path}")
        
    except Exception as e:
        print(f"An error occurred while writing: {e}")
    
    return filtered_name_list
    
Acceptable_character = "abcd"  # Not used

def main():
    try:
        print("input 1 for by name input\ninput 2 for by file input.")
        user_input = int(input("Your selection: "))
    except ValueError:
        print("Invalid input. Please input 1 or 2.")
        return
    
    if user_input == 1:
        while True:
            user_input = input("Please input your file name: ")
            if user_input != "":
                filtered_name = filter_name(user_input)
                print(f"Fixed name: {filtered_name}")
            else:
                break
            
    elif user_input == 2:
        
        filtered_name_list = full_list_name_filter()
        
        
        