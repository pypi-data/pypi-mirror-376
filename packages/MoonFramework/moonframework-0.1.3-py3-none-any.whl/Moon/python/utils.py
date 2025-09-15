import os
import inspect
from typing import final, List
from Moon import DLL_FOUND_PATH, DLL_LOCAL_FOUND_PATH, DLL_MODULE_FOUND_PATH
from colorama import Fore

class LibraryLoadError(Exception):
    """Ошибка загрузки нативной библиотеки"""
    pass


def find_library() -> str:
    """
    #### Поиск пути к нативной библиотеке BUILD.dll
    
    ---
    
    :Returns:
        str: Абсолютный путь к библиотеке
        
    ---
    
    :Raises:
        LibraryLoadError: Если библиотека не найдена
    """
    # Получаем информацию о вызывающем файле
    caller_frame = inspect.stack()[1]
    caller_filename = os.path.basename(caller_frame.filename)
    
    # Список возможных путей к библиотеке, в порядке приоритета
    possible_paths: List[str] = [
        DLL_FOUND_PATH,
        DLL_LOCAL_FOUND_PATH,
        DLL_MODULE_FOUND_PATH,
    ]

    # Поиск по указанным путям
    for lib_path in possible_paths:
        if os.path.exists(lib_path):
            print(f"{Fore.GREEN}{caller_filename:<20}{Fore.RESET} -> Library found at: {lib_path}")
            return lib_path

    # Если не найдено по указанным путям, ищем рекурсивно
    print(f"{Fore.YELLOW}{caller_filename:<20}{Fore.RESET} -> Library not found in standard paths, starting recursive search...")
    
    # Начинаем поиск от текущей рабочей директории
    start_dir = os.getcwd()
    found_path = recursive_find_library(start_dir, caller_filename)
    
    if found_path:
        return found_path

    # Если ни один из путей не сработал
    raise LibraryLoadError(
        f"Moon library (Moon.dll) not found in any of the expected locations: {possible_paths}\n"
        f"Also not found during recursive search from: {start_dir}"
    )


def recursive_find_library(start_dir: str, caller_filename: str, max_depth: int = 5) -> str:
    """
    Рекурсивный поиск библиотеки Moon.dll в поддиректориях
    
    :param start_dir: Директория для начала поиска
    :param caller_filename: Имя файла вызывающего кода (для вывода)
    :param max_depth: Максимальная глубина рекурсии
    :return: Путь к найденной библиотеке
    """
    from colorama import Fore
    
    # Ищем файлы с подходящими именами
    target_names = ['Moon.dll', 'libMoon.so', 'libMoon.dylib']  # Добавьте другие возможные имена
    
    for depth in range(max_depth + 1):
        for root, dirs, files in os.walk(start_dir):
            # Проверяем глубину текущей директории
            current_depth = root[len(start_dir):].count(os.sep)
            if current_depth > depth:
                continue
            
            for file in files:
                if file in target_names:
                    found_path = os.path.join(root, file)
                    print(f"{Fore.GREEN}{caller_filename:<20}{Fore.RESET} -> Library found recursively at: {found_path}")
                    return found_path
        
        # Если на этой глубине не найдено, продолжаем поиск на следующей глубине
    
    return None


# Альтернативная более простая версия рекурсивного поиска (раскомментируйте если нужно)
"""
def recursive_find_library(start_dir: str, caller_filename: str) -> str:
    \"\"\"
    Рекурсивный поиск библиотеки Moon.dll в поддиректориях
    
    :param start_dir: Директория для начала поиска
    :param caller_filename: Имя файла вызывающего кода (для вывода)
    :return: Путь к найденной библиотеке
    \"\"\"
    from colorama import Fore
    
    target_names = ['Moon.dll', 'libMoon.so', 'libMoon.dylib']
    
    for root, dirs, files in os.walk(start_dir):
        for file in files:
            if file in target_names:
                found_path = os.path.join(root, file)
                print(f"{Fore.GREEN}{caller_filename:<20}{Fore.RESET} -> Library found recursively at: {found_path}")
                return found_path
    
    return None
"""