import time
import psutil
import getpass

def get_battery_info():
    try:
        batt = psutil.sensors_battery()
        if not batt:
            return {"battery": "No battery detected"}
        return {
            "percent": batt.percent,
            "secsleft": batt.secsleft,
            "power_plugged": batt.power_plugged
        }
    except Exception as e:
        return {"error": f"battery info error: {e}"}

def get_uptime():
    try:
        boot = psutil.boot_time()
        now = time.time()
        return {"seconds_since_boot": int(now - boot)}
    except Exception as e:
        return {"error": f"uptime error: {e}"}

def get_logged_users():
    try:
        users = psutil.users()
        return [{"name": u.name, "terminal": u.terminal, "host": u.host, "started": u.started} for u in users]
    except Exception as e:
        return {"error": f"users info error: {e}"}
