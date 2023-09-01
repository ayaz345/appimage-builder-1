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
from pathlib import Path

from appimagebuilder.utils.finder import Finder
from .base_helper import BaseHelper
from ..environment import Environment


class Qt(BaseHelper):
    def __init__(self, app_dir, app_dir_files):
        super().__init__(app_dir, app_dir_files)
        self.app_dir = Path(app_dir)
        self._qt4_dirs = {}
        self._qt5_dirs = {}
        self._qt6_dirs = {}

    def configure(self, env: Environment, preserve_files):
        self._configure_qt4()
        self._configure_qt5()
        self._configure_qt6()

    def _configure_qt4(self):
        self._locate_qt4_dirs()
        if self._qt4_dirs:
            # deploy a qt.conf file next to executable files that may start a Qt application
            exec_dirs = self._find_exec_dirs()
            for path in exec_dirs:
                qt_conf = self._generate_conf(path, self._qt4_dirs)
                self._write_qt_conf(qt_conf, path)

    def _configure_qt5(self):
        self._locate_qt5_dirs()
        if self._qt5_dirs:
            # deploy a qt.conf file next to executable files that may start a Qt application
            exec_dirs = self._find_exec_dirs()
            for path in exec_dirs:
                qt_conf = self._generate_conf(path, self._qt5_dirs)
                self._write_qt_conf(qt_conf, path)

    def _find_exec_dirs(self):
        return self.finder.find_dirs_containing(
            file_checks=[Finder.is_file, Finder.is_executable]
        )

    def _write_qt6_conf(self, qt_conf: {str: str}, target_dir: Path):
        path = target_dir / "qt6.conf"
        logging.info(f"Creating {path.relative_to(self.app_dir)}")
        with path.open("w") as f:
            f.write("[Paths]\n")
            for k, v in qt_conf.items():
                f.write("%s = %s\n" % (k, v))

    def _write_qt_conf(self, qt_conf: {str: str}, target_dir: Path):
        path = target_dir / "qt.conf"
        logging.info(f"Creating {path.relative_to(self.app_dir)}")
        with path.open("w") as f:
            f.write("[Paths]\n")
            for k, v in qt_conf.items():
                f.write("%s = %s\n" % (k, v))

    def _generate_conf(self, base_path, content: dict):
        config = {"Prefix": os.path.relpath(self.app_dir, base_path)}
        for k, v in content.items():
            config[k] = v.relative_to(self.app_dir)

        return config

    def _locate_qt4_dirs(self):
        if libqt4core_path := self.finder.find_one(
            "*/libQtCore.so.4.*", [Finder.is_file, Finder.is_elf_shared_lib]
        ):
            self._qt4_dirs["Libraries"] = libqt4core_path.parent
        else:
            # don't go any forward if libQtCore.so.4.... is not found
            return

        paths = list(
            self.finder.find_dirs_containing(
                pattern="qmake",
                file_checks=[Finder.is_file, Finder.is_executable],
                excluded_patterns=[
                    "*/qt5/*",
                    "*/qt6/*",
                    "/usr/bin",
                ],
            )
        )
        if qmake_path := paths[0]:
            self._qt4_dirs["Binaries"] = qmake_path.parent

        if libqminimal_path := self.finder.find_one(
            "*/libqjpcodecs.so", [Finder.is_file, Finder.is_elf]
        ):
            self._qt4_dirs["Plugins"] = libqminimal_path.parent.parent

        if builtins_qmltypes_path := self.finder.find_one(
            "*/builtins.qmltypes", [Finder.is_file]
        ):
            self._qt4_dirs["Qml2Imports"] = builtins_qmltypes_path.parent

        if qtbase_translations_path := self.finder.find_one(
            "*/qt4/translations", [Finder.is_dir]
        ):
            self._qt4_dirs["Translations"] = qtbase_translations_path

    def _locate_qt5_dirs(self):
        if libqt5core_path := self.finder.find_one(
            "*/libQt5Core.so.*", [Finder.is_file, Finder.is_elf_shared_lib]
        ):
            self._qt5_dirs["Libraries"] = libqt5core_path.parent
        else:
            # don't go any forward if libQt5Core is not found
            return

        if qtwebengine_path := self.finder.find_one(
            "*/QtWebEngineProcess", [Finder.is_file, Finder.is_executable]
        ):
            self._qt5_dirs["LibraryExecutables"] = qtwebengine_path.parent

        if qmake_path := self.finder.find_one(
            "*/qmake", [Finder.is_file, Finder.is_executable]
        ):
            self._qt5_dirs["Binaries"] = qmake_path.parent

        if libqminimal_path := self.finder.find_one(
            "*/libqminimal.so", [Finder.is_file, Finder.is_elf]
        ):
            self._qt5_dirs["Plugins"] = libqminimal_path.parent.parent

        if builtins_qmltypes_path := self.finder.find_one(
            "*/builtins.qmltypes", [Finder.is_file]
        ):
            self._qt5_dirs["Qml2Imports"] = builtins_qmltypes_path.parent

        if qtbase_translations_path := self.finder.find_one(
            "*/qt5/translations", [Finder.is_dir]
        ):
            self._qt5_dirs["Translations"] = qtbase_translations_path

        if data_path := self.finder.find_one("*/qt5/resources", [Finder.is_dir]):
            self._qt5_dirs["Data"] = data_path.parent

    def _configure_qt6(self):
        # https://doc.qt.io/qt-6/qt-conf.html
        self._locate_qt6_dirs()
        if self._qt6_dirs:
            # deploy a qt.conf file next to executable files that may start a Qt application
            exec_dirs = self._find_exec_dirs()
            for path in exec_dirs:
                qt_conf = self._generate_conf(path, self._qt6_dirs)
                self._write_qt6_conf(qt_conf, path)

    def _locate_qt6_dirs(self):
        if libqt6core_path := self.finder.find_one(
            "*/libQt6Core.so.*", [Finder.is_file, Finder.is_elf_shared_lib]
        ):
            self._qt6_dirs["Libraries"] = libqt6core_path.parent
        else:
            # don't go any forward if libQt6Core is not found
            return

        if qtwebengine_path := self.finder.find_one(
            "*/QtWebEngineProcess", [Finder.is_file, Finder.is_executable]
        ):
            self._qt6_dirs["LibraryExecutables"] = qtwebengine_path.parent

        if qmake_path := self.finder.find_one(
            "*/qmake6", [Finder.is_file, Finder.is_executable]
        ):
            self._qt6_dirs["Binaries"] = qmake_path.parent

        if libqminimal_path := self.finder.find_one(
            "*/libqminimal.so", [Finder.is_file, Finder.is_elf]
        ):
            self._qt6_dirs["Plugins"] = libqminimal_path.parent.parent

        if builtins_qmltypes_path := self.finder.find_one(
            "*/builtins.qmltypes", [Finder.is_file]
        ):
            self._qt6_dirs["QmlImports"] = builtins_qmltypes_path.parent
            self._qt6_dirs["Qml2Imports"] = builtins_qmltypes_path.parent

        if qtbase_translations_path := self.finder.find_one(
            "*/qt6/translations", [Finder.is_dir]
        ):
            self._qt6_dirs["Translations"] = qtbase_translations_path

        if data_path := self.finder.find_one("*/qt6/resources", [Finder.is_dir]):
            self._qt6_dirs["Data"] = data_path.parent
