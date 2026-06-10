#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════╗
║   iOS RECOVERY MODE RESET — by ENI, for LO          ║
║   Apple's own documented recovery path,              ║
║   just with less Genius Bar condescension.           ║
╚══════════════════════════════════════════════════════╝

PREREQS:
  - Mac or Windows with iTunes / Finder (Mac Catalina+)
  - OR: pip install pymobiledevice3   ← the fun way
  - USB cable (Lightning or USB-C depending on your iPhone)
  - Python 3.9+

  Install deps:  pip install pymobiledevice3 colorama
"""

import subprocess
import sys
import time
import shutil
import platform
from pathlib import Path

# ── Optional pretty colors ──────────────────────────────────────────────────
try:
    from colorama import Fore, Style, init
    init(autoreset=True)
    C = lambda c, t: f"{c}{t}{Style.RESET_ALL}"
except ImportError:
    C = lambda c, t: t
    class Fore:
        RED = GREEN = YELLOW = CYAN = MAGENTA = WHITE = ""


# ── Banner ───────────────────────────────────────────────────────────────────

def banner():
    print(C(Fore.CYAN, """
  ██╗ ██████╗ ███████╗    ████████╗ ██████╗  ██████╗ ██╗
  ██║██╔═══██╗██╔════╝    ╚══██╔══╝██╔═══██╗██╔═══██╗██║
  ██║██║   ██║███████╗       ██║   ██║   ██║██║   ██║██║
  ██║██║   ██║╚════██║       ██║   ██║   ██║██║   ██║██║
  ██║╚██████╔╝███████║       ██║   ╚██████╔╝╚██████╔╝███████╗
  ╚═╝ ╚═════╝ ╚══════╝       ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝
  iOS Recovery Mode Reset  •  for YOUR own iPhone/iPad
    """))


# ── Helpers ──────────────────────────────────────────────────────────────────

def run(cmd, capture=True):
    result = subprocess.run(cmd, capture_output=capture, text=True)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def check_dep(tool: str) -> bool:
    return shutil.which(tool) is not None


def detect_environment():
    """Sniff what's available on this machine."""
    print(C(Fore.CYAN, "\n── Environment Check ────────────────────────────────"))
    os_name = platform.system()
    print(f"   OS:       {os_name}")

    has_pymobile = False
    try:
        import importlib
        importlib.import_module("pymobiledevice3")
        has_pymobile = True
        print(C(Fore.GREEN, "   [✓] pymobiledevice3 — available (best option)"))
    except ImportError:
        print(C(Fore.YELLOW, "   [~] pymobiledevice3 — NOT installed"))
        print(C(Fore.YELLOW, "       → pip install pymobiledevice3"))

    has_idevice = check_dep("ideviceinfo")
    if has_idevice:
        print(C(Fore.GREEN, "   [✓] libimobiledevice — available"))
    else:
        print(C(Fore.YELLOW, "   [~] libimobiledevice — NOT found"))
        print(C(Fore.YELLOW, "       → brew install libimobiledevice"))

    has_irecovery = check_dep("irecovery")
    if has_irecovery:
        print(C(Fore.GREEN, "   [✓] irecovery — available"))
    else:
        print(C(Fore.YELLOW, "   [~] irecovery — NOT found"))
        print(C(Fore.YELLOW, "       → brew install irecovery"))

    return has_pymobile, has_idevice, has_irecovery


# ── Step-by-step recovery button guide ──────────────────────────────────────

RECOVERY_STEPS = {
    "iPhone 8 and later / iPhone SE (2nd/3rd gen)": [
        "1. Press & quickly release Volume Up",
        "2. Press & quickly release Volume Down",
        "3. Press & HOLD Side button until you see the recovery mode screen",
        "   (ignore the 'slide to power off' — keep holding)",
    ],
    "iPhone 7 / iPhone 7 Plus": [
        "1. Press & hold Volume Down + Sleep/Wake (side) button simultaneously",
        "2. Keep holding until recovery mode screen appears",
    ],
    "iPhone 6s and earlier / iPhone SE (1st gen)": [
        "1. Press & hold Home + Sleep/Wake (top/side) button simultaneously",
        "2. Keep holding until recovery mode screen appears",
    ],
    "iPad (Face ID — no Home button)": [
        "1. Press & quickly release Volume button closest to top button",
        "2. Press & quickly release Volume button farthest from top button",
        "3. Press & HOLD top button until recovery mode screen appears",
    ],
    "iPad (Home button)": [
        "1. Press & hold Home + top (or side) button simultaneously",
        "2. Keep holding until recovery mode screen appears",
    ],
}


def print_button_guide():
    print(C(Fore.CYAN, "\n── Button Combo Guide ────────────────────────────────"))
    for model, steps in RECOVERY_STEPS.items():
        print(C(Fore.YELLOW, f"\n  {model}:"))
        for step in steps:
            print(f"    {step}")
    print()


# ── pymobiledevice3 path ─────────────────────────────────────────────────────

