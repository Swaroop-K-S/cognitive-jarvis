# BRO Android Controller - Wireless Setup

## Quick Start: Wireless Control

Control your Android phone from your PC **without any cables** (after one-time setup).

### One-Time Setup (Requires USB)

1. **Enable USB Debugging:**
   - Settings > About Phone > Tap "Build Number" 7 times
   - Settings > Developer Options > Enable "USB Debugging"

2. **Connect via USB** (just once)

3. **Enable WiFi Mode:**
   ```powershell
   cd "c:\Users\swaro\Code\New folder (3)\BRO"
   python tools/android_control.py enable-wifi
   ```
   This shows your phone's IP address.

4. **Disconnect USB** - you won't need it again!

### Daily Wireless Use

```powershell
# Connect wirelessly (replace with your phone's IP)
python tools/android_control.py wifi 192.168.1.100

# Control your phone!
python tools/android_control.py open youtube
python tools/android_control.py swipe up
python tools/android_control.py type "Hello"
```

### Find Your Phone's IP

- Settings > About Phone > Status > IP Address
- Or: Settings > WiFi > Tap connected network > IP Address

### Commands

| Command | Description |
|:--------|:------------|
| `wifi <IP>` | Connect wirelessly |
| `open <app>` | Open app (youtube, whatsapp, chrome) |
| `swipe <dir>` | Swipe up/down/left/right |
| `tap <X> <Y>` | Tap coordinates |
| `type <text>` | Type text |
| `home` | Press home button |
| `back` | Press back button |
| `screen` | Take screenshot |

### Supported Apps

YouTube, WhatsApp, Chrome, Instagram, Spotify, Telegram, Gmail, Maps, Settings, Camera, and more!

### Troubleshooting

**"Connection refused"**
- Make sure phone and PC are on same WiFi network
- Re-run `enable-wifi` command with USB

**"ADB not found"**
- Install Android Platform Tools
- Download: https://developer.android.com/studio/releases/platform-tools
- Add to PATH

**WiFi disconnects after phone sleep**
- Re-connect with `wifi <IP>` command
- Or keep phone screen on during use
