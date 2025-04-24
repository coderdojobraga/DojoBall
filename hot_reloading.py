import os
import shutil
import traceback
import inspect
from importlib import reload
from pygments.lexers.python import PythonTracebackLexer
from pygments.formatters import Terminal256Formatter
from pygments import highlight


lexer = PythonTracebackLexer(stripall=True)
formatter = Terminal256Formatter(style="default")

def hot_cycle(fun, *args, **kwargs):
    module = inspect.getmodule(fun)

    last_mtime = os.stat("loop.py").st_mtime
    shutil.copyfile("loop.py", ".loop_backup")

    running = True
    while running:
        current_mtime = os.stat("loop.py").st_mtime

        if current_mtime > last_mtime:
            last_mtime = current_mtime
            try:
                reload(module)
                print("loop module reloaded")
                try:
                    running = fun(*args, **kwargs)
                    shutil.copyfile("loop.py", ".loop_backup")
                    continue
                except Exception as e:
                    print("Error in reloaded game loop:\n")
                    print(highlight(traceback.format_exc(), lexer, formatter))
                    print("Reverting to backup.\n")
                    shutil.copyfile("loop.py", ".loop_error")
                    shutil.copyfile(".loop_backup", "loop.py")
                    reload(module)
                    shutil.copyfile(".loop_error", "loop.py")
                    last_mtime = os.stat("loop.py").st_mtime
            except Exception as e:
                print("Error reloading loop module:\n")
                print(highlight(traceback.format_exc(), lexer, formatter))
                print("Reverting to backup.\n")

        try:
            running = fun(*args, **kwargs)
        except Exception as e:
            print("Error in game loop:\n")
            print(highlight(traceback.format_exc(), lexer, formatter))

# if touch
#   if reload
#     if run
#       backup
#       continue
#     else
#       fix
# run
