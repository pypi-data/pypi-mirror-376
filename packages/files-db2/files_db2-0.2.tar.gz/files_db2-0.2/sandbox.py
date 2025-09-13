import os
os.scandir(".")
for entry in os.scandir("."):
    print(entry)
    print(entry.name, "Directory" if entry.is_dir() else "File")
