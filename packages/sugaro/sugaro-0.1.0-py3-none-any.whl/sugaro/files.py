import json
from pathlib import Path

def read(path: str, mode="r", encoding="utf-8"):
    """Read file content in one line."""
    return Path(path).read_text(encoding=encoding) if "b" not in mode else Path(path).read_bytes()

def write(path: str, data, mode="w", encoding="utf-8"):
    """Write to file in one line."""
    p = Path(path)
    if "b" in mode:
        p.write_bytes(data)
    else:
        p.write_text(str(data), encoding=encoding)
    return True

def jload(path: str):
    """Load JSON file into dict."""
    return json.loads(read(path))

def jdump(obj, path: str, indent=2):
    """Dump dict to JSON file."""
    write(path, json.dumps(obj, indent=indent))
    return True
