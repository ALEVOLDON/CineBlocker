import sys
import os

# IP-адрес для перенаправления заблокированных сайтов (локальный хост)
REDIRECT_IP = "127.0.0.1"
# Уникальный комментарий, чтобы идентифицировать наши записи в файле hosts
HOSTS_COMMENT = "# Blocked by CineBlocker"

# Список сайтов для блокировки
SITES_TO_BLOCK = [
    "www.youtube.com",
    "youtube.com",
    "www.netflix.com",
    "netflix.com",
    # Можно добавить другие, например: "vk.com", "www.instagram.com",
]

def get_hosts_path():
    """Определяет путь к файлу hosts в зависимости от ОС."""
    if sys.platform == "win32":
        return os.path.join(os.environ["SystemRoot"], "System32", "drivers", "etc", "hosts")
    else: # macOS и Linux
        return "/etc/hosts"

HOSTS_PATH = get_hosts_path()

def _clear_cineblocker_entries(file_handle):
    """Вспомогательная функция для очистки файла от наших записей."""
    content = [line for line in file_handle.readlines() if HOSTS_COMMENT not in line]
    file_handle.seek(0)
    file_handle.writelines(content)
    file_handle.truncate()

def block_sites():
    """Добавляет записи в файл hosts для блокировки сайтов."""
    print("🔒 Активируем блокировку сайтов...")
    try:
        with open(HOSTS_PATH, 'r+') as file:
            _clear_cineblocker_entries(file)

            # Добавляем новые записи
            file.write("\n")
            for site in SITES_TO_BLOCK:
                file.write(f"{REDIRECT_IP}\t{site}\t{HOSTS_COMMENT}\n")
        print("✅ Сайты успешно заблокированы.")
        return True
    except PermissionError:
        print("\n❌ ОШИБКА: Нет прав для записи в файл hosts. Пожалуйста, запустите скрипт от имени администратора.")
        return False
    except Exception as e:
        print(f"\n❌ Произошла непредвиденная ошибка при блокировке: {e}")
        return False

def unblock_sites():
    """Удаляет записи CineBlocker из файла hosts."""
    print("🔓 Снимаем блокировку сайтов...")
    try:
        with open(HOSTS_PATH, 'r+') as file:
            _clear_cineblocker_entries(file)
        print("✅ Сайты успешно разблокированы.")
        return True
    except PermissionError:
        # В этом случае ошибка не критична, просто сообщаем
        print("\n⚠️ Не удалось снять блокировку из-за отсутствия прав администратора.")
        return False
    except Exception as e:
        print(f"\n❌ Произошла непредвиденная ошибка при разблокировке: {e}")
        return False