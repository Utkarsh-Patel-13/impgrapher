from sys import platform
import os
import json

from stdlib_list import stdlib_list

libraries = stdlib_list("3.8")


class Walker:
    """A class to walk through the files and directories in the path. And parse imports for all files

    Args:
        path (str): the path to walk

    """

    def __init__(self, path, include_lib=False):
        self.path = path
        self.imports = dict()
        self.include_lib = include_lib

        self.excludes = [
            "venv", "__pycache__",
            "node_modules", ".git", ".vscode", ".idea"
        ]

    def walk(self, path=None):
        """Walk through the files and directories in the path.
        """
        if not path:
            path = self.path

        if path.endswith(".py"):
            with open(path, "r") as f:

                if platform.startswith("win32"):
                    self.imports[path.split("\\")[-1][:-3]] = {
                        "path": path,
                        "imports": []
                    }

                else:
                    self.imports[path.split("/")[-1][:-3]] = {
                        "imports": []
                    }

                for line in f.readlines():
                    line = line.strip(" \n")
                    if "import" in line:
                        if platform.startswith("win32"):
                            self.imports[path.split(
                                "\\")[-1][:-3]]["imports"].append(self.parse_imports(line))
                        else:
                            self.imports[path.split(
                                "/")[-1][:-3]]["imports"].append(self.parse_imports(line))

        for root, dirs, files in os.walk(path):
            # walk files
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)

                    self.imports[file[:-3]] = {
                        "imports": []
                    }

                    with open(file_path, "r") as f:
                        for line in f.readlines():
                            line = line.strip(" \n")
                            if "import" in line:
                                self.imports[
                                    file[:-3]
                                ]["imports"].append(self.parse_imports(line))

            # walk subdirectories
            dirs[:] = [d for d in dirs if d not in self.excludes]
            for dir in dirs:
                self.walk(os.path.join(root, dir))

        # removing duplicates, null and comma seperated values
        for elem in self.imports:
            temp_imports = []
            for imp in self.imports[elem]["imports"]:
                if imp is None:
                    continue

                for v in imp.split(","):
                    if v not in temp_imports:
                        temp_imports.append(v)

            self.imports[elem]["imports"] = temp_imports

        if self.include_lib:
            self.remove_standard_libs()

    def parse_imports(self, line):
        """Parses modules from the import statement.

        Args:
            line (str): the import line (Ex. "import foo", "from foo import bar", "from foo.bar import baz")

        Returns:
            str: string of modules imported (Ex. ["foo"], ["foo", "bar"])
        """

        line_as_list = line.split(" ")

        imports = []

        if line_as_list[0] == "import":
            for i in range(1, len(line_as_list)):
                if line_as_list[i] == "as":
                    break
                imports.append(line_as_list[i].split(".")[0].strip(" ,"))

        elif line_as_list[0] == "from":
            for i in range(1, len(line_as_list)):
                if line_as_list[i] == "import":
                    break
                imports.append(line_as_list[i].split(".")[0].strip(" ,"))

        if imports != []:
            return ",".join(imports)

    def remove_standard_libs(self):
        """Removes standard libraries from the imports
        """
        for k in self. imports:
            self.imports[k]["imports"] = [
                i for i in self.imports[k]
                ["imports"] if i not in libraries
            ]

    def save_as_json(self, path):
        """Save the imports as json.
        """
        with open(path, "w") as f:
            json.dump(self.imports, f, indent=4)
