### shell-lib

`shell-lib` is designed to simplify the writing of Shell-like scripts.

This module was co-created with Google Gemini.

### Why shell-lib?

- **Clean and Readable Syntax**: Write scripts in readable Python, freeing from complex shell command syntax.
- **Reliable Error Handling**: Use Python's exception to manage command failure. If a command fails, by default, it raises a `subprocess.CalledProcessError` exception. For commands that may fail, user can also only check the exit-code.
- **Unified File System Operations**: Provide a consistent and intuitive file system operations API, that clearly distinguish between file and directory operations.
- **Cross-Platform Compatibility**: Write a single script that works across Linux, macOS, and Windows platforms.
- **Rich Ecosystem Integration**: Easily integrate with both the CLI tool and Python library ecosystems.
- **Lightweight and Portable**: Only uses Python standard library.

### Usage

```python
#!/usr/bin/python3
from shell_lib import sh

PROJECT_PATH = "my_project"
FILE = "hello.txt"

# `with sh:` is a *top-level* context manager.
# Its main purpose is, if `sh()` or `sh.safe_run()` fails, return the error
# exit-code from the command. If you don't need this, don't use it.
with sh:
    sh.create_dir(PROJECT_PATH)
    # sh.cd() context manager restores the previous working directory when
    # exiting the code block, even if an exception raised within the code block.
    with sh.cd(PROJECT_PATH):
        sh(f"echo 'Hello, World!' > {FILE}")
        print(f"File size: {sh.get_path_info(FILE).size} bytes")
    sh.remove_dir(PROJECT_PATH)
```

### API Reference


#### File and Directory Operations

Path parameters can be `str`, `bytes` or `pathlib.Path` object.

- `sh.home_dir() -> Path`: Gets the current user's home directory, a `pathlib.Path` object.
- `sh.path(path) -> Path`: Converts a `str`/`bytes` path to a `pathlib.Path` object. Can utilize the rich features of [pathlib module](https://docs.python.org/3/library/pathlib.html).

- `sh.create_dir(path, *, exist_ok=False)`: Creates a directory.
- `sh.remove_file(path, *, ignore_missing=False)`: Removes a file.
- `sh.remove_dir(path, *, ignore_missing=False)`: Recursively removes a directory.
- `sh.clear_dir(path) -> None`: Clear the contents of a directory.
- `sh.copy_file(src, dst, *, remove_existing_dst=False)`: Copies a file.
- `sh.copy_dir(src, dst, *, remove_existing_dst=False)`: Copies a directory.
- `sh.move_file(src, dst, *, remove_existing_dst=False)`: Moves a file.
- `sh.move_dir(src, dst, *, remove_existing_dst=False)`: Moves a directory.
- `sh.rename_file(src, dst)`: Renames a file.
- `sh.rename_dir(src, dst)`: Renames a directory.

- `sh.list_dir(path)`: Lists all entry names within a directory.
- `sh.walk_dir(path, top_down=True)`: A generator that traverses a directory tree, yield a tuple(directory_path, file_name).
- `sh.cd(path: str|bytes|Path|None)`: Changing the working directory. Can be used as a context manager.

- `sh.split_path(path)`: [os.path.split()](https://docs.python.org/3/library/os.path.html#os.path.split) alias.
- `sh.join_path(*paths)`: [os.path.join()](https://docs.python.org/3/library/os.path.html#os.path.join) alias.

- `sh.path_exists(path) -> bool`: Checks if a path exists.
- `sh.is_file(path) -> bool`: Checks if a path is a file.
- `sh.is_dir(path) -> bool`: Checks if a path is a directory.
- `sh.get_path_info(path) -> PathInfo`: Retrieves detailed information about an existing file or directory:

```
>>> sh.get_path_info('/usr/bin/')  # directory
PathInfo(path=/usr/bin/, size=69632, ctime=2025-09-13 09:05:36.561248,
mtime=2025-09-13 09:05:36.561248, atime=2025-09-14 09:31:12.406677,
is_dir=True, is_file=False, is_link=False, permissions=755)

>>> sh.get_path_info('/usr/bin/python3')  # file
PathInfo(path=/usr/bin/python3, size=8021824, ctime=2025-08-29 13:12:47.657879,
mtime=2025-08-15 01:47:21, atime=2025-09-13 13:40:22.696961,
is_dir=False, is_file=True, is_link=True, permissions=755)
```

#### Shell Command Execution

Executes a command with `shell=True`. Allows shell features like pipes (|) or redirection (>).
```
sh(command: str, *,
   text: bool = True,
   input: str|bytes|None = None,
   timeout: int|float|None = None,
   print_output: bool = True,
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
            text: bool = True,
            input: str|bytes|None = None,
            timeout: int|float|None = None,
            print_output: bool = True,
            fail_on_error: bool = True) -> subprocess.CompletedProcess
```

#### Script Control

- `sh.pause(msg: str|None = None) -> None`: Prompts the user to press any key to continue.
- `sh.ask_choice(title: str, *choices: str) -> int`: Displays a menu and gets a 1-based index from the user's choice.
- `sh.ask_yes_no(title: str) -> bool`: Asks user to answer yes or no.
- `sh.ask_regex_input(title: str, pattern: str, *, print_pattern: bool = False) -> re.Match`: Ask user to input a string, and verify it with a regex pattern.
- `sh.exit(exit_code: int = 0)`: Exits the script with a specified exit code.

#### Get system information

- `sh.get_preferred_encoding() -> str`: Get the preferred encoding for the current locale.
- `sh.get_filesystem_encoding() -> str`: Get the encoding used by the OS for filenames.
- `sh.get_username() -> str`: Get the current username. On Linux, if running a script with `sudo -E ./script.py`, return `root`. To get the username in this case, use: `sh.home_dir().name`
- `sh.is_elevated() -> bool`: If the script is running with elevated (admin/root) privilege.
- `sh.is_os(os_mask: int) -> bool`: Test whether it's the OS specified by the parameter.

```
# os_mask can be:
sh.OS_Windows
sh.OS_Cygwin
sh.OS_Linux
sh.OS_macOS
sh.OS_Unix
sh.OS_Unix_like  # It's (OS_Cygwin | OS_Linux | OS_macOS | OS_Unix)

# Support bit OR (|) combination:
if sh.is_os(sh.OS_Linux | sh.OS_macOS):
    ...
elif sh.is_os(sh.OS_Windows):
    ...
```
