import logging
import datetime
import json

import os
from datetime import datetime



LOG_FILE = ("logs.json")

class JsonLogHandler(logging.Handler):
    def __init__(self, filename):
        super().__init__()
        self.filename = filename
        # Create file if missing or empty/invalid
        if not os.path.exists(self.filename) or os.stat(self.filename).st_size == 0:
            with open(self.filename, "w") as f:
                json.dump([], f)
        else:
            try:
                with open(self.filename, "r") as f:
                    json.load(f)
            except json.JSONDecodeError:
                with open(self.filename, "w") as f:
                    json.dump([], f)

    def emit(self, record):
        log_entry = {
            "level": record.levelname,
            "message": record.getMessage(),
            "timestamp": datetime.fromtimestamp(record.created).isoformat()
        }
        try:
            with open(self.filename, "r+") as f:
                logs = json.load(f)
                logs.append(log_entry)
                f.seek(0)
                json.dump(logs, f, indent=4)
        except Exception as e:
            print("⚠️ Failed to write to log file:", e)

# Initialize logger
logger = logging.getLogger("jsonLogger")
logger.setLevel(logging.DEBUG)
logger.addHandler(JsonLogHandler(LOG_FILE))
