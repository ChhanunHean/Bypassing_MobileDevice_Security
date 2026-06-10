# 📱 device-tools

> **Your own phone. Your own problem. Let's fix it.**

[![Python](https://img.shields.io/badge/Python-3.7%2B-blue?style=flat-square&logo=python)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Android%20%7C%20iOS-green?style=flat-square)]()
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)]()
[![ADB](https://img.shields.io/badge/ADB-Required%20for%20Android-orange?style=flat-square&logo=android)]()

A small collection of Python scripts for recovering **your own** Android or iOS device when you're locked out, forgotten your PIN, or just want to automate unlock flows. All methods documented here are publicly available through Google and Apple's own developer documentation.

---

## 📂 Scripts

| File | Platform | What it does |
|------|----------|--------------|
| [`android_forgot_pin.py`](#-android-forgot-pin) | Android | Full triage + recovery when you've forgotten your PIN |
| [`android_adb_unlock.py`](#-android-adb-unlock) | Android | Automation tool when you know your PIN |
| [`ios_recovery_reset.py`](#-ios-recovery-mode-reset) | iOS | Put your iPhone/iPad into recovery mode and restore |

---

## ⚙️ Requirements

### General
- Python 3.7+
- `pip install colorama` — pretty terminal output (optional but nice)

### For Android scripts
```bash
# macOS / Linux
brew install android-platform-tools

# Windows
# Download from: https://developer.android.com/tools/releases/platform-tools
# Add to PATH
```

### For iOS script
```bash
# Option 1 — Python library (recommended)
pip install pymobiledevice3

# Option 2 — CLI tools
brew install libimobiledevice irecovery
```

---

## 🤖 Android — Forgot PIN

**File:** `android_forgot_pin.py`

The main recovery script. Starts with a **2-question triage** to figure out which paths are actually available to you, then routes you accordingly. No wasted time going down dead ends.

### Decision tree

```
Was USB Debugging ON before lockout?
├── YES
│   ├── Device is Rooted?
│   │   ├── YES → Path A: Delete lock DB  ← best, no data loss
│   │   │         Path B: Factory reset via ADB
│   │   │         Path C: Bruteforce PIN (4–6 digit only)
│   │   │         Path D: Google Find My Device
│   │   └── NO  → Path B: Factory reset via ADB
│   │             Path C: Bruteforce PIN
│   │             Path D: Google Find My Device
└── NO
    → Path D: Google Find My Device
      Path E: OEM account (Samsung / Xiaomi / OnePlus)
      Path F: Hardware button factory reset
```

### Paths explained

#### Path A — Delete Lock DB *(Rooted + USB Debugging, no data loss)*
Removes the credential files Android uses to verify your PIN. Works across Android 4 through 14. All your data stays. This is the cleanest option.

Files it targets:
```
/data/system/gesture.key
/data/system/password.key
/data/system/locksettings.db  (+wal, +shm)
/data/system/gatekeeper.password.key
/data/system/gatekeeper.pattern.key
/data/system/gatekeeper.pin.key
```

#### Path B — Factory Reset via ADB *(USB Debugging was ON)*
Reboots to recovery and wipes. **Data is gone.** Only use if you have a backup or don't care.

#### Path C — PIN Bruteforce *(USB Debugging was ON, 4–6 digit PINs)*
Automates PIN guesses via ADB input. Each attempt ~1.5s. Supports custom start/end range. Stops immediately on success.

> ⚠️ Only practical for 4-digit PINs (~4hrs max sweep). 6-digit is 1M combos — worth it if you remember part of the PIN and can narrow the range.

#### Path D — Google Find My Device *(phone must be online)*
Opens [myaccount.google.com/find-your-phone](https://myaccount.google.com/find-your-phone). Use **Lock** to set a temporary password that overrides your forgotten PIN.

#### Path E — OEM Account Unlock
- Samsung: [findmymobile.samsung.com](https://findmymobile.samsung.com)
- Xiaomi: [i.mi.com](https://i.mi.com)
- OnePlus: [account.oneplus.com](https://account.oneplus.com)

#### Path F — Hardware Button Factory Reset *(no computer needed)*
Physical button combos to boot into recovery mode. Works on any Android. Wipes device.

| Brand | Combo |
|-------|-------|
| Samsung Galaxy | Vol Up + Power (newer) or Vol Up + Bixby + Power |
| Google Pixel | Power + Vol Down → Recovery |
| Xiaomi / Redmi | Vol Up + Power |
| OnePlus | Vol Down + Power |
| LG | Vol Down + Power |

### Usage

```bash
pip install colorama
python android_forgot_pin.py
```

---

## 🤖 Android — ADB Unlock (know your PIN, just automating)

**File:** `android_adb_unlock.py`

Simpler tool for when you know your PIN but want to type it or control the device programmatically over USB. Also includes the root delete-lock path.

```bash
python android_adb_unlock.py
```

---

## 🍎 iOS — Recovery Mode Reset

**File:** `ios_recovery_reset.py`

Three modes:

| Mode | What it does | Needs |
|------|--------------|-------|
| Button guide | Prints exact button combo for your iPhone model | Nothing |
| Auto recovery | Puts device in recovery mode via software | pymobiledevice3 or libimobiledevice |
| Manual walkthrough | Step-by-step guide using just a cable | Just a USB cable + iTunes/Finder |

### Button combos by model

| Model | Combo |
|-------|-------|
| iPhone 8+ / SE 2nd/3rd | Vol Up → Vol Down → Hold Side button |
| iPhone 7 / 7 Plus | Hold Vol Down + Side simultaneously |
| iPhone 6s and earlier / SE 1st | Hold Home + Top/Side simultaneously |
| iPad (Face ID) | Vol Up → Vol Down → Hold Top button |
| iPad (Home button) | Hold Home + Top/Side simultaneously |

### Recovery restore flow

1. Put device in recovery mode (script or button combo)
2. Connect to Mac/PC
3. **Mac (Catalina+):** Finder → your iPhone → **Restore**
4. **Mac (older) / Windows:** iTunes → phone icon → **Restore iPhone**
5. Wait ~20 min. Done.

### Usage

```bash
pip install pymobiledevice3 colorama
python ios_recovery_reset.py
```

---

## 🔒 Important Notes

- **These tools only work on your own device.** Android's ADB requires the device to have previously authorized your computer (USB debugging on + trust prompt accepted). iOS requires you to have trusted the computer before.
- **USB Debugging must have been enabled *before* lockout** for ADB to work. If it wasn't on, ADB cannot communicate with a locked device — use Google/OEM/hardware routes instead.
- **iOS recovery erases the device.** Apple's restore process is a full wipe. Restore from iCloud/iTunes backup afterwards.
- **Root (Android Path A)** leaves your data intact — it's the surgical option vs the nuclear factory reset.

---

## 📦 Install everything at once

```bash
pip install colorama pymobiledevice3
brew install android-platform-tools libimobiledevice
```

---

## 📄 License

MIT — do whatever you want, it's your phone.

---

*Built with way too much coffee and mild personal frustration at forgetting PINs.*
