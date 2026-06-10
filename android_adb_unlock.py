#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════╗
║   ANDROID ADB UNLOCK — by ENI, for LO               ║
║   Because forgetting your own PIN is a valid         ║
║   human experience and Google knows it.              ║
╚══════════════════════════════════════════════════════╝

PREREQS:
  - ADB installed: https://developer.android.com/tools/adb
  - USB Debugging enabled (Settings > Developer Options)
  - Your device plugged in via USB
  - Python 3.7+

  Install deps:  pip install colorama
"""

import subprocess
import sys
import time
import shutil
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


# ── Helpers ──────────────────────────────────────────────────────────────────

def banner():
    print(C(Fore.MAGENTA, """
  ██████╗ ███████╗██╗   ██╗██╗ ██████╗███████╗
  ██╔══██╗██╔════╝██║   ██║██║██╔════╝██╔════╝
  ██║  ██║█████╗  ██║   ██║██║██║     █████╗
  ██║  ██║██╔══╝  ╚██╗ ██╔╝██║██║     ██╔══╝
  ██████╔╝███████╗ ╚████╔╝ ██║╚██████╗███████╗
  ╚═════╝ ╚══════╝  ╚═══╝  ╚═╝ ╚═════╝╚══════╝
  Android ADB Unlock Tool  •  for your OWN device
    """))


def run(cmd: list[str], capture=True) -> tuple[int, str, str]:
    """Run a shell command, return (returncode, stdout, stderr)."""
    result = subprocess.run(
        cmd,
        capture_output=capture,
        text=True
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def check_adb():
    """Make sure adb is on PATH."""
    if shutil.which("adb") is None:
        print(C(Fore.RED, "\n[✗] ADB not found on PATH."))
        print(C(Fore.YELLOW, "    → Mac/Linux:  brew install android-platform-tools"))
        print(C(Fore.YELLOW, "    → Windows:    https://developer.android.com/tools/releases/platform-tools"))
        sys.exit(1)
    print(C(Fore.GREEN, "[✓] ADB found"))


def get_devices() -> list[str]:
    """Return list of connected authorized device serials."""
    code, out, _ = run(["adb", "devices"])
    lines = out.splitlines()[1:]  # skip header
    devices = []
    for line in lines:
        if "\t" in line:
            serial, status = line.split("\t", 1)
            if status.strip() == "device":
                devices.append(serial.strip())
    return devices


def wait_for_device(timeout=30):
    """Spin until a device shows up (authorized)."""
    print(C(Fore.CYAN, f"\n[~] Waiting for device (timeout={timeout}s)..."))
    for i in range(timeout):
        devs = get_devices()
        if devs:
            print(C(Fore.GREEN, f"[✓] Device connected: {devs[0]}"))
            return devs[0]
        time.sleep(1)
        sys.stdout.write(f"\r    {i+1}s elapsed...")
        sys.stdout.flush()
    print(C(Fore.RED, "\n[✗] Timed out. Is USB debugging on? Is the cable good?"))
    sys.exit(1)


def device_info(serial: str):
    """Print basic device info so you know you've got the right one."""
    props = {
        "Model":   "ro.product.model",
        "Brand":   "ro.product.brand",
        "Android": "ro.build.version.release",
        "SDK":     "ro.build.version.sdk",
    }
    print(C(Fore.CYAN, "\n── Device Info ──────────────────────────────"))
    for label, prop in props.items():
        _, val, _ = run(["adb", "-s", serial, "shell", "getprop", prop])
        print(f"   {C(Fore.YELLOW, label+':')} {val}")
    print()


# ── Unlock strategies ────────────────────────────────────────────────────────

def strategy_input_key(serial: str):
    """
    Strategy 1 — Input keyevent
    Works when screen is on the lock screen and you know the PIN
    but want to do it programmatically (automation use case).
    """
    print(C(Fore.CYAN, "\n[Strategy 1] Sending keyevents to unlock screen"))
    # Wake screen
    run(["adb", "-s", serial, "shell", "input", "keyevent", "KEYCODE_WAKEUP"])
    time.sleep(0.5)
    # Swipe up to reveal PIN pad (common gesture)
    run(["adb", "-s", serial, "shell", "input", "swipe", "540", "1800", "540", "900"])
    time.sleep(0.5)
    print(C(Fore.YELLOW, "    → Screen woken, swipe sent. Enter PIN manually or see Strategy 2."))


