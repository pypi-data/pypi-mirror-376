from core.checker import check_syntax_py, quick_fix_suggestion
from core.ai import ask
from core.utils import read_file, write_file, run_subprocess, diff_text
from core.config import CONFIG_DIR
from core.logger import logger
import os
from rich.console import Console
console = Console()

def dispatch_command(text: str):
    parts = text.split()
    if not parts:
        return
    cmd = parts[0]
    args = ' '.join(parts[1:])
    handlers = {
        'help': lambda: help_handler(),
        'check': lambda: check_handler(args),
        'explain': lambda: explain_handler(args),
        'ask': lambda: ask_handler(args),
        'fix': lambda: fix_handler(args)[0],
        'run': lambda: run_handler(args),
        'generate': lambda: generate_handler(parts[2], parts[3]) if len(parts) > 3 and parts[1] == 'project' else print("Invalid generate"),
        'snippet': lambda: snippet_handler(parts[1], parts[2] if len(parts) > 2 else None, ' '.join(parts[3:]) if len(parts) > 3 else None),
    }
    if cmd in handlers:
        result = handlers[cmd]()
        if result:
            print(result)
    else:
        print(f"Unknown command: {cmd}. Try 'help' for available commands.")

def help_handler():
    return """Available commands:
    help          - Show this help message
    check <file>  - Check syntax and linting of a Python file
    explain <file> - Explain the code in a file
    ask <question> - Ask a question to the AI
    fix <file>    - Suggest fixes for a file (use --apply to write changes)
    run <command> - Run a shell command
    generate project <template> <name> - Generate a project (e.g., fastapi)
    snippet add|list|remove <name> [content] - Manage code snippets
    exit          - Exit the shell"""

def check_handler(file: str):
    ok, messages = check_syntax_py(file)
    if ok and not messages:
        return "Syntax OK"
    elif ok:
        return "\n".join(["Syntax OK, but linter warnings:"] + messages)
    else:
        return "\n".join(["Syntax errors:"] + messages)

def explain_handler(file: str):
    code = read_file(file)
    prompt = f"Explain this code step by step, including potential pitfalls, performance notes, and complexity:\n```py\n{code}\n```"
    return ask(prompt)

def ask_handler(question: str):
    return ask(question)

def fix_handler(file: str):
    code = read_file(file)
    prompt = f"Fix any errors or improvements in this code and provide the corrected version:\n```py\n{code}\n```"
    new_code = ask(prompt)
    diff = diff_text(code, new_code)
    return f"Proposed fixes:\n{diff}", diff, new_code

def run_handler(command: str):
    logger.info(f"Executing: {command}")
    try:
        result = run_subprocess(command, timeout=120)
        return result.returncode, result.stdout.decode(), result.stderr.decode()
    except TimeoutError:
        return 124, "", "Timeout"
    except Exception as e:
        return 1, "", str(e)

def generate_handler(template: str, name: str):
    if template == 'fastapi':
        template_path = os.path.join(os.path.dirname(__file__), 'resources', 'fastapi_template.py')
        code = read_file(template_path)
        os.makedirs(name, exist_ok=True)
        write_file(os.path.join(name, 'main.py'), code)
    else:
        console.print("Unknown template.")

def snippet_handler(action: str, name: str | None, content: str | None):
    snippets_dir = os.path.join(CONFIG_DIR, 'snippets')
    os.makedirs(snippets_dir, exist_ok=True)
    if action == 'add':
        if name and content:
            write_file(os.path.join(snippets_dir, name), content)
            return "Snippet added."
    elif action == 'list':
        return '\n'.join(os.listdir(snippets_dir))
    elif action == 'remove':
        if name:
            os.remove(os.path.join(snippets_dir, name))
            return "Snippet removed."
    return "Invalid snippet action."