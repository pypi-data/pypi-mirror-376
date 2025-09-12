"""Sound helpers: beep, alarm, error ding, type clicks."""
import sys, threading, time

def play_beep(freq=750, ms=250):
    try:
        if sys.platform.startswith("win"):
            import winsound
            winsound.Beep(int(freq), int(ms))
        else:
            # best-effort terminal bell
            print("\a", end="", flush=True)
    except Exception:
        pass

def play_error_ding():
    try:
        if sys.platform.startswith("win"):
            import winsound
            winsound.PlaySound("SystemHand", winsound.SND_ALIAS)
        else:
            print("\a", end="", flush=True)
    except Exception:
        pass

def play_alarm(seconds=3, freq=900, ms=180):
    end = time.time() + max(0, seconds)
    while time.time() < end:
        play_beep(freq=freq, ms=ms)
        time.sleep(max(0.05, ms/1000.0))

def type_clicks(chars=30, delay=0.03):
    # small click per char
    for _ in range(max(0, int(chars))):
        play_beep(freq=1100, ms=25)
        time.sleep(max(0.0, float(delay)))
