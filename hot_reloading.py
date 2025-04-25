import inspect
import os
import shutil
import traceback
from importlib import reload
from pygments import highlight
from pygments.lexers.python import PythonTracebackLexer
from pygments.formatters import Terminal256Formatter


lexer = PythonTracebackLexer(stripall=True)
formatter = Terminal256Formatter(style="default")


def hot_cycle(fun, *args, **kwargs):
    prev_e = None
    error_count = 0

    module = inspect.getmodule(fun)

    MODULE_FILE = module.__file__
    BACKUP_FILE = f".{module.__name__}_backup"
    ERROR_FILE = f".{module.__name__}_error"

    last_mtime = os.stat(MODULE_FILE).st_mtime
    shutil.copyfile(MODULE_FILE, BACKUP_FILE)

    running = True
    while running:
        current_mtime = os.stat(MODULE_FILE).st_mtime

        if current_mtime > last_mtime:
            last_mtime = current_mtime
            try:
                reload(module)
                running = fun(*args, **kwargs)
                print(f"{module.__name__} module reloaded.")
                shutil.copyfile(MODULE_FILE, BACKUP_FILE)
                continue
            except Exception as e:
                print(f"Error reloading {module.__name__}:\n")
                print(highlight(traceback.format_exc(), lexer, formatter))
                print("Reverting to backup.\n")
                shutil.copyfile(MODULE_FILE, ERROR_FILE)
                shutil.copyfile(BACKUP_FILE, MODULE_FILE)
                reload(module)
                shutil.copyfile(ERROR_FILE, MODULE_FILE)
                last_mtime = os.stat(MODULE_FILE).st_mtime

        try:
            running = fun(*args, **kwargs)
        except Exception as e:
            if str(e) == str(prev_e):
                print(f"\rError count: {error_count} ", end="", flush=True)
                error_count += 1
            else:
                error_count = 1
                prev_e = e
                print(f"Error in {module.__name__}.{fun.__name__}:\n")
                print(highlight(traceback.format_exc(), lexer, formatter))
