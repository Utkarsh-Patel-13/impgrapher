import os
import sys
import json

import grapher

from stdlib_list import stdlib_list
libraries = stdlib_list("3.8")


args = sys.argv

path = args[1]

imports = {}


def clean_import_string(imp):
    i = 0
    for index, elem in enumerate(imp.split(" ")):
        if elem == "import":
            i = index
            break

    if i != 0:
        return "".join(imp.split(" ")[1:i])
    else:
        return "".join([v.strip(" ,") for v in imp.split(" ")[i+1:]])


def traverse(path):
    # walk through all files at path
    for root, dirs, files in os.walk(path):

        dirs[:] = [d for d in dirs if d not in [
            "venv", "__pycache__", 'node_modules', ".git", ".vscode", ".idea"]]

        # print all files
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                with open(file_path, "r") as f:
                    imports[file[:-3]] = {
                        "path": file_path,
                        "imports": list(dict.fromkeys([clean_import_string(line.strip(" \n")) for line in f.readlines()
                                                       if "import" in line.split(" ")]))
                    }

        # print all directories
        for dir in dirs:
            traverse(os.path.join(root, dir))


traverse(path)


for k in imports:
    imports[k]["imports"] = [
        i for i in imports[k]
        ["imports"] if i not in libraries
    ]

grapher.plot_graph(imports)

# with open("imports.json", "w") as f:
#     json.dump(imports, f, indent=4)
