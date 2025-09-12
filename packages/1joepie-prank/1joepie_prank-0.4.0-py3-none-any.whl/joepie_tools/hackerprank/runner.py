"""Runner that shows consent modal, optional beep, reveal hotkey, and starts multiple pranks."""
import tkinter as tk
import threading, time
from .fake_screens import fake_hack_screen
from .matrix_screen import fake_matrix
from .fake_terminal import fake_terminal
from .file_dump import fake_file_dump
from .popup import fake_warning_popup
from .bsod import fake_bsod
from .update_screen import fake_update_screen
from .virus_scan import fake_virus_scan
from .random_popups import random_popups
from .sound import play_beep

def _consent():
    confirmed = {'v': False}
    def _show():
        root = tk.Tk()
        root.title("Consent required")
        root.geometry("480x160")
        lbl = tk.Label(root, text="Confirm you will tell the person it's a joke afterwards.", wraplength=440)
        lbl.pack(pady=8)
        var = tk.BooleanVar(value=False)
        chk = tk.Checkbutton(root, text="I promise to reveal it's fake afterwards.", variable=var)
        chk.pack()
        def ok():
            confirmed['v'] = var.get()
            root.destroy()
        tk.Button(root, text="OK", command=ok).pack(pady=8)
        root.mainloop()
    t = threading.Thread(target=_show)
    t.start()
    t.join()
    return confirmed['v']

def _controller(stop_event, reveal_hotkey="F12"):
    root = tk.Tk()
    root.title("Prank Controller — joepie_tools")
    root.geometry("360x140")
    lbl = tk.Label(root, text=f"Press {reveal_hotkey} to show 'This is a prank' overlay.
Press STOP to quit.", font=("Helvetica", 10))
    lbl.pack(pady=8)
    overlay = {'w': None}
    def reveal():
        if overlay['w'] is not None:
            try:
                overlay['w'].destroy()
            except Exception:
                pass
            overlay['w'] = None
            return
        w = tk.Toplevel(root)
        w.title("Reveal")
        w.geometry("600x120+40+40")
        w.configure(bg="yellow")
        tk.Label(w, text="THIS IS A PRANK — DIT IS NEP", bg="yellow", fg="black", font=("Helvetica", 20, "bold")).pack(expand=True, fill="both")
        overlay['w'] = w
    root.bind(f"<{reveal_hotkey}>", lambda e: reveal())
    tk.Button(root, text="Reveal (toggle)", command=reveal).pack()
    tk.Button(root, text="STOP", command=lambda:(stop_event.set(), root.destroy())).pack(pady=6)
    root.protocol("WM_DELETE_WINDOW", lambda:(stop_event.set(), root.destroy()))
    root.mainloop()

def run_full_prank(require_ack=True, beep=True, reveal_hotkey="F12", num_windows=3, duration=8.0):
    if require_ack and not _consent():
        return False
    stop_event = threading.Event()
    # Controller window
    threading.Thread(target=_controller, args=(stop_event,reveal_hotkey), daemon=True).start()
    if beep:
        play_beep()
    # Run a bunch of pranks staggered
    threading.Thread(target=fake_hack_screen, kwargs={'num_windows':num_windows, 'duration':duration, 'stop_event':stop_event}, daemon=True).start()
    time.sleep(0.5)
    threading.Thread(target=fake_terminal, kwargs={'duration':max(5.0,duration*1.2), 'theme':"powershell", 'stop_event':stop_event}, daemon=True).start()
    time.sleep(0.5)
    threading.Thread(target=fake_matrix, kwargs={'duration':max(6.0,duration*1.2), 'stop_event':stop_event}, daemon=True).start()
    time.sleep(0.5)
    threading.Thread(target=fake_virus_scan, kwargs={'duration':max(7.0,duration*1.5), 'max_threats':999, 'stop_event':stop_event}, daemon=True).start()
    time.sleep(0.5)
    threading.Thread(target=fake_file_dump, kwargs={'duration':max(5.0,duration), 'file_count':4, 'delay':0.3, 'stop_event':stop_event}, daemon=True).start()
    time.sleep(0.5)
    threading.Thread(target=random_popups, kwargs={'count':8, 'duration':max(6.0,duration), 'stop_event':stop_event}, daemon=True).start()
    # No blocking mainloop here; functions own their loops; controller handles stop
    return True
