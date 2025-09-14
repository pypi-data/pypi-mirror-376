import psutil
from operator import itemgetter

def get_top_processes(limit=10, by="cpu"):
    try:
        procs = []
        for p in psutil.process_iter(["pid", "name", "username", "cpu_percent", "memory_percent", "create_time"]):
            info = p.info
            procs.append({
                "pid": info.get("pid"),
                "name": info.get("name"),
                "user": info.get("username"),
                "cpu_percent": info.get("cpu_percent"),
                "memory_percent": round(info.get("memory_percent") or 0, 3),
                "create_time": info.get("create_time")
            })
        key = "cpu_percent" if by == "cpu" else "memory_percent"
        procs_sorted = sorted(procs, key=itemgetter(key), reverse=True)
        return procs_sorted[:limit]
    except Exception as e:
        return {"error": f"processes info error: {e}"}
