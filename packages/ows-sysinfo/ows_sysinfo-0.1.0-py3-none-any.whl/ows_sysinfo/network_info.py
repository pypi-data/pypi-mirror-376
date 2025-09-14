import socket

def _safe_import(name):
    try:
        mod = __import__(name)
        return mod
    except Exception:
        return None

def get_network_info(do_speedtest=False):
    try:
        import psutil, requests
        net_if_addrs = psutil.net_if_addrs()
        interfaces = {}
        for iface, addrs in net_if_addrs.items():
            interfaces[iface] = []
            for a in addrs:
                interfaces[iface].append({
                    "family": str(a.family),
                    "address": a.address,
                    "netmask": a.netmask,
                    "broadcast": a.broadcast
                })
        # public ip
        public_ip = None
        try:
            r = requests.get("https://api64.ipify.org?format=json", timeout=5)
            public_ip = r.json().get("ip")
        except Exception:
            public_ip = "Unavailable"

        # default local ip
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
        except Exception:
            local_ip = "Unavailable"

        out = {
            "hostname": socket.gethostname(),
            "local_ip": local_ip,
            "public_ip": public_ip,
            "interfaces": interfaces
        }

        if do_speedtest:
            st_mod = _safe_import("speedtest")
            if st_mod:
                try:
                    st = st_mod.Speedtest()
                    st.get_best_server()
                    res = st.download(), st.upload()
                    out["speed_test"] = {
                        "download_bps": res[0],
                        "upload_bps": res[1],
                        "ping_ms": st.results.ping
                    }
                except Exception as e:
                    out["speed_test"] = {"error": str(e)}
            else:
                out["speed_test"] = {"error": "speedtest-cli not installed"}

        # try to get wifi info (best-effort)
        netifaces = _safe_import("netifaces")
        if netifaces:
            try:
                gateways = netifaces.gateways()
                out["gateways"] = gateways
            except Exception:
                out["gateways"] = "Unavailable"
        return out
    except Exception as e:
        return {"error": f"network info error: {e}"}
