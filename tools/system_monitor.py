"""
BRO System Monitor
Monitor PC health: CPU, RAM, Battery, Disk, Network.
Optimized for performance using psutil.
"""

import os
import sys
import subprocess
import shutil
from typing import Dict

# Try to import psutil
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =============================================================================
# SYSTEM INFO (Optimized)
# =============================================================================

def get_cpu_usage() -> Dict:
    """Get CPU usage percentage."""
    if PSUTIL_AVAILABLE:
        # interval=None is non-blocking (returns time since last call)
        # We assume this is called periodically
        return {
            "usage": psutil.cpu_percent(interval=None),
            "cores": psutil.cpu_count(logical=True)
        }
    else:
        # Fallback (Slow)
        try:
            result = subprocess.run([
                "powershell", "-Command",
                "(Get-Counter '\\Processor(_Total)\\% Processor Time').CounterSamples.CookedValue"
            ], capture_output=True, text=True, timeout=2)
            usage = float(result.stdout.strip())
            return {"usage": round(usage, 1), "cores": os.cpu_count()}
        except:
            return {"usage": 0, "cores": os.cpu_count()}


def get_memory_usage() -> Dict:
    """Get RAM usage."""
    if PSUTIL_AVAILABLE:
        mem = psutil.virtual_memory()
        return {
            "used_gb": round(mem.used / (1024**3), 1),
            "total_gb": round(mem.total / (1024**3), 1),
            "percent": mem.percent
        }
    else:
        # Fallback (Slow)
        try:
            result = subprocess.run([
                "powershell", "-Command",
                "$os = Get-WmiObject Win32_OperatingSystem; "
                "$total = [math]::Round($os.TotalVisibleMemorySize/1MB, 1); "
                "$free = [math]::Round($os.FreePhysicalMemory/1MB, 1); "
                "$used = $total - $free; "
                "Write-Output \"$used,$total\""
            ], capture_output=True, text=True, timeout=2)
            parts = result.stdout.strip().split(",")
            used = float(parts[0])
            total = float(parts[1])
            return {
                "used_gb": used,
                "total_gb": total,
                "percent": round(used / total * 100, 1) if total > 0 else 0
            }
        except:
            return {"used_gb": 0, "total_gb": 0, "percent": 0}


def get_battery_status() -> Dict:
    """Get battery status."""
    if PSUTIL_AVAILABLE and hasattr(psutil, "sensors_battery"):
        bat = psutil.sensors_battery()
        if bat:
            return {
                "percent": bat.percent,
                "charging": bat.power_plugged,
                "plugged_in": bat.power_plugged
            }
        
    # Fallback or Desktop
    return {"percent": None, "charging": None, "plugged_in": True}


def get_disk_usage() -> Dict:
    """Get disk usage."""
    disks = {}
    if PSUTIL_AVAILABLE:
        try:
            for part in psutil.disk_partitions():
                if 'cdrom' in part.opts or part.fstype == '':
                    continue
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    disks[part.device] = {
                        "used_gb": round(usage.used / (1024**3), 1),
                        "total_gb": round(usage.total / (1024**3), 1),
                        "percent": usage.percent
                    }
                except:
                    pass
        except: pass
        return disks
    
    return {} # Skip slow powershell for disks unless needed explicitly


def get_network_info() -> Dict:
    """Get network connection info."""
    # Fast check
    connected = False
    name = "Unknown"
    
    if PSUTIL_AVAILABLE:
        stats = psutil.net_if_stats()
        for iface, stat in stats.items():
            if stat.isup and 'Wi-Fi' in iface or 'Wireless' in iface:
                connected = True
                name = iface
                break
            if stat.isup and 'Ethernet' in iface:
                connected = True
                name = "Ethernet"
                
    return {"wifi_name": name if connected else None, "signal": None, "connected": connected}


def get_gpu_info() -> Dict:
    """Get GPU info (Still uses nvidia-smi, might be slow, call sparingly)."""
    try:
        # Check if nvidia-smi exists first to avoid timeout
        if not shutil.which("nvidia-smi"):
             return {"name": "N/A", "available": False}

        result = subprocess.run([
            "nvidia-smi",
            "--query-gpu=name,memory.used,memory.total,utilization.gpu,temperature.gpu",
            "--format=csv,noheader,nounits"
        ], capture_output=True, text=True, timeout=1) # Low timeout
        
        if result.returncode != 0:
            return {"name": "N/A", "available": False}
        
        parts = result.stdout.strip().split(",")
        return {
            "name": parts[0].strip(),
            "vram_used_mb": int(parts[1].strip()),
            "vram_total_mb": int(parts[2].strip()),
            "utilization": int(parts[3].strip()),
            "temperature": int(parts[4].strip()),
            "available": True
        }
    except:
        return {"name": "N/A", "available": False}


# =============================================================================
# FORMATTED OUTPUT
# =============================================================================

def system_status() -> str:
    """Get full system status."""
    cpu = get_cpu_usage()
    mem = get_memory_usage()
    battery = get_battery_status()
    
    # CPU bar
    cpu_bar = "█" * int(cpu["usage"] / 10) + "░" * (10 - int(cpu["usage"] / 10))
    
    # RAM bar
    mem_bar = "█" * int(mem["percent"] / 10) + "░" * (10 - int(mem["percent"] / 10))
    
    output = f"""
💻 BRO SYSTEM MONITOR
{'='*45}

🔲 CPU: [{cpu_bar}] {cpu['usage']}%
   Cores: {cpu['cores']}

🧠 RAM: [{mem_bar}] {mem['percent']}%
   {mem['used_gb']:.1f} GB / {mem['total_gb']:.1f} GB

"""
    
    # Battery
    if battery["percent"] is not None:
        bat_icon = "🔌" if battery["plugged_in"] else "🔋"
        percent = battery["percent"]
        bat_bar = "█" * int(percent / 10) + "░" * (10 - int(percent / 10))
        charging = "⚡ Charging" if battery["charging"] else ""
        output += f"{bat_icon} Battery: [{bat_bar}] {percent}% {charging}\n\n"
    
    return output


def quick_status() -> str:
    """Quick one-line status."""
    cpu = get_cpu_usage()
    mem = get_memory_usage()
    return f"CPU: {cpu['usage']}% | RAM: {mem['percent']}%"


# =============================================================================
# CONVENIENCE
# =============================================================================

def cpu() -> str:
    return f"🔲 CPU: {get_cpu_usage()['usage']}%"

def ram() -> str:
    mem = get_memory_usage()
    return f"🧠 RAM: {mem['percent']}%"

if __name__ == "__main__":
    print(system_status())
