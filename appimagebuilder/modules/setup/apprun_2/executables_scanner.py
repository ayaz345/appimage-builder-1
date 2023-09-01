#  Copyright  2022 Alexis Lopez Zubieta
#
#  Permission is hereby granted, free of charge, to any person obtaining a
#  copy of this software and associated documentation files (the "Software"),
#  to deal in the Software without restriction, including without limitation the
#  rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
#  sell copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.

#  Copyright  2020 Alexis Lopez Zubieta
#
#  Permission is hereby granted, free of charge, to any person obtaining a
#  copy of this software and associated documentation files (the "Software"),
#  to deal in the Software without restriction, including without limitation the
#  rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
#  sell copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
import logging
import os

from appimagebuilder.modules.setup import apprun_utils
from appimagebuilder.modules.setup.apprun_2.executables import (
    Executable,
    BinaryExecutable,
    InterpretedExecutable,
)
from appimagebuilder.utils import elf
from appimagebuilder.utils.finder import Finder


class MissingInterpreterError(RuntimeError):
    pass


class ExecutablesScanner:
    def __init__(self, appdir, files_cache: Finder):
        self.appdir = appdir
        self.files_cache = files_cache

    def scan_file(self, path) -> [Executable]:
        results = []
        iterations = 0
        binary_found = False
        while iterations < 5 and not binary_found:
            if shebang := apprun_utils.read_shebang(path):
                try:
                    executable = InterpretedExecutable(path, shebang)
                    path = self._resolve_interpreter_path(shebang)
                except MissingInterpreterError as err:
                    logging.warning(f"{err.__str__()} while processing {path.__str__()}")
                    break
            elif elf.has_magic_bytes(path) and elf.has_start_symbol(path):
                arch = elf.get_arch(path)
                executable = BinaryExecutable(path, arch)
                binary_found = True
            else:
                break

            if results:
                results[-1].interpreter = executable

            results.append(executable)
            iterations += 1

        if iterations >= 5:
            raise RuntimeError(f"Loop found while resolving the interpreter of '{path}'")

        return results

    def _resolve_interpreter_path(self, shebang):
        if shebang[0] == "/usr/bin/env":
            interpreter = shebang[1].strip(" ")
        else:
            interpreter = shebang[0].strip(" ")

        interpreter_name = os.path.basename(interpreter)
        path = self.files_cache.find_one(
            interpreter_name, [self.files_cache.is_file, self.files_cache.is_executable]
        )
        if not path:
            raise MissingInterpreterError(
                f"Required interpreter '{interpreter_name}' could not be found in the AppDir"
            )

        if path := os.path.relpath(path):
            return path
        else:
            raise MissingInterpreterError(
                f"Required interpreter '{interpreter_name}' could not be found in the AppDir"
            )
