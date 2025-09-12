"""Realistic-looking fake terminal (SIMULATED)."""
import tkinter as tk
import random, time, threading
from .sound import type_clicks

DEFAULT_COMMANDS = [
    "whoami",
    "ipconfig /all",
    "netstat -a",
    "tasklist",
    "dir C:\\Users",
    "type C:\\Windows\\system32\\drivers\\etc\\hosts"
]

SIMULATED_OUTPUTS = {
    "whoami": "noah\\desktop-user",
    "ipconfig /all": "Windows IP Configuration\n   Host Name . . . . . . . . : DESKTOP-EXAMPLE",
    "netstat -a": "Active Connections\n  Proto  Local Address          Foreign Address        State",
    "tasklist": "Image Name                     PID Session Name        Session#    Mem Usage",
    "dir C:\\Users": " Directory of C:\\Users\n\n User1\n Public\n noah",
    "type C:\\Windows\\system32\\drivers\\etc\\hosts": "# localhost\n127.0.0.1 localhost"
}

def _type_text(text_widget, text, delay=20, stop_event=None, click=False):
    def run(i=0):
        if stop_event and stop_event.is_set():
            return
        if i < len(text):
            try:
                text_widget.insert("end", text[i])
                text_widget.see("end")
            except Exception:
                pass
            if click and i % max(1, int(50/delay)) == 0:
                # occasional click sound
                threading.Thread(target=type_clicks, kwargs={"chars":1,"delay":0.0}, daemon=True).start()
            text_widget.after(delay, run, i+1)
    run()

def fake_terminal(duration: float = 10.0, commands=None, typing_delay=20, theme="green", stop_event=None):
    stop_event = stop_event or threading.Event()
    root = tk.Tk()
    root.title("Terminal — joepie_tools")
    # theme
    if theme == "powershell":
        bg, fg = "#012456", "#E5E5E5"
    elif theme == "monokai":
        bg, fg = "#272822", "#F8F8F2"
    else:  # classic green
        bg, fg = "black", "lime"
    txt = tk.Text(root, bg=bg, fg=fg, font=("Consolas", 11))
    txt.pack(expand=True, fill="both")
    start = time.time()

    def close():
        stop_event.set()
        try:
            root.destroy()
        except Exception:
            pass
    root.protocol("WM_DELETE_WINDOW", close)

    cmd_list = commands or DEFAULT_COMMANDS

    def chat_loop():
        if stop_event.is_set():
            close(); return
        if time.time() - start < duration:
            cmd = random.choice(cmd_list)
            _type_text(txt, f"$ {cmd}\n", delay=typing_delay, stop_event=stop_event, click=True)
            output = SIMULATED_OUTPUTS.get(cmd, "Done.\n")
            txt.after(600 + random.randint(0,500), lambda out=output: _type_text(txt, out + "\n\n", delay=max(6,int(typing_delay/2)), stop_event=stop_event))
            txt.after(1200 + random.randint(0,1200), chat_loop)
        else:
            close()
    chat_loop()
    root.mainloop()
