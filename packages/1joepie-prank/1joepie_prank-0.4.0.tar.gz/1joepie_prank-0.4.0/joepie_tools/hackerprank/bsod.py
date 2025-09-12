"""Fake Blue Screen of Death (fullscreen)."""
import tkinter as tk
import time, threading

def fake_bsod(duration: float = 8.0, stop_event=None):
    stop_event = stop_event or threading.Event()
    root = tk.Tk()
    root.title(" ")
    # Fullscreen
    try:
        root.attributes("-fullscreen", True)
    except Exception:
        root.geometry("900x600")
    root.configure(bg="#0078D7")  # Win10-ish blue

    msg = ":(" + "\n\nYour PC ran into a problem and needs to restart."
    lbl = tk.Label(root, text=msg, bg="#0078D7", fg="white", font=("Segoe UI", 28))
    lbl.pack(expand=True)

    start = time.time()
    def tick():
        if stop_event.is_set():
            try:
                root.destroy()
            except Exception:
                pass
            return
        if time.time() - start < duration:
            root.after(250, tick)
        else:
            try:
                root.destroy()
            except Exception:
                pass
    root.bind("<Escape>", lambda e: (stop_event.set(), root.destroy()))
    tick()
    root.mainloop()
