from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.patch_stdout import patch_stdout
from core.config import HISTORY_FILE, CONFIG_DIR
from core.completer import OmgaCompleter
from core.commands import dispatch_command
from core.logger import logger
import os

def run_shell():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    session = PromptSession(history=FileHistory(HISTORY_FILE))
    completer = OmgaCompleter()
    print("Welcome to omga-cli shell. Type 'exit' or Ctrl-D to quit.")

    while True:
        with patch_stdout():
            try:
                text = session.prompt('omga-cli> ', completer=completer)
                if text.strip() == 'exit':
                    break
                if text.strip():
                    dispatch_command(text)
            except KeyboardInterrupt:
                print("Input cleared (Ctrl-C).")
            except EOFError:
                print("Exiting...")
            except Exception as e:
                logger.error(f"Error: {e}")
                print(f"Error: {e}")