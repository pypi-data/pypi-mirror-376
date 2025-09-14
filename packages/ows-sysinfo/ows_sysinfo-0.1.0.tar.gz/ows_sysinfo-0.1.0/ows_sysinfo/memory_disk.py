import shutil
import psutil

def get_memory_info():
    try:
        vm = psutil.virtual_memory()
        swap = psutil.swap_memory()
        return {
            "total_gb": round(vm.total / (1024**3), 2),
            "available_gb": round(vm.available / (1024**3), 2),
            "used_gb": round(vm.used / (1024**3), 2),
            "percent": vm.percent,
            "swap_total_gb": round(swap.total / (1024**3), 2),
            "swap_used_gb": round(swap.used / (1024**3), 2),
            "swap_percent": swap.percent
        }
    except Exception as e:
        return {"error": f"memory info error: {e}"}

def get_disk_info():
    try:
        parts = []
        for p in psutil.disk_partitions(all=False):
            try:
                usage = shutil.disk_usage(p.mountpoint)
                parts.append({
                    "device": p.device,
                    "mountpoint": p.mountpoint,
                    "fstype": p.fstype,
                    "total_gb": round(usage.total / (1024**3), 2),
                    "used_gb": round(usage.used / (1024**3), 2),
                    "free_gb": round(usage.free / (1024**3), 2),
                    "percent": round(usage.used / usage.total * 100, 2) if usage.total else None
                })
            except PermissionError:
                parts.append({
                    "device": p.device,
                    "mountpoint": p.mountpoint,
                    "fstype": p.fstype,
                    "error": "Permission denied"
                })
        disk_io = psutil.disk_io_counters()
        return {"partitions": parts, "disk_io": disk_io._asdict() if disk_io else {}}
    except Exception as e:
        return {"error": f"disk info error: {e}"}
