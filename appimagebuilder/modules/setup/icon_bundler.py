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
import re
import shutil


class IconBundler:
    class Error(RuntimeError):
        pass

    def __init__(self, app_dir, icon):
        self.app_dir = app_dir
        self.icon = icon
        if icon.endswith(".ico"):
            logging.info(
                f"File .ico is not supported as app icon, searching for svg or png files: {icon} "
            )
            self.icon = icon[:-4]
        elif icon.endswith(".png") or icon.endswith(".svg"):
            logging.info(
                f"Don't use extension in app icon file name, cutting it down: {icon} "
            )
            self.icon = icon[:-4]

    def bundle_icon(self):
        source_icon_path = self._get_icon_path()
        if not source_icon_path:
            raise IconBundler.Error(f"Unable to find any app icon named: {self.icon}")

        target_icon_path = os.path.join(
            self.app_dir, os.path.basename(source_icon_path)
        )
        try:
            logging.info(
                f"Setting AppDir: {source_icon_path} to {os.path.relpath(target_icon_path, self.app_dir)}"
            )
            shutil.copyfile(source_icon_path, target_icon_path)
            app_dir_icon_path = self.app_dir / ".DirIcon"
            if os.path.exists(app_dir_icon_path):
                os.remove(app_dir_icon_path)
            os.symlink(os.path.basename(source_icon_path), app_dir_icon_path)
        except Exception:
            raise IconBundler.Error(
                f"Unable to copy icon from: {source_icon_path} to {target_icon_path}"
            )

    def _get_icon_path(self):
        # include target AppDir paths
        search_paths = [
            os.path.join(self.app_dir, "usr", "share"),
            os.path.join(self.app_dir, "usr", "local", "share"),
        ]

        # include system data dirs
        data_dirs = os.getenv("XDG_DATA_DIRS", default="")
        search_paths.extend(data_dirs.split(":"))

        refined_search_paths = []
        for path in search_paths:
            refined_search_paths.extend((f"{path}/icons", f"{path}/pixmaps"))
        for path in refined_search_paths:
            if path := self._search_icon(path):
                return path

        return None

    def _search_icon(self, search_path):
        logging.info(f"Looking app icon at: {search_path}")
        path = None
        size = 0

        svg_icon_name = f"{self.icon}.svg"
        png_icon_name = f"{self.icon}.png"

        for root, dirs, files in os.walk(search_path):
            # prefer svg files over png
            if svg_icon_name in files:
                return os.path.join(root, svg_icon_name)

            if png_icon_name in files:
                new_path = os.path.join(root, png_icon_name)
                new_size = self._extract_icon_size_from_path(new_path)

                if new_size >= size:
                    size = new_size
                    path = new_path

        return path

    def _extract_icon_size_from_path(self, path):
        if size_search := re.search(".*/(\d+)x\d+/.*", path, re.IGNORECASE):
            return int(size_search[1])
        else:
            logging.warning(f"Icon size can not be guessed from path: {path}")

        return 0
