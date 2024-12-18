import logging


def setup_log(log_file='project.log'):
    # Создаем и настраиваем логгер
    logger = logging.getLogger('PriceMachineLogger')
    logger.setLevel(logging.DEBUG)

    # Создаем обработчик для записи лога в файл
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)

    # Форматтер для вывода логов
    format_ = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(format_)

    # Добавляем обработчик в логгер
    logger.addHandler(file_handler)

    return logger
