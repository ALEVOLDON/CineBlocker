import psutil

print("="*50)
print("🔎 Список всех запущенных процессов:")
print("1. Убедитесь, что ваш DAW запущен.")
print("2. Найдите в этом списке процесс вашего DAW и скопируйте его точное имя.")
print("="*50)

# Получаем уникальные имена процессов и сортируем их для удобства
process_names = sorted(set(p.name() for p in psutil.process_iter(['name'])))

for name in process_names:
    print(name)

print("="*50)
print("✅ Теперь добавьте скопированное имя в список DAW_PROCESS_NAMES в файле daw_tracker.py")
print("="*50)