import json
from datetime import datetime
from rich import print_json
from .system_info import get_system_info
from .cpu_info import get_cpu_info
from .memory_disk import get_memory_info, get_disk_info
from .gpu_info import get_gpu_info
from .network_info import get_network_info
from .processes_info import get_top_processes
from .miscellaneous import get_battery_info, get_uptime, get_logged_users

def collect_full_report(speedtest=False, top_n=10):
    report = {
        "collected_at": datetime.utcnow().isoformat() + "Z",
        "system": get_system_info(),
        "cpu": get_cpu_info(),
        "memory": get_memory_info(),
        "disk": get_disk_info(),
        "gpu": get_gpu_info(),
        "network": get_network_info(do_speedtest=speedtest),
        "processes_top": get_top_processes(limit=top_n),
        "battery": get_battery_info(),
        "uptime": get_uptime(),
        "users": get_logged_users()
    }
    return report

def generate_report(outfile=None, pretty=False, speedtest=False, top_n=10):
    rpt = collect_full_report(speedtest=speedtest, top_n=top_n)
    if outfile:
        with open(outfile, "w", encoding="utf-8") as f:
            json.dump(rpt, f, indent=2)
    if pretty:
        try:
            print_json(data=json.dumps(rpt))
        except Exception:
            print(json.dumps(rpt, indent=2))
    return rpt

def generate_html_report(outfile="sys_report.html", speedtest=False, top_n=10):
    rpt = collect_full_report(speedtest=speedtest, top_n=top_n)
    html = "<html><head><meta charset='utf-8'><title>System Report</title></head><body>"
    html += f"<h1>System Report - {rpt['collected_at']}</h1>"
    html += "<pre>" + json.dumps(rpt, indent=2) + "</pre>"
    html += "</body></html>"
    with open(outfile, "w", encoding="utf-8") as f:
        f.write(html)
    return outfile
