#  Copyright  2021 Alexis Lopez Zubieta
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
import shutil
import subprocess

from appimagebuilder.utils import shell


def has_magic_bytes(path):
    with open(path, "rb") as f:
        bits = f.read(4)
        if bits == b"\x7fELF":
            return True

    return False


def has_soname(path):
    """
    Determine if an elf is a library

    Elf must have a SONAME tag in the dynamic section
    """
    readelf_path = shell.require_executable("readelf")
    # note: don't use `shell=True` as it forces the usage of the system shell which cases a failure if readelf is embed.
    _proc = subprocess.run(
        [readelf_path, "-d", path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    has_soname_tag = False
    if _proc.returncode == 0:
        output = _proc.stdout.decode("utf-8")
        has_soname_tag = "SONAME" in output
    return has_soname_tag


def has_start_symbol(path):
    """
    Determine if an elf is executable

    The `_start` symbol must be present in every runnable elf file.
    http://www.dbp-consulting.com/tutorials/debugging/linuxProgramStartup.html
    """
    readelf_path = shell.require_executable("readelf")
    # note: don't use `shell=True` as it forces the usage of the system shell which cases a failure if readelf is embed.
    _proc = subprocess.run(
        [readelf_path, "-s", path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    has_main_method = False
    if _proc.returncode == 0:
        output = _proc.stdout.decode("utf-8")
        has_main_method = "_start" in output
    return has_main_method


def get_arch(path):
    """
    Read the target instructions set architecture and maps it to a name known by appimage-builder

    https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#File_header
    """
    known_architectures = {
        b"\xB7": "aarch64",
        b"\x28": "gnueabihf",
        b"\x03": "i386",
        b"\x3E": "x86_64",
    }

    with open(path, "rb") as f:
        f.seek(18)
        e_machine = f.read(1)
        if e_machine in known_architectures:
            return known_architectures[e_machine]
        else:
            raise RuntimeError(
                f"Unknown instructions set architecture `{e_machine.hex()}` on: {path}"
            )
