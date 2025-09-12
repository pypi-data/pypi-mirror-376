"""Fake update screen (fullscreen with progress)."""
import tkinter as tk
import time, threading

def fake_update_screen(duration: float = 15.0, message="Working on updates...", stop_event=None):
    stop_event = stop_event or threading.Event()
    root = tk.Tk()
    try:
        root.attributes("-fullscreen", True)
    except Exception:
        root.geometry("900x600")
    root.configure(bg="#0e639c")
    lbl = tk.Label(root, text=message, bg="#0e639c", fg="white", font=("Segoe UI", 26))
    lbl.pack(pady=40)
    pct_lbl = tk.Label(root, text="0%", bg="#0e639c", fg="white", font=("Segoe UI", 48))
    pct_lbl.pack(pady=20)

    start = time.time()
    def loop():
        if stop_event.is_set():
            try:
                root.destroy()
            except Exception:
                pass
            return
        elapsed = time.time() - start
        pct = int(min(100, (elapsed / max(0.1, duration)) * 100))
        pct_lbl.config(text=f"{pct}%")
        if pct < 100:
            root.after(200, loop)
        else:
            try:
                root.destroy()
            except Exception:
                pass
    root.bind("<Escape>", lambda e: (stop_event.set(), root.destroy()))
    loop()
    root.mainloop()
