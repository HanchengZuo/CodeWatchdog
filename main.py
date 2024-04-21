import os
import hashlib
import time
import sys
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import platform

# Importing analyzers for various types of code checks.
from analyzers.flake8_analyzer import Flake8Analyzer
from analyzers.pylint_analyzer import PylintAnalyzer
from analyzers.mypy_analyzer import MypyAnalyzer
from analyzers.bandit_analyzer import BanditAnalyzer


class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, directory):
        super().__init__()
        self.directory = directory  # Directory to be monitored
        self.file_contents = {}  # Stores content of each file
        self.file_hashes = {}  # Stores hash of each file's contents for comparison
        self.last_modified_times = {}  # Stores the last modified time for each file
        # Stores flags for ignoring first detection on macOS
        self.first_detection_ignored = {}
        self.initialize_file_tracking()

        # Initialize code analyzers
        self.flake8_analyzer = Flake8Analyzer()
        self.pylint_analyzer = PylintAnalyzer()
        self.mypy_analyzer = MypyAnalyzer()
        self.bandit_analyzer = BanditAnalyzer()

    def initialize_file_tracking(self):
        """Scans the directory to initialize tracking of all Python files, ignoring checkpoints."""
        for root, dirs, files in os.walk(self.directory, topdown=True):
            # Ignore specific directories
            dirs[:] = [d for d in dirs if d not in ['.ipynb_checkpoints']]
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    self.load_file(file_path)
                    if platform.system() == 'Darwin':  # Ignore First Changes on macOS Only
                        self.first_detection_ignored[file_path] = True

    def load_file(self, file_path):
        """Loads a file's contents, computes its hash, and initializes tracking."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                contents = file.readlines()
            self.file_contents[file_path] = contents
            self.file_hashes[file_path] = self.compute_hash(contents)
            self.last_modified_times[file_path] = os.path.getmtime(file_path)
        except IOError as e:
            print(f"Failed to load file {file_path}: {e}")

    def compute_hash(self, contents):
        """Generates an MD5 hash for the given file contents."""
        hasher = hashlib.md5()
        for line in contents:
            hasher.update(line.encode('utf-8'))
        return hasher.hexdigest()

    def safe_get_mtime(self, file_path):
        """Preventing Temporary Files from Interfering."""
        try:
            return os.path.getmtime(file_path)
        except FileNotFoundError:
            return None

    def should_ignore_event(self, event):
        """Determines if the modification event should be ignored based on timing and path."""
        ignored_paths = ['.~', '__pycache__', '.ipynb_checkpoints']
        if any(ignored in event.src_path for ignored in ignored_paths):
            return True
        if not os.path.exists(event.src_path):
            return True
        time.sleep(0.5)
        last_modified = self.safe_get_mtime(event.src_path)
        if last_modified is None:
            return True
        return (last_modified - self.last_modified_times.get(event.src_path, 0)) < 1

    def on_modified(self, event):
        """Handles file modification events."""
        if not event.src_path.endswith('.py') or self.should_ignore_event(event):
            return

        if self.first_detection_ignored.get(event.src_path, False):
            # If it's the first time the change is detected, the flag is ignored and updated
            self.first_detection_ignored[event.src_path] = False
            return

        self.process_modification(event.src_path)

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
        print(
            f'\n[{current_time_str}] Detected changes in the file \'{file_path}\':')
        added_line_numbers = []
        for i, line in enumerate(new_contents, start=1):
            if i > len(self.file_contents.get(file_path, [])) or line != self.file_contents[file_path][i-1]:
                print(f"New/Changed line at {i}: {line.strip()}")
                added_line_numbers.append(i)
        return added_line_numbers

    def run_analyzers(self, file_path, added_line_numbers):
        """Run the code analyser."""
        self.flake8_analyzer.run_flake8_analysis(file_path, added_line_numbers)
        self.pylint_analyzer.run_pylint_analysis(file_path, added_line_numbers)
        self.mypy_analyzer.run_mypy_analysis(file_path, added_line_numbers)
        self.bandit_analyzer.run_bandit_analysis(file_path, added_line_numbers)
        print("\n" + "=" * 80 + "\nEnd of Analysis\n" + "=" * 80 + "\n" * 3)

    def process_modification(self, file_path):
        """Processes modifications by loading new contents, logging changes, and running analyzers."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                new_contents = file.readlines()
        except IOError as e:
            print(f"Error opening file {file_path}: {e}")
            return

        if self.has_content_changed(file_path, new_contents):
            added_line_numbers = self.log_changes(file_path, new_contents)
            self.file_contents[file_path] = new_contents
            self.last_modified_times[file_path] = os.path.getmtime(file_path)
            self.run_analyzers(file_path, added_line_numbers)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <directory_to_watch>")
        sys.exit(1)

    directory = sys.argv[1]
    if not os.path.isdir(directory):
        print(f"The provided path '{directory}' is not a directory.")
        sys.exit(1)

    print("\nStarting file monitoring...")

    if platform.system() == 'Darwin':
        print("MacOS detected, applying special logic for first file opening (ignore the first change event).")

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