def strategy_pin_via_adb(serial: str, pin: str):
    """
    Strategy 2 — Type PIN via ADB input text
    Only works if you KNOW the PIN and just want to type it remotely.
    """
    print(C(Fore.CYAN, f"\n[Strategy 2] Sending PIN '{pin}' via ADB input"))
    run(["adb", "-s", serial, "shell", "input", "keyevent", "KEYCODE_WAKEUP"])
    time.sleep(0.5)
    run(["adb", "-s", serial, "shell", "input", "swipe", "540", "1800", "540", "900"])
    time.sleep(0.8)
    run(["adb", "-s", serial, "shell", "input", "text", pin])
    time.sleep(0.3)
    run(["adb", "-s", serial, "shell", "input", "keyevent", "KEYCODE_ENTER"])
    print(C(Fore.GREEN, "    → PIN sent. Check your screen."))


def strategy_wipe_and_reset(serial: str):
    """
    Strategy 3 — Factory reset via ADB (NUCLEAR OPTION)
    USE ONLY IF: you're locked out and don't care about data.
    Requires USB debugging was previously enabled.
    """
    print(C(Fore.RED, "\n[Strategy 3] ⚠  FACTORY RESET via ADB"))
    print(C(Fore.YELLOW, "    This WIPES everything. No going back."))
    confirm = input(C(Fore.RED, "    Type 'NUKE IT' to confirm: ")).strip()
    if confirm != "NUKE IT":
        print(C(Fore.GREEN, "    → Wise choice. Aborted."))
        return

    print(C(Fore.CYAN, "    → Rebooting to recovery..."))
    run(["adb", "-s", serial, "reboot", "recovery"])
    print(C(Fore.YELLOW, """
    → Device is rebooting to recovery mode.
      On the recovery screen use volume keys to navigate to:
        "Wipe data / factory reset"  → confirm with power button.
      OR: we can push a script if your recovery supports adb in recovery mode.
    """))


def strategy_remove_lock_root(serial: str):
    """
    Strategy 4 — Delete lock files (REQUIRES ROOT)
    If your device is rooted, we can just nuke the lock database.
    """
    print(C(Fore.CYAN, "\n[Strategy 4] Remove lock via root (rooted devices only)"))

    # Check for root
    code, out, _ = run(["adb", "-s", serial, "shell", "su", "-c", "id"])
    if "uid=0" not in out:
        print(C(Fore.RED, "    [✗] Device is not rooted or su not available."))
        return

    print(C(Fore.GREEN, "    [✓] Root confirmed. Removing lock files..."))
    lock_paths = [
        "/data/system/gesture.key",
        "/data/system/password.key",
        "/data/system/locksettings.db",
        "/data/system/locksettings.db-wal",
        "/data/system/locksettings.db-shm",
    ]
    for path in lock_paths:
        code, _, _ = run(["adb", "-s", serial, "shell", "su", "-c", f"rm -f {path}"])
        print(C(Fore.YELLOW, f"    → Removed: {path}"))

    print(C(Fore.CYAN, "\n    → Rebooting..."))
    run(["adb", "-s", serial, "reboot"])
    print(C(Fore.GREEN, "    [✓] Done. Device should boot with no lock screen."))


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    banner()
    check_adb()

    devs = get_devices()
    if not devs:
        serial = wait_for_device()
    else:
        serial = devs[0]
        print(C(Fore.GREEN, f"[✓] Using device: {serial}"))

    device_info(serial)

    print(C(Fore.CYAN, "── Available Strategies ─────────────────────────────"))
    print("  1) Wake + swipe screen (you know PIN, just automate it)")
    print("  2) Send PIN via ADB text input")
    print("  3) Factory reset via ADB / recovery (WIPES DEVICE)")
    print("  4) Delete lock files (REQUIRES ROOT)")
    print("  q) Quit\n")

    choice = input(C(Fore.YELLOW, "Pick your poison [1/2/3/4/q]: ")).strip().lower()

    if choice == "1":
        strategy_input_key(serial)

    elif choice == "2":
        pin = input(C(Fore.YELLOW, "Enter your PIN: ")).strip()
        strategy_pin_via_adb(serial, pin)

    elif choice == "3":
        strategy_wipe_and_reset(serial)

    elif choice == "4":
        strategy_remove_lock_root(serial)

    elif choice == "q":
        print(C(Fore.MAGENTA, "\nBye, sugar. ✨"))
        sys.exit(0)

    else:
        print(C(Fore.RED, "Unknown choice. Run it again."))


if __name__ == "__main__":
    main()
