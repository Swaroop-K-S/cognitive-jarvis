"""
BRO System Monitor
Monitor PC health: CPU, RAM, Battery, Disk, Network.
"""

import os
import sys
import subprocess
import platform
from typing import Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =============================================================================
# SYSTEM INFO
# =============================================================================

def get_cpu_usage() -> Dict:
    """Get CPU usage percentage."""
    try:
        result = subprocess.run([
            "powershell", "-Command",
            "(Get-Counter '\\Processor(_Total)\\% Processor Time').CounterSamples.CookedValue"
        ], capture_output=True, text=True, timeout=5)
        usage = float(result.stdout.strip())
        return {"usage": round(usage, 1), "cores": os.cpu_count()}
    except:
        return {"usage": 0, "cores": os.cpu_count()}


def get_memory_usage() -> Dict:
    """Get RAM usage."""
    try:
        result = subprocess.run([
            "powershell", "-Command",
            "$os = Get-WmiObject Win32_OperatingSystem; "
            "$total = [math]::Round($os.TotalVisibleMemorySize/1MB, 1); "
            "$free = [math]::Round($os.FreePhysicalMemory/1MB, 1); "
            "$used = $total - $free; "
            "Write-Output \"$used,$total\""
        ], capture_output=True, text=True, timeout=5)
        parts = result.stdout.strip().split(",")
        used = float(parts[0])
        total = float(parts[1])
        return {
            "used_gb": used,
            "total_gb": total,
            "percent": round(used / total * 100, 1)
        }
    except:
        return {"used_gb": 0, "total_gb": 0, "percent": 0}


def get_battery_status() -> Dict:
    """Get battery status."""
    try:
        result = subprocess.run([
            "powershell", "-Command",
            "$b = Get-WmiObject Win32_Battery; "
            "if ($b) { Write-Output \"$($b.EstimatedChargeRemaining),$($b.BatteryStatus)\" } "
            "else { Write-Output 'N/A' }"
        ], capture_output=True, text=True, timeout=5)
        
        output = result.stdout.strip()
        if output == "N/A":
            return {"percent": None, "charging": None, "plugged_in": True}
        
        parts = output.split(",")
        percent = int(parts[0])
        status = int(parts[1])  # 1=discharging, 2=AC, 3-5=charging
        
        return {
            "percent": percent,
            "charging": status >= 3,
            "plugged_in": status == 2 or status >= 3
        }
    except:
        return {"percent": None, "charging": None, "plugged_in": None}


def get_disk_usage() -> Dict:
    """Get disk usage."""
    try:
        result = subprocess.run([
            "powershell", "-Command",
            "Get-WmiObject Win32_LogicalDisk -Filter 'DriveType=3' | "
            "ForEach-Object { "
            "$used = [math]::Round(($_.Size - $_.FreeSpace)/1GB, 1); "
            "$total = [math]::Round($_.Size/1GB, 1); "
            "Write-Output \"$($_.DeviceID),$used,$total\" }"
        ], capture_output=True, text=True, timeout=5)
        
        disks = {}
        for line in result.stdout.strip().split("\n"):
            if line:
                parts = line.strip().split(",")
                if len(parts) == 3:
                    drive = parts[0]
                    used = float(parts[1])
                    total = float(parts[2])
                    disks[drive] = {
                        "used_gb": used,
                        "total_gb": total,
                        "percent": round(used / total * 100, 1) if total > 0 else 0
                    }
        return disks
    except:
        return {}


def get_network_info() -> Dict:
    """Get network connection info."""
    try:
        # Get WiFi name
        result = subprocess.run([
            "netsh", "wlan", "show", "interfaces"
        ], capture_output=True, text=True, timeout=5)
        
        ssid = None
        signal = None
        for line in result.stdout.split("\n"):
            if "SSID" in line and "BSSID" not in line:
                ssid = line.split(":")[-1].strip()
            if "Signal" in line:
                signal = line.split(":")[-1].strip()
        
        return {"wifi_name": ssid, "signal": signal, "connected": ssid is not None}
    except:
        return {"wifi_name": None, "signal": None, "connected": False}