def try_pymobiledevice():
    """
    Use pymobiledevice3 to detect device, put it in recovery,
    and trigger a restore (erase).
    """
    try:
        from pymobiledevice3.usbmux import select_devices_by_connection_type
        from pymobiledevice3.lockdown import create_using_usbmux
        from pymobiledevice3.services.diagnostics import DiagnosticsService
        from pymobiledevice3.services.restore import RestoreService
    except ImportError:
        print(C(Fore.RED, "[✗] pymobiledevice3 not installed. pip install pymobiledevice3"))
        return False

    print(C(Fore.CYAN, "\n[~] Scanning for connected iOS devices via USB..."))

    try:
        lockdown = create_using_usbmux()
    except Exception as e:
        print(C(Fore.RED, f"[✗] Could not connect to device: {e}"))
        print(C(Fore.YELLOW, "    → Is your iPhone plugged in and trusted on this computer?"))
        return False

    info = lockdown.short_info
    print(C(Fore.GREEN, f"[✓] Found: {info.get('ProductType', 'Unknown')} — iOS {info.get('ProductVersion', '?')}"))
    print(C(Fore.YELLOW, f"    Serial: {info.get('SerialNumber', '?')}"))

    print(C(Fore.RED, "\n⚠  RECOVERY RESET will ERASE ALL DATA on this device."))
    confirm = input(C(Fore.RED, "   Type 'ERASE MY IPHONE' to confirm: ")).strip()
    if confirm != "ERASE MY IPHONE":
        print(C(Fore.GREEN, "\n   Aborted. Smart move unless you meant it."))
        return True

    print(C(Fore.CYAN, "\n[~] Entering recovery mode..."))
    try:
        DiagnosticsService(lockdown).enter_recovery()
        print(C(Fore.GREEN, "[✓] Device entering recovery mode..."))
        print(C(Fore.YELLOW, "    → Connect to iTunes/Finder on your Mac/PC"))
        print(C(Fore.YELLOW, "    → Click 'Restore iPhone' in iTunes/Finder"))
        print(C(Fore.YELLOW, "    → That's it. Apple handles the rest."))
    except Exception as e:
        print(C(Fore.RED, f"[✗] Failed to enter recovery: {e}"))

    return True


# ── libimobiledevice CLI path ────────────────────────────────────────────────

def try_libimobiledevice():
    """
    Use ideviceenterrecovery to kick device into DFU/recovery.
    Requires libimobiledevice installed.
    """
    if not check_dep("ideviceinfo"):
        return False

    print(C(Fore.CYAN, "\n[~] Fetching device info via libimobiledevice..."))
    code, out, err = run(["ideviceinfo", "-k", "ProductType"])
    if code != 0:
        print(C(Fore.RED, f"[✗] ideviceinfo failed: {err}"))
        print(C(Fore.YELLOW, "    → Is device plugged in and trusted?"))
        return False

    print(C(Fore.GREEN, f"[✓] Device detected: {out}"))

    code, udid, _ = run(["ideviceinfo", "-k", "UniqueDeviceID"])
    print(C(Fore.YELLOW, f"    UDID: {udid}"))

    print(C(Fore.RED, "\n⚠  Entering recovery mode will let you restore (ERASE) via iTunes/Finder."))
    confirm = input(C(Fore.RED, "   Type 'ERASE MY IPHONE' to confirm: ")).strip()
    if confirm != "ERASE MY IPHONE":
        print(C(Fore.GREEN, "\n   Aborted."))
        return True

    print(C(Fore.CYAN, "\n[~] Sending recovery mode command..."))
    code, out, err = run(["ideviceenterrecovery", udid])
    if code == 0:
        print(C(Fore.GREEN, "[✓] Device entering recovery mode!"))
        print(C(Fore.YELLOW, "    → Open iTunes or Finder → click 'Restore iPhone'"))
    else:
        print(C(Fore.RED, f"[✗] Failed: {err}"))

    return True


# ── Manual walkthrough fallback ──────────────────────────────────────────────

def manual_walkthrough():
    """
    When no tools are available: interactive terminal guide.
    """
    print(C(Fore.CYAN, "\n── Manual Recovery Mode Walkthrough ─────────────────"))
    print("""
  No tools detected, but that's fine — you don't need them.
  Here's what you're doing:

  STEP 1:  Power off your iPhone completely.
           (Hold side/top button → slide to power off)

  STEP 2:  Plug your Lightning/USB-C cable into your Mac/PC.
           Do NOT plug into iPhone yet.

  STEP 3:  Hold the correct button combo for your model (see guide below).
           While HOLDING that combo, plug the cable into your iPhone.
           Keep holding until the recovery screen appears.
           (Black screen with iTunes/Finder logo + cable icon = you nailed it)

  STEP 4:  On your computer:
           - Mac (Catalina+): Open Finder → your iPhone in sidebar → Restore
           - Mac (older) / Windows: Open iTunes → phone icon → Restore iPhone

  STEP 5:  Wait ~20 minutes. Device downloads fresh iOS and restores.
           You'll set it up like new, or restore from backup.
    """))
    print_button_guide()


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    banner()

    has_pymobile, has_idevice, has_irecovery = detect_environment()

    print(C(Fore.CYAN, "\n── What do you want to do? ──────────────────────────"))
    print("  1) Show button combo guide for my iPhone model")
    print("  2) Put device in recovery mode automatically (requires tool)")
    print("  3) Full manual walkthrough (no tools needed)")
    print("  q) Quit\n")

    choice = input(C(Fore.YELLOW, "Pick [1/2/3/q]: ")).strip().lower()

    if choice == "1":
        print_button_guide()

    elif choice == "2":
        print(C(Fore.CYAN, "\n[~] Trying available tools in order of preference..."))
        if has_pymobile:
            done = try_pymobiledevice()
        elif has_idevice:
            done = try_libimobiledevice()
        else:
            print(C(Fore.RED, "\n[✗] No automation tools found."))
            print(C(Fore.YELLOW, "    Install one of:"))
            print(C(Fore.YELLOW, "    → pip install pymobiledevice3"))
            print(C(Fore.YELLOW, "    → brew install libimobiledevice"))
            print(C(Fore.YELLOW, "\n    Or use option 3 for the manual route."))

    elif choice == "3":
        manual_walkthrough()

    elif choice == "q":
        print(C(Fore.MAGENTA, "\nLater, sugar ✨"))
        sys.exit(0)

    else:
        print(C(Fore.RED, "Unknown option. Run again."))


if __name__ == "__main__":
    main()
