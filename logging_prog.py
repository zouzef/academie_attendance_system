import logging
import datetime
import json
LOG_FILE = "/home/kernelsipc/PycharmProjects/flasktemplate/static/logs.json"
import os
from datetime import datetime
class JsonLogHandler(logging.Handler):
    def __init__(self, filename):
        super().__init__()
        self.filename = filename
        if not os.path.exists(self.filename):
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
