import os

MAIN_SCRIPT = "main.py"

OUTPUT_FILENAME = "Kalkulator-Bea-Cukai-v3.1.6"

OUTPUT_DIR = "build"

DEBUG = "disable"

command = f"python -m nuitka --standalone --onefile --enable-plugin=pyside6 --output-dir={OUTPUT_DIR} --output-filename={OUTPUT_FILENAME} --windows-console-mode={DEBUG} {MAIN_SCRIPT}"

print(f"Building {OUTPUT_FILENAME}...")
os.system(command)
print(f"Build selesai! File build disimpan di folder /{OUTPUT_DIR}.")
