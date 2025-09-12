"""Fake virus scan window."""
import tkinter as tk
import time, random, threading

FILES = [
    "C:/Windows/System32/ntdll.dll","C:/Users/Public/Downloads/setup.exe",
    "C:/Program Files/Common Files/driver.sys","C:/Users/noah/Documents/taxes.pdf",
    "C:/Windows/Temp/tmp123.tmp","C:/Users/noah/AppData/Local/Cache/index.dat",
]

def fake_virus_scan(duration: float = 12.0, max_threats: int = 500, stop_event=None):
    stop_event = stop_event or threading.Event()
    root = tk.Tk()
    root.title("Antivirus — joepie_tools")
    root.geometry("600x340")
    lbl = tk.Label(root, text="Scanning...", font=("Segoe UI", 14))
    lbl.pack(pady=8)
    log = tk.Text(root, height=12, width=70)
    log.pack(padx=8, pady=6)
    status = tk.Label(root, text="Threats found: 0", fg="red")
    status.pack(pady=6)
    threats = 0
    start = time.time()

    def step():
        nonlocal threats
        if stop_event.is_set():
            try:
                root.destroy()
            except Exception:
                pass
            return
        if time.time() - start < duration:
            f = random.choice(FILES)
            log.insert("end", f"Scanning {f}... OK\n" if random.random()<0.8 else f"Scanning {f}... SUSPICIOUS\n")
            log.see("end")
            if random.random() < 0.25 and threats < max_threats:
                threats += random.randint(1,5)
                status.config(text=f"Threats found: {threats}")
            root.after(120, step)
        else:
            log.insert("end", "\nScan complete. Action required.\n")
            log.see("end")
            try:
                root.after(1500, root.destroy)
            except Exception:
                pass

    root.protocol("WM_DELETE_WINDOW", lambda: (stop_event.set(), root.destroy()))
    step()
    root.mainloop()
