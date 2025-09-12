"""Matrix-style falling text effect."""
import tkinter as tk
import random, time, threading

CHARS = "abcdefghijklmnopqrstuvwxyz0123456789@#$%^&*()[]{}<> "

def _spawn_col(canvas, x, height, speed, stop_event):
    y = -random.randint(0, 300)
    text = "".join(random.choice(CHARS) for _ in range(random.randint(6,18)))
    t = canvas.create_text(x, y, text=text, font=("Consolas", 12), anchor="nw", fill="#00FF00")
    def step():
        nonlocal y
        if stop_event.is_set():
            try:
                canvas.delete(t)
            except Exception:
                pass
            return
        y += speed
        try:
            canvas.move(t, 0, speed)
        except Exception:
            pass
        if y < height + 50:
            canvas.after(80, step)
        else:
            try:
                canvas.delete(t)
            except Exception:
                pass
    step()

def fake_matrix(duration: float = 10.0, stop_event=None):
    stop_event = stop_event or threading.Event()
    root = tk.Tk()
    root.title("Matrix — joepie_tools")
    w, h = 700, 420
    canvas = tk.Canvas(root, width=w, height=h, bg="black")
    canvas.pack()
    start = time.time()
    def spawn_loop():
        if stop_event.is_set():
            try:
                root.destroy()
            except Exception:
                pass
            return
        if time.time() - start < duration:
            for _ in range(random.randint(2,6)):
                x = random.randint(0, w-50)
                speed = random.uniform(1.0, 4.0)
                _spawn_col(canvas, x, h, speed, stop_event)
            canvas.after(350, spawn_loop)
        else:
            try:
                root.destroy()
            except Exception:
                pass
    spawn_loop()
    root.protocol("WM_DELETE_WINDOW", lambda: (stop_event.set(), root.destroy()))
    root.mainloop()
