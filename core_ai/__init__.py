import logging

console_handler = logging.StreamHandler()
file_handler = logging.FileHandler('app.log')

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[console_handler, file_handler])