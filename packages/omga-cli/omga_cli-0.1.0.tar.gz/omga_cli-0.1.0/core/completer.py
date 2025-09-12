from prompt_toolkit.completion import Completer, Completion
from threading import Thread, Lock
import time
from core.ai import ask
from core.cache_db import get, set_
from core.logger import logger

class OmgaCompleter(Completer):
    def __init__(self):
        self.static_suggestions = ['check', 'explain', 'ask', 'fix', 'run', 'generate', 'project', 'snippet', 'add', 'list', 'remove']
        self.cache_lock = Lock()
        self.ai_cache = {}  # In-memory for speed, backed by db
        self.load_cache()

    def load_cache(self):
        for key in self.static_suggestions:
            cached = get(f"completion_{key}")
            if cached:
                self.ai_cache[key] = cached.split(',')

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        words = text.split()
        if not words:
            return

        partial = words[-1]
        # Return static immediately
        for sug in self.static_suggestions:
            if sug.startswith(partial):
                yield Completion(sug, start_position=-len(partial))

        # Check cache
        with self.cache_lock:
            if partial in self.ai_cache:
                for sug in self.ai_cache[partial]:
                    yield Completion(sug, start_position=-len(partial))

        # Start background thread for AI if not cached
        if partial not in self.ai_cache:
            Thread(target=self.fetch_ai_completions, args=(partial,)).start()

    def fetch_ai_completions(self, partial):
        try:
            prompt = f"Suggest up to 5 completions for this partial CLI command: {partial}"
            suggestions = ask(prompt).strip().split('\n')[:5]
            with self.cache_lock:
                self.ai_cache[partial] = suggestions
                set_(f"completion_{partial}", ','.join(suggestions))
        except Exception as e:
            logger.error(f"AI completion error: {e}")