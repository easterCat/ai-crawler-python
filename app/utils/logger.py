import glob
import logging
import os
import time
from datetime import datetime

import colorlog


class MyLogger:

    def __init__(self, log_dir):
        self.logger = logging.getLogger()
        # DEBUG（最低级别）：用于调试和详细信息记录。
        # INFO：用于提供一般性的信息记录。
        # WARNING：用于表示可能的问题或警告。
        # ERROR：用于表示错误情况，但不影响程序继续运行。
        # CRITICAL（最高级别）：用于表示严重的错误，可能导致程序无法继续运行。
        self.logger.setLevel(logging.DEBUG)

        console_handler = logging.StreamHandler()
        formatter = colorlog.ColoredFormatter(
            '%(log_color)s%(asctime)s %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'blue',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'bold_red',
            }
        )
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        current_date = datetime.now().strftime('%Y-%m-%d')
        log_file = os.path.join(log_dir, f'log_{current_date}.log')
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
        self.logger.addHandler(file_handler)

    def set_level(self, level=''):
        if isinstance(level, str):
            level = logging.getLevelName(level)
        self.logger.setLevel(level)

    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def critical(self, message):
        self.logger.critical(message)

    @staticmethod
    def clean_logs(log_dir, days_to_keep):
        current_time = time.time()
        file_pattern = os.path.join(log_dir, 'log_*.log')
        log_files = glob.glob(file_pattern)

        for log_file in log_files:
            file_name = os.path.basename(log_file)
            file_date = file_name[4:14]
            file_time = datetime.strptime(file_date, '%Y-%m-%d')
            if current_time - file_time.timestamp() >= days_to_keep * 24 * 60 * 60:
                os.remove(log_file)
