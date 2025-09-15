import hashlib

import staticpipes.utils
from staticpipes.current_info import CurrentInfo
from staticpipes.pipe_base import BasePipe


class PipeCopyWithVersioning(BasePipe):
    """
    A pipline that copies files from the source directory
    to the build site (unless already excluded) while
    renaming the file based on a hash of the contents,
    thus allowing them to be versioned.

    The new filename is put in the context so later pipes
    (eg Jinja2 templates) can use it.

    Pass:

    - extensions - a list of file extensions that will be copied
    eg ["js", "css"].
    You can pass an empty list to copy all files.

    - source_sub_directory - if your files are in a subdirectory
    pass that here.
    Any files outside that will be ignored and the subdirectory
    will not appear in the build directory.
    eg pass "assets" and "assets/main.css"
    will appear in build site as "main.css"

    - context_key - the key in the context that
    new filenames will be stored in

    - directories - Only items in these directories and
    their children will be copied.
    """

    def __init__(
        self,
        extensions=["js", "css"],
        context_key="versioning_new_filenames",
        source_sub_directory=None,
        directories: list = ["/"],
    ):
        self.extensions = extensions
        self.context_key = context_key
        self.source_sub_directory = (
            "/" + source_sub_directory
            if source_sub_directory and not source_sub_directory.startswith("/")
            else source_sub_directory
        )
        self.mapping: dict[str, str] = {}
        self.directories: list = directories

    def prepare_file(self, dir: str, filename: str, current_info: CurrentInfo) -> None:
        """"""
        # Check Extensions
        if self.extensions and not staticpipes.utils.does_filename_have_extension(
            filename, self.extensions
        ):
            return

        # Directories
        if not staticpipes.utils.is_directory_in_list(dir, self.directories):
            return

        # Source Sub Dir then copy
        if self.source_sub_directory:
            test_dir = "/" + dir if not dir.startswith("/") else dir
            if not test_dir.startswith(self.source_sub_directory):
                return
            out_dir = dir[len(self.source_sub_directory) :]
        else:
            out_dir = dir

        contents = self.source_directory.get_contents_as_bytes(dir, filename)

        hash = hashlib.md5(contents).hexdigest()
        filename_bits = filename.split(".")
        filename_extension = filename_bits.pop()
        new_filename = ".".join(filename_bits) + "." + hash + "." + filename_extension

        current_info.set_context(
            [
                self.context_key,
                staticpipes.utils.make_path_from_dir_and_filename(out_dir, filename),
            ],
            staticpipes.utils.make_path_from_dir_and_filename(out_dir, new_filename),
        )

        self.mapping[dir + "#####" + filename] = new_filename

    def build_file(self, dir: str, filename: str, current_info: CurrentInfo) -> None:
        """"""
        # Check Extensions
        if self.extensions and not staticpipes.utils.does_filename_have_extension(
            filename, self.extensions
        ):
            return

        # Directories
        if not staticpipes.utils.is_directory_in_list(dir, self.directories):
            return

        # Source Sub Dir then copy
        if self.source_sub_directory:
            test_dir = "/" + dir if not dir.startswith("/") else dir
            if not test_dir.startswith(self.source_sub_directory):
                return
            out_dir = dir[len(self.source_sub_directory) :]
        else:
            out_dir = dir

        new_filename = self.mapping[dir + "#####" + filename]

        self.build_directory.copy_in_file(
            out_dir,
            new_filename,
            self.source_directory.get_full_filename(dir, filename),
        )

    def file_changed_during_watch(self, dir, filename, current_info):
        """"""
        self.prepare_file(dir, filename, current_info)
        self.build_file(dir, filename, current_info)
