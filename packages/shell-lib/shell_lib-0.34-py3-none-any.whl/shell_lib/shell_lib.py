# Co-created with Google Gemini
import os
import sys
import shutil
import stat
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Generator, Union, Optional, overload

PathTypes = Union[str, bytes, Path]
FS_ENCODING = sys.getfilesystemencoding()

if os.name == 'nt':
    def color(s: str):
        return s
else:
    def color(s: str):
        return f'\033[93m{s}\033[0m'

class PathInfo:
    """
    A class that encapsulates information about a file or directory.
    """
    def __init__(self, path: PathTypes, size: int,
                 ctime: datetime, mtime: datetime, atime: datetime,
                 is_dir: bool, is_file: bool,
                 permissions: str):
        self.path: str = path.decode(FS_ENCODING) \
                            if isinstance(path, bytes) \
                            else str(path)
        self.size: int = size
        self.ctime: datetime = ctime
        self.mtime: datetime = mtime
        self.atime: datetime = atime
        self.is_dir: bool = is_dir
        self.is_file: bool = is_file
        self.permissions: str = permissions

    def __repr__(self):
        s = (f"PathInfo(path={self.path}, size={self.size}, "
             f"ctime={self.ctime}, mtime={self.mtime}, atime={self.atime}, "
             f"is_dir={self.is_dir}, is_file={self.is_file}, "
             f"permissions={self.permissions})")
        return s

class CDContextManager:
    def __init__(self, path: Union[PathTypes, None]) -> None:
        self.original_cwd = os.getcwd()
        if path is not None:
            print(color(f"Change directory to: {path!r}"))
            os.chdir(path)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print(color(f"Change directory to: {self.original_cwd}"))
        os.chdir(self.original_cwd)