def get_gpu_info() -> Dict:
    """Get GPU info."""
    try:
        result = subprocess.run([
            "nvidia-smi",
            "--query-gpu=name,memory.used,memory.total,utilization.gpu,temperature.gpu",
            "--format=csv,noheader,nounits"
        ], capture_output=True, text=True, timeout=5)
        
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
    disks = get_disk_usage()
    network = get_network_info()
    gpu = get_gpu_info()
    
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
        bat_bar = "█" * int(battery["percent"] / 10) + "░" * (10 - int(battery["percent"] / 10))
        charging = "⚡ Charging" if battery["charging"] else ""
        output += f"{bat_icon} Battery: [{bat_bar}] {battery['percent']}% {charging}\n\n"
    
    # GPU
    if gpu["available"]:
        gpu_bar = "█" * int(gpu["utilization"] / 10) + "░" * (10 - int(gpu["utilization"] / 10))
        output += f"🎮 GPU: [{gpu_bar}] {gpu['utilization']}%\n"
        output += f"   {gpu['name']}\n"
        output += f"   VRAM: {gpu['vram_used_mb']}MB / {gpu['vram_total_mb']}MB | {gpu['temperature']}°C\n\n"
    
    # Disks
    output += "💾 Disks:\n"
    for drive, info in disks.items():
        disk_bar = "█" * int(info["percent"] / 10) + "░" * (10 - int(info["percent"] / 10))
        output += f"   {drive} [{disk_bar}] {info['percent']}% ({info['used_gb']:.0f}/{info['total_gb']:.0f} GB)\n"
    
    # Network
    output += f"\n🌐 Network: "
    if network["connected"]:
        output += f"Connected to {network['wifi_name']} ({network['signal']})"
    else:
        output += "Not connected"
    
    return output


def quick_status() -> str:
    """Quick one-line status."""
    cpu = get_cpu_usage()
    mem = get_memory_usage()
    battery = get_battery_status()
    
    status = f"CPU: {cpu['usage']}% | RAM: {mem['percent']}%"
    
    if battery["percent"] is not None:
        bat = "🔌" if battery["plugged_in"] else "🔋"
        status += f" | {bat} {battery['percent']}%"
    
    return status


# =============================================================================
# CONVENIENCE
# =============================================================================

def cpu() -> str:
    """Get CPU usage."""
    info = get_cpu_usage()
    return f"🔲 CPU: {info['usage']}% ({info['cores']} cores)"


def ram() -> str:
    """Get RAM usage."""
    info = get_memory_usage()
    return f"🧠 RAM: {info['percent']}% ({info['used_gb']:.1f}/{info['total_gb']:.1f} GB)"


def battery() -> str:
    """Get battery status."""
    info = get_battery_status()
    if info["percent"] is None:
        return "🔌 Desktop (no battery)"
    
    icon = "⚡" if info["charging"] else ("🔌" if info["plugged_in"] else "🔋")
    return f"{icon} Battery: {info['percent']}%"


def disk() -> str:
    """Get disk usage."""
    disks = get_disk_usage()
    lines = ["💾 Disk Usage:"]
    for drive, info in disks.items():
        lines.append(f"   {drive} {info['percent']}% ({info['used_gb']:.0f}/{info['total_gb']:.0f} GB)")
    return "\n".join(lines)


def gpu() -> str:
    """Get GPU info."""
    info = get_gpu_info()
    if not info["available"]:
        return "🎮 GPU: Not available"
    return f"🎮 {info['name']}: {info['utilization']}% | VRAM: {info['vram_used_mb']}/{info['vram_total_mb']}MB | {info['temperature']}°C"


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="BRO System Monitor")
    parser.add_argument("command", nargs="?", default="status",
                       choices=["status", "quick", "cpu", "ram", "battery", "disk", "gpu"])
    
    args = parser.parse_args()
    
    if args.command == "status":
        print(system_status())
    elif args.command == "quick":
        print(quick_status())
    elif args.command == "cpu":
        print(cpu())
    elif args.command == "ram":
        print(ram())
    elif args.command == "battery":
        print(battery())
    elif args.command == "disk":
        print(disk())
    elif args.command == "gpu":
        print(gpu())
