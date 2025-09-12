"""Fake file-dump window."""
import tkinter as tk
import random, time, threading

FILENAMES = ["passwords.txt","secrets.db","tokens.json","wallet.dump","notes.txt","credentials.csv","db_backup.sql","secrets_backup.enc"]

def _random_filename():
    return random.choice(FILENAMES)

def _random_hex_line():
    return " ".join(f"{random.randint(0,255):02x}" for _ in range(12))

def fake_file_dump(duration: float = 6.0, file_count=3, delay=0.5, stop_event=None):
    stop_event = stop_event or threading.Event()
    root = tk.Tk()
    root.title("FileDump — joepie_tools")
    text = tk.Text(root, font=("Consolas", 10))
    text.pack(expand=True, fill="both")
    start = time.time()
    shown = 0

    def update():
        nonlocal shown
        if stop_event.is_set():
            try:
                root.destroy()
            except Exception:
                pass
            return
        if time.time() - start < duration and shown < file_count:
            text.insert("end", f"--- Opening {_random_filename()} ---\n")
            for _ in range(random.randint(6,12)):
                text.insert("end", _random_hex_line() + "\n")
            text.insert("end", "\n")
            text.see("end")
            shown += 1
            root.after(int(delay*1000), update)
        else:
            try:
                root.destroy()
            except Exception:
                pass
    root.protocol("WM_DELETE_WINDOW", lambda: (stop_event.set(), root.destroy()))
    update()
    root.mainloop()
