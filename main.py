import os
import hashlib
import time
import sys
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, directory, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.directory = directory
        self.file_contents = {}
        self.file_contents_hash = {} 
        self.last_detected_change = {}
        self.preload_file_contents()

    def preload_file_contents(self):
        """Preload the contents of all .py files in the directory"""
        for root, _, files in os.walk(self.directory):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        contents = f.readlines()
                        self.file_contents[file_path] = contents
                        self.file_contents_hash[file_path] = self.compute_hash(contents)
                        self.last_detected_change[file_path] = os.path.getmtime(file_path)
                        

    def compute_hash(self, contents):
        """Calculate the hash value of file contents"""
        md5 = hashlib.md5()
        for line in contents:
            md5.update(line.encode('utf-8'))
        return md5.hexdigest()

    def on_modified(self, event):
        if not event.src_path.endswith('.py'):
            return

        time.sleep(0.5)

        last_modified = os.path.getmtime(event.src_path)
        if last_modified - self.last_detected_change.get(event.src_path, 0) < 1:
            return

        try:
            with open(event.src_path, 'r', encoding='utf-8') as file:
                new_contents = file.readlines()
        except IOError as e:
            print(f"Error opening file: {e}")
            return

        old_contents = self.file_contents.get(event.src_path, [])
        content_changed = False

        for i, line in enumerate(new_contents, start=1):
            if i > len(old_contents) or line != old_contents[i-1]:
                content_changed = True
                print(f"New/Changed line at {i}: {line}", end='')

        if content_changed:
            current_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f'\n[{current_time_str}] Detected changes in the file: [{event.src_path}]')
            self.file_contents[event.src_path] = new_contents
            self.last_detected_change[event.src_path] = last_modified
        else:
            print("No new/changed lines detected.")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else '.'

    if not os.path.isdir(path):
        print("The provided path is not a directory.")
        sys.exit(1)

    event_handler = FileChangeHandler(path)
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
