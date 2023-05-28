import time
import os
import re
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class MyHandler(FileSystemEventHandler):
    def on_modified(self, event):
        for filename in os.listdir(log_dir):
            if filename.endswith(".log"):
                filepath = os.path.join(log_dir, filename)
                with open(filepath, 'r') as f:
                    lines = f.readlines()
                    for line in lines:
                        # update your condition based on the logs
                        if "ingestion completed" in line:
                            print(f"Ingestion completed successfully in file {filename}")
                        elif re.search(r'error', line, re.I):
                            print(f"Error found in file {filename}: {line}")

if __name__ == "__main__":
    log_dir = "/logs"
    event_handler = MyHandler()
    observer = Observer()
    observer.schedule(event_handler, path=log_dir, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
