from logging_config import setup_logger  
from filename_checker import main as filename_checker_main  
from vector_config import main as vector_config_main  
  
logger = setup_logger('main', log_file='project_main.log', level='DEBUG')  
  
def main():  
    logger.info("Project started.")  
    menu = """  
    === Project Menu ===  
    1. Filename Filtering  
    2. Vector Space JSON Config Generation  
    0. Exit  
    """  
    while True:  
        print(menu)  
        try:  
            choice = int(input("Select an option: "))  
        except ValueError:  
            logger.warning("Invalid input: not an integer.")  
            print("Invalid input. Please enter a number.")  
            continue  
  
        if choice == 1:  
            logger.info("Running filename filtering module.")  
            filename_checker_main()  
        elif choice == 2:  
            logger.info("Running vector space config generation module.")  
            vector_config_main()  
        elif choice == 0:  
            logger.info("Exiting project.")  
            print("Goodbye!")  
            break  
        else:  
            logger.warning(f"Invalid menu choice: {choice}")  
            print("Invalid choice. Please select 1, 2, or 0.")  
  
if __name__ == "__main__":  
    main()  