import functools
import unittest
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
from shell_lib.shell_lib import Shell, PathInfo

def optional_exception(exception_type, expected_message):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                func(self, *args, **kwargs)
            except exception_type as e:
                self.assertIn(expected_message, str(e))
                print((f"\n{func.__name__} raised expected exception: "
                       f"{exception_type} {e}"))
            except:
                raise
        return wrapper
    return decorator

def path2bytes(path):
    assert isinstance(path, Path)
    s = str(path)
    return s.encode(sys.getfilesystemencoding())

class TestShell(unittest.TestCase):
    def setUp(self):
        """
        Set up a temporary directory and a Shell instance for testing.
        """
        self.sh = Shell()
        self.test_dir = Path(tempfile.mkdtemp())
        self.file_path = self.test_dir / 'test_file.txt'
        self.dir_path = self.test_dir / 'test_dir'
        self.sub_file_path = self.dir_path / 'sub_file.txt'

        # Create some files and directories for testing
        with open(self.file_path, 'w') as f:
            f.write("Hello, World!")
        os.makedirs(self.dir_path, exist_ok=True)
        with open(self.sub_file_path, 'w') as f:
            f.write("Sub file content.")

        # Reset the cached OS value before each test
        Shell._CURRENT_OS = None

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_set_attr(self):
        with self.assertRaises(AttributeError):
            self.sh.aaa = 123
        with self.assertRaises(AttributeError):
            self.sh.OS_Linux = 123

    # --- File and Directory Operations API Tests ---
    def test_path_converts_to_pathlib(self):
        self.assertEqual(self.sh.path(self.file_path), self.file_path)
        self.assertEqual(self.sh.path(str(self.file_path)), self.file_path)
        self.assertEqual(self.sh.path(path2bytes(self.file_path)), self.file_path)

    def test_create_remove_dir(self):
        # create Path -----------
        path_dir = self.test_dir / 'new_dir'
        self.sh.create_dir(path_dir)
        self.assertTrue(os.path.isdir(path_dir))

        # create str
        str_dir = str(self.test_dir / 'str_dir')
        self.sh.create_dir(str_dir)
        self.assertTrue(os.path.isdir(str_dir))

        # create bytes
        bytes_dir = path2bytes(self.test_dir / 'bytes_dir')
        self.sh.create_dir(bytes_dir)
        self.assertTrue(os.path.isdir(bytes_dir))

        # remove Path -----------
        self.sh.remove_dir(path_dir)
        self.assertFalse(os.path.exists(path_dir))

        # remove str
        self.sh.remove_dir(str_dir)
        self.assertFalse(os.path.exists(str_dir))

        # remove bytes
        self.sh.remove_dir(bytes_dir)
        self.assertFalse(os.path.exists(bytes_dir))

    def test_create_dir_exist_ok(self):
        # keyword only arg
        with self.assertRaises(TypeError):
            self.sh.create_dir(self.dir_path, True)

        # exist
        with self.assertRaises(FileExistsError):
            self.sh.create_dir(self.dir_path, exist_ok=False)

        self.sh.create_dir(self.dir_path, exist_ok=True)
        self.assertTrue(os.path.isdir(self.dir_path))

        # no exist
        new_dir = self.test_dir / 'new_dir'
        self.sh.create_dir(new_dir, exist_ok=True)
        self.assertTrue(os.path.isdir(new_dir))

    def test_remove_dir_ignore_missing(self):
        # keyword only arg
        with self.assertRaises(TypeError):
            self.sh.remove_dir(self.dir_path, True)

        # exist
        self.sh.remove_dir(self.dir_path, ignore_missing=True)
        self.assertFalse(os.path.exists(self.dir_path))

        # no exist
        non_existent_dir = self.test_dir / 'non_existent_dir'
        with self.assertRaises(FileNotFoundError):
            self.sh.remove_dir(non_existent_dir, ignore_missing=False)

        self.sh.remove_dir(non_existent_dir, ignore_missing=True)
        self.assertFalse(os.path.exists(non_existent_dir))

    def test_remove_file(self):
        for i in range(3):
            with open(self.dir_path / str(i), 'wb') as f:
                f.write(b'123')

        # Path
        path_file = self.dir_path / '0'
        self.sh.remove_file(path_file)
        self.assertFalse(os.path.exists(path_file))

        # str
        str_file = str(self.dir_path / '1')
        self.sh.remove_file(str_file)
        self.assertFalse(os.path.exists(str_file))

        # bytes
        bytes_file = path2bytes(self.dir_path / '2')
        self.sh.remove_file(bytes_file)
        self.assertFalse(os.path.exists(bytes_file))

    def test_remove_file_ignore_missing(self):
        # keyword only arg
        with self.assertRaises(TypeError):
            self.sh.remove_file(self.dir_path, True)

        # exist
        self.sh.remove_file(self.file_path, ignore_missing=True)
        self.assertFalse(os.path.exists(self.file_path))

        # no exist
        non_existent_file = self.test_dir / 'non_existent_file.txt'
        with self.assertRaises(FileNotFoundError):
            self.sh.remove_file(non_existent_file, ignore_missing=False)

        self.sh.remove_file(non_existent_file, ignore_missing=True)
        self.assertFalse(os.path.exists(non_existent_file))

    def test_copy_file(self):
        # Path
        path_1 = self.test_dir / '1.txt'
        self.sh.copy_file(self.file_path, path_1)
        self.assertTrue(os.path.isfile(path_1))
        with open(path_1, 'r') as f:
            self.assertEqual(f.read(), "Hello, World!")

        # str
        path_2 = self.test_dir / '2.txt'
        self.sh.copy_file(str(path_1), str(path_2))
        self.assertTrue(os.path.isfile(path_2))
        with open(path_2, 'r') as f:
            self.assertEqual(f.read(), "Hello, World!")

        # bytes
        path_3 = self.test_dir / '3.txt'
        self.sh.copy_file(path2bytes(path_2), path2bytes(path_3))
        self.assertTrue(os.path.isfile(path_3))
        with open(path_3, 'r') as f:
            self.assertEqual(f.read(), "Hello, World!")

    def test_copy_file_replace_existing(self):
        dst_path = self.test_dir / 'copied_file.txt'
        with open(dst_path, 'w') as f:
            f.write('copied_file')

        # keyword only arg
        with self.assertRaises(TypeError):
            self.sh.copy_file(self.file_path, dst_path, True)

        # exist
        with self.assertRaises(FileExistsError):
            self.sh.copy_file(self.file_path, dst_path, replace_existing=False)

        self.sh.copy_file(self.file_path, dst_path, replace_existing=True)
        with open(dst_path, 'r') as f:
            self.assertEqual(f.read(), "Hello, World!")

        # no exist
        no_exist_path = self.test_dir / 'newfile.txt'
        self.sh.copy_file(self.file_path, no_exist_path, replace_existing=True)
        with open(no_exist_path, 'r') as f:
            self.assertEqual(f.read(), "Hello, World!")

    def test_copy_dir(self):
        # Path
        path_1 = self.test_dir / '1'
        path_path = path_1
        self.sh.copy_dir(self.dir_path, path_path)
        self.assertTrue(os.path.isdir(path_path))
        self.assertTrue(os.path.isfile(path_path / 'sub_file.txt'))

        # str
        path_2 = self.test_dir / '2'
        str_path = str(path_2)
        self.sh.copy_dir(str(self.dir_path), str_path)
        self.assertTrue(os.path.isdir(str_path))
        self.assertTrue(os.path.isfile(path_2 / 'sub_file.txt'))

        # bytes
        path_3 = self.test_dir / '3'
        bytes_path = path2bytes(path_3)
        self.sh.copy_dir(path2bytes(self.dir_path), bytes_path)
        self.assertTrue(os.path.isdir(bytes_path))
        self.assertTrue(os.path.isfile(path_3 / 'sub_file.txt'))

    def test_copy_dir_replace_existing(self):
        dst_path = self.test_dir / 'copied_dir'
        os.makedirs(dst_path, exist_ok=True)
        with open(dst_path / 'existing.txt', 'w') as f:
            f.write('existing content')

        # exist
        with self.assertRaises(FileExistsError):
            self.sh.copy_dir(self.dir_path, dst_path, replace_existing=False)
        self.assertTrue(os.path.exists(dst_path / 'existing.txt'))
        self.assertFalse(os.path.exists(dst_path / 'sub_file.txt'))

        # overwrite
        self.sh.copy_dir(self.dir_path, dst_path, replace_existing=True)
        self.assertTrue(os.path.isdir(dst_path))
        self.assertTrue(os.path.isfile(dst_path / 'sub_file.txt'))
        self.assertFalse(os.path.exists(dst_path / 'existing.txt'))

        # no exist
        no_exist_path = self.test_dir / 'new_dir'
        self.sh.copy_dir(self.dir_path, no_exist_path, replace_existing=True)
        self.assertTrue(os.path.isdir(no_exist_path))
        self.assertTrue(os.path.isfile(no_exist_path / 'sub_file.txt'))

    def test_move_file(self):
        # Path
        path_1 = self.test_dir / '1.txt'
        self.sh.move_file(self.file_path, path_1)
        self.assertFalse(os.path.exists(self.file_path))
        self.assertTrue(os.path.exists(path_1))
        with open(path_1, 'r') as f:
            self.assertEqual(f.read(), "Hello, World!")

        # str
        path_2 = self.test_dir / '2.txt'
        self.sh.move_file(str(path_1), str(path_2))
        self.assertFalse(os.path.exists(path_1))
        self.assertTrue(os.path.exists(path_2))
        with open(path_2, 'r') as f:
            self.assertEqual(f.read(), "Hello, World!")

        # bytes
        path_3 = self.test_dir / '3.txt'
        self.sh.move_file(path2bytes(path_2), path2bytes(path_3))
        self.assertFalse(os.path.exists(path_2))
        self.assertTrue(os.path.exists(path_3))
        with open(path_3, 'r') as f:
            self.assertEqual(f.read(), "Hello, World!")

    def test_move_file_replace_existing(self):
        dst_path = self.test_dir / 'moved_file.txt'
        with open(dst_path, 'w') as f:
            f.write('moved_file')

        # keyword only arg
        with self.assertRaises(TypeError):
            self.sh.move_file(self.file_path, dst_path, True)

        # exist
        with self.assertRaises(FileExistsError):
            self.sh.move_file(self.file_path, dst_path, replace_existing=False)

        # overwrite
        self.sh.move_file(self.file_path, dst_path, replace_existing=True)
        self.assertFalse(os.path.exists(self.file_path))
        with open(dst_path, 'r') as f:
            self.assertEqual(f.read(), "Hello, World!")

        # no exist
        no_exist_path = self.test_dir / 'newfile.txt'
        self.sh.move_file(dst_path, no_exist_path, replace_existing=True)
        self.assertFalse(os.path.exists(dst_path))
        self.assertTrue(os.path.exists(no_exist_path))

    def test_move_dir(self):
        # Path
        dst_path_1 = self.test_dir / 'moved_dir_1'
        self.sh.move_dir(self.dir_path, dst_path_1)
        self.assertFalse(os.path.exists(self.dir_path))
        self.assertTrue(os.path.exists(dst_path_1))
        self.assertTrue(os.path.exists(dst_path_1 / 'sub_file.txt'))

        # str
        src_path_2 = dst_path_1
        dst_path_2 = self.test_dir / 'moved_dir_2'
        self.sh.move_dir(str(src_path_2), str(dst_path_2))
        self.assertFalse(os.path.exists(src_path_2))
        self.assertTrue(os.path.exists(dst_path_2))
        self.assertTrue(os.path.exists(dst_path_2 / 'sub_file.txt'))

        # bytes
        src_path_3 = dst_path_2
        dst_path_3 = self.test_dir / 'moved_dir_3'
        self.sh.move_dir(path2bytes(src_path_3), path2bytes(dst_path_3))
        self.assertFalse(os.path.exists(src_path_3))
        self.assertTrue(os.path.exists(dst_path_3))
        self.assertTrue(os.path.exists(dst_path_3 / 'sub_file.txt'))

    def test_move_dir_replace_existing(self):
        src = self.test_dir / 'src'
        dst = self.test_dir / 'dst'
        os.makedirs(src)
        os.makedirs(dst)

        # keyword only arg
        with self.assertRaises(TypeError):
            self.sh.move_dir(src, dst, True)

        # exist
        self.sh.move_dir(src, dst, replace_existing=True)
        self.assertTrue(os.path.exists(dst))
        self.assertFalse(os.path.exists(src))

        # no exist
        self.sh.create_dir(src)
        self.sh.remove_dir(dst)
        self.sh.move_dir(src, dst, replace_existing=True)
        self.assertTrue(os.path.exists(dst))
        self.assertFalse(os.path.exists(src))

    def test_move_dir_no_replace_existing(self):
        # exist
        src = self.test_dir / 'src'
        dst = self.test_dir / 'dst'
        os.makedirs(src)
        os.makedirs(dst)
        with self.assertRaises(FileExistsError):
            self.sh.move_dir(src, dst, replace_existing=False)

        # no exist
        self.sh.remove_dir(dst)
        self.sh.move_dir(src, dst, replace_existing=False)
        self.assertTrue(os.path.exists(dst))
        self.assertFalse(os.path.exists(src))

    def test_move_dir_remove_existing_types(self):
        # Path
        src_path = self.test_dir / 'src_path'
        dst_path = self.test_dir / 'dst_path'
        os.makedirs(src_path, exist_ok=True)
        os.makedirs(dst_path, exist_ok=True)
        self.sh.move_dir(src_path, dst_path, replace_existing=True)
        self.assertFalse(os.path.exists(src_path))
        self.assertTrue(os.path.exists(dst_path))

        # str
        src_str = str(self.test_dir / 'src_str')
        dst_str = str(self.test_dir / 'dst_str')
        os.makedirs(src_str, exist_ok=True)
        os.makedirs(dst_str, exist_ok=True)
        self.sh.move_dir(src_str, dst_str, replace_existing=True)
        self.assertFalse(os.path.exists(src_str))
        self.assertTrue(os.path.exists(dst_str))

        # bytes
        src_bytes = path2bytes(self.test_dir / 'src_bytes')
        dst_bytes = path2bytes(self.test_dir / 'dst_bytes')
        os.makedirs(src_bytes, exist_ok=True)
        os.makedirs(dst_bytes, exist_ok=True)
        self.sh.move_dir(src_bytes, dst_bytes, replace_existing=True)
        self.assertFalse(os.path.exists(src_bytes))
        self.assertTrue(os.path.exists(dst_bytes))

    def test_rename_file(self):
        # Path
        new_path_1 = self.test_dir / 'renamed_file_1.txt'
        self.sh.rename_file(self.file_path, new_path_1)
        self.assertFalse(os.path.exists(self.file_path))
        self.assertTrue(os.path.exists(new_path_1))
        with open(new_path_1, 'r') as f:
            self.assertEqual(f.read(), "Hello, World!")

        # str
        new_path_2 = self.test_dir / 'renamed_file_2.txt'
        self.sh.rename_file(str(new_path_1), str(new_path_2))
        self.assertFalse(os.path.exists(new_path_1))
        self.assertTrue(os.path.exists(new_path_2))
        with open(new_path_2, 'r') as f:
            self.assertEqual(f.read(), "Hello, World!")

        # bytes
        new_path_3 = self.test_dir / 'renamed_file_3.txt'
        self.sh.rename_file(path2bytes(new_path_2), path2bytes(new_path_3))
        self.assertFalse(os.path.exists(new_path_2))
        self.assertTrue(os.path.exists(new_path_3))
        with open(new_path_3, 'r') as f:
            self.assertEqual(f.read(), "Hello, World!")

    def test_rename_dir(self):
        # Path
        new_path_1 = self.test_dir / 'renamed_dir_1'
        self.sh.rename_dir(self.dir_path, new_path_1)
        self.assertFalse(os.path.exists(self.dir_path))
        self.assertTrue(os.path.exists(new_path_1))
        self.assertTrue(os.path.exists(new_path_1 / 'sub_file.txt'))

        # str
        new_path_2 = self.test_dir / 'renamed_dir_2'
        self.sh.rename_dir(str(new_path_1), str(new_path_2))
        self.assertFalse(os.path.exists(new_path_1))
        self.assertTrue(os.path.exists(new_path_2))
        self.assertTrue(os.path.exists(new_path_2 / 'sub_file.txt'))

        # bytes
        new_path_3 = self.test_dir / 'renamed_dir_3'
        self.sh.rename_dir(path2bytes(new_path_2), path2bytes(new_path_3))
        self.assertFalse(os.path.exists(new_path_2))
        self.assertTrue(os.path.exists(new_path_3))
        self.assertTrue(os.path.exists(new_path_3 / 'sub_file.txt'))

    def test_get_path_info_for_file(self):
        info = self.sh.get_path_info(self.file_path)
        self.assertIsInstance(info, PathInfo)
        self.assertEqual(info.path, str(self.file_path))
        self.assertTrue(info.is_file)
        self.assertFalse(info.is_dir)
        self.assertIsInstance(info.size, int)
        self.assertRegex(repr(info),
                         (r"PathInfo\(path=.*?, size=.*?, "
                          r"ctime=.*?, mtime=.*?, atime=.*?, "
                          r"is_dir=.*?, is_file=.*?, permissions=.*?\)"))

        with self.assertRaises(FileNotFoundError):
            self.sh.get_path_info(self.test_dir / 'non_existent')

    def test_list_dir(self):
        # Path
        contents = self.sh.list_dir(self.test_dir)
        self.assertIn('test_file.txt', contents)
        self.assertIn('test_dir', contents)
        with self.assertRaises(FileNotFoundError):
            self.sh.list_dir(self.test_dir / 'non_existent')

        # str
        contents = self.sh.list_dir(str(self.test_dir))
        self.assertIn('test_file.txt', contents)
        self.assertIn('test_dir', contents)
        with self.assertRaises(FileNotFoundError):
            self.sh.list_dir(str(self.test_dir / 'non_existent'))

        # bytes
        contents = self.sh.list_dir(path2bytes(self.test_dir))
        self.assertIn(b'test_file.txt', contents)
        self.assertIn(b'test_dir', contents)
        with self.assertRaises(FileNotFoundError):
            self.sh.list_dir(path2bytes(self.test_dir / 'non_existent'))

    def test_walk_dir(self):
        # Path
        contents = list(self.sh.walk_dir(self.test_dir))
        self.assertEqual(len(contents), 2)
        self.assertEqual(type(contents[0]), tuple)
        self.assertEqual(len(contents[0]), 2)
        self.assertEqual(type(contents[0][0]), str)
        tmp = [item[1] for item in contents]
        self.assertIn('test_file.txt', tmp)
        self.assertIn('sub_file.txt', tmp)
        with self.assertRaises(FileNotFoundError):
            list(self.sh.walk_dir(self.test_dir / 'non_existent'))

        # str
        contents = list(self.sh.walk_dir(str(self.test_dir)))
        self.assertEqual(len(contents), 2)
        self.assertEqual(type(contents[0]), tuple)
        self.assertEqual(len(contents[0]), 2)
        self.assertEqual(type(contents[0][0]), str)
        tmp = [item[1] for item in contents]
        self.assertIn('test_file.txt', tmp)
        self.assertIn('sub_file.txt', tmp)
        with self.assertRaises(FileNotFoundError):
            list(self.sh.walk_dir(str(self.test_dir / 'non_existent')))

        # bytes
        contents = list(self.sh.walk_dir(path2bytes(self.test_dir)))
        self.assertEqual(len(contents), 2)
        self.assertEqual(type(contents[0]), tuple)
        self.assertEqual(len(contents[0]), 2)
        self.assertEqual(type(contents[0][0]), bytes)
        tmp = [item[1] for item in contents]
        self.assertIn(b'test_file.txt', tmp)
        self.assertIn(b'sub_file.txt', tmp)
        with self.assertRaises(FileNotFoundError):
            list(self.sh.walk_dir(path2bytes(self.test_dir / 'non_existent')))

    def test_cd_context_manager(self):
        original_cwd = os.getcwd()
        # Path
        with self.sh.cd(self.dir_path):
            self.assertEqual(os.getcwd(), str(self.dir_path))
        self.assertEqual(os.getcwd(), original_cwd)
        # str
        with self.sh.cd(str(self.dir_path)):
            self.assertEqual(os.getcwd(), str(self.dir_path))
        self.assertEqual(os.getcwd(), original_cwd)
        # bytes
        with self.sh.cd(path2bytes(self.dir_path)):
            self.assertEqual(os.getcwd(), str(self.dir_path))
        self.assertEqual(os.getcwd(), original_cwd)

        # None
        with self.sh.cd(None):
            self.sh.cd(self.dir_path)
        self.assertEqual(os.getcwd(), original_cwd)

        # exception
        try:
            with self.sh.cd(self.test_dir):
                self.assertEqual(os.getcwd(), str(self.test_dir))
                raise ValueError("Test Exception")
        except ValueError:
            pass
        self.assertEqual(os.getcwd(), original_cwd)

    def test_path_exists(self):
        # Path/str/bytes types tested below
        self.assertTrue(self.sh.path_exists(self.file_path))
        self.assertFalse(self.sh.path_exists(self.test_dir / 'non_existent'))

    def test_is_file(self):
        # Path
        self.assertTrue(self.sh.is_file(self.file_path))
        self.assertTrue(self.sh.path_exists(self.file_path))
        self.assertFalse(self.sh.is_file(self.dir_path))
        self.assertTrue(self.sh.path_exists(self.test_dir))

        # str
        self.assertTrue(self.sh.is_file(str(self.file_path)))
        self.assertTrue(self.sh.path_exists(str(self.file_path)))
        self.assertFalse(self.sh.is_file(str(self.dir_path)))
        self.assertTrue(self.sh.path_exists(str(self.dir_path)))

        # bytes
        self.assertTrue(self.sh.is_file(path2bytes(self.file_path)))
        self.assertTrue(self.sh.path_exists(path2bytes(self.file_path)))
        self.assertFalse(self.sh.is_file(path2bytes(self.dir_path)))
        self.assertTrue(self.sh.path_exists(path2bytes(self.dir_path)))

    def test_is_dir(self):
        # Path
        self.assertTrue(self.sh.is_dir(self.dir_path))
        self.assertTrue(self.sh.path_exists(self.dir_path))
        self.assertFalse(self.sh.is_dir(self.file_path))
        self.assertTrue(self.sh.path_exists(self.file_path))

        # str
        self.assertTrue(self.sh.is_dir(str(self.dir_path)))
        self.assertTrue(self.sh.path_exists(str(self.dir_path)))
        self.assertFalse(self.sh.is_dir(str(self.file_path)))
        self.assertTrue(self.sh.path_exists(str(self.file_path)))

        # bytes
        self.assertTrue(self.sh.is_dir(path2bytes(self.dir_path)))
        self.assertTrue(self.sh.path_exists(path2bytes(self.dir_path)))
        self.assertFalse(self.sh.is_dir(path2bytes(self.file_path)))
        self.assertTrue(self.sh.path_exists(path2bytes(self.file_path)))

    def test_split_path(self):
        # Path
        parent_dir, filename = self.sh.split_path(self.file_path)
        self.assertEqual(parent_dir, str(self.test_dir))
        self.assertEqual(filename, 'test_file.txt')

        # str
        parent_dir, filename = self.sh.split_path(str(self.file_path))
        self.assertEqual(parent_dir, str(self.test_dir))
        self.assertEqual(filename, 'test_file.txt')

        # bytes
        parent_dir, filename = self.sh.split_path(path2bytes(self.file_path))
        self.assertEqual(parent_dir, path2bytes(self.test_dir))
        self.assertEqual(filename, b'test_file.txt')

    def test_join_path(self):
        # Path
        path_path = self.sh.join_path(self.test_dir, self.sh.path('test_file.txt'))
        self.assertEqual(type(path_path), str) # <- str
        self.assertTrue(self.sh.is_file(path_path))

        # str
        str_path = self.sh.join_path(str(self.test_dir), 'test_file.txt')
        self.assertEqual(type(str_path), str)
        self.assertTrue(self.sh.is_file(str_path))

        # bytes
        bytes_path = self.sh.join_path(path2bytes(self.test_dir), b'test_file.txt')
        self.assertEqual(type(bytes_path), bytes)
        self.assertTrue(self.sh.is_file(bytes_path))

    # --- Shell Command Execution API Tests ---

    @patch('subprocess.run')
    def test_call_executes_shell_command(self, mock_run):
        self.sh("echo hello")
        mock_run.assert_called_once()
        self.assertTrue(mock_run.call_args[0][0].startswith('echo hello'))

    @patch('subprocess.run')
    def test_safe_run_executes_securely(self, mock_run):
        self.sh.safe_run(['ls', '-l'])
        mock_run.assert_called_once()
        self.assertEqual(mock_run.call_args[0][0], ['ls', '-l'])

    @patch('subprocess.run', side_effect=subprocess.CalledProcessError(90, 'cmd'))
    @patch('sys.exit')
    def test_context_manager_exits_on_error(self, mock_exit, mock_run):
        try:
            with self.sh:
                self.sh("bad command")
        except subprocess.CalledProcessError:
            pass
        mock_exit.assert_called_once_with(90)

    # --- Script Control API Mocked Tests ---
    @patch('builtins.input', side_effect=['invalid', '4', '0', '2 '])
    @patch('builtins.print')
    def test_ask_choice(self, mock_print, mock_input):
        choice = self.sh.ask_choice("Choose an option:",
                                     "Option 1", "Option 2", "Option 3")
        self.assertEqual(choice, 2)
        self.assertEqual(mock_input.call_count, 4)

    def test_ask_choice_raises_error_with_no_choices(self):
        with self.assertRaises(ValueError):
            self.sh.ask_choice("Choose an option:")

    @patch('builtins.input', side_effect=['xxx', 'yes',
                                          '', ' YeS ',
                                          '1', 'y ',
                                          'ys', 'yas ', ' Y'])
    @patch('builtins.print')
    def test_ask_yes_no_yes(self, mock_print, mock_input):
        self.assertTrue(self.sh.ask_yes_no("Do you agree?"))
        self.assertTrue(self.sh.ask_yes_no("Do you agree?"))
        self.assertTrue(self.sh.ask_yes_no("Do you agree?"))
        self.assertTrue(self.sh.ask_yes_no("Do you agree?"))
        self.assertEqual(mock_input.call_count, 9)

    @patch('builtins.input', side_effect=['xxx', 'no',
                                          '', ' No ',
                                          '1', 'n ',
                                          'not', ' none', ' N'])
    @patch('builtins.print')
    def test_ask_yes_no_no(self, mock_print, mock_input):
        self.assertFalse(self.sh.ask_yes_no("Do you agree?"))
        self.assertFalse(self.sh.ask_yes_no("Do you agree?"))
        self.assertFalse(self.sh.ask_yes_no("Do you agree?"))
        self.assertFalse(self.sh.ask_yes_no("Do you agree?"))
        self.assertEqual(mock_input.call_count, 9)

    @patch('sys.exit')
    def test_exit(self, mock_exit):
        self.sh.exit(91)
        mock_exit.assert_called_once_with(91)

    # --- Utility and OS-specific Tests ---
    @optional_exception(RuntimeError, 'Unable to get')
    def test_get_username(self):
        self.assertEqual(type(self.sh.get_username()), str)
        if sys.platform == 'linux':
            self.assertEqual(self.sh.get_username(),
                             self.sh.split_path(self.sh.home_dir())[1])

    @optional_exception(RuntimeError, 'Unable to get')
    def test_is_elevated(self):
        self.assertEqual(type(self.sh.is_elevated()), bool)

    def test_get_preferred_encoding(self):
        self.assertEqual(type(self.sh.get_preferred_encoding()), str)

    def test_get_filesystem_encoding(self):
        self.assertEqual(type(self.sh.get_filesystem_encoding()), str)
        self.assertEqual(self.sh.get_filesystem_encoding(),
                         sys.getfilesystemencoding())

    def test_os_constants(self):
        a = ['OS_Windows', 'OS_Cygwin',
             'OS_Linux', 'OS_macOS', 'OS_Unix', 'OS_Unix_like']
        b = [one for one in dir(self.sh)
                 if one.startswith('OS_')]
        a.sort()
        b.sort()
        self.assertEqual(a, b)

        self.assertEqual(self.sh.OS_Windows, 1)
        self.assertEqual(self.sh.OS_Cygwin, 2)
        self.assertEqual(self.sh.OS_Linux, 4)
        self.assertEqual(self.sh.OS_macOS, 8)
        self.assertEqual(self.sh.OS_Unix, 16)
        self.assertEqual(self.sh.OS_Unix_like,
                         self.sh.OS_Cygwin | self.sh.OS_Linux |
                         self.sh.OS_macOS | self.sh.OS_Unix)

    def test_is_os_mock(self):
        with patch('sys.platform', 'win32'):
            self.assertTrue(self.sh.is_os(self.sh.OS_Windows))
            self.assertFalse(self.sh.is_os(self.sh.OS_Cygwin))
            self.assertFalse(self.sh.is_os(self.sh.OS_macOS))
            self.assertFalse(self.sh.is_os(self.sh.OS_Unix_like))

        Shell._CURRENT_OS = None
        with patch('sys.platform', 'linux'):
            self.assertTrue(self.sh.is_os(self.sh.OS_Linux))
            self.assertTrue(self.sh.is_os(self.sh.OS_Unix_like))
            self.assertFalse(self.sh.is_os(self.sh.OS_Windows))

        Shell._CURRENT_OS = None
        with patch('sys.platform', 'darwin'):
            self.assertTrue(self.sh.is_os(self.sh.OS_macOS))
            self.assertTrue(self.sh.is_os(self.sh.OS_Unix_like))
            self.assertFalse(self.sh.is_os(self.sh.OS_Linux))

        Shell._CURRENT_OS = None
        with patch('sys.platform', 'cygwin'):
            self.assertTrue(self.sh.is_os(self.sh.OS_Cygwin))
            self.assertTrue(self.sh.is_os(self.sh.OS_Unix_like))
            self.assertFalse(self.sh.is_os(self.sh.OS_Windows))

        Shell._CURRENT_OS = None
        with patch('sys.platform', 'freebsd'):
            with patch('os.name', 'posix'):
                self.assertTrue(self.sh.is_os(self.sh.OS_Unix))
                self.assertTrue(self.sh.is_os(self.sh.OS_Unix_like))
                self.assertFalse(self.sh.is_os(self.sh.OS_Linux))

if __name__ == '__main__':
    unittest.main(verbosity=2)