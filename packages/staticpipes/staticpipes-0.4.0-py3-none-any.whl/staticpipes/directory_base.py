import os
from contextlib import contextmanager


class BaseDirectory:

    def __init__(self, dir: str):
        self.dir = dir

    @contextmanager
    def get_contents_as_filepointer(self, dir, filename, mode=""):
        fp = open(self.get_full_filename(dir, filename), "r" + mode)
        yield fp
        fp.close()

    def get_contents_as_bytes(self, dir, filename) -> bytes:
        with self.get_contents_as_filepointer(dir, filename, "b") as fp:
            return fp.read()

    def get_contents_as_str(self, dir, filename) -> str:
        with self.get_contents_as_filepointer(dir, filename, "") as fp:
            return fp.read()

    def get_full_filename(self, dir: str, filename: str) -> str:
        if dir != "/":
            if dir.startswith("/"):
                dir = dir[1:]
            return os.path.join(self.dir, dir, filename)
        else:
            return os.path.join(self.dir, filename)

    def has_file(self, dir, filename) -> bool:
        return os.path.exists(self.get_full_filename(dir, filename))
