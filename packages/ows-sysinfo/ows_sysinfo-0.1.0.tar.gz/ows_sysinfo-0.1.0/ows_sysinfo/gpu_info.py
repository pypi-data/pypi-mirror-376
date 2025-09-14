def get_gpu_info():
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        if not gpus:
            return {"gpus": []}
        out = []
        for g in gpus:
            out.append({
                "id": g.id,
                "name": g.name,
                "load": g.load,
                "memoryTotalMB": g.memoryTotal,
                "memoryUsedMB": g.memoryUsed,
                "memoryFreeMB": g.memoryFree,
                "temperatureC": g.temperature,
                "uuid": getattr(g, "uuid", None)
            })
        return {"gpus": out}
    except Exception as e:
        return {"error": f"gpu info error (GPUtil missing or not supported): {e}"}
