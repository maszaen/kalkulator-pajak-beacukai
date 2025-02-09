import os

MAIN_SCRIPT = "main.py"

OUTPUT_FILENAME = "Kalkulator-Bea-Cukai-by-maszaen-v2.0"

OUTPUT_DIR = "build"

command = f"python -m nuitka --standalone --onefile --enable-plugin=pyside6 --output-dir={OUTPUT_DIR} --output-filename={OUTPUT_FILENAME} --disable-console {MAIN_SCRIPT}"

print(f"Building {OUTPUT_FILENAME}...")
os.system(command)
print(f"Build selesai! File build disimpan di folder /{OUTPUT_DIR}.")
