"""Random popup windows at random positions."""
import tkinter as tk
import random, time, threading

MESSAGES = [
    "System breach detected!", "Disk full!", "License expired!",
    "Firewall disabled!", "Update required", "Unknown USB device",
    "Driver error", "Malware quarantined", "Backup failed"
]

def random_popups(count=10, duration: float = 8.0, stop_event=None):
    stop_event = stop_event or threading.Event()
    root = tk.Tk()
    root.withdraw()
    wins = []
    def spawn_one():
        if stop_event.is_set():
            return
        win = tk.Toplevel(root)
        win.title("System Notice")
        w, h = 300, 120
        try:
            # place randomly
            x = random.randint(10, 800)
            y = random.randint(10, 500)
            win.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:
            win.geometry(f"{w}x{h}")
        tk.Label(win, text=random.choice(MESSAGES), font=("Segoe UI", 11)).pack(pady=10)
        tk.Button(win, text="OK", command=win.destroy).pack()
        wins.append(win)
    for _ in range(max(1, int(count))):
        root.after(random.randint(50, 500), spawn_one)

    def quitlater():
        time.sleep(max(1.0, duration))
        for w in list(wins):
            try:
                w.destroy()
            except Exception:
                pass
        try:
            root.destroy()
        except Exception:
            pass
    threading.Thread(target=quitlater, daemon=True).start()
    root.mainloop()
