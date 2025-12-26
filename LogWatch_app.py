import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import time
from datetime import datetime, timedelta
import os
import json

# --- НАСТРОЙКИ UI ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

COLORS = {
    "bg": "#1a1a1a",
    "card": "#2b2b2b",
    "accent": "#1f6aa5",
    "success": "#2cc985",
    "warning": "#e2b63e",
    "danger": "#ff5f5f"
}

FILE_DB = "logwatch_db.json"
FILE_SETTINGS = "logwatch_settings.json"


class LogWatchPro(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Основное окно
        self.title("LogWatch v0.3.1 Ultimate")
        self.geometry("1400x900")

        # --- STATE ---
        self.running = False
        self.start_time = 0
        self.accumulated_time = 0
        self.current_date = datetime.now().strftime("%Y-%m-%d")

        # Загрузка данных
        self.db = self.load_data()
        self.settings = self.load_settings()

        # Горячие клавиши
        self.bind("<space>", lambda e: self.toggle_timer())
        self.bind("<Return>", lambda e: self.log_lap())
        self.bind("<Control-z>", lambda e: self.undo_last_log())

        # --- UI LAYOUT ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. SIDEBAR
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.setup_sidebar()

        # 2. MAIN AREA
        self.main_view = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_view.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        # Инициализация вкладок
        self.frames = {}
        self.setup_dashboard()
        self.setup_analytics()
        self.setup_history()
        self.setup_settings()

        self.select_frame("Dashboard")

        # Запуск таймера
        self.update_timer_loop()

    # --- DATA ENGINE ---
    def load_data(self):
        if os.path.exists(FILE_DB):
            try:
                df = pd.read_json(FILE_DB, orient='records')
                if not df.empty:
                    df['datetime'] = pd.to_datetime(df['datetime'])
                    df['date_str'] = df['datetime'].dt.strftime('%Y-%m-%d')
                    # Нормализация тэгов
                    df['tag'] = df['tag'].str.title()
                return df
            except:
                return pd.DataFrame(columns=["datetime", "date_str", "tag", "task", "duration", "note"])
        return pd.DataFrame(columns=["datetime", "date_str", "tag", "task", "duration", "note"])

    def save_data(self):
        self.db.to_json(FILE_DB, orient='records', date_format='iso')

    def load_settings(self):
        default = {
            "goals": {"daily": 6, "weekly": 35, "global": 1000},
            "tags": ["Work", "Study", "Project", "Personal"],
            "theme": "blue"
        }
        if os.path.exists(FILE_SETTINGS):
            try:
                with open(FILE_SETTINGS, 'r') as f:
                    return json.load(f)
            except:
                return default
        return default

    def save_settings(self):
        with open(FILE_SETTINGS, 'w') as f:
            json.dump(self.settings, f, indent=2)

    # --- UI SETUP ---
    def setup_sidebar(self):
        title = ctk.CTkLabel(self.sidebar, text="LOGWATCH\nULTIMATE", font=("Roboto", 20, "bold"))
        title.pack(pady=30)

        buttons = [
            ("Dashboard", "Dashboard"),
            ("Analytics", "Analytics"),
            ("History", "History"),
            ("Settings", "Settings")
        ]

        for text, frame_name in buttons:
            btn = ctk.CTkButton(self.sidebar, text=text,
                                command=lambda f=frame_name: self.select_frame(f),
                                fg_color="transparent", border_width=2)
            btn.pack(pady=10, padx=20, fill="x")

        # Goals Progress
        ctk.CTkLabel(self.sidebar, text="DAILY GOAL", font=("Arial", 10)).pack(pady=(40, 5))
        self.progress_daily = ctk.CTkProgressBar(self.sidebar, height=15)
        self.progress_daily.pack(padx=20, fill="x")
        self.lbl_daily_prog = ctk.CTkLabel(self.sidebar, text="0%")
        self.lbl_daily_prog.pack()

        ctk.CTkLabel(self.sidebar, text="WEEKLY GOAL", font=("Arial", 10)).pack(pady=(20, 5))
        self.progress_weekly = ctk.CTkProgressBar(self.sidebar, height=15)
        self.progress_weekly.pack(padx=20, fill="x")
        self.lbl_weekly_prog = ctk.CTkLabel(self.sidebar, text="0%")
        self.lbl_weekly_prog.pack()

    def select_frame(self, name):
        for frame in self.frames.values():
            frame.pack_forget()
        self.frames[name].pack(fill="both", expand=True)

        if name == "Analytics":
            self.refresh_charts()
        elif name == "History":
            self.refresh_table()
        elif name == "Settings":
            self.refresh_settings_ui()

    # --- DASHBOARD ---
    def setup_dashboard(self):
        frame = ctk.CTkScrollableFrame(self.main_view, fg_color="transparent")
        self.frames["Dashboard"] = frame

        # Timer Section
        timer_card = ctk.CTkFrame(frame, fg_color=COLORS["card"])
        timer_card.pack(fill="x", pady=10)

        self.lbl_main_timer = ctk.CTkLabel(timer_card, text="00:00:00",
                                           font=("Roboto Mono", 80, "bold"),
                                           text_color=COLORS["success"])
        self.lbl_main_timer.pack(pady=20)

        ctrl_frame = ctk.CTkFrame(timer_card, fg_color="transparent")
        ctrl_frame.pack(pady=10)

        self.btn_start = ctk.CTkButton(ctrl_frame, text="START (Space)", width=180, height=50,
                                       font=("Arial", 14, "bold"),
                                       fg_color=COLORS["success"],
                                       command=self.toggle_timer)
        self.btn_start.pack(side="left", padx=10)

        ctk.CTkButton(ctrl_frame, text="LOG (Enter)", width=180, height=50,
                      font=("Arial", 14, "bold"),
                      fg_color=COLORS["accent"],
                      command=self.log_lap).pack(side="left", padx=10)

        ctk.CTkButton(ctrl_frame, text="UNDO (Ctrl+Z)", width=180, height=50,
                      font=("Arial", 14, "bold"),
                      fg_color=COLORS["danger"],
                      command=self.undo_last_log).pack(side="left", padx=10)

        # Stats Row
        stats_row = ctk.CTkFrame(frame, fg_color="transparent")
        stats_row.pack(fill="x", pady=10)

        self.create_stat_box(stats_row, "TODAY TOTAL", "0h 0m", "today_lbl")
        self.create_stat_box(stats_row, "THIS WEEK", "0h 0m", "week_lbl")
        self.create_stat_box(stats_row, "CURRENT TAG", "0h 0m", "tag_lbl")
        self.create_stat_box(stats_row, "STREAK", "0 days", "streak_lbl")

        # Input Section
        input_card = ctk.CTkFrame(frame, fg_color=COLORS["card"])
        input_card.pack(fill="x", pady=10)

        input_grid = ctk.CTkFrame(input_card, fg_color="transparent")
        input_grid.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(input_grid, text="Task Description").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.entry_task = ctk.CTkEntry(input_grid, width=400, placeholder_text="What are you working on?")
        self.entry_task.grid(row=1, column=0, padx=10, pady=(0, 10))

        ctk.CTkLabel(input_grid, text="Tag").grid(row=0, column=1, padx=10, pady=5, sticky="w")
        self.combo_tag = ctk.CTkComboBox(input_grid, values=self.settings["tags"], width=200)
        self.combo_tag.set(self.settings["tags"][0] if self.settings["tags"] else "Work")
        self.combo_tag.grid(row=1, column=1, padx=10, pady=(0, 10))

        ctk.CTkLabel(input_grid, text="Note (optional)").grid(row=2, column=0, columnspan=2, padx=10, pady=5,
                                                              sticky="w")
        self.entry_note = ctk.CTkEntry(input_grid, width=620, placeholder_text="Additional notes...")
        self.entry_note.grid(row=3, column=0, columnspan=2, padx=10, pady=(0, 10))

        # Recent Logs (NEW!)
        recent_card = ctk.CTkFrame(frame, fg_color=COLORS["card"])
        recent_card.pack(fill="both", expand=True, pady=10)

        ctk.CTkLabel(recent_card, text="RECENT LOGS", font=("Arial", 14, "bold")).pack(pady=10)

        # Простая таблица для последних 5 записей
        self.recent_logs_frame = ctk.CTkFrame(recent_card, fg_color="transparent")
        self.recent_logs_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def create_stat_box(self, parent, title, val, attr_name):
        box = ctk.CTkFrame(parent, fg_color=COLORS["card"])
        box.pack(side="left", fill="both", expand=True, padx=5)
        ctk.CTkLabel(box, text=title, text_color="gray", font=("Arial", 10)).pack(pady=(10, 0))
        lbl = ctk.CTkLabel(box, text=val, font=("Roboto Mono", 20, "bold"))
        lbl.pack(pady=(5, 10))
        setattr(self, attr_name, lbl)

    def refresh_recent_logs(self):
        """Обновление списка последних логов на Dashboard"""
        for widget in self.recent_logs_frame.winfo_children():
            widget.destroy()

        if self.db.empty:
            ctk.CTkLabel(self.recent_logs_frame, text="No logs yet",
                         text_color="gray").pack(pady=20)
            return

        recent = self.db.sort_values('datetime', ascending=False).head(5)

        for idx, row in recent.iterrows():
            log_frame = ctk.CTkFrame(self.recent_logs_frame, fg_color=COLORS["bg"])
            log_frame.pack(fill="x", pady=5, padx=10)

            time_str = row['datetime'].strftime("%H:%M")
            dur_str = self.format_time(row['duration'], short=True)

            info_text = f"[{time_str}] {row['tag']} - {row['task'][:40]}{'...' if len(row['task']) > 40 else ''}"

            ctk.CTkLabel(log_frame, text=info_text, anchor="w").pack(side="left", padx=10, pady=8, fill="x",
                                                                     expand=True)
            ctk.CTkLabel(log_frame, text=dur_str, font=("Roboto Mono", 12, "bold"),
                         text_color=COLORS["success"]).pack(side="right", padx=10, pady=8)

    # --- ANALYTICS ---
    def setup_analytics(self):
        frame = ctk.CTkScrollableFrame(self.main_view, fg_color="transparent")
        self.frames["Analytics"] = frame

        # Stats Cards
        self.stats_frame = ctk.CTkFrame(frame, fg_color="transparent")
        self.stats_frame.pack(fill="x", pady=10)

        # Chart Container
        self.chart_frame = ctk.CTkFrame(frame, fg_color=COLORS["card"])
        self.chart_frame.pack(fill="both", expand=True, pady=10)

    def refresh_charts(self):
        # Clear old widgets
        for widget in self.stats_frame.winfo_children():
            widget.destroy()
        for widget in self.chart_frame.winfo_children():
            widget.destroy()

        if self.db.empty:
            ctk.CTkLabel(self.chart_frame, text="No data available yet.",
                         font=("Arial", 16)).pack(expand=True)
            return

        # === STAT CARDS ===
        today = pd.Timestamp.now().normalize()
        yesterday = today - pd.Timedelta(days=1)
        week_start = today - pd.Timedelta(days=today.weekday())

        today_hours = self.db[self.db['date_str'] == today.strftime('%Y-%m-%d')]['duration'].sum() / 3600
        yesterday_hours = self.db[self.db['date_str'] == yesterday.strftime('%Y-%m-%d')]['duration'].sum() / 3600
        week_hours = self.db[self.db['datetime'] >= week_start]['duration'].sum() / 3600
        total_hours = self.db['duration'].sum() / 3600

        cards_data = [
            ("TODAY", f"{today_hours:.1f}h", f"{'↑' if today_hours > yesterday_hours else '↓'} vs yesterday"),
            ("THIS WEEK", f"{week_hours:.1f}h", f"Avg: {week_hours / 7:.1f}h/day"),
            ("ALL TIME", f"{total_hours:.1f}h", f"{len(self.db)} sessions"),
            ("AVG/DAY", f"{total_hours / max(len(self.db['date_str'].unique()), 1):.1f}h", "Overall")
        ]

        for title, val, subtitle in cards_data:
            card = ctk.CTkFrame(self.stats_frame, fg_color=COLORS["card"])
            card.pack(side="left", fill="both", expand=True, padx=5)
            ctk.CTkLabel(card, text=title, text_color="gray", font=("Arial", 10)).pack(pady=(10, 0))
            ctk.CTkLabel(card, text=val, font=("Roboto Mono", 24, "bold")).pack(pady=5)
            ctk.CTkLabel(card, text=subtitle, text_color="gray", font=("Arial", 9)).pack(pady=(0, 10))

        # === CHARTS ===
        fig = plt.figure(figsize=(14, 10), facecolor=COLORS["card"])
        gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)

        # 1. Last 14 days bar chart
        ax1 = fig.add_subplot(gs[0, :])
        start_date = today - pd.Timedelta(days=13)
        date_range = pd.date_range(start=start_date, end=today, freq='D')
        daily_data = []

        for date in date_range:
            day_str = date.strftime('%Y-%m-%d')
            hours = self.db[self.db['date_str'] == day_str]['duration'].sum() / 3600
            daily_data.append(hours)

        bars = ax1.bar(range(len(date_range)), daily_data, color=COLORS["success"], alpha=0.8)
        ax1.axhline(y=self.settings["goals"]["daily"], color=COLORS["warning"],
                    linestyle='--', label='Daily Goal')
        ax1.set_title("Last 14 Days (Hours)", color="white", fontsize=14, pad=10)
        ax1.set_xticks(range(len(date_range)))
        ax1.set_xticklabels([d.strftime('%m/%d') for d in date_range], rotation=45)
        ax1.tick_params(colors="white")
        ax1.set_facecolor(COLORS["card"])
        ax1.legend(facecolor=COLORS["card"], edgecolor="white", labelcolor="white")
        for spine in ax1.spines.values():
            spine.set_edgecolor('#444')

        # 2. Tag distribution pie
        ax2 = fig.add_subplot(gs[1, 0])
        tag_sum = self.db.groupby('tag')['duration'].sum()
        if not tag_sum.empty:
            wedges, texts, autotexts = ax2.pie(tag_sum.values, labels=tag_sum.index,
                                               autopct='%1.1f%%', startangle=90,
                                               textprops={'color': "white", 'fontsize': 10})
            ax2.set_title("Time by Tag (All Time)", color="white", fontsize=12, pad=10)

        # 3. Heatmap - hours by weekday
        ax3 = fig.add_subplot(gs[1, 1])
        self.db['weekday'] = self.db['datetime'].dt.dayofweek
        self.db['hour'] = self.db['datetime'].dt.hour

        heatmap_data = np.zeros((7, 24))
        for _, row in self.db.iterrows():
            heatmap_data[row['weekday'], row['hour']] += row['duration'] / 3600

        im = ax3.imshow(heatmap_data, cmap='YlGn', aspect='auto', interpolation='nearest')
        ax3.set_yticks(range(7))
        ax3.set_yticklabels(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])
        ax3.set_xticks(range(0, 24, 3))
        ax3.set_xticklabels(range(0, 24, 3))
        ax3.set_title("Activity Heatmap (Hour x Weekday)", color="white", fontsize=12, pad=10)
        ax3.tick_params(colors="white")
        ax3.set_facecolor(COLORS["card"])
        plt.colorbar(im, ax=ax3, label='Hours')

        # 4. Tag trends over last 4 weeks
        ax4 = fig.add_subplot(gs[2, :])
        weeks_back = 4
        week_starts = [today - pd.Timedelta(weeks=i) for i in range(weeks_back, -1, -1)]

        top_tags = tag_sum.nlargest(5).index
        for tag in top_tags:
            weekly_hours = []
            for i in range(len(week_starts) - 1):
                mask = (self.db['datetime'] >= week_starts[i]) & \
                       (self.db['datetime'] < week_starts[i + 1]) & \
                       (self.db['tag'] == tag)
                hours = self.db[mask]['duration'].sum() / 3600
                weekly_hours.append(hours)

            ax4.plot(range(len(weekly_hours)), weekly_hours, marker='o', label=tag, linewidth=2)

        ax4.set_title("Tag Trends (Last 4 Weeks)", color="white", fontsize=14, pad=10)
        ax4.set_xticks(range(weeks_back))
        ax4.set_xticklabels([f"Week {i + 1}" for i in range(weeks_back)])
        ax4.tick_params(colors="white")
        ax4.set_facecolor(COLORS["card"])
        ax4.legend(facecolor=COLORS["card"], edgecolor="white", labelcolor="white")
        ax4.grid(alpha=0.2)
        for spine in ax4.spines.values():
            spine.set_edgecolor('#444')

        # Embed in Tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

    # --- HISTORY ---
    def setup_history(self):
        frame = ctk.CTkFrame(self.main_view, fg_color="transparent")
        self.frames["History"] = frame

        # Filters
        filter_frame = ctk.CTkFrame(frame, fg_color="transparent")
        filter_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(filter_frame, text="Filter by tag:").pack(side="left", padx=5)
        self.filter_combo = ctk.CTkComboBox(filter_frame, values=["All"] + self.settings["tags"],
                                            command=lambda _: self.refresh_table(), width=150)
        self.filter_combo.set("All")
        self.filter_combo.pack(side="left", padx=5)

        ctk.CTkButton(filter_frame, text="Export CSV",
                      command=self.export_csv).pack(side="right", padx=5)
        ctk.CTkButton(filter_frame, text="Clear Filters",
                      command=self.clear_filters).pack(side="right", padx=5)

        # Treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#2b2b2b", foreground="white",
                        fieldbackground="#2b2b2b", borderwidth=0, rowheight=30)
        style.configure("Treeview.Heading", background="#1a1a1a", foreground="white", relief="flat")
        style.map("Treeview", background=[('selected', COLORS["accent"])])

        columns = ("date", "time", "tag", "task", "duration", "note")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", height=20)

        for col, width in [("date", 100), ("time", 80), ("tag", 120),
                           ("task", 350), ("duration", 100), ("note", 200)]:
            self.tree.heading(col, text=col.title())
            self.tree.column(col, width=width)

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def refresh_table(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        if self.db.empty:
            return

        # Apply filter
        df_filtered = self.db.copy()
        selected_tag = self.filter_combo.get()
        if selected_tag != "All":
            df_filtered = df_filtered[df_filtered['tag'] == selected_tag]

        sorted_df = df_filtered.sort_values(by='datetime', ascending=False)

        for index, row in sorted_df.iterrows():
            time_str = row['datetime'].strftime("%H:%M")
            dur_str = self.format_time(row['duration'])
            note = row.get('note', '') or ''
            self.tree.insert("", "end", values=(row['date_str'], time_str, row['tag'],
                                                row['task'], dur_str, note))

    def clear_filters(self):
        self.filter_combo.set("All")
        self.refresh_table()

    # --- SETTINGS ---
    def setup_settings(self):
        frame = ctk.CTkScrollableFrame(self.main_view, fg_color="transparent")
        self.frames["Settings"] = frame

        # Goals Section
        goals_card = ctk.CTkFrame(frame, fg_color=COLORS["card"])
        goals_card.pack(fill="x", pady=10, padx=10)

        ctk.CTkLabel(goals_card, text="GOALS", font=("Arial", 16, "bold")).pack(pady=10)

        goals_grid = ctk.CTkFrame(goals_card, fg_color="transparent")
        goals_grid.pack(padx=20, pady=10)

        ctk.CTkLabel(goals_grid, text="Daily Goal (hours):").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.entry_daily_goal = ctk.CTkEntry(goals_grid, width=100)
        self.entry_daily_goal.grid(row=0, column=1, padx=10, pady=10)

        ctk.CTkLabel(goals_grid, text="Weekly Goal (hours):").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.entry_weekly_goal = ctk.CTkEntry(goals_grid, width=100)
        self.entry_weekly_goal.grid(row=1, column=1, padx=10, pady=10)

        ctk.CTkLabel(goals_grid, text="Global Goal (hours):").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.entry_global_goal = ctk.CTkEntry(goals_grid, width=100)
        self.entry_global_goal.grid(row=2, column=1, padx=10, pady=10)

        ctk.CTkButton(goals_card, text="Save Goals", command=self.save_goals_settings,
                      fg_color=COLORS["success"]).pack(pady=10)

        # Tags Section
        tags_card = ctk.CTkFrame(frame, fg_color=COLORS["card"])
        tags_card.pack(fill="x", pady=10, padx=10)

        ctk.CTkLabel(tags_card, text="TAGS MANAGEMENT", font=("Arial", 16, "bold")).pack(pady=10)

        tags_controls = ctk.CTkFrame(tags_card, fg_color="transparent")
        tags_controls.pack(padx=20, pady=10)

        self.entry_new_tag = ctk.CTkEntry(tags_controls, placeholder_text="New tag name", width=200)
        self.entry_new_tag.pack(side="left", padx=5)

        ctk.CTkButton(tags_controls, text="Add Tag", command=self.add_tag,
                      fg_color=COLORS["success"], width=100).pack(side="left", padx=5)

        # Tags list
        self.tags_listbox_frame = ctk.CTkFrame(tags_card, fg_color=COLORS["bg"])
        self.tags_listbox_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Info
        info_card = ctk.CTkFrame(frame, fg_color=COLORS["card"])
        info_card.pack(fill="x", pady=10, padx=10)

        ctk.CTkLabel(info_card, text="KEYBOARD SHORTCUTS", font=("Arial", 16, "bold")).pack(pady=10)

        shortcuts = [
            ("Space", "Start/Pause timer"),
            ("Enter", "Log current session"),
            ("Ctrl+Z", "Undo last log")
        ]

        for key, desc in shortcuts:
            row = ctk.CTkFrame(info_card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=5)
            ctk.CTkLabel(row, text=key, font=("Roboto Mono", 12, "bold"),
                         text_color=COLORS["accent"]).pack(side="left", padx=10)
            ctk.CTkLabel(row, text=desc).pack(side="left")

    def refresh_settings_ui(self):
        # Load current values
        self.entry_daily_goal.delete(0, 'end')
        self.entry_daily_goal.insert(0, str(self.settings["goals"]["daily"]))

        self.entry_weekly_goal.delete(0, 'end')
        self.entry_weekly_goal.insert(0, str(self.settings["goals"]["weekly"]))

        self.entry_global_goal.delete(0, 'end')
        self.entry_global_goal.insert(0, str(self.settings["goals"]["global"]))

        # Refresh tags list
        for widget in self.tags_listbox_frame.winfo_children():
            widget.destroy()

        for tag in self.settings["tags"]:
            tag_row = ctk.CTkFrame(self.tags_listbox_frame, fg_color=COLORS["card"])
            tag_row.pack(fill="x", padx=5, pady=3)

            ctk.CTkLabel(tag_row, text=tag, font=("Arial", 12)).pack(side="left", padx=10, pady=5)
            ctk.CTkButton(tag_row, text="Remove", command=lambda t=tag: self.remove_tag(t),
                          fg_color=COLORS["danger"], width=80).pack(side="right", padx=10, pady=5)

    def save_goals_settings(self):
        try:
            self.settings["goals"]["daily"] = float(self.entry_daily_goal.get())
            self.settings["goals"]["weekly"] = float(self.entry_weekly_goal.get())
            self.settings["goals"]["global"] = float(self.entry_global_goal.get())
            self.save_settings()
            messagebox.showinfo("Success", "Goals updated successfully!")
            self.update_progress_bar()
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for goals")

    def add_tag(self):
        new_tag = self.entry_new_tag.get().strip().title()  # Normalize to Title Case
        if not new_tag:
            messagebox.showwarning("Warning", "Tag name cannot be empty")
            return

        if new_tag in self.settings["tags"]:
            messagebox.showwarning("Warning", "Tag already exists")
            return

        self.settings["tags"].append(new_tag)
        self.save_settings()
        self.entry_new_tag.delete(0, 'end')
        self.refresh_settings_ui()

        # Update combo boxes
        self.combo_tag.configure(values=self.settings["tags"])
        self.filter_combo.configure(values=["All"] + self.settings["tags"])

        messagebox.showinfo("Success", f"Tag '{new_tag}' added!")

    def remove_tag(self, tag):
        if messagebox.askyesno("Confirm", f"Remove tag '{tag}'? (Existing logs will keep this tag)"):
            self.settings["tags"].remove(tag)
            self.save_settings()
            self.refresh_settings_ui()
            self.combo_tag.configure(values=self.settings["tags"])
            self.filter_combo.configure(values=["All"] + self.settings["tags"])

    # --- LOGIC ---
    def toggle_timer(self):
        if not self.running:
            self.running = True
            self.start_time = time.time()
            self.btn_start.configure(text="PAUSE (Space)", fg_color=COLORS["warning"], text_color="black")
        else:
            self.running = False
            self.accumulated_time += time.time() - self.start_time
            self.btn_start.configure(text="RESUME (Space)", fg_color=COLORS["success"], text_color="white")

    def get_current_duration(self):
        if self.running:
            return self.accumulated_time + (time.time() - self.start_time)
        return self.accumulated_time

    def log_lap(self):
        duration = self.get_current_duration()
        if duration < 1:
            messagebox.showwarning("Warning", "Timer must run for at least 1 second")
            return

        tag = self.combo_tag.get().strip().title()  # Normalize case
        task = self.entry_task.get().strip() or "Unnamed Task"
        note = self.entry_note.get().strip()

        # Add to DataFrame
        new_row = {
            "datetime": datetime.now(),
            "date_str": datetime.now().strftime("%Y-%m-%d"),
            "tag": tag,
            "task": task,
            "duration": duration,
            "note": note
        }

        new_df = pd.DataFrame([new_row])
        self.db = pd.concat([self.db, new_df], ignore_index=True)

        self.save_data()

        # Reset
        self.running = False
        self.accumulated_time = 0
        self.start_time = 0
        self.btn_start.configure(text="START (Space)", fg_color=COLORS["success"])
        self.entry_task.delete(0, 'end')
        self.entry_note.delete(0, 'end')

        self.update_progress_bar()
        self.refresh_recent_logs()

        messagebox.showinfo("Logged!", f"Session logged: {self.format_time(duration)}")

    def undo_last_log(self):
        if self.db.empty:
            messagebox.showinfo("Info", "No logs to undo")
            return

        if messagebox.askyesno("Confirm", "Delete the last log entry?"):
            self.db = self.db.iloc[:-1]
            self.save_data()
            self.update_progress_bar()
            self.refresh_recent_logs()
            if self.frames["History"].winfo_ismapped():
                self.refresh_table()
            messagebox.showinfo("Success", "Last log removed")

    def calculate_streak(self):
        """Вычисление streak (дней подряд с выполненной целью)"""
        if self.db.empty:
            return 0

        daily_goal_sec = self.settings["goals"]["daily"] * 3600
        dates = self.db.groupby('date_str')['duration'].sum()
        dates = dates[dates >= daily_goal_sec].sort_index(ascending=False)

        if dates.empty:
            return 0

        streak = 0
        current_date = pd.Timestamp.now().normalize()

        for date_str in dates.index:
            date = pd.Timestamp(date_str)
            if date == current_date - pd.Timedelta(days=streak):
                streak += 1
            else:
                break

        return streak

    def update_timer_loop(self):
        # Current Lap
        dur = self.get_current_duration()
        ms = int((dur % 1) * 100)
        self.lbl_main_timer.configure(text=f"{self.format_time(dur)}.{ms:02d}")

        # Stats Update
        if not self.db.empty:
            today_str = datetime.now().strftime("%Y-%m-%d")
            tag = self.combo_tag.get().title()

            # Today total
            today_total = self.db[self.db['date_str'] == today_str]['duration'].sum()
            if self.running:
                today_total += dur

            # Week total
            week_start = pd.Timestamp.now().normalize() - pd.Timedelta(days=pd.Timestamp.now().weekday())
            week_total = self.db[self.db['datetime'] >= week_start]['duration'].sum()
            if self.running:
                week_total += dur

            # Current tag today
            tag_total = self.db[(self.db['date_str'] == today_str) & (self.db['tag'] == tag)]['duration'].sum()
            if self.running:
                tag_total += dur

            # Streak
            streak = self.calculate_streak()

            self.today_lbl.configure(text=self.format_time(today_total, short=True))
            self.week_lbl.configure(text=self.format_time(week_total, short=True))
            self.tag_lbl.configure(text=self.format_time(tag_total, short=True))
            self.streak_lbl.configure(text=f"{streak} days")

        # Refresh recent logs periodically (every 5 seconds when dashboard is visible)
        if hasattr(self, '_last_refresh'):
            if time.time() - self._last_refresh > 5 and self.frames["Dashboard"].winfo_ismapped():
                self.refresh_recent_logs()
                self._last_refresh = time.time()
        else:
            self._last_refresh = time.time()
            self.refresh_recent_logs()

        self.after(50, self.update_timer_loop)

    def update_progress_bar(self):
        if self.db.empty:
            self.progress_daily.set(0)
            self.lbl_daily_prog.configure(text="0%")
            self.progress_weekly.set(0)
            self.lbl_weekly_prog.configure(text="0%")
            return

        # Daily
        today_str = datetime.now().strftime("%Y-%m-%d")
        total_today = self.db[self.db['date_str'] == today_str]['duration'].sum()
        daily_goal_sec = self.settings["goals"]["daily"] * 3600

        daily_ratio = min(total_today / daily_goal_sec, 1.0)
        self.progress_daily.set(daily_ratio)
        self.lbl_daily_prog.configure(text=f"{int(daily_ratio * 100)}% ({self.format_time(total_today, short=True)})")

        # Weekly
        week_start = pd.Timestamp.now().normalize() - pd.Timedelta(days=pd.Timestamp.now().weekday())
        total_week = self.db[self.db['datetime'] >= week_start]['duration'].sum()
        weekly_goal_sec = self.settings["goals"]["weekly"] * 3600

        weekly_ratio = min(total_week / weekly_goal_sec, 1.0)
        self.progress_weekly.set(weekly_ratio)
        self.lbl_weekly_prog.configure(text=f"{int(weekly_ratio * 100)}% ({self.format_time(total_week, short=True)})")

    def format_time(self, seconds, short=False):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        if short:
            return f"{h}h {m}m"
        return f"{h:02}:{m:02}:{s:02}"

    def export_csv(self):
        if self.db.empty:
            messagebox.showinfo("Info", "No data to export")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.db.to_csv(filename, index=False)
            messagebox.showinfo("Success", f"Data exported to {filename}")


if __name__ == "__main__":
    app = LogWatchPro()
    app.mainloop()