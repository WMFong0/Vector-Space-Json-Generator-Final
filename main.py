import logging  
from filename_checker import main as filename_checker_main  
from vector_config import main as vector_config_main  
  
def setup_logging(log_path='project.log'):  
    """  
    Sets up logging configuration.  
    Logs INFO and above to console, DEBUG and above to file.  
    """  
    logging.basicConfig(  
        level=logging.DEBUG,  
        format='%(asctime)s [%(levelname)s] %(message)s',  
        handlers=[  
            logging.FileHandler(log_path, mode='a', encoding='utf-8'),  
            logging.StreamHandler()  
        ]  
    )  
    logging.info("Logging initialized.")  
  
def main():  
    setup_logging()  
    logging.info("Project started.")  
  
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
            logging.warning("Invalid input: not an integer.")  
            print("Invalid input. Please enter a number.")  
            continue  
  
        if choice == 1:  
            logging.info("Running filename filtering module.")  
            filename_checker_main()  
        elif choice == 2:  
            logging.info("Running vector space config generation module.")  
            vector_config_main()  
        elif choice == 0:  
            logging.info("Exiting project.")  
            print("Goodbye!")  
            break  
       