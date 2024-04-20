import os
import hashlib
import time
import sys
import subprocess
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import platform

from analyzers.flake8_analyzer import Flake8Analyzer
from analyzers.pylint_analyzer import PylintAnalyzer
from analyzers.mypy_analyzer import MypyAnalyzer
from analyzers.bandit_analyzer import BanditAnalyzer


class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, directory):
        super().__init__()
        self.directory = directory
        self.file_contents = {}
        self.file_hashes = {}
        self.last_modified_times = {}
        self.detection_counts = {}
        self.initialize_file_tracking()

        self.flake8_analyzer = Flake8Analyzer()
        self.pylint_analyzer = PylintAnalyzer()
        self.mypy_analyzer = MypyAnalyzer()
        self.bandit_analyzer = BanditAnalyzer()

    def initialize_file_tracking(self):
        """Initializes file tracking for all Python files in the specified directory."""
        for root, _, files in os.walk(self.directory):
            for file in files:
                if file.endswith('.py'):
                    self.load_file(os.path.join(root, file))

    def load_file(self, file_path):
        """Loads a file's contents, computes its hash, and initializes tracking."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                contents = file.readlines()
            self.file_contents[file_path] = contents
            self.file_hashes[file_path] = self.compute_hash(contents)
            self.last_modified_times[file_path] = os.path.getmtime(file_path)
            self.detection_counts[file_path] = 0
        except IOError as e:
            print(f"Failed to load file {file_path}: {e}")

    def compute_hash(self, contents):
        """Generates an MD5 hash for the given file contents."""
        hasher = hashlib.md5()
        for line in contents:
            hasher.update(line.encode('utf-8'))
        return hasher.hexdigest()

    def on_modified(self, event):
        if not event.src_path.endswith('.py') or self.should_ignore_event(event):
            return

        self.process_modification(event.src_path)

    def should_ignore_event(self, event):
        """Determines if the modification event should be ignored based on timing."""
        time.sleep(0.5)
        last_modified = os.path.getmtime(event.src_path)
        return (last_modified - self.last_modified_times.get(event.src_path, 0)) < 1

    def has_content_changed(self, file_path, new_contents):
        """Checks if the file's content has changed since the last update."""
        old_contents = self.file_contents.get(file_path, [])
        for i, line in enumerate(new_contents, start=1):
            if i > len(old_contents) or line != old_contents[i-1]:
                return True
        return False

    def log_changes(self, file_path, new_contents):
        """Logs the detected changes to the console."""
        current_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.detection_counts[file_path] += 1
        # Only log changes after the first detection
        if self.detection_counts[file_path] > 0:
            added_line_numbers = []
            for i, line in enumerate(new_contents, start=1):
                if i > len(self.file_contents.get(file_path, [])) or line != self.file_contents[file_path][i-1]:
                    print(f"New/Changed line at {i}: {line.strip()}")
                    added_line_numbers.append(i)
            print(f'[{current_time_str}] Detected changes in the file: {file_path}')
        return added_line_numbers

    def run_analyzers(self, file_path, added_line_numbers):
        self.flake8_analyzer.run_flake8_analysis(file_path, added_line_numbers)
        self.pylint_analyzer.run_pylint_analysis(file_path, added_line_numbers)
        self.mypy_analyzer.run_mypy_analysis(file_path, added_line_numbers)
        self.bandit_analyzer.run_bandit_analysis(file_path, added_line_numbers)

    def process_modification(self, file_path):
        """Processes a file modification event."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                new_contents = file.readlines()
        except IOError as e:
            print(f"Error opening file {file_path}: {e}")
            return

        if file_path not in self.detection_counts:
            self.load_file(file_path)

        if self.has_content_changed(file_path, new_contents):
            self.log_changes(file_path, new_contents)
            self.file_contents[file_path] = new_contents
            self.last_modified_times[file_path] = os.path.getmtime(file_path)
            added_line_numbers = self.log_changes(file_path, new_contents)
            self.run_analyzers(file_path, added_line_numbers)


if __name__ == "__main__":
    directory = sys.argv[1] if len(sys.argv) > 1 else '.'
    if not os.path.isdir(directory):
        print("The provided path is not a directory.")
        sys.exit(1)

    print("Starting file monitoring...")

    if platform.system() == 'Darwin':
        print("MacOS detected, applying special logic for first file opening.")

    observer = Observer()
    event_handler = FileChangeHandler(directory)
    observer.schedule(event_handler, directory, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
