import platform, socket, os
# (paste full system_info.py code)
import platform
import socket
import os
from datetime import datetime

def get_system_info():
    try:
        uname = platform.uname()
        boot_time = None
        try:
            import psutil
            boot_time = datetime.fromtimestamp(psutil.boot_time()).isoformat()
        except Exception:
            boot_time = "Unavailable"

        return {
            "node": uname.node,
            "system": uname.system,
            "release": uname.release,
            "version": uname.version,
            "machine": uname.machine,
            "processor": uname.processor or platform.processor(),
            "python_version": platform.python_version(),
            "hostname": socket.gethostname(),
            "cwd": os.getcwd(),
            "boot_time": boot_time
        }
    except Exception as e:
        return {"error": f"system info error: {e}"}
