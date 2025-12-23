import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
import time
from datetime import datetime


class LogWatch:
    def __init__(self, root):
        self.root = root
        self.root.title("00:00:00 - LogWatchCore")
        self.root.geometry("1100x800")
        self.root.configure(bg="#0d0d0d")

        # Backend Data
        self.total_seconds = 0
        self.lap_seconds = 0
        self.tag_storage = {}

        self.last_update_time = 0
        self.running = False
        self.data_storage = []

        # UI Widths
        self.widths = {"id": 4, "task": 25, "tag": 15, "lap": 12, "sec": 12, "tot": 12, "date": 14}

        self.setup_ui()
        self.refresh_loop()

    def setup_ui(self):
        # 1. Header Control
        ctrl_p = tk.Frame(self.root, bg="#161616", pady=10)
        ctrl_p.pack(fill="x")

        self.btn_start = tk.Button(ctrl_p, text="START / PAUSE", width=15, bg="#27ae60", fg="white",
                                   font=("Arial", 10, "bold"), bd=0, command=self.toggle)
        self.btn_start.pack(side="left", padx=15)

        tk.Button(ctrl_p, text="NEXT LAP (ENTER)", width=18, bg="#2980b9", fg="white",
                  bd=0, command=self.add_lap).pack(side="left", padx=5)

        tk.Button(ctrl_p, text="VIEW ALL TAGS", width=15, bg="#8e44ad", fg="white",
                  bd=0, command=self.show_tags_window).pack(side="left", padx=5)

        # 2. Main Visual Timers
        display_f = tk.Frame(self.root, bg="#0d0d0d", pady=25)
        display_f.pack(fill="x")

        self.total_disp = self.create_timer_block(display_f, "SESSION TOTAL", "#e74c3c")
        self.total_disp.pack(side="left", expand=True)

        self.tag_disp = self.create_timer_block(display_f, "TAG ACCUMULATED", "#f1c40f")
        self.tag_disp.pack(side="left", expand=True)

        self.lap_disp = self.create_timer_block(display_f, "CURRENT TASK LAP", "#3498db")
        self.lap_disp.pack(side="left", expand=True)

        # 3. Input Section
        in_p = tk.Frame(self.root, bg="#0d0d0d", pady=10)
        in_p.pack(fill="x", padx=35)

        tk.Label(in_p, text="TASK DESCRIPTION:", bg="#0d0d0d", fg="#555", font=("Arial", 9, "bold")).grid(row=0,
                                                                                                          column=0,
                                                                                                          sticky="w")
        self.ent_task = tk.Entry(in_p, bg="#1a1a1a", fg="white", borderwidth=0, width=45, font=("Consolas", 12))
        self.ent_task.grid(row=1, column=0, padx=(0, 25), ipady=10)
        self.ent_task.bind("<Return>", lambda e: self.add_lap())

        tk.Label(in_p, text="ACTIVE TAG / MODULE:", bg="#0d0d0d", fg="#f1c40f", font=("Arial", 9, "bold")).grid(row=0,
                                                                                                                column=1,
                                                                                                                sticky="w")
        self.ent_tag = tk.Entry(in_p, bg="#1a1a1a", fg="#f1c40f", borderwidth=0, width=25,
                                font=("Consolas", 12, "bold"))
        self.ent_tag.grid(row=1, column=1, ipady=10)

        # 4. Data Table (Listbox)
        self.log_box = tk.Listbox(self.root, bg="#111", fg="#ccc", font=("Consolas", 10),
                                  borderwidth=0, highlightthickness=1, highlightcolor="#333", selectbackground="#444")
        self.log_box.pack(fill="both", expand=True, padx=35, pady=20)

        # 5. Bottom Navigation
        bot_p = tk.Frame(self.root, bg="#161616", pady=10)
        bot_p.pack(fill="x")

        tk.Button(bot_p, text="IMPORT LOG", bg="#333", fg="white", bd=0, width=12, command=self.do_import).pack(
            side="left", padx=15)
        tk.Button(bot_p, text="SAVE (EXPORT)", bg="#333", fg="#27ae60", bd=0, width=15, command=self.do_export).pack(
            side="left", padx=5)
        tk.Button(bot_p, text="EDIT ENTRY", bg="#333", fg="white", bd=0, width=12, command=self.do_edit).pack(
            side="left", padx=5)

        # Default values
        self.ent_tag.insert(0, "Module_1")

    def create_timer_block(self, parent, label_text, color):
        frame = tk.Frame(parent, bg="#0d0d0d")
        tk.Label(frame, text=label_text, bg="#0d0d0d", fg="#444", font=("Arial", 9, "bold")).pack()
        lbl_time = tk.Label(frame, text="00:00:00", bg="#0d0d0d", fg=color, font=("Consolas", 32, "bold"))
        lbl_time.pack()
        if label_text == "TAG ACCUMULATED":
            self.tag_name_lbl = tk.Label(frame, text="(Module_1)", bg="#0d0d0d", fg="#666",
                                         font=("Arial", 10, "italic"))
            self.tag_name_lbl.pack()
        return lbl_time

    def format_time(self, seconds, ms=False):
        h, rem = divmod(int(seconds), 3600)
        m, s = divmod(rem, 60)
        if ms:
            msec = int((seconds - int(seconds)) * 10)
            return f"{h:02}:{m:02}:{s:02}.{msec}"
        return f"{h:02}:{m:02}:{s:02}"

    def refresh_loop(self):
        # Update logic
        if self.running:
            now = time.time()
            delta = now - self.last_update_time
            self.last_update_time = now
            self.total_seconds += delta
            self.lap_seconds += delta

        # Display Updates (Always active to reflect Tag changes)
        current_tag = self.ent_tag.get().strip() or "None"
        tag_acc = self.tag_storage.get(current_tag, 0) + (self.lap_seconds if self.running else 0)

        self.total_disp.config(text=self.format_time(self.total_seconds))
        self.lap_disp.config(text=self.format_time(self.lap_seconds, True))
        self.tag_disp.config(text=self.format_time(tag_acc))
        self.tag_name_lbl.config(text=f"({current_tag})")

        self.root.title(f"{self.format_time(self.total_seconds)} - LogWatchCore")
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
            "id": str(len(self.data_storage) + 1),
            "task": self.ent_task.get().strip() or "Unnamed Task",
            "tag": tag,
            "lap": self.format_time(self.lap_seconds, True),
            "sec": self.format_time(self.tag_storage[tag]),
            "tot": self.format_time(self.total_seconds),
            "date": datetime.now().strftime("%d.%m %H:%M")
        }
        self.data_storage.append(entry)
        self.lap_seconds = 0
        self.ent_task.delete(0, tk.END)
        self.render_table()

    def render_table(self):
        self.log_box.delete(0, tk.END)
        w = self.widths.copy()
        for item in self.data_storage:
            for key in w:
                w[key] = max(w[key], len(str(item.get(key, ""))))

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
        win = tk.Toplevel(self.root)
        win.title("LogWatchCore Tags")
        win.geometry("450x450")
        win.configure(bg="#111")

        tk.Label(win, text="REGISTERED TAGS & ACCUMULATED TIME", bg="#111", fg="#666", font=("Arial", 9, "bold")).pack(
            pady=15)

        lb = tk.Listbox(win, bg="#000", fg="#f1c40f", font=("Consolas", 10), borderwidth=0)
        lb.pack(fill="both", expand=True, padx=25, pady=10)

        # Sort tags by time (descending)
        sorted_tags = sorted(self.tag_storage.items(), key=lambda x: x[1], reverse=True)
        for tag, sec in sorted_tags:
            lb.insert(tk.END, f"{tag.ljust(20)} | {self.format_time(sec)}")

        def use_selected():
            sel = lb.curselection()
            if sel:
                t = lb.get(sel[0]).split("|")[0].strip()
                self.ent_tag.delete(0, tk.END)
                self.ent_tag.insert(0, t)
                win.destroy()

        tk.Button(win, text="ACTIVATE SELECTED TAG", command=use_selected, bg="#333", fg="white", bd=0, height=2).pack(
            fill="x", padx=25, pady=20)

    def do_edit(self):
        sel = self.log_box.curselection()
        if not sel or sel[0] < 2: return
        idx = sel[0] - 2
        new_val = simpledialog.askstring("Edit Task", "New description:", initialvalue=self.data_storage[idx]['task'])
        if new_val:
            self.data_storage[idx]['task'] = new_val
            self.render_table()

    def do_export(self):
        p = filedialog.asksaveasfilename(defaultextension=".txt",
                                         initialfile=f"LogWatch_{datetime.now().strftime('%Y%m%d')}.txt")
        if p:
            with open(p, "w", encoding="utf-8") as f:
                for i in range(self.log_box.size()): f.write(self.log_box.get(i) + "\n")

    def do_import(self):
        p = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if p:
            with open(p, "r", encoding="utf-8") as f:
                lines = f.readlines()
                new_data = []
                self.tag_storage = {}
                for line in lines:
                    if "|" in line and "#" not in line and "—" not in line:
                        v = [val.strip() for val in line.split("|")]
                        if len(v) >= 6:
                            tag_name = v[2]
                            lap_s = self.parse_to_sec(v[3])
                            self.tag_storage[tag_name] = self.tag_storage.get(tag_name, 0) + lap_s
                            new_data.append(
                                {"id": v[0], "task": v[1], "tag": tag_name, "lap": v[3], "sec": v[4], "tot": v[5],
                                 "date": v[6] if len(v) > 6 else ""})
                if new_data:
                    self.data_storage = new_data
                    self.total_seconds = self.parse_to_sec(new_data[-1]['tot'])
                    self.render_table()

    def parse_to_sec(self, s_str):
        try:
            h, m, s = map(int, s_str.split(".")[0].split(":"))
            return h * 3600 + m * 60 + s
        except:
            return 0


if __name__ == "__main__":
    root = tk.Tk()
    app = LogWatch(root)
    root.mainloop()