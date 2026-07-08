# url_manager.py
"""
Модул за управление на JSON база с URL адреси.
Поддържа CRUD операции и автоматично инкрементиране.
"""

import json
import os
import re
from urllib.parse import urlparse


class UrlManager:
    """
    Управлява списък от URL адреси, съхраняван в JSON файл.
    """

    def __init__(self, file_path='urls.json'):
        """
        Инициализира мениджъра с път до JSON файла.

        Args:
            file_path: Път до JSON файла (по подразбиране 'urls.json')
        """
        self.file_path = file_path
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """Създава празен JSON файл, ако не съществува."""
        if not os.path.exists(self.file_path):
            self._save_raw([])

    def _save_raw(self, urls):
        """
        Записва списък от URL адреси във файла.

        Args:
            urls: Списък от URL низове
        """
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(urls, f, indent=2, ensure_ascii=False)

    def load_urls(self):
        """
        Зарежда списъка от URL адреси от JSON файла.

        Returns:
            list: Списък от URL низове. При грешка връща празен списък.
        """
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return []
                return json.loads(content)
        except (json.JSONDecodeError, FileNotFoundError):
            # При повреден файл - създаваме резервно копие и започваме наново
            if os.path.exists(self.file_path):
                backup_path = self.file_path + '.backup'
                try:
                    os.rename(self.file_path, backup_path)
                    print(f"[UrlManager] Повреден JSON файл. Резервно копие: {backup_path}")
                except Exception:
                    pass
            self._save_raw([])
            return []
        except Exception as e:
            print(f"[UrlManager] Грешка при зареждане: {e}")
            return []

    def save_urls(self, urls):
        """
        Записва списък от URL адреси във файла (публичен метод).

        Args:
            urls: Списък от URL низове
        """
        self._save_raw(urls)

    @staticmethod
    def get_base_url(url):
        """
        Извлича основната директория на URL за проверка на дублиране.

        Връща протокол + домейн + първото ниво на пътя (или по-малко, ако няма).
        Пример: https://content3.erosberry.com/wowgirls.com/0017/00.jpg
             → https://content3.erosberry.com/wowgirls.com

        Args:
            url: Пълен URL адрес

        Returns:
            str: Нормализиран базов URL
        """
        url = url.strip().rstrip('/')

        # Използваме urlparse за надеждно разбиване
        parsed = urlparse(url)
        scheme = parsed.scheme or 'https'
        netloc = parsed.netloc or parsed.path.split('/')[0]

        # Вземаме path-а без водещата /
        path = parsed.path.lstrip('/')

        # Разделяме path-а на части
        parts = path.split('/')

        # Вземаме първата 1 част след домейна (или по-малко)
        # Това е: ниво1
        base_parts = parts[:1]

        base_url = f"{scheme}://{netloc}"
        if base_parts:
            base_url += '/' + '/'.join(base_parts)

        return base_url.rstrip('/')

    def is_duplicate(self, url):
        """
        Проверява дали URL адресът вече съществува в списъка
        (сравнявайки по основна директория).

        Args:
            url: URL адрес за проверка

        Returns:
            bool: True, ако URL-ът вече съществува
        """
        base_new = self.get_base_url(url)
        existing_urls = self.load_urls()

        for existing_url in existing_urls:
            base_existing = self.get_base_url(existing_url)
            if base_new == base_existing:
                return True

        return False

    def add_url(self, url):
        """
        Добавя нов URL адрес в списъка, ако не е дубликат.

        Args:
            url: URL адрес за добавяне

        Returns:
            tuple: (success: bool, message: str)
        """
        url = url.strip()
        if not url:
            return False, "URL адресът е празен."

        urls = self.load_urls()

        if self.is_duplicate(url):
            base = self.get_base_url(url)
            return False, f"Основната директория вече съществува в списъка: {base}"

        urls.append(url)
        self._save_raw(urls)
        return True, f"URL адресът е добавен успешно."

    def delete_url(self, index):
        """
        Изтрива URL адрес на посочената позиция.

        Args:
            index: Индекс на URL-а в списъка

        Returns:
            tuple: (success: bool, message: str)
        """
        urls = self.load_urls()

        if index < 0 or index >= len(urls):
            return False, f"Невалиден индекс: {index}. Списъкът съдържа {len(urls)} адреса."

        removed = urls.pop(index)
        self._save_raw(urls)
        return True, f"URL адресът е изтрит: {removed}"

    def update_url(self, index, new_url):
        """
        Променя URL адрес на посочената позиция.

        Args:
            index: Индекс на URL-а в списъка
            new_url: Нов URL адрес

        Returns:
            tuple: (success: bool, message: str)
        """
        new_url = new_url.strip()
        if not new_url:
            return False, "Новият URL адрес е празен."

        urls = self.load_urls()

        if index < 0 or index >= len(urls):
            return False, f"Невалиден индекс: {index}. Списъкът съдържа {len(urls)} адреса."

        # Запазваме стария URL за сравнение при проверка за дублиране
        old_url = urls[index]

        # Проверка за дублиране, но не спрямо себе си
        base_new = self.get_base_url(new_url)
        for i, existing_url in enumerate(urls):
            if i == index:
                continue
            base_existing = self.get_base_url(existing_url)
            if base_new == base_existing:
                return False, f"Основната директория вече съществува в списъка: {base_new}"

        urls[index] = new_url
        self._save_raw(urls)
        return True, f"URL адресът е обновен: {old_url} → {new_url}"

    @staticmethod
    def increment_path_number(url):
        """
        Инкрементира числото в последната директория на пътя (преди името на файла).

        Пример:
            https://content3.erosberry.com/wowgirls.com/0017/00.jpg
            → https://content3.erosberry.com/wowgirls.com/0018/00.jpg

        Args:
            url: URL адрес за инкрементиране

        Returns:
            str: URL с инкрементирана директория, или оригиналния URL при грешка
        """
        url = url.strip()
        parsed = urlparse(url)
        scheme = parsed.scheme or 'https'
        netloc = parsed.netloc

        # Вземаме path-а без водещата /
        path = parsed.path.lstrip('/')

        # Разделяме на части
        parts = path.split('/')

        if len(parts) < 2:
            # Няма достатъчно части за инкрементиране
            return url

        # Предпоследната част е директорията преди файла
        dir_index = len(parts) - 2
        dir_part = parts[dir_index]

        # Търсим число в директорията
        match = re.search(r'(\d+)', dir_part)
        if not match:
            # Няма число за инкрементиране
            return url

        num_str = match.group(1)
        padding = len(num_str)
        num = int(num_str)
        new_num = num + 1
        new_num_str = str(new_num).zfill(padding)

        # Заменяме числото в директорията
        new_dir_part = dir_part[:match.start(1)] + new_num_str + dir_part[match.end(1):]
        parts[dir_index] = new_dir_part

        # Конструираме новия URL
        new_path = '/'.join(parts)

        # Възстановяваме path-а
        result = f"{scheme}://{netloc}/{new_path}"
        if parsed.query:
            result += f"?{parsed.query}"
        if parsed.fragment:
            result += f"#{parsed.fragment}"

        return result

    def increment_url(self, index):
        """
        Инкрементира URL на посочената позиция с 1 стъпка и записва промяната.

        Args:
            index: Индекс на URL-а в списъка

        Returns:
            tuple: (success: bool, old_url: str, new_url: str)
        """
        return self.increment_url_by_count(index, 1)

    def increment_url_by_count(self, index, count):
        """
        Инкрементира URL на посочената позиция с N стъпки и записва промяната.

        Args:
            index: Индекс на URL-а в списъка
            count: Брой стъпки за инкрементиране

        Returns:
            tuple: (success: bool, old_url: str, final_new_url: str)
        """
        urls = self.load_urls()

        if index < 0 or index >= len(urls):
            return False, None, None

        old_url = urls[index]
        current_url = old_url

        for _ in range(count):
            next_url = self.increment_path_number(current_url)
            if next_url == current_url:
                # Не може да се инкрементира повече
                break
            current_url = next_url

        if current_url == old_url:
            return False, old_url, None

        urls[index] = current_url
        self._save_raw(urls)
        return True, old_url, current_url
