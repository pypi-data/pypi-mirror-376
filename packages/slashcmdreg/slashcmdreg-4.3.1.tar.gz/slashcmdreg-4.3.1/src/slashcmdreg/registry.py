import os
import importlib
from .command import SlashCommand
from .exceptions import InvalidCommandError

def load_commands(path=".", package=""):
    commands = []
    for file in os.listdir(path):
        if file.endswith(".py") and not file.startswith("__"):
            module_name = f"{package}.{file[:-3]}" if package else file[:-3]
            mod = importlib.import_module(module_name)
            if hasattr(mod, "setup"):
                cmd = mod.setup()
                if isinstance(cmd, SlashCommand):
                    commands.append(cmd)
                else:
                    raise InvalidCommandError(f"{file} did not return a valid SlashCommand instance.")
            else:
                raise InvalidCommandError(f"{file} is missing a setup() function.")
    return commands