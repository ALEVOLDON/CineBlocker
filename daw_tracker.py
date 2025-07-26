import psutil
import time
import mido
import threading
from datetime import datetime, timedelta

# Импортируем наш новый модуль для работы с БД
import database
import site_blocker # Импортируем модуль блокировки

# Список исполняемых файлов DAW, которые мы хотим отслеживать.
# Названия могут отличаться в зависимости от версии и ОС.
# ❗️ВАЖНО: Добавьте сюда имя процесса вашей DAW, если его нет в списке.
# Используйте find_processes.py, чтобы узнать точное имя.
# Все имена должны быть в НИЖНЕМ РЕГИСТРЕ.
DAW_PROCESS_NAMES = [
    "ableton live 12 lite.exe", # <- Привел к нижнему регистру для корректной работы
    "ableton live 11 suite.exe",
    "fl64.exe",
    "bitwigstudio.exe",
    "reaper.exe",
    "studio one.exe",
]

IDLE_THRESHOLD_SECONDS = 60  # Порог неактивности в секундах
TARGET_SECONDS_PER_DAY = 30 * 60 # Цель на день: 30 минут
LOOP_INTERVAL = 5 # Интервал проверки в секундах

def is_daw_running():
    """
    Проверяет, запущен ли какой-либо из указанных DAW-процессов.
    Возвращает имя процесса, если он найден, иначе None.
    """
    for proc in psutil.process_iter(['name']):
        # Сравниваем в нижнем регистре для надежности
        if proc.info['name'].lower() in DAW_PROCESS_NAMES:
            return proc.info['name'] # Возвращаем оригинальное имя для вывода
    return None

def monitor_midi_activity(stop_event, last_midi_activity_ref):
    """
    Эта функция запускается в отдельном потоке, слушает MIDI-события
    и обновляет время последней активности.
    """
    try:
        # mido.open_input() без аргументов открывает первый доступный порт
        with mido.open_input() as port:
            print(f"🎧 Слушаем MIDI-порт: {port.name}")
            # Обновляем время, чтобы сессия сразу считалась активной
            last_midi_activity_ref[0] = datetime.now()
            
            while not stop_event.is_set():
                # Проверяем наличие сообщений без блокировки
                if port.poll():
                    last_midi_activity_ref[0] = datetime.now()
                time.sleep(0.1) # Небольшая пауза, чтобы не грузить CPU

    except (IOError, OSError):
        print("⚠️ MIDI-устройства не найдены. Отслеживание будет только по факту запуска DAW.")
        # В этом случае мы просто обновляем время, пока DAW открыт
        while not stop_event.is_set():
             last_midi_activity_ref[0] = datetime.now()
             time.sleep(1)

class CineBlockerTracker:
    def __init__(self):
        # --- Состояние трекера ---
        self.total_today_seconds = 0
        self.session_active = False
        self.sites_are_blocked = None
        self.is_idle = False
        self.daw_process_name = None
        self.status_text = "Инициализация..."
        self.time_text = "00:00 / 30:00"

        # --- Управление потоками ---
        self.last_midi_activity = [None] # В списке для передачи по ссылке
        self.midi_thread = None
        self.stop_midi_thread_event = threading.Event()
        self._stop_main_loop_event = threading.Event()

    def _update_time_text(self):
        """Форматирует строку времени для GUI."""
        done_mins, done_secs = divmod(self.total_today_seconds, 60)
        target_mins, _ = divmod(TARGET_SECONDS_PER_DAY, 60)
        self.time_text = f"{done_mins:02d}:{done_secs:02d} / {target_mins:02d}:00"

    def run(self):
        """Основной цикл трекера. Запускается в отдельном потоке."""
        print("🚀 Трекер запущен...")
        database.init_db()
        self.total_today_seconds = database.get_today_activity()
        self._update_time_text()

        # Начальная проверка и установка блокировки
        if self.total_today_seconds < TARGET_SECONDS_PER_DAY:
            self.sites_are_blocked = site_blocker.block_sites()
        else:
            if site_blocker.unblock_sites():
                self.sites_are_blocked = False

        while not self._stop_main_loop_event.is_set():
            running_daw = is_daw_running()

            if running_daw and not self.session_active:
                # Начало сессии
                self.session_active = True
                self.daw_process_name = running_daw
                self.status_text = f"✅ Обнаружен DAW: {self.daw_process_name}"
                self.stop_midi_thread_event.clear()
                self.midi_thread = threading.Thread(
                    target=monitor_midi_activity,
                    args=(self.stop_midi_thread_event, self.last_midi_activity),
                    daemon=True
                )
                self.midi_thread.start()

            elif running_daw and self.session_active:
                # Сессия активна
                self.is_idle = self.last_midi_activity[0] and \
                               (datetime.now() - self.last_midi_activity[0]) > timedelta(seconds=IDLE_THRESHOLD_SECONDS)

                if self.is_idle:
                    self.status_text = "😴 Пользователь неактивен, таймер на паузе..."
                else:
                    self.status_text = "🎶 Сессия активна, время идет!"
                    self.total_today_seconds += LOOP_INTERVAL
                    self._update_time_text()

                    if self.sites_are_blocked and self.total_today_seconds >= TARGET_SECONDS_PER_DAY:
                        print("\n🎉 Поздравляем! Цель достигнута!")
                        database.save_today_activity(self.total_today_seconds)
                        if site_blocker.unblock_sites():
                            self.sites_are_blocked = False
                        self.status_text = f"✅ Цель достигнута! Наслаждайтесь отдыхом."

            elif not running_daw and self.session_active:
                # Завершение сессии
                self.status_text = "🛑 DAW закрыт. Сессия завершена."
                database.save_today_activity(self.total_today_seconds)
                self.session_active = False
                self.stop_midi_thread_event.set()
                if self.midi_thread:
                    self.midi_thread.join()
                self.last_midi_activity[0] = None
            else:
                # Ожидание
                if self.total_today_seconds < TARGET_SECONDS_PER_DAY:
                    self.status_text = "...Ожидаем запуска DAW. Сайты заблокированы."
                else:
                    self.status_text = "...Ожидаем запуска DAW. Цель на день выполнена."

            time.sleep(LOOP_INTERVAL)

        self._shutdown()

    def stop(self):
        """Сигнализирует основному циклу и потокам о необходимости остановиться."""
        print("Получен сигнал на остановку трекера...")
        self._stop_main_loop_event.set()
        self.stop_midi_thread_event.set()

    def _shutdown(self):
        """Выполняет чистое завершение работы: сохраняет данные, снимает блокировку."""
        print("Трекер завершает работу, сохраняем данные...")
        database.save_today_activity(self.total_today_seconds)
        if self.sites_are_blocked:
            print("Снимаем блокировку сайтов перед выходом...")
            site_blocker.unblock_sites()
        if self.midi_thread and self.midi_thread.is_alive():
            self.midi_thread.join()
        print("👋 Трекер полностью остановлен.")