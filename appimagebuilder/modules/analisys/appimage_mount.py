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
import os
import logging
import subprocess


class AppImageMount:
    def __init__(self, appimage_path):
        self._appimage_path = appimage_path
        self.path = None
        self._process = None

    def __del__(self):
        if self._process:
            self.unmount()

    def __enter__(self):
        self.mount()
        return self

    def __exit__(self):
        self.unmount()
        return self

    def mount(self):
        if self._process:
            raise RuntimeError("The target is mounted already")

        abs_target_path = os.path.abspath(self._appimage_path)
        self._process = subprocess.Popen(
            [abs_target_path, "--appimage-mount"], stdout=subprocess.PIPE
        )
        self.path = self._process.stdout.readline().decode("utf-8").strip()
        if ret_code := self._process.poll():
            raise RuntimeError(f"Unable to run: {self._appimage_path} --appimage-mount")
        logging.info(f"AppImage mounted at: {self.path}")
        return self.path

    def unmount(self):
        self._process.kill()
        self._process.wait()

        self.path = None
        self._process = None

        logging.info("AppImage unmounted")