class Shell:
    """
    A simple API designed to replace Linux Shell scripts.
    It unifies common file system operations and Shell command execution.
    """
    def __setattr__(self, name, _):
        raise AttributeError(f"Can't set attribute {name!r}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            if issubclass(exc_type, subprocess.CalledProcessError):
                msg = color(f"\nError: Command failed with exit code {exc_val.returncode}")
                print(msg, file=sys.stderr)
                self.exit(exc_val.returncode)
            else:
                import traceback
                traceback.print_exception(exc_type, exc_val, exc_tb, file=sys.stderr)
                self.exit(1)

    # --- File and Directory Operations API ---

    def home_dir(self) -> Path:
        """
        Returns the current user's home directory, a pathlib.Path object.
        """
        return Path.home()

    def path(self, path: PathTypes) -> Path:
        """
        Converts a str/bytes path to a pathlib.Path object.
        """
        if isinstance(path, bytes):
            path = path.decode(FS_ENCODING)
        return Path(path)

    def create_dir(self, path: PathTypes, *, exist_ok: bool = False) -> None:
        """
        Creates a directory.

        :param path: The path of the directory to create.
        :param exist_ok: If True, existing directories will not raise an error.
        """
        print(color(f"Create directory: {path!r}"))
        os.makedirs(path, exist_ok=exist_ok)

    def remove_dir(self, path: PathTypes, *, ignore_missing: bool = False) -> None:
        """
        Recursively removes a directory and its contents.

        :param path: The path of the directory to remove.
        :param ignore_missing: If True, no error is raised if the directory is missing.
        """
        if ignore_missing and not os.path.isdir(path):
            return
        print(color(f"Remove directory: {path!r}"))
        shutil.rmtree(path)

    def remove_file(self, path: PathTypes, *, ignore_missing: bool = False) -> None:
        """
        Removes a file.

        :param path: The path of the file to remove.
        :param ignore_missing: If True, no error is raised if the file is missing.
        """
        if ignore_missing and not os.path.isfile(path):
            return
        print(color(f"Remove file: {path!r}"))
        os.remove(path)

    def copy_file(self, src: PathTypes, dst: PathTypes, *, replace_existing: bool = False) -> None:
        """
        Copies a file.

        :param src: The source file path.
        :param dst: The destination file path.
        :param replace_existing: If True, overwrites the destination if it exists.
        """
        print(color(f"Copy file from '{src!r}' to '{dst!r}'"))
        if not replace_existing and os.path.isfile(dst):
            raise FileExistsError(f"Destination file '{dst!r}' already exists.")

        shutil.copy2(src, dst) # type: ignore

    def copy_dir(self, src: PathTypes, dst: PathTypes, *, replace_existing: bool = False) -> None:
        """
        Copies a directory.

        :param src: The source directory path.
        :param dst: The destination directory path.
        :param replace_existing: If True, removes the exist destination before copying.
        """
        print(color(f"Copy directory from '{src!r}' to '{dst!r}'"))
        if os.path.isdir(dst):
            if not replace_existing:
                raise FileExistsError(f"Destination directory '{dst!r}' already exists.")
            shutil.rmtree(dst)

        shutil.copytree(src, dst) # type: ignore

    def move_file(self, src: PathTypes, dst: PathTypes, *, replace_existing: bool = False) -> None:
        """
        Moves a file.

        :param src: The source file path.
        :param dst: The destination file path.
        :param replace_existing: If True, overwrites the destination if it exists.
        """
        print(color(f"Move file from '{src!r}' to '{dst!r}'"))
        if os.path.isfile(dst):
            if not replace_existing:
                raise FileExistsError(f"Destination file '{dst!r}' already exists.")
            os.remove(dst)

        shutil.move(src, dst) # type: ignore

    def move_dir(self, src: PathTypes, dst: PathTypes, *, replace_existing: bool = False) -> None:
        """
        Moves a directory.

        :param src: The source directory path.
        :param dst: The destination directory path.
        :param replace_existing: If True, removes the exist destination before moving.
        """
        print(color(f"Move directory from '{src!r}' to '{dst!r}'"))
        if os.path.isdir(dst):
            if not replace_existing:
                raise FileExistsError(f"Destination directory '{dst!r}' already exists.")
            shutil.rmtree(dst)

        shutil.move(src, dst) # type: ignore

    def rename_file(self, src: PathTypes, dst: PathTypes) -> None:
        """
        Renames a file.

        :param src: The source file path.
        :param dst: The destination file path.
        """
        print(color(f"Rename file from '{src!r}' to '{dst!r}'"))
        if not os.path.isfile(src):
            raise FileNotFoundError(f"Source file '{src!r}' does not exist.")
        if os.path.isfile(dst):
            raise FileExistsError(f"Destination file '{dst!r}' already exists.")
        os.rename(src, dst)

    def rename_dir(self, src: PathTypes, dst: PathTypes) -> None:
        """
        Renames a directory.

        :param src: The source directory path.
        :param dst: The destination directory path.
        """
        print(color(f"Rename directory from '{src!r}' to '{dst!r}'"))
        if not os.path.isdir(src):
            raise FileNotFoundError(f"Source directory '{src!r}' does not exist.")
        if os.path.isdir(dst):
            raise FileExistsError(f"Destination directory '{dst!r}' already exists.")
        os.rename(src, dst)

    def get_path_info(self, path: PathTypes) -> PathInfo:
        """
        Retrieves detailed information about an existing file or directory.

        If the path doesn't exist, raise a FileNotFoundError exception.

        :param path: The path of the file or directory.
        :return: A PathInfo object containing detailed information.
        """
        stats = os.stat(path)
        mode = stats.st_mode
        return PathInfo(
            path=path,
            size=stats.st_size,
            ctime=datetime.fromtimestamp(stats.st_ctime),
            mtime=datetime.fromtimestamp(stats.st_mtime),
            atime=datetime.fromtimestamp(stats.st_atime),
            is_dir=stat.S_ISDIR(mode),
            is_file=stat.S_ISREG(mode),
            permissions=oct(mode)[-3:]
        )

    @overload
    def list_dir(self, path: Union[str, Path]) -> List[str]:
        ...

    @overload
    def list_dir(self, path: bytes) -> List[bytes]:
        ...

    def list_dir(self, path):
        """
        Lists all files and subdirectories within a directory.

        :param path: The directory path.
        :return: A list of all entry names.
        """
        return os.listdir(path)

    @overload
    def walk_dir(self, top_dir: Union[str, Path]) -> Generator[Tuple[str, str], None, None]:
        ...

    @overload
    def walk_dir(self, top_dir: bytes) -> Generator[Tuple[bytes, bytes], None, None]:
        ...

    def walk_dir(self, top_dir):
        """
        A generator that traverses a directory and all its subdirectories,
        yielding (directory_path, filename) tuples.

        :param top_dir: The root directory to start walking from.
        :yields: (dirpath, filename) tuples of str or bytes, depending on the input type.
        """
        if not os.path.isdir(top_dir):
            raise FileNotFoundError(f"Top directory '{top_dir!r}' does not exist.")

        for dirpath, dirnames, filenames in os.walk(top_dir):
            for filename in filenames:
                yield (dirpath, filename)

    def cd(self, path: Union[PathTypes, None]):
        """
        Changes the current working directory.

        This method supports to be used as a context manager (`with` statement).
        The original working directory will be restored automatically upon exiting
        the `with` block, even if an exception occurs.

        :param path: The path to the directory to change to.
                     None means no change, using the 'with' statement ensures
                     returning to the current directory.
        """
        return CDContextManager(path)

    def path_exists(self, path: PathTypes) -> bool:
        """
        Checks if a path exists.

        :param path: The file or directory path.
        :return: True if the path exists, False otherwise.
        """
        return os.path.exists(path)

    def is_file(self, path: PathTypes) -> bool:
        """
        Checks if a path is a file.

        :param path: The file path.
        :return: True if the path is a file, False otherwise.
        """
        return os.path.isfile(path)

    def is_dir(self, path: PathTypes) -> bool:
        """
        Checks if a path is a directory.

        :param path: The directory path.
        :return: True if the path is a directory, False otherwise.
        """
        return os.path.isdir(path)

    def split_path(self, path: PathTypes) -> Union[Tuple[str, str], Tuple[bytes, bytes]]:
        """
        Splits a path into its directory name and file name.

        :param path: The file or directory path.
        :return: A 2-element tuple containing (directory name, file name).
        """
        return os.path.split(path)

    @overload
    def join_path(self, *paths: Union[str, Path]) -> str:
        ...

    @overload
    def join_path(self, *paths: bytes) -> bytes:
        ...

    def join_path(self, *paths):
        """
        Safely joins path components.

        :param paths: Path components to join.
        :return: The joined path string.
        """
        return os.path.join(*paths)

    # --- Shell Command Execution API ---
    def __call__(self,
                 command: str, *,
                 print_output: bool = True,
                 text: bool = True,
                 input: Union[str, bytes, None] = None,
                 timeout: Union[int, float, None] = None,
                 fail_on_error: bool = True) -> subprocess.CompletedProcess:
        """
        Executes a shell command using `shell=True`. Recommended for commands
        that require shell features like pipes or wildcards.

        :param command: The command string to execute.
        :param print_output: If True, streams stdout and stderr to the console.
        :param text: If True, output is decoded as text.
        :param input: Data to be sent to the child process.
        :param timeout: Timeout in seconds.
        :param fail_on_error: If True, raises a subprocess.CalledProcessError on failure.
        :return: A subprocess.CompletedProcess object.
        """
        print(color(command))
        return subprocess.run(
                command,
                shell=True,
                check=fail_on_error,
                capture_output=not print_output,
                text=text,
                input=input,
                timeout=timeout
                )

    def safe_run(self,
                 command: List[str], *,
                 print_output: bool = True,
                 text: bool = True,
                 input: Union[str, bytes, None] = None,
                 timeout: Union[int, float, None] = None,
                 fail_on_error: bool = True) -> subprocess.CompletedProcess:
        """
        Executes a command securely, without a shell. Use for commands with
        untrusted user input to prevent shell injection.

        :param command: The command as a list of strings (e.g., ['rm', 'file.txt']).
        :param print_output: If True, streams stdout and stderr to the console.
        :param text: If True, output is decoded as text.
        :param input: Data to be sent to the child process.
        :param timeout: Timeout in seconds.
        :param fail_on_error: If True, raises a subprocess.CalledProcessError on failure.
        :return: A subprocess.CompletedProcess object.
        """
        if not isinstance(command, list):
            raise TypeError("Command must be a list of strings to ensure security.")

        print(color(f"Securely execute: {command}"))
        return subprocess.run(
                command,
                shell=False,
                check=fail_on_error,
                capture_output=not print_output,
                text=text,
                input=input,
                timeout=timeout
                )

    # --- Script Control API ---
    def pause(self, msg: Optional[str] = None) -> None:
        """
        Prompts the user to press any key to continue.

        :param msg: The message to print.
        """
        if msg:
            print(color(msg))
        print(color("Press any key to continue..."), end="", flush=True)

        if os.name == 'nt':
            import msvcrt
            msvcrt.getch()
        else:
            import termios, tty
            fd = sys.stdin.fileno()
            old = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
        print()

    def ask_choice(self, title: str, *choices: str) -> int:
        """
        Displays a menu and gets a choice from the user.

        :param title: The title for the menu.
        :param choices: The choices as strings.
        :return: The 1-based index of the user's choice.
        """
        if not choices:
            raise ValueError("Must have at least one choice.")

        print(color(title))
        for i, choice in enumerate(choices, 1):
            print(color(f"{i}, {choice}"))

        while True:
            answer = input(color("Please choose: "))
            try:
                index = int(answer)
            except ValueError:
                print(color("Invalid input. Please input a number."))
                continue

            if 1 <= index <= len(choices):
                return index
            print(color(f"Invalid choice. Please input a number from 1 to {len(choices)}."))

    def ask_yes_no(self, title: str) -> bool:
        """
        Ask user to answer yes or no.

        :param title: The message to display.
        :return: True for yes, False for no.
        """
        print(color(title))
        while True:
            answer = input(color("Please answer yes(y) or no(n): ")).strip().lower()
            if answer in ("yes", "y"):
                return True
            elif answer in ("no", "n"):
                return False
            print(color("Invalid answer. Please input yes/y/no/n."))

    def exit(self, exit_code: int = 0) -> None:
        """
        Exits the script with a specified exit code.

        :param exit_code: The exit code, defaults to 0.
        """
        sys.exit(exit_code)

    def get_username(self) -> str:
        """
        Get the current username.

        On Linux, if running a script with sudo, return `root`.
        """
        if os.name == "posix":  # macOS, Linux, etc.
            try:
                import pwd
                uid = os.getuid()
                return pwd.getpwuid(uid).pw_name
            except:
                pass
        elif os.name == "nt":  # Windows
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Volatile Environment')
                username, _ = winreg.QueryValueEx(key, 'USERNAME')
                winreg.CloseKey(key)
                return username
            except:
                pass

        # Fall back to environment variable
        for name in ('LOGNAME', 'USER', 'LNAME', 'USERNAME'):
            username = os.environ.get(name)
            if username:
                return username
        raise RuntimeError("Unable to get the current username.")

    def is_elevated(self) -> bool:
        """
        Checks if the script is running with elevated (admin/root) privileges.
        """
        if os.name == "posix": # macOS, Linux, etc.
            return os.geteuid() == 0
        elif os.name == "nt":  # Windows
            try:
                import ctypes
                return bool(ctypes.windll.shell32.IsUserAnAdmin())
            except:
                pass

        raise RuntimeError(f"Unable to get privilege status.")

    def get_preferred_encoding(self) -> str:
        """
        Returns the preferred encoding for the current locale.

        This is useful for decoding subprocess output or files
        that don't specify an encoding.
        """
        import locale
        try:
            return locale.getpreferredencoding(False)
        except:
            # Fallback for systems where locale module might fail.
            return sys.getdefaultencoding()

    def get_filesystem_encoding(self) -> str:
        """
        Returns the encoding used by the operating system for filenames.
        """
        return FS_ENCODING

    # Operating system constants
    OS_Windows = 1
    OS_Cygwin = 2
    OS_Linux = 4
    OS_macOS = 8
    OS_Unix = 16
    OS_Unix_like = (OS_Cygwin | OS_Linux | OS_macOS | OS_Unix)

    _CURRENT_OS = None

    @classmethod
    def _get_current_os(cls):
        """
        Internal method to initialize the current operating system value.
        """
        if sys.platform == "win32":
            cls._CURRENT_OS = cls.OS_Windows
        elif sys.platform == "linux":
            cls._CURRENT_OS = cls.OS_Linux
        elif sys.platform == "darwin":
            cls._CURRENT_OS = cls.OS_macOS
        elif sys.platform == "cygwin":
            cls._CURRENT_OS = cls.OS_Cygwin
        else: # Unknown OS
            if os.name == "posix":
                cls._CURRENT_OS = cls.OS_Unix
            else:
                cls._CURRENT_OS = 0

    def is_os(self, os_mask: int) -> bool:
        """
        Test whether it's the operating system specified by the parameter.

        :param os_mask: Can be sh.OS_Windows, sh.OS_Cygwin, sh.OS_Linux,
                        sh.OS_macOS, sh.OS_Unix, sh.OS_Unix_like.
                        Support bit OR (|) combination.
        """
        if self._CURRENT_OS is None:
            self._get_current_os()
        return bool(os_mask & self._CURRENT_OS) # type: ignore

sh = Shell()