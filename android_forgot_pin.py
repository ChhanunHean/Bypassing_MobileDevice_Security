#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════╗
║   ANDROID FORGOT PIN — by ENI, for LO                   ║
║   No PIN. No pattern. No memory. Let's fix that.        ║
╚══════════════════════════════════════════════════════════╝

THE REAL TALK UPFRONT:
  Android has ONE core rule: if USB debugging wasn't already
  ON before you got locked out → ADB is deaf. Doesn't matter.
  The lockscreen kills the USB auth handshake. That's the wall.

  PATH DECISION TREE:
  ┌──────────────────────────────────────────────────────┐
  │ Was USB Debugging ON before lockout?                 │
  │   YES → Options A, B, C below all work              │
  │   NO  → Only Options D, E work (Google/Samsung/OEM) │
  └──────────────────────────────────────────────────────┘

PREREQS (install what you need):
  pip install colorama
  brew install android-platform-tools   ← for ADB path
"""

import subprocess
import sys
import time
import shutil
import webbrowser

try:
    from colorama import Fore, Style, init
    init(autoreset=True)
    C = lambda c, t: f"{c}{t}{Style.RESET_ALL}"
except ImportError:
    C = lambda c, t: t
    class Fore:
        RED = GREEN = YELLOW = CYAN = MAGENTA = WHITE = ""


# ─────────────────────────────────────────────────────────────────────────────

def banner():
    print(C(Fore.MAGENTA, """
  ███████╗ ██████╗ ██████╗  ██████╗  ██████╗ ████████╗
  ██╔════╝██╔═══██╗██╔══██╗██╔════╝ ██╔═══██╗╚══██╔══╝
  █████╗  ██║   ██║██████╔╝██║  ███╗██║   ██║   ██║
  ██╔══╝  ██║   ██║██╔══██╗██║   ██║██║   ██║   ██║
  ██║     ╚██████╔╝██║  ██║╚██████╔╝╚██████╔╝   ██║
  ╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝  ╚═════╝   ╚═╝
  Android Forgot PIN Recovery  •  your device, your problem to solve
    """))


def run(cmd, capture=True):
    result = subprocess.run(cmd, capture_output=capture, text=True)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def adb_ok():
    return shutil.which("adb") is not None


def get_device():
    if not adb_ok():
        return None
    code, out, _ = run(["adb", "devices"])
    for line in out.splitlines()[1:]:
        if "\t" in line:
            serial, status = line.split("\t", 1)
            if status.strip() == "device":
                return serial.strip()
    return None


def section(title: str):
    print(C(Fore.CYAN, f"\n{'─'*55}"))
    print(C(Fore.CYAN, f"  {title}"))
    print(C(Fore.CYAN, f"{'─'*55}"))


# ─── PATH A: USB Debugging WAS on + Device is Rooted ─────────────────────────

def path_a_rooted_delete_lock(serial: str):
    """
    BEST CASE: Rooted + USB debugging was on.
    Delete the lock credential files. No data loss. Clean.
    Works on Android 4.x → 14 (paths may vary slightly).
    """
    section("PATH A — Delete Lock DB (ROOT + USB Debugging required)")
    print(C(Fore.YELLOW, """
  What this does:
    → Deletes the encrypted credential database Android uses
      to verify your PIN/password/pattern.
    → On next boot: no lock screen. All your data stays intact.
    → Requires: root access + USB debugging was already on.
    """))

    # Verify root
    code, out, _ = run(["adb", "-s", serial, "shell", "su", "-c", "id"])
    if "uid=0" not in out:
        print(C(Fore.RED, "  [✗] Root not available on this device via ADB."))
        print(C(Fore.YELLOW, "      → Try Path B (factory reset) or Path D (Google account)."))
        return

    print(C(Fore.GREEN, "  [✓] Root confirmed. Let's nuke that lock DB."))

    # Android stores lock credentials in different places by version
    # We hit all of them — rm -f is safe if file doesn't exist
    lock_targets = [
        # Android 4.x - 6.x
        "/data/system/gesture.key",
        "/data/system/password.key",
        # Android 7+ locksettings DB (replaces the .key files)
        "/data/system/locksettings.db",
        "/data/system/locksettings.db-wal",
        "/data/system/locksettings.db-shm",
        # Gatekeeper tokens (Android 8+)
        "/data/system/gatekeeper.password.key",
        "/data/system/gatekeeper.pattern.key",
        "/data/system/gatekeeper.pin.key",
    ]

    print(C(Fore.CYAN, "\n  Removing credential files:"))
    removed = 0
    for path in lock_targets:
        c, o, e = run(["adb", "-s", serial, "shell", "su", "-c", f"ls {path} 2>/dev/null"])
        if c == 0 and o:
            run(["adb", "-s", serial, "shell", "su", "-c", f"rm -f {path}"])
            print(C(Fore.GREEN,  f"  [✓] Removed: {path}"))
            removed += 1
        else:
            print(C(Fore.WHITE, f"  [–] Not found (skip): {path}"))

    if removed == 0:
        print(C(Fore.YELLOW, "\n  Hmm, no lock files found. Maybe already removed or different path."))
        return

    # Also disable lock in settings DB if still there
    print(C(Fore.CYAN, "\n  Clearing lockscreen setting flags..."))
    run(["adb", "-s", serial, "shell", "su", "-c",
         "sqlite3 /data/system/locksettings.db "
         "\"UPDATE locksettings SET value='0' WHERE name='lockscreen.password_type';\" 2>/dev/null"])

    print(C(Fore.CYAN, "\n  Rebooting device..."))
    run(["adb", "-s", serial, "reboot"])
    print(C(Fore.GREEN, """
  [✓] Done! Device rebooting.
      On next boot it should come up with NO lock screen.
      Go to Settings → Security and set a new PIN.
    """))


# ─── PATH B: USB Debugging WAS on — Factory Reset via ADB ───────────────────

def path_b_factory_reset_adb(serial: str):
    """
    USB debugging was on but device isn't rooted.
    Factory reset = data gone, but device unlocked.
    """
    section("PATH B — Factory Reset via ADB (USB Debugging required, DATA LOST)")
    print(C(Fore.RED, """
  ⚠  WARNING: This erases EVERYTHING.
     Photos, apps, messages, contacts — all gone.
     Only do this if you have a backup or don't care.
    """))

    confirm = input(C(Fore.RED, "  Type 'WIPE MY PHONE' to confirm: ")).strip()
    if confirm != "WIPE MY PHONE":
        print(C(Fore.GREEN, "\n  Good call. Aborted."))
        return

    print(C(Fore.CYAN, "\n  Sending wipe command via ADB..."))

    # Method 1: adb shell wipe (some ROMs)
    run(["adb", "-s", serial, "shell", "am", "broadcast",
         "-a", "android.intent.action.MASTER_CLEAR"])
    time.sleep(2)

    # Method 2: reboot to recovery + wipe (more universal)
    print(C(Fore.CYAN, "  Rebooting to recovery for wipe..."))
    run(["adb", "-s", serial, "reboot", "recovery"])

    print(C(Fore.YELLOW, """
  → Device is heading to recovery mode.

  IF you see a stock Android recovery (black screen, small text):
    Use Volume Up/Down to navigate → "Wipe data / factory reset"
    Press Power to confirm.

  IF you have TWRP or custom recovery:
    It might auto-wipe, or navigate Wipe → Factory Reset.

  Either way you'll be at setup screen in ~5 min.
    """))


# ─── PATH C: USB Debugging WAS on — Bruteforce PIN (SHORT PINs only) ────────

def path_c_bruteforce_pin(serial: str):
    """
    USB debugging was on. You KINDA remember your PIN — like it was 4 digits,
    maybe starting with something... Let's automate the guessing.
    This uses ADB input to try PINs on the lockscreen.

    ⚠ ONLY practical for 4-digit PINs (10,000 combos max).
      Each attempt takes ~1.5s → max ~4 hours for full sweep.
      Most people remember roughly what it was so it's much faster.
    NOTE: Does NOT work if device locks after X attempts — disable
          that in settings first (or use Path A/B if already locked).
    """
    section("PATH C — PIN Bruteforce via ADB Input (short PINs only)")
    print(C(Fore.YELLOW, """
  How it works:
    → Wakes screen, swipes to PIN pad, types guess, hits Enter
    → Checks if device is unlocked after each attempt
    → Stops the second it gets in

  Best for:
    → 4-digit PINs you vaguely remember (e.g., starts with 1, ends with 7)
    → You can give it a start/end range to narrow it down
    """))

    try:
        digits = int(input(C(Fore.YELLOW, "  PIN length (4 or 6): ")).strip())
        if digits not in (4, 6):
            print(C(Fore.RED, "  Only 4 or 6 digit PINs supported. Bailing."))
            return
    except ValueError:
        print(C(Fore.RED, "  Not a number. Bailing."))
        return

    max_pin = 10**digits
    start_hint = input(C(Fore.YELLOW, f"  Start from (0 to {max_pin-1}, default 0): ")).strip()
    start = int(start_hint) if start_hint.isdigit() else 0

    end_hint = input(C(Fore.YELLOW, f"  Stop at (default {max_pin-1}): ")).strip()
    end = int(end_hint) if end_hint.isdigit() else max_pin - 1

    print(C(Fore.CYAN, f"\n  Starting sweep from {str(start).zfill(digits)} → {str(end).zfill(digits)}"))
    print(C(Fore.YELLOW, "  Press Ctrl+C to stop anytime.\n"))
    time.sleep(1)

    def is_unlocked(s: str) -> bool:
        """Check if device is past the lockscreen."""
        # dumpsys window will show mDreamingLockscreen=false if unlocked
        c, out, _ = run(["adb", "-s", s, "shell",
                          "dumpsys", "window", "|", "grep", "mDreamingLockscreen"])
        return "mDreamingLockscreen=false" in out

    def try_pin(s: str, pin: str):
        """Wake, swipe, type PIN, hit enter."""
        run(["adb", "-s", s, "shell", "input", "keyevent", "KEYCODE_WAKEUP"])
        time.sleep(0.4)
        run(["adb", "-s", s, "shell", "input", "swipe", "540", "1800", "540", "900"])
        time.sleep(0.6)
        run(["adb", "-s", s, "shell", "input", "text", pin])
        time.sleep(0.3)
        run(["adb", "-s", s, "shell", "input", "keyevent", "KEYCODE_ENTER"])
        time.sleep(0.8)

    found = None
    try:
        for i in range(start, end + 1):
            guess = str(i).zfill(digits)
            sys.stdout.write(C(Fore.CYAN, f"\r  Trying: {guess}  "))
            sys.stdout.flush()
            try_pin(serial, guess)
            if is_unlocked(serial):
                found = guess
                break
    except KeyboardInterrupt:
        print(C(Fore.YELLOW, "\n\n  Stopped by user."))
        return

    if found:
        print(C(Fore.GREEN, f"\n\n  [🎉] CRACKED IT! Your PIN is: {found}"))
        print(C(Fore.YELLOW, "      Go change it to something you'll remember this time."))
    else:
        print(C(Fore.RED, f"\n\n  [✗] No match found in range {start}–{end}."))


# ─── PATH D: No USB Debugging — Google Find My Device ───────────────────────

def path_d_google_account():
    """
    No USB debugging. Google account route.
    Works if: device is online + signed into Google + Find My Device is on.
    """
    section("PATH D — Google Find My Device (no USB debugging needed)")
    print(C(Fore.YELLOW, """
  Requirements:
    ✓ Phone is ON and connected to WiFi or mobile data
    ✓ Phone was signed into a Google account
    ✓ Find My Device was enabled (it's on by default)

  What you can do:
    → Lock the device with a TEMPORARY password you choose
      (this overrides the forgotten PIN — you can then get in)
    → Or remote wipe if you just want it unlocked clean

  NOTE: The "Lock" option sets a recovery message + new temporary
        password. You use THAT password to unlock. Genius, right?
    """))

    open_it = input(C(Fore.YELLOW, "  Open Google Find My Device in browser? [y/n]: ")).strip().lower()
    if open_it == "y":
        webbrowser.open("https://myaccount.google.com/find-your-phone")
        print(C(Fore.GREEN, "  → Opened. Sign in → select your device → Lock → set temp password."))
    else:
        print(C(Fore.CYAN, "  → Manual URL: https://myaccount.google.com/find-your-phone"))


# ─── PATH E: No USB Debugging — Samsung / OEM specific ──────────────────────

def path_e_oem_options():
    """
    Samsung Find My Mobile, Xiaomi Mi Cloud, OnePlus, etc.
    Each OEM has their own remote unlock if you were signed into their account.
    """
    section("PATH E — OEM Account Unlock (Samsung / Xiaomi / OnePlus / etc.)")
    print(C(Fore.YELLOW, """
  Pick your brand:
    1) Samsung  → Samsung Find My Mobile
    2) Xiaomi   → Mi Cloud
    3) OnePlus  → OnePlus Account (limited)
    4) Google Pixel → Google Find My Device (see Path D)
    q) Back
    """))

    oem_urls = {
        "1": ("Samsung Find My Mobile",  "https://findmymobile.samsung.com"),
        "2": ("Xiaomi Mi Cloud",          "https://i.mi.com"),
        "3": ("OnePlus Account",          "https://account.oneplus.com"),
    }

    pick = input(C(Fore.YELLOW, "  Pick [1/2/3/4/q]: ")).strip().lower()

    if pick in oem_urls:
        name, url = oem_urls[pick]
        open_it = input(C(Fore.YELLOW, f"  Open {name} in browser? [y/n]: ")).strip().lower()
        if open_it == "y":
            webbrowser.open(url)
            print(C(Fore.GREEN, f"  → Opened {name}. Sign in and use 'Unlock' or 'Lock with new password'."))
        else:
            print(C(Fore.CYAN, f"  → URL: {url}"))
    elif pick == "q":
        return
    else:
        print(C(Fore.RED, "  Unknown pick."))


# ─── TRIAGE: figure out what situation we're in ──────────────────────────────

def triage():
    """Ask a couple questions to route LO to the right path."""
    section("SITUATION TRIAGE")
    print(C(Fore.YELLOW, """
  Answer 2 quick questions so we don't waste time on dead ends.
    """))

    q1 = input(C(Fore.YELLOW,
        "  Was USB Debugging ON before you got locked out? [y/n/unsure]: "
    )).strip().lower()

    if q1 in ("y", "yes"):
        print(C(Fore.GREEN, "\n  → USB debugging was on. ADB paths are available. Nice."))
        q2 = input(C(Fore.YELLOW,
            "  Is your device rooted? [y/n]: "
        )).strip().lower()

        if q2 in ("y", "yes"):
            return "rooted"
        else:
            return "adb_no_root"
    else:
        print(C(Fore.RED, "\n  → USB debugging was off (or unknown). ADB is blind. Google/OEM routes only."))
        return "no_adb"


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    banner()

    situation = triage()

    if situation == "rooted":
        section("AVAILABLE OPTIONS (Rooted + USB Debugging)")
        print("""
  A) Delete lock credential files  ← BEST. No data loss.
  B) Factory reset via ADB         ← DATA GONE but works
  C) Bruteforce PIN via ADB        ← slow but worth a shot
  D) Google Find My Device         ← if phone is online
  q) Quit
        """)
        pick = input(C(Fore.YELLOW, "  Pick [A/B/C/D/q]: ")).strip().upper()

        serial = get_device()
        if not serial and pick in ("A", "B", "C"):
            print(C(Fore.RED, "\n  [✗] No device detected via ADB. Is it plugged in and authorized?"))
            return

        if pick == "A":   path_a_rooted_delete_lock(serial)
        elif pick == "B": path_b_factory_reset_adb(serial)
        elif pick == "C": path_c_bruteforce_pin(serial)
        elif pick == "D": path_d_google_account()
        elif pick == "Q": print(C(Fore.MAGENTA, "\nLater ✨")); sys.exit(0)

    elif situation == "adb_no_root":
        section("AVAILABLE OPTIONS (USB Debugging ON, Not Rooted)")
        print("""
  B) Factory reset via ADB         ← DATA GONE but works
  C) Bruteforce PIN via ADB        ← worth it for 4-digit PINs
  D) Google Find My Device         ← if phone is online
  q) Quit
        """)
        pick = input(C(Fore.YELLOW, "  Pick [B/C/D/q]: ")).strip().upper()

        serial = get_device()
        if not serial and pick in ("B", "C"):
            print(C(Fore.RED, "\n  [✗] No device detected via ADB. Plugged in?"))
            return

        if pick == "B":   path_b_factory_reset_adb(serial)
        elif pick == "C": path_c_bruteforce_pin(serial)
        elif pick == "D": path_d_google_account()
        elif pick == "Q": print(C(Fore.MAGENTA, "\nLater ✨")); sys.exit(0)

    else:  # no_adb
        section("AVAILABLE OPTIONS (No USB Debugging)")
        print("""
  D) Google Find My Device         ← best shot if phone is online
  E) OEM account unlock            ← Samsung / Xiaomi / OnePlus
  F) Manual hardware factory reset ← last resort, volume button combo
  q) Quit
        """)
        pick = input(C(Fore.YELLOW, "  Pick [D/E/F/q]: ")).strip().upper()

        if pick == "D":   path_d_google_account()
        elif pick == "E": path_e_oem_options()
        elif pick == "F": hardware_reset_guide()
        elif pick == "Q": print(C(Fore.MAGENTA, "\nLater ✨")); sys.exit(0)


def hardware_reset_guide():
    """Volume button factory reset guide — no ADB, no computer needed."""
    section("PATH F — Hardware Factory Reset (no computer needed)")
    print(C(Fore.YELLOW, """
  This is the physical button combo that boots your phone into recovery.
  Works on ANY Android even without USB debugging.
  DATA WILL BE WIPED.

  Common combos (try the one that matches your phone):

  ┌─────────────────────────────────────────────────────┐
  │ Samsung Galaxy:                                     │
  │   Power OFF → hold Vol Up + Bixby + Power           │
  │   (newer: Vol Up + Power, no Bixby button)          │
  ├─────────────────────────────────────────────────────┤
  │ Google Pixel:                                       │
  │   Power OFF → hold Power + Vol Down → Recovery      │
  ├─────────────────────────────────────────────────────┤
  │ Xiaomi / Redmi:                                     │
  │   Power OFF → hold Vol Up + Power                   │
  ├─────────────────────────────────────────────────────┤
  │ OnePlus:                                            │
  │   Power OFF → hold Vol Down + Power                 │
  ├─────────────────────────────────────────────────────┤
  │ LG:                                                 │
  │   Power OFF → hold Vol Down + Power                 │
  └─────────────────────────────────────────────────────┘

  Once in recovery:
    → Navigate with Volume keys
    → Select "Wipe data / factory reset"
    → Confirm → Reboot

  Phone comes up fresh. Set it up again (or restore from Google backup).
    """))


if __name__ == "__main__":
    main()
