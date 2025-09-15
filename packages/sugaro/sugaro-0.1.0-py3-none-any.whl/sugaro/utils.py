import os
import uuid
from datetime import datetime

def uid():
    """Generate UUID string."""
    return str(uuid.uuid4())

def now(fmt="%Y-%m-%d %H:%M:%S"):
    """Return current time as formatted string."""
    return datetime.now().strftime(fmt)

def mkdir(path: str):
    """Create directory if not exists."""
    os.makedirs(path, exist_ok=True)
    return path
