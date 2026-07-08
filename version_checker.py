# version_checker.py
import os
import json
import requests
import subprocess
import threading
from datetime import datetime
from typing import Optional, Dict, Tuple

# GitHub configuration
GITHUB_OWNER = "DeyanShahov"
GITHUB_REPO = "image-downloader"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/commits/main"

# Files
VERSION_FILE = "version.txt"
LOCAL_VERSION_FILE = "local_version.json"

# Constants
REQUEST_TIMEOUT = 10  # seconds


class version_info:
    """Структура за съхраняване на информация за версията."""
    def __init__(self, version: str, last_commit_date: str, update_check_time: str):
        self.version = version
        self.last_commit_date = last_commit_date
        self.update_check_time = update_check_time
    
    def to_dict(self):
        """Конвертира в dictionary за JSON serialize."""
        return {
            'version': self.version,
            'last_commit_date': self.last_commit_date,
            'update_check_time': self.update_check_time
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Създава VersionInfo от dictionary."""
        return cls(
            version=data.get('version', '0.0.0'),
            last_commit_date=data.get('last_commit_date', ''),
            update_check_time=data.get('update_check_time', '')
        )


def get_local_version() -> version_info:
    """
    Чете локалната версия от файловете.
    
    Priority:
    1. local_version.json (ако съществува)
    2. version.txt (ако съществува)
    3. Default: 0.0.0
    """
    # Опция 1: Чет от local_version.json
    if os.path.exists(LOCAL_VERSION_FILE):
        try:
            with open(LOCAL_VERSION_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return version_info.from_dict(data)
        except Exception as e:
            print(f"[WARNING] Неуспешно четене на {LOCAL_VERSION_FILE}: {e}")
    
    # Опция 2: Чет от version.txt
    if os.path.exists(VERSION_FILE):
        try:
            with open(VERSION_FILE, 'r', encoding='utf-8') as f:
                version = f.read().strip()
                return version_info(
                    version=version,
                    last_commit_date='',
                    update_check_time=''
                )
        except Exception as e:
            print(f"[WARNING] Неуспешно четене на {VERSION_FILE}: {e}")
    
    # Опция 3: Default версия
    return version_info('0.0.0', '', '')


def save_local_version(version_info_obj: version_info):
    """Запазва локалната версия в local_version.json."""
    try:
        with open(LOCAL_VERSION_FILE, 'w', encoding='utf-8') as f:
            json.dump(version_info_obj.to_dict(), f, indent=2, ensure_ascii=False)
        print(f"[OK] Локална версия запазена: {version_info_obj.version}")
    except Exception as e:
        print(f"[ERROR] Неуспешно запазване на локална версия: {e}")


def get_github_latest_commit() -> Optional[Dict]:
    """
    Извлича информация за последния commit от GitHub.
    
    Returns:
        Dict с информация за commit-а или None при грешка
    """
    try:
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'ImageDownloader-UpdateChecker/1.0'
        }
        
        response = requests.get(GITHUB_API_URL, headers=headers, timeout=REQUEST_TIMEOUT)
        
        if response.status_code == 200:
            commit_data = response.json()[0]  # Най-нов е първи
            return {
                'sha': commit_data['sha'],
                'date': commit_data['commit']['committer']['date'],
                'message': commit_data['commit']['message'],
                'author': commit_data['commit']['author']['name']
            }
        elif response.status_code == 403:
            print("[ERROR] GitHub API rate limit достигнат. Опитай пак след час.")
        elif response.status_code == 404:
            print(f"[ERROR] Repository не е намерен: {GITHUB_OWNER}/{GITHUB_REPO}")
        else:
            print(f"[ERROR] GitHub API върна статус {response.status_code}")
        
        return None
        
    except requests.exceptions.Timeout:
        print(f"[ERROR] Timeout при свързване с GitHub API ({REQUEST_TIMEOUT}s)")
        return None
    except requests.exceptions.ConnectionError:
        print("[ERROR] Няма интернет връзка. Не може да се провери за обновления.")
        return None
    except Exception as e:
        print(f"[ERROR] Грешка при проверка на GitHub: {e}")
        return None


def parse_github_date(date_string: str) -> datetime:
    """Парсва GitHub дата string в datetime объект."""
    # GitHub date формат: "2024-01-15T10:30:00Z"
    return datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%SZ")


def compare_dates(github_date_str: str, local_date_str: str) -> bool:
    """
    Сравнява две дати.
    
    Returns:
        True ако github_date_str е по-нова от local_date_str
    """
    if not local_date_str:
        return True  # Ако няма местна дата, считаме че има обновление
    
    try:
        github_dt = parse_github_date(github_date_str)
        local_dt = datetime.strptime(local_date_str, "%Y-%m-%dT%H:%M:%SZ")
        return github_dt > local_dt
    except Exception as e:
        print(f"[WARNING] Грешка при сравнение на дати: {e}")
        return True  # При грешка считаме че има обновление


def check_for_updates() -> Tuple[bool, Optional[Dict], Optional[str]]:
    """
    Проверява дали има налична обновлена версия.
    
    Returns:
        Tuple[bool, Dict|None, str]:
        - bool: Дали има обновление
        - Dict: Информация за GitHub commit-а (ако има) или None
        - str: Съобщение за резултата
    """
    print("[INFO] Проверка за обновления...")
    
    # Четем локална версия
    local_ver = get_local_version()
    print(f"[INFO] Локална версия: {local_ver.version} (последно обновление: {local_ver.last_commit_date})")
    
    # Получаваме информация от GitHub
    github_commit = get_github_latest_commit()
    
    if not github_commit:
        return False, None, "Неуспешно получаване на информация от GitHub"
    
    github_date = github_commit['date']
    print(f"[INFO] Последен commit в GitHub: {github_date}")
    
    # Сравняваме дати
    has_update = compare_dates(github_date, local_ver.last_commit_date)
    
    if has_update:
        message = (
            f"Налична е нова версия!\n"
            f"Локална: {local_ver.version} ({local_ver.last_commit_date})\n"
            f"GitHub: {github_commit['sha'][:8]} ({github_date})\n"
            f"Последно обновление: {github_commit['message']}"
        )
        print(f"[UPDATE] {message}")
        return True, github_commit, message
    else:
        message = "Вашата версия е актуална."
        print(f"[OK] {message}")
        
        # Ако имаме GitHub commit info, актуализираме local_version.json
        if github_commit:
            local_ver.last_commit_date = github_date
            save_local_version(local_ver)
        
        return False, None, message


def perform_update() -> Tuple[bool, str]:
    """
    Изпълнява `git pull` за обновяване на локалното repository.
    
    Returns:
        Tuple[bool, str]: (успех, съобщение)
    """
    print("[UPDATE] Стартиране на git pull...")
    
    # Проверка дали сме в git repository
    if not os.path.exists('.git'):
        error_msg = "Неуспешно: Не сте в git repository. Моля, клонирайте проекта отново."
        print(f"[ERROR] {error_msg}")
        return False, error_msg
    
    # Проверка дали git е наличен
    try:
        subprocess.run(['git', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        error_msg = "Неуспешно: Git не е инсталиран или не е в PATH."
        print(f"[ERROR] {error_msg}")
        return False, error_msg
    
    try:
        # Изпълнение на git pull
        result = subprocess.run(
            ['git', 'pull', 'origin', 'main'],
            capture_output=True,
            text=True,
            timeout=60,
            check=False
        )
        
        if result.returncode == 0:
            success_msg = f"Обновяването е успешно!\n{result.stdout}"
            print(f"[OK] {success_msg}")
            
            # Актуализираме местната версия
            local_ver = get_local_version()
            github_commit = get_github_latest_commit()
            if github_commit:
                local_ver.last_commit_date = github_commit['date']
                save_local_version(local_ver)
            
            return True, success_msg
        else:
            error_msg = f"Git pull се провали с код {result.returncode}:\n{result.stderr}"
            print(f"[ERROR] {error_msg}")
            return False, error_msg
            
    except subprocess.TimeoutExpired:
        error_msg = "Git pull заговори. Timeout след 60 секунди."
        print(f"[ERROR] {error_msg}")
        return False, error_msg
    except Exception as e:
        error_msg = f"Грешка при изпълнение на git pull: {e}"
        print(f"[ERROR] {error_msg}")
        return False, error_msg


def update_check_thread_callback(on_update_available, on_check_complete):
    """
    Callback функция за изпълнение на проверка в отделен thread.
    
    Args:
        on_update_available: Функция (update_info) - вика се когато има обновление
        on_check_complete: Функция (has_update, message) - вика се след всяка проверка
    """
    try:
        has_update, github_commit, message = check_for_updates()
        
        if has_update and github_commit:
            on_update_available(github_commit, message)
        
        on_check_complete(has_update, message)
    except Exception as e:
        print(f"[ERROR] Грешка в update check thread: {e}")
        on_check_complete(False, f"Грешка при проверка: {e}")


def start_background_update_check(on_update_available=None, on_check_complete=None):
    """
    Стартира асинхронна проверка за обновления в отделен thread.
    
    Args:
        on_update_available: Callback (github_commit, message) при налично обновление
        on_check_complete: Callback (has_update, message) след завършване на проверката
    """
    def default_on_update_available(github_commit, message):
        print(f"\n{'='*60}")
        print(f"[UPDATE НАЛИЧНО] {message}")
        print(f"{'='*60}\n")
    
    def default_on_check_complete(has_update, message):
        print(f"[INFO] Проверката за обновления приключи: {message}")
    
    # Използвай дефолтни callbacks ако не са предоставени
    if on_update_available is None:
        on_update_available = default_on_update_available
    if on_check_complete is None:
        on_check_complete = default_on_check_complete
    
    # Стартирай в thread за да не блокира основното приложение
    thread = threading.Thread(
        target=update_check_thread_callback,
        args=(on_update_available, on_check_complete),
        daemon=True
    )
    thread.start()
    print("[INFO] Проверката за обновления стартира в background.")


# Тестов модул
if __name__ == "__main__":
    print("="*60)
    print("Тест на version_checker.py")
    print("="*60)
    
    # Тест 1: Проверка за обновления
    print("\n1. Проверка за обновления...")
    has_update, github_commit, message = check_for_updates()
    print(f"Резултат: {message}")
    
    # Тест 2: Ако има обновление, предложи го
    if has_update:
        print("\n2. Има налично обновление!")
        user_input = input("Искате ли да се обновите сега? (y/n): ")
        
        if user_input.lower() == 'y':
            print("\n3. Стартиране на обновление...")
            success, update_msg = perform_update()
            print(f"Резултат: {update_msg}")
        else:
            print("Обновяването е отхвърлено от потребителя.")
    else:
        print("Вашата версия е актуална.")
    
    print("\n" + "="*60)
    print("Тест приключи.")