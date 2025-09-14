import math

def get_cpu_info():
    try:
        import psutil
        import cpuinfo
        info = cpuinfo.get_cpu_info()

        cpu_count_logical = psutil.cpu_count(logical=True)
        cpu_count_physical = psutil.cpu_count(logical=False)
        cpu_percent = psutil.cpu_percent(interval=1, percpu=False)

        per_cpu = psutil.cpu_percent(interval=0.5, percpu=True)

        return {
            "brand": info.get("brand_raw") or info.get("brand", "Unknown"),
            "arch": info.get("arch"),
            "bits": info.get("bits"),
            "hz_advertised": info.get("hz_advertised_friendly"),
            "logical_cores": cpu_count_logical,
            "physical_cores": cpu_count_physical,
            "cpu_usage_percent": cpu_percent,
            "per_cpu_percent": per_cpu
        }
    except Exception as e:
        return {"error": f"cpu info error: {e}"}
