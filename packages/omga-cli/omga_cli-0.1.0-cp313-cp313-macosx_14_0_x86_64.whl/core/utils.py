import subprocess
import difflib

def read_file(path: str) -> str:
    with open(path, 'r') as f:
        return f.read()

def write_file(path: str, content: str):
    with open(path, 'w') as f:
        f.write(content)

def run_subprocess(cmd: str, timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, shell=True, capture_output=True, timeout=timeout)

def diff_text(old: str, new: str) -> str:
    diff = difflib.unified_diff(old.splitlines(), new.splitlines(), lineterm='')
    return '\n'.join(diff)