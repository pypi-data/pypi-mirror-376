### shell-lib

`shell-lib` is designed to simplify the writing of Shell-like scripts.

This module was co-created with Google Gemini.

### Why shell-lib?

- **Clean and Readable Syntax**: Write scripts in readable Python, freeing from complex shell command syntax.
- **Reliable Error Handling**: Leverage Python's robust exception handling to manage errors, eliminating the need for tedious `$?` or set `-e` checks. When a command fails, it raises a `subprocess.CalledProcessError`, which you can handle gracefully like any other Python exception.
- **Unified File System Operations**: Provides a consistent and intuitive API for common file system operations.
- **Cross-Platform Compatibility**: Write a single script that works across Linux, macOS, and Windows platforms.
- **Rich Ecosystem Integration**: Easily integrate with both the CLI tool and Python library ecosystems.
- **Lightweight and Portable**: Only uses Python standard library.

### Usage

```python
#!/usr/bin/python3
from shell_lib import sh

# `with sh:` context:
# This is a top-level context manager for handling unhandled exceptions.
# If an exception occurs within the `with` block, the program will automatically exit
# with a non-zero status code.
# Specifically, if `sh()` or `sh.safe_run()` fails, it returns the error exit code from the command.
#
# If you want to handle exceptions yourself and prevent the program from exiting, do not use this context manager.
FILE = "hello.txt"
with sh:
    # `sh.path()` returns a pathlib.Path object for easy cross-platform path manipulation.
    project_path = sh.path("my_project")
    sh.create_dir(project_path)

    # `with sh.cd():` is a directory change context manager.
    # It changes to the specified directory and returns to the previous directory upon exiting,
    # regardless of whether an exception occurred.
    with sh.cd(project_path):
        # Use sh() to run commands, allow shell features like pipes or redirection.
        sh(f"echo 'Hello, World!' > {FILE}")
        print(f"File size: {sh.get_path_info(FILE).size} bytes")

    sh.remove_dir(project_path)
```

### API Reference


#### File and Directory Operations

Path parameters can be `str`, `bytes` or `pathlib.Path` object.

- `sh.home_dir() -> Path`: Gets the current user's home directory, a `pathlib.Path` object.
- `sh.path(path) -> Path`: Converts a `str`/`bytes` path to a `pathlib.Path` object.

- `sh.create_dir(path, *, exist_ok=False)`: Creates a directory.
- `sh.remove_file(path, *, ignore_missing=False)`: Removes a file.
- `sh.remove_dir(path, *, ignore_missing=False)`: Recursively removes a directory.
- `sh.copy_file(src, dst, *, replace_existing=False)`: Copies a file.
- `sh.copy_dir(src, dst, *, replace_existing=False)`: Copies a directory.
- `sh.move_file(src, dst, *, replace_existing=False)`: Moves a file.
- `sh.move_dir(src, dst, *, replace_existing=False)`: Moves a directory.
- `sh.rename_file(src, dst)`: Renames a file.
- `sh.rename_dir(src, dst)`: Renames a directory.

- `sh.list_dir(path)`: Lists all entry names within a directory.
- `sh.walk_dir(top_dir)`: A generator that traverses a directory tree, yield a tuple(directory_path, file_name).
- `sh.cd(path: str|bytes|Path|None)`: Changing the working directory. Can be used as a context manager.

- `sh.split_path(path)`: [os.path.split()](https://docs.python.org/3/library/os.path.html#os.path.split) alias.
- `sh.join_path(*paths)`: [os.path.join()](https://docs.python.org/3/library/os.path.html#os.path.join) alias.

- `sh.path_exists(path) -> bool`: Checks if a path exists.
- `sh.is_file(path) -> bool`: Checks if a path is a file.
- `sh.is_dir(path) -> bool`: Checks if a path is a directory.
- `sh.get_path_info(path) -> PathInfo`: Retrieves detailed information about an existing file or directory:

```
>>> sh.get_path_info('/usr/bin/')  # directory
PathInfo(path=/usr/bin/, size=69632, ctime=2025-09-10 07:40:50.176999,
mtime=2025-09-10 07:40:50.176999, atime=2025-09-10 07:41:00.214666,
is_dir=True, is_file=False, permissions=755)

>>> sh.get_path_info('/usr/bin/python3')  # file
PathInfo(path=/usr/bin/python3, size=8021824, ctime=2025-08-29 13:12:47.657879,
mtime=2025-08-15 01:47:21, atime=2025-09-09 10:52:05.785934,
is_dir=False, is_file=True, permissions=755)
```

#### Shell Command Execution

Executes a command with `shell=True`. Use this for commands that require shell features like pipes (|) or redirection (>).
```
sh(command: str, *,
   print_output: bool = True,
   text: bool = True,
   input: str|bytes|None = None,
   timeout: int|float|None = None,
   fail_on_error: bool = True) -> subprocess.CompletedProcess

print_output:
    True: streams stdout and stderr to the console.
    False: stdout and stderr are saved in return value's `stdout`/`stderr` attributes.
fail_on_error:
    True: raises a subprocess.CalledProcessError on failure.
    False: doesn't raise exception, need to check return value's `returncode` attribute
           to see if it has failed.
```

Securely executes a command with `shell=False`. It only accepts a list of strings to prevent Shell injection. Use this method when the command contains external input.
```
sh.safe_run(command: list[str], *,
            print_output: bool = True,
            text: bool = True,
            input: str|bytes|None = None,
            timeout: int|float|None = None,
            fail_on_error: bool = True) -> subprocess.CompletedProcess
```

#### Script Control

- `sh.pause(msg: str|None = None) -> None`: Prompts the user to press any key to continue.
- `sh.ask_choice(title: str, *choices: str) -> int`: Displays a menu and gets a 1-based index from the user's choice.
- `sh.ask_yes_no(title: str) -> bool`: Asks user to answer yes or no.
- `sh.exit(exit_code: int = 0)`: Exits the script with a specified exit code.

#### Get system information

- `sh.get_preferred_encoding() -> str`: Get the preferred encoding for the current locale.
- `sh.get_filesystem_encoding() -> str`: Get the encoding used by the OS for filenames.
- `sh.get_username() -> str`: Get the current username. On Linux, if running a script with sudo, return `root`, to get the username in this case, use: `sh.split_path(sh.home_dir())[1]`
- `sh.is_elevated() -> bool`: If the script is running with elevated (admin/root) privilege.
- `sh.is_os(os_mask: int) -> bool`: Test whether it's the OS specified by the parameter.

```
# os_mask can be:
sh.OS_Windows
sh.OS_Windows_Cygwin
sh.OS_Linux
sh.OS_macOS
sh.OS_Unix
sh.OS_Unix_like  # It's (OS_Windows_Cygwin | OS_Linux | OS_macOS | OS_Unix)

# Support bit OR (|) combination:
if sh.is_os(sh.OS_Linux | sh.OS_macOS):
    ...
elif sh.is_os(sh.OS_Windows):
    ...
```
