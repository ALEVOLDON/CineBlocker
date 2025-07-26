import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import threading
import sys
import os
import ctypes
from typing import Optional
from daw_tracker import CineBlockerTracker

def is_admin() -> bool:
    """Проверяет, запущен ли скрипт с правами администратора."""
    try:
        if sys.platform == "win32":
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        # Для macOS и Linux
        return os.geteuid() == 0
    except (AttributeError, Exception): # AttributeError для систем без geteuid
        return False

class App(tk.Tk):
    def __init__(self, tracker: CineBlockerTracker) -> None:
        super().__init__()

        self.tracker = tracker
        self.after_id: Optional[str] = None

        # --- Настройка окна ---
        self.title("CineBlocker")
        self.geometry("400x150")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # --- Стили ---
        style = ttk.Style(self)
        style.configure("TLabel", font=("Helvetica", 10))
        style.configure("Status.TLabel", font=("Helvetica", 12, "bold"))
        style.configure("Time.TLabel", font=("Courier", 24, "bold"))

        # --- Виджеты ---
        main_frame = ttk.Frame(self, padding="10 10 10 10")
        main_frame.pack(expand=True, fill="both")

        self.status_label = ttk.Label(main_frame, text="Инициализация...", style="Status.TLabel", wraplength=380)
        self.status_label.pack(pady=(0, 10))

        self.time_label = ttk.Label(main_frame, text="00:00 / 30:00", style="Time.TLabel")
        self.time_label.pack(pady=10)

        # --- Запуск обновления UI ---
        self.update_ui()

    def update_ui(self) -> None:
        """Обновляет текст в виджетах, читая данные из трекера."""
        self.status_label.config(text=self.tracker.status_text)
        self.time_label.config(text=self.tracker.time_text)

        # Запланировать следующее обновление через 1000 мс (1 секунду)
        self.after_id = self.after(1000, self.update_ui)

    def on_closing(self) -> None:
        """Обработчик закрытия окна."""
        print("Окно закрывается, останавливаем трекер...")
        if self.after_id:
            self.after_cancel(self.after_id) # Корректно останавливаем цикл обновлений
        self.tracker.stop()
        # Мы не ждем здесь завершения потока, чтобы GUI не зависал.
        # ОС закроет daemon-поток после выхода из основного.
        self.destroy()

if __name__ == "__main__":
    if not is_admin():
        messagebox.showerror(
            "Требуются права администратора",
            "Для редактирования файла hosts и блокировки сайтов, пожалуйста, запустите CineBlocker от имени администратора."
        )
        sys.exit(1)

    # 1. Создаем экземпляр нашего трекера
    tracker = CineBlockerTracker()

    # 2. Запускаем его в отдельном фоновом потоке (daemon=True)
    tracker_thread = threading.Thread(target=tracker.run, daemon=True)
    tracker_thread.start()

    # 3. Создаем и запускаем GUI
    app = App(tracker)
    app.mainloop()