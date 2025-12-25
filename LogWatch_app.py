import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
import time
from datetime import datetime


class LogWatch:
    def __init__(self, root):
        self.root = root
        self.root.title("00:00:00.0 - LogWatch")
        self.root.geometry("1100x850")
        self.root.configure(bg="#0a0a0a")

        # Backend
        self.total_seconds = 0
        self.lap_seconds = 0
        self.tag_storage = {}
        self.running = False
        self.last_update_time = 0
        self.data_storage = []

        self.auto_pause = tk.BooleanVar(value=False)
        self.widths = {"id": 4, "task": 25, "tag": 15, "lap": 12, "sec": 12, "tot": 12, "date": 14}

        self.setup_ui()
        self.refresh_loop()

    def setup_ui(self):
        # 1. Controls
        ctrl_p = tk.Frame(self.root, bg="#111", pady=10)
        ctrl_p.pack(fill="x", side="top")

        self.btn_start = tk.Button(ctrl_p, text="START / PAUSE", width=15, bg="#27ae60", fg="white",
                                   font=("Arial", 10, "bold"), bd=0, command=self.toggle)
        self.btn_start.pack(side="left", padx=15)

        tk.Button(ctrl_p, text="NEXT LAP (MARK)", width=18, bg="#2980b9", fg="white",
                  bd=0, command=self.add_lap).pack(side="left", padx=5)

        tk.Checkbutton(ctrl_p, text="Auto-pause after lap", variable=self.auto_pause,
                       bg="#111", fg="#888", selectcolor="#000", activebackground="#111").pack(side="left", padx=20)

        # 2. DASHBOARD (TIMERS)
        self.dash_frame = tk.Frame(self.root, bg="#0a0a0a", pady=20)
        self.dash_frame.pack(fill="x")

        # LAP
        f1 = tk.Frame(self.dash_frame, bg="#0a0a0a")
        f1.pack(side="left", expand=True)
        tk.Label(f1, text="CURRENT LAP", bg="#0a0a0a", fg="#555", font=("Arial", 9, "bold")).pack()
        self.lap_disp = tk.Label(f1, text="00:00:00.0", bg="#0a0a0a", fg="#3498db", font=("Consolas", 40, "bold"))
        self.lap_disp.pack()

        # TAG
        f2 = tk.Frame(self.dash_frame, bg="#0a0a0a")
        f2.pack(side="left", expand=True)
        tk.Label(f2, text="TAG TOTAL", bg="#0a0a0a", fg="#555", font=("Arial", 9, "bold")).pack()
        self.tag_disp = tk.Label(f2, text="00:00:00", bg="#0a0a0a", fg="#f1c40f", font=("Consolas", 30, "bold"))
        self.tag_disp.pack()
        self.tag_sub_lbl = tk.Label(f2, text="(Module_1)", bg="#0a0a0a", fg="#444", font=("Arial", 10))
        self.tag_sub_lbl.pack()

        # TOTAL
        f3 = tk.Frame(self.dash_frame, bg="#0a0a0a")
        f3.pack(side="left", expand=True)
        tk.Label(f3, text="SESSION TOTAL", bg="#0a0a0a", fg="#555", font=("Arial", 9, "bold")).pack()
        self.total_disp = tk.Label(f3, text="00:00:00", bg="#0a0a0a", fg="#e74c3c", font=("Consolas", 30, "bold"))
        self.total_disp.pack()

        # 3. Inputs
        in_p = tk.Frame(self.root, bg="#0a0a0a", padx=40, pady=10)
        in_p.pack(fill="x")

        tk.Label(in_p, text="TASK NAME:", bg="#0a0a0a", fg="#555", font=("Arial", 8, "bold")).grid(row=0, column=0,
                                                                                                   sticky="w")
        self.ent_task = tk.Entry(in_p, bg="#161616", fg="white", borderwidth=0, width=50, font=("Consolas", 12))
        self.ent_task.grid(row=1, column=0, padx=(0, 20), ipady=8)
        self.ent_task.bind("<Return>", lambda e: self.add_lap())

        tk.Label(in_p, text="TAG / MODULE:", bg="#0a0a0a", fg="#f1c40f", font=("Arial", 8, "bold")).grid(row=0,
                                                                                                         column=1,
                                                                                                         sticky="w")
        self.ent_tag = tk.Entry(in_p, bg="#161616", fg="#f1c40f", borderwidth=0, width=25,
                                font=("Consolas", 12, "bold"))
        self.ent_tag.grid(row=1, column=1, ipady=8)
        self.ent_tag.insert(0, "Module_1")

        # 4. Table
        self.log_box = tk.Listbox(self.root, bg="#0f0f0f", fg="#bbb", font=("Consolas", 10),
                                  borderwidth=0, highlightthickness=1, highlightcolor="#222", selectbackground="#333")
        self.log_box.pack(fill="both", expand=True, padx=40, pady=10)

        # 5. Footer
        bot_p = tk.Frame(self.root, bg="#111", pady=10)
        bot_p.pack(fill="x", side="bottom")

        tk.Button(bot_p, text="IMPORT", bg="#333", fg="white", command=self.do_import).pack(side="left", padx=15)
        tk.Button(bot_p, text="SAVE FILE", bg="#333", fg="#2ecc71", command=self.do_export).pack(side="left", padx=5)
        tk.Button(bot_p, text="EDIT ENTRY", bg="#333", fg="white", command=self.do_edit).pack(side="left", padx=20)
        tk.Button(bot_p, text="DELETE", bg="#422", fg="#f55", command=self.do_delete).pack(side="left", padx=5)
        tk.Button(bot_p, text="VIEW TAGS", bg="#222", fg="#f1c40f", command=self.show_tags_window).pack(side="right",
                                                                                                        padx=15)

    def format_time(self, seconds, ms=False):
        h, rem = divmod(int(seconds), 3600)
        m, s = divmod(rem, 60)
        if ms:
            msec = int((seconds - int(seconds)) * 10)
            return f"{h:02}:{m:02}:{s:02}.{msec}"
        return f"{h:02}:{m:02}:{s:02}"

    def refresh_loop(self):
        if self.running:
            now = time.time()
            delta = now - self.last_update_time
            self.last_update_time = now
            self.total_seconds += delta
            self.lap_seconds += delta

        cur_tag = self.ent_tag.get().strip() or "None"
        tag_acc = self.tag_storage.get(cur_tag, 0) + (self.lap_seconds if self.running else 0)

        self.lap_disp.config(text=self.format_time(self.lap_seconds, True))
        self.tag_disp.config(text=self.format_time(tag_acc))
        self.total_disp.config(text=self.format_time(self.total_seconds))
        self.tag_sub_lbl.config(text=f"({cur_tag})")

        self.root.title(f"{self.format_time(self.lap_seconds, True)} - LogWatch")
        self.root.after(100, self.refresh_loop)

    def toggle(self):
        if not self.running:
            self.last_update_time = time.time()
            self.running = True
            self.btn_start.config(text="PAUSE", bg="#f1c40f", fg="black")
        else:
            self.running = False
            self.btn_start.config(text="RESUME", bg="#27ae60", fg="white")

    def add_lap(self):
        if self.total_seconds == 0 and not self.running: return
        tag = self.ent_tag.get().strip() or "General"
        if tag not in self.tag_storage: self.tag_storage[tag] = 0
        self.tag_storage[tag] += self.lap_seconds

        entry = {
            "id": str(len(self.data_storage) + 1), "task": self.ent_task.get().strip() or "Manual Mark",
            "tag": tag, "lap": self.format_time(self.lap_seconds, True),
            "sec": self.format_time(self.tag_storage[tag]), "tot": self.format_time(self.total_seconds),
            "date": datetime.now().strftime("%d.%m %H:%M"), "raw_lap": self.lap_seconds
        }
        self.data_storage.append(entry)
        self.lap_seconds = 0
        self.ent_task.delete(0, tk.END)
        self.render_table()
        if self.auto_pause.get(): self.toggle()

    def do_delete(self):
        sel = self.log_box.curselection()
        if not sel or sel[0] < 2: return
        idx = sel[0] - 2
        if messagebox.askyesno("Delete", "Revert time and delete?"):
            e = self.data_storage.pop(idx)
            self.total_seconds -= e['raw_lap']
            self.tag_storage[e['tag']] -= e['raw_lap']
            for i, d in enumerate(self.data_storage): d['id'] = str(i + 1)
            self.render_table()

    def do_edit(self):
        sel = self.log_box.curselection()
        if not sel or sel[0] < 2: return
        idx = sel[0] - 2
        e = self.data_storage[idx]
        mode = messagebox.askquestion("Edit", "Yes: TASK / No: TAG")
        if mode == 'yes':
            new = simpledialog.askstring("Edit", "Task:", initialvalue=e['task'])
            if new: e['task'] = new
        else:
            new = simpledialog.askstring("Edit", "Tag:", initialvalue=e['tag'])
            if new:
                self.tag_storage[e['tag']] -= e['raw_lap']
                e['tag'] = new
                self.tag_storage[new] = self.tag_storage.get(new, 0) + e['raw_lap']
        self.render_table()

    def render_table(self):
        self.log_box.delete(0, tk.END)
        w = self.widths.copy()
        for item in self.data_storage:
            for key in w: w[key] = max(w[key], len(str(item.get(key, ""))))
        head = (f"{'#'.ljust(w['id'])} | {'Task Description'.ljust(w['task'])} | "
                f"{'Tag'.ljust(w['tag'])} | {'Lap'.ljust(w['lap'])} | "
                f"{'Tag Total'.ljust(w['sec'])} | {'Session'.ljust(w['tot'])} | Date")
        self.log_box.insert(tk.END, head)
        self.log_box.insert(tk.END, "—" * (len(head) + 10))
        for d in self.data_storage:
            row = (f"{d['id'].ljust(w['id'])} | {d['task'].ljust(w['task'])} | "
                   f"{d['tag'].ljust(w['tag'])} | {d['lap'].ljust(w['lap'])} | "
                   f"{d['sec'].ljust(w['sec'])} | {d['tot'].ljust(w['tot'])} | {d['date']}")
            self.log_box.insert(tk.END, row)
        self.log_box.see(tk.END)

    def show_tags_window(self):
        win = tk.Toplevel(self.root);
        win.title("Tags History");
        win.geometry("400x400");
        win.configure(bg="#111")
        lb = tk.Listbox(win, bg="#000", fg="#f1c40f", font=("Consolas", 10), borderwidth=0)
        lb.pack(fill="both", expand=True, padx=20, pady=20)
        for t, s in sorted(self.tag_storage.items()): lb.insert(tk.END, f"{t.ljust(20)} | {self.format_time(s)}")
        tk.Button(win, text="USE TAG", command=lambda: self.apply_tag(lb, win)).pack(pady=10)

    def apply_tag(self, lb, win):
        if lb.curselection():
            t = lb.get(lb.curselection()).split("|")[0].strip()
            self.ent_tag.delete(0, tk.END);
            self.ent_tag.insert(0, t);
            win.destroy()

    def do_export(self):
        p = filedialog.asksaveasfilename(defaultextension=".txt")
        if p:
            with open(p, "w", encoding="utf-8") as f:
                for i in range(self.log_box.size()): f.write(self.log_box.get(i) + "\n")

    def do_import(self):
        p = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if p:
            with open(p, "r", encoding="utf-8") as f:
                self.tag_storage = {};
                new_d = []
                for line in f:
                    if "|" in line and "—" not in line and "#" not in line:
                        v = [x.strip() for x in line.split("|")]
                        if len(v) >= 6:
                            ls = self.parse_to_sec(v[3])
                            self.tag_storage[v[2]] = self.tag_storage.get(v[2], 0) + ls
                            new_d.append({"id": v[0], "task": v[1], "tag": v[2], "lap": v[3], "sec": v[4], "tot": v[5],
                                          "date": v[6], "raw_lap": ls})
                if new_d: self.data_storage = new_d; self.total_seconds = self.parse_to_sec(
                    new_d[-1]['tot']); self.render_table()

    def parse_to_sec(self, t_str):
        try:
            # Берем часть до точки (миллисекунды нам не нужны для парсинга секунд)
            clean_time = t_str.split(".")[0]
            parts = clean_time.split(":")
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        except:
            return 0


if __name__ == "__main__":
    root = tk.Tk()
    app = LogWatch(root)
    root.mainloop()