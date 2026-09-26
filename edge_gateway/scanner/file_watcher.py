import os
import time
import json
from typing import List, Dict, Any
from app.core.logging import logger

class EdgeFileWatcher:
    """
    Scans local enterprise directories and hot-folders for incoming financial statements or KYC drops.
    """
    def __init__(self, watch_dir: str = "./sample_data"):
        self.watch_dir = watch_dir
        self.seen_files = set()

    def scan_directory(self) -> List[str]:
        if not os.path.exists(self.watch_dir):
            os.makedirs(self.watch_dir, exist_ok=True)
            return []

        new_files = []
        for root, _, files in os.walk(self.watch_dir):
            for f in files:
                full_path = os.path.join(root, f)
                if full_path not in self.seen_files:
                    self.seen_files.add(full_path)
                    new_files.append(full_path)
        return new_files
