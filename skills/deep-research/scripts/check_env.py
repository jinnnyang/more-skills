import os
import sys
import time
import subprocess
import urllib.request
import json

def check_network(url, name):
    start = time.time()
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                latency = round((time.time() - start) * 1000, 2)
                return {"status": "ok", "latency_ms": latency}
    except Exception as e:
        return {"status": "failed", "error": str(e)}
    return {"status": "failed", "error": "Non-200 status code"}

def check_git():
    try:
        res = subprocess.run(["git", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=3)
        if res.returncode == 0:
            return {"status": "ok", "version": res.stdout.strip()}
    except Exception as e:
        return {"status": "failed", "error": str(e)}
    return {"status": "failed", "error": "git command not found or failed"}

def check_write_permissions():
    test_file = ".write_test_temp"
    try:
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("test")
        os.remove(test_file)
        return {"status": "ok"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def check_libraries():
    # Only urllib is required, which is a Python standard library.
    libs = ["urllib"]
    results = {}
    for lib in libs:
        try:
            __import__(lib)
            results[lib] = {"status": "ok"}
        except ImportError:
            results[lib] = {"status": "missing"}
    return results

def main():
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "python_version": sys.version,
        "connectivity": {
            "google": check_network("https://www.google.com", "Google"),
            "bing": check_network("https://www.bing.com", "Bing"),
            "europepmc": check_network("https://europepmc.org", "EuropePMC")
        },
        "git": check_git(),
        "write_permissions": check_write_permissions(),
        "libraries": check_libraries()
    }
    
    # Check if all critical dependencies are ok
    critical_ok = True
    warnings = []
    
    if report["git"]["status"] != "ok":
        # Non-blocking, will automatically skip Git commits if missing
        warnings.append("Git CLI is not installed or not in PATH. Version tracking will be automatically skipped.")
        
    if report["write_permissions"]["status"] != "ok":
        critical_ok = False
        warnings.append("No write permissions in the current workspace directory.")
        
    network_ok = any(v["status"] == "ok" for v in report["connectivity"].values())
    if not network_ok:
        critical_ok = False
        warnings.append("No internet connectivity detected. Deep research searches will fail.")
        
    report["status"] = "PASSED" if critical_ok else "FAILED"
    report["warnings"] = warnings
    
    # Print JSON output for integration
    print(json.dumps(report, indent=2, ensure_ascii=False))
    
    if not critical_ok:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()

