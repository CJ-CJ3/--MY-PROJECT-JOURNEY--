"""
NOISE - Task Management Application
Vintage Notebook with Desktop Widget, Timer Alerts & Sub-tasks
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import json
import os
import threading
import time
import sys
import calendar

# For Windows startup and sounds
try:
    import winreg

    WINREG_AVAILABLE = True
except ImportError:
    WINREG_AVAILABLE = False

try:
    import winsound

    SOUND_AVAILABLE = True
except ImportError:
    SOUND_AVAILABLE = False


class CalendarDropdown(tk.Frame):
    """Dropdown calendar for date selection"""

    def __init__(self, parent, bg_color="#FFFACD", **kwargs):
        self.paper_color = bg_color

        super().__init__(parent, bg=self.paper_color)

        self.selected_date = datetime.now()
        self.date_var = tk.StringVar(value=self.selected_date.strftime("%Y-%m-%d"))

        entry_frame = tk.Frame(self, bg=self.paper_color)
        entry_frame.pack(side=tk.LEFT)

        border = tk.Frame(entry_frame, bg="#1a1a1a", padx=1, pady=1)
        border.pack()

        self.entry = tk.Entry(border, textvariable=self.date_var,
                              font=("Comic Sans MS", 11),
                              bg=self.paper_color, fg="#2D2015",
                              width=12, relief=tk.FLAT,
                              highlightthickness=0)
        self.entry.pack(padx=3, pady=2)

        self.cal_btn = tk.Canvas(self, width=32, height=32,
                                 bg=self.paper_color, highlightthickness=0,
                                 cursor="hand2")
        self.cal_btn.pack(side=tk.LEFT, padx=(5, 0))

        self.cal_btn.create_rectangle(3, 5, 29, 29, fill="#D4694A",
                                      outline="#1a1a1a", width=2)
        self.cal_btn.create_rectangle(3, 5, 29, 13, fill="#B85040",
                                      outline="#1a1a1a", width=2)
        self.cal_btn.create_text(16, 21, text="31", font=("Arial", 9, "bold"),
                                 fill="#FFFFFF")

        self.cal_btn.bind("<Button-1>", self.show_calendar)
        self.calendar_window = None

    def show_calendar(self, event=None):
        if self.calendar_window and self.calendar_window.winfo_exists():
            self.calendar_window.destroy()
            return

        self.calendar_window = tk.Toplevel(self)
        self.calendar_window.overrideredirect(True)
        self.calendar_window.attributes("-topmost", True)

        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() + 5
        self.calendar_window.geometry(f"+{x}+{y}")

        cal_frame = tk.Frame(self.calendar_window, bg="#FFFACD",
                             highlightthickness=3, highlightbackground="#1a1a1a")
        cal_frame.pack()

        self.build_calendar(cal_frame, self.selected_date.year,
                            self.selected_date.month)

    def build_calendar(self, parent, year, month):
        for widget in parent.winfo_children():
            widget.destroy()

        header = tk.Frame(parent, bg="#D4694A")
        header.pack(fill=tk.X)

        prev_btn = tk.Label(header, text="◄", font=("Arial", 12, "bold"),
                            bg="#D4694A", fg="#FFFFFF", cursor="hand2",
                            padx=10, pady=5)
        prev_btn.pack(side=tk.LEFT)
        prev_btn.bind("<Button-1>", lambda e: self.change_month(-1, parent))

        month_label = tk.Label(header,
                               text=f"{calendar.month_name[month]} {year}",
                               font=("Comic Sans MS", 11, "bold"),
                               bg="#D4694A", fg="#FFFFFF", pady=5)
        month_label.pack(side=tk.LEFT, expand=True)

        next_btn = tk.Label(header, text="►", font=("Arial", 12, "bold"),
                            bg="#D4694A", fg="#FFFFFF", cursor="hand2",
                            padx=10, pady=5)
        next_btn.pack(side=tk.RIGHT)
        next_btn.bind("<Button-1>", lambda e: self.change_month(1, parent))

        days_frame = tk.Frame(parent, bg="#FFFACD")
        days_frame.pack()

        for day in ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]:
            lbl = tk.Label(days_frame, text=day, font=("Arial", 9, "bold"),
                           bg="#FFFACD", fg="#6D5D4D", width=4)
            lbl.pack(side=tk.LEFT)

        cal = calendar.Calendar(firstweekday=0)
        month_days = cal.monthdayscalendar(year, month)

        for week in month_days:
            week_frame = tk.Frame(parent, bg="#FFFACD")
            week_frame.pack()

            for day in week:
                if day == 0:
                    lbl = tk.Label(week_frame, text="", width=4, bg="#FFFACD")
                else:
                    is_today = (day == datetime.now().day and
                                month == datetime.now().month and
                                year == datetime.now().year)

                    bg = "#FFD700" if is_today else "#FFFACD"

                    lbl = tk.Label(week_frame, text=str(day),
                                   font=("Arial", 10),
                                   bg=bg, fg="#2D2015", width=4,
                                   cursor="hand2")
                    lbl.bind("<Button-1>",
                             lambda e, d=day: self.select_date(year, month, d))
                    lbl.bind("<Enter>", lambda e, l=lbl: l.config(bg="#E0D4BC"))
                    lbl.bind("<Leave>", lambda e, l=lbl, b=bg: l.config(bg=b))

                lbl.pack(side=tk.LEFT)

        self.current_year = year
        self.current_month = month

    def change_month(self, delta, parent):
        month = self.current_month + delta
        year = self.current_year

        if month > 12:
            month = 1
            year += 1
        elif month < 1:
            month = 12
            year -= 1

        self.build_calendar(parent, year, month)

    def select_date(self, year, month, day):
        self.selected_date = datetime(year, month, day)
        self.date_var.set(self.selected_date.strftime("%Y-%m-%d"))
        self.close_calendar()

    def close_calendar(self):
        if self.calendar_window and self.calendar_window.winfo_exists():
            self.calendar_window.destroy()

    def get(self):
        return self.date_var.get()


class DesktopWidget(tk.Toplevel):
    """Desktop widget showing timer tasks"""

    def __init__(self, parent, app, **kwargs):
        super().__init__(parent)

        self.app = app
        self.colors = app.colors

        # Window setup
        self.title("NOISE Timer Widget")
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.95)

        # Position at bottom right of screen
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.widget_width = 300
        self.widget_height = 400

        x = screen_width - self.widget_width - 20
        y = screen_height - self.widget_height - 60

        self.geometry(f"{self.widget_width}x{self.widget_height}+{x}+{y}")

        # Dragging
        self._drag_data = {"x": 0, "y": 0}
        self.is_minimized = False
        self.minimized_height = 40

        self.create_widget()
        self.update_timer_id = None
        self.start_updates()

    def create_widget(self):
        # Main container
        self.main_frame = tk.Frame(self, bg="#2D2015", highlightthickness=3,
                                   highlightbackground="#1a1a1a")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        self.header = tk.Frame(self.main_frame, bg="#D4694A", cursor="hand2")
        self.header.pack(fill=tk.X)

        # Bind drag to header
        self.header.bind("<Button-1>", self.start_drag)
        self.header.bind("<B1-Motion>", self.on_drag)

        # Title
        title_label = tk.Label(self.header, text="⏱️ TIMER TASKS",
                               font=("Impact", 14, "bold"),
                               bg="#D4694A", fg="#FFFFFF",
                               padx=10, pady=8)
        title_label.pack(side=tk.LEFT)
        title_label.bind("<Button-1>", self.start_drag)
        title_label.bind("<B1-Motion>", self.on_drag)

        # Control buttons
        btn_frame = tk.Frame(self.header, bg="#D4694A")
        btn_frame.pack(side=tk.RIGHT, padx=5)

        # Minimize button
        self.min_btn = tk.Label(btn_frame, text="─", font=("Arial", 12, "bold"),
                                bg="#D4694A", fg="#FFFFFF", padx=5,
                                cursor="hand2")
        self.min_btn.pack(side=tk.LEFT, padx=2)
        self.min_btn.bind("<Button-1>", self.toggle_minimize)
        self.min_btn.bind("<Enter>", lambda e: self.min_btn.config(bg="#B85040"))
        self.min_btn.bind("<Leave>", lambda e: self.min_btn.config(bg="#D4694A"))

        # Close button
        close_btn = tk.Label(btn_frame, text="✕", font=("Arial", 12, "bold"),
                             bg="#D4694A", fg="#FFFFFF", padx=5,
                             cursor="hand2")
        close_btn.pack(side=tk.LEFT, padx=2)
        close_btn.bind("<Button-1>", self.close_widget)
        close_btn.bind("<Enter>", lambda e: close_btn.config(bg="#B85040"))
        close_btn.bind("<Leave>", lambda e: close_btn.config(bg="#D4694A"))

        # Content area
        self.content_frame = tk.Frame(self.main_frame, bg="#F5ECD7")
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)

        # Scrollable task list
        self.canvas = tk.Canvas(self.content_frame, bg="#F5ECD7",
                                highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical",
                                       command=self.canvas.yview)

        self.task_frame = tk.Frame(self.canvas, bg="#F5ECD7")

        self.task_frame.bind("<Configure>",
                             lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.canvas_window = self.canvas.create_window((0, 0), window=self.task_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind("<Configure>",
                         lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Mousewheel scrolling
        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", self._on_mousewheel))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))

        # Footer with open main app button
        self.footer = tk.Frame(self.main_frame, bg="#E0D4BC")
        self.footer.pack(fill=tk.X, padx=3, pady=(0, 3))

        open_btn = tk.Label(self.footer, text="📓 Open Notebook",
                            font=("Comic Sans MS", 10, "bold"),
                            bg="#4A8B4A", fg="#FFFFFF",
                            padx=10, pady=5, cursor="hand2")
        open_btn.pack(fill=tk.X, padx=5, pady=5)
        open_btn.bind("<Button-1>", self.open_main_app)
        open_btn.bind("<Enter>", lambda e: open_btn.config(bg="#3A7B3A"))
        open_btn.bind("<Leave>", lambda e: open_btn.config(bg="#4A8B4A"))

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def start_drag(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def on_drag(self, event):
        x = self.winfo_x() + (event.x - self._drag_data["x"])
        y = self.winfo_y() + (event.y - self._drag_data["y"])
        self.geometry(f"+{x}+{y}")

    def toggle_minimize(self, event=None):
        if self.is_minimized:
            # Restore
            self.geometry(f"{self.widget_width}x{self.widget_height}")
            self.content_frame.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
            self.footer.pack(fill=tk.X, padx=3, pady=(0, 3))
            self.min_btn.config(text="─")
            self.is_minimized = False
        else:
            # Minimize
            self.content_frame.pack_forget()
            self.footer.pack_forget()
            self.geometry(f"{self.widget_width}x{self.minimized_height}")
            self.min_btn.config(text="□")
            self.is_minimized = True

    def close_widget(self, event=None):
        self.stop_updates()
        self.app.widget = None
        self.app.widget_var.set(False)
        self.destroy()

    def open_main_app(self, event=None):
        self.app.root.deiconify()
        self.app.root.lift()
        self.app.root.focus_force()

    def start_updates(self):
        self.update_tasks()

    def stop_updates(self):
        if self.update_timer_id:
            self.after_cancel(self.update_timer_id)

    def update_tasks(self):
        if not self.winfo_exists():
            return

        # Clear existing tasks
        for widget in self.task_frame.winfo_children():
            widget.destroy()

        # Get timer tasks only (pending)
        timer_tasks = [t for t in self.app.tasks
                       if t.get('is_timer') and t['status'] == 'pending']

        # Sort by deadline
        timer_tasks.sort(key=lambda x: x['deadline'])

        if not timer_tasks:
            empty_label = tk.Label(self.task_frame, text="No active timers",
                                   font=("Comic Sans MS", 11, "italic"),
                                   bg="#F5ECD7", fg="#6D5D4D", pady=20)
            empty_label.pack()
        else:
            for task in timer_tasks:
                self.create_task_item(task)

        # Schedule next update
        self.update_timer_id = self.after(1000, self.update_tasks)

    def create_task_item(self, task):
        item_frame = tk.Frame(self.task_frame, bg="#FFFACD",
                              highlightthickness=2, highlightbackground="#1a1a1a")
        item_frame.pack(fill=tk.X, padx=5, pady=3)

        # Task name
        name_label = tk.Label(item_frame, text=task['name'],
                              font=("Comic Sans MS", 10, "bold"),
                              bg="#FFFACD", fg="#2D2015",
                              anchor="w", wraplength=220)
        name_label.pack(fill=tk.X, padx=8, pady=(5, 2))

        # Subtask progress if exists
        subtasks = task.get('subtasks', [])
        if subtasks:
            completed = sum(1 for s in subtasks if s.get('completed'))
            total = len(subtasks)
            progress_text = f"📋 {completed}/{total} steps"
            progress_color = "#4A8B4A" if completed == total else "#B86000"

            progress_label = tk.Label(item_frame, text=progress_text,
                                      font=("Comic Sans MS", 8, "bold"),
                                      bg="#FFFACD", fg=progress_color)
            progress_label.pack(anchor="w", padx=8)

        # Time remaining
        deadline = datetime.strptime(task['deadline'], '%Y-%m-%d %H:%M:%S')
        time_left, urgency = self.get_time_left(deadline)

        if urgency == "critical":
            time_bg = "#FF6B6B"
            time_fg = "#FFFFFF"
        elif urgency == "warning":
            time_bg = "#FFB347"
            time_fg = "#2D2015"
        else:
            time_bg = "#90EE90"
            time_fg = "#2D2015"

        time_frame = tk.Frame(item_frame, bg=time_bg)
        time_frame.pack(fill=tk.X, padx=8, pady=(2, 5))

        time_label = tk.Label(time_frame, text=f"⏰ {time_left}",
                              font=("Impact", 11),
                              bg=time_bg, fg=time_fg,
                              pady=2)
        time_label.pack(side=tk.LEFT, padx=5)

        # Complete button
        complete_btn = tk.Label(time_frame, text="✓",
                                font=("Arial", 11, "bold"),
                                bg="#4A8B4A", fg="#FFFFFF",
                                padx=6, pady=1, cursor="hand2")
        complete_btn.pack(side=tk.RIGHT, padx=5)
        complete_btn.bind("<Button-1>", lambda e, t=task: self.complete_task(t))

    def get_time_left(self, deadline):
        now = datetime.now()
        if deadline < now:
            return "OVERDUE!", "critical"

        diff = deadline - now
        total_seconds = diff.total_seconds()
        days = diff.days
        hours, remainder = divmod(diff.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        # Determine urgency
        if total_seconds <= 60:  # 1 minute or less
            urgency = "critical"
        elif total_seconds <= 300:  # 5 minutes or less
            urgency = "warning"
        else:
            urgency = "normal"

        if days > 0:
            return f"{days}D {hours}H {minutes}M", urgency
        elif hours > 0:
            return f"{hours}H {minutes}M {seconds}S", urgency
        elif minutes > 0:
            return f"{minutes}M {seconds}S", urgency
        else:
            return f"{seconds}S", urgency

    def complete_task(self, task):
        self.app.complete_task(task)


class TimerAlertPopup(tk.Toplevel):
    """Alert popup when timer is about to expire"""

    def __init__(self, parent, app, task, time_left, **kwargs):
        super().__init__(parent)

        self.app = app
        self.task = task
        self.colors = app.colors

        # Window setup
        self.title("⏰ Timer Alert!")
        self.overrideredirect(True)
        self.attributes("-topmost", True)

        # Center on screen
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        w, h = 380, 250
        x = (screen_width - w) // 2
        y = (screen_height - h) // 2

        self.geometry(f"{w}x{h}+{x}+{y}")

        self.create_alert(time_left)

        # Auto close after 30 seconds
        self.auto_close_id = self.after(30000, self.close_alert)

        # Flash effect
        self.flash_count = 0
        self.flash_alert()

    def create_alert(self, time_left):
        # Main frame with border
        main_frame = tk.Frame(self, bg="#1a1a1a")
        main_frame.pack(fill=tk.BOTH, expand=True)

        inner_frame = tk.Frame(main_frame, bg="#FFDDDD")
        inner_frame.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)

        # Header
        header = tk.Frame(inner_frame, bg="#D4694A")
        header.pack(fill=tk.X)

        tk.Label(header, text="⏰ TIME'S ALMOST UP!",
                 font=("Impact", 18, "bold"),
                 bg="#D4694A", fg="#FFFFFF",
                 pady=10).pack(side=tk.LEFT, padx=15)

        # Close button
        close_btn = tk.Label(header, text="✕", font=("Arial", 14, "bold"),
                             bg="#D4694A", fg="#FFFFFF", padx=10,
                             cursor="hand2")
        close_btn.pack(side=tk.RIGHT, padx=5, pady=5)
        close_btn.bind("<Button-1>", self.close_alert)

        # Content
        content = tk.Frame(inner_frame, bg="#FFDDDD")
        content.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        # Task name
        tk.Label(content, text="📋 Task:",
                 font=("Comic Sans MS", 10),
                 bg="#FFDDDD", fg="#6D5D4D").pack(anchor="w")

        tk.Label(content, text=self.task['name'],
                 font=("Comic Sans MS", 14, "bold"),
                 bg="#FFDDDD", fg="#2D2015",
                 wraplength=340).pack(anchor="w", pady=(0, 5))

        # Subtask progress
        subtasks = self.task.get('subtasks', [])
        if subtasks:
            completed = sum(1 for s in subtasks if s.get('completed'))
            total = len(subtasks)
            tk.Label(content, text=f"📝 Steps: {completed}/{total} completed",
                     font=("Comic Sans MS", 10),
                     bg="#FFDDDD", fg="#6D5D4D").pack(anchor="w")

        # Time remaining
        self.time_label = tk.Label(content, text=f"⏱️ {time_left} remaining!",
                                   font=("Impact", 16),
                                   bg="#FF6B6B", fg="#FFFFFF",
                                   padx=15, pady=8)
        self.time_label.pack(pady=8)

        # Buttons
        btn_frame = tk.Frame(content, bg="#FFDDDD")
        btn_frame.pack(pady=10)

        # Complete button
        complete_btn = tk.Frame(btn_frame, bg="#1a1a1a", padx=2, pady=2)
        complete_btn.pack(side=tk.LEFT, padx=10)

        complete_inner = tk.Label(complete_btn, text="✓ COMPLETE NOW",
                                  font=("Impact", 12, "bold"),
                                  bg="#4A8B4A", fg="#FFFFFF",
                                  padx=15, pady=8, cursor="hand2")
        complete_inner.pack()
        complete_inner.bind("<Button-1>", self.complete_task)

        # Dismiss button
        dismiss_btn = tk.Frame(btn_frame, bg="#1a1a1a", padx=2, pady=2)
        dismiss_btn.pack(side=tk.LEFT, padx=10)

        dismiss_inner = tk.Label(dismiss_btn, text="DISMISS",
                                 font=("Impact", 12, "bold"),
                                 bg="#888888", fg="#FFFFFF",
                                 padx=15, pady=8, cursor="hand2")
        dismiss_inner.pack()
        dismiss_inner.bind("<Button-1>", self.close_alert)

        # Start time update
        self.update_time()

    def update_time(self):
        if not self.winfo_exists():
            return

        deadline = datetime.strptime(self.task['deadline'], '%Y-%m-%d %H:%M:%S')
        now = datetime.now()

        if deadline < now:
            self.time_label.config(text="⏱️ TIME'S UP!")
            return

        diff = deadline - now
        total_seconds = int(diff.total_seconds())

        if total_seconds >= 60:
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            time_str = f"{minutes}M {seconds}S"
        else:
            time_str = f"{total_seconds}S"

        self.time_label.config(text=f"⏱️ {time_str} remaining!")

        # Continue updating
        self.after(1000, self.update_time)

    def flash_alert(self):
        if not self.winfo_exists():
            return

        if self.flash_count < 6:
            current_bg = self.time_label.cget("bg")
            new_bg = "#FFFFFF" if current_bg == "#FF6B6B" else "#FF6B6B"
            new_fg = "#FF6B6B" if current_bg == "#FF6B6B" else "#FFFFFF"
            self.time_label.config(bg=new_bg, fg=new_fg)
            self.flash_count += 1
            self.after(300, self.flash_alert)
        else:
            self.time_label.config(bg="#FF6B6B", fg="#FFFFFF")

    def complete_task(self, event=None):
        self.app.complete_task(self.task)
        self.close_alert()

    def close_alert(self, event=None):
        if self.auto_close_id:
            self.after_cancel(self.auto_close_id)
        self.destroy()


class NotebookBackground(tk.Canvas):
    """Canvas with vintage notebook paper background"""

    def __init__(self, parent, **kwargs):
        self.paper_color = "#E0D4BC"
        self.paper_light = "#F5ECD7"
        self.line_color = "#C9BDAA"
        self.margin_color = "#CC7777"

        super().__init__(parent, bg=self.paper_color, highlightthickness=0, **kwargs)

        self.line_spacing = 30
        self.bind("<Configure>", self.draw_notebook)

    def draw_notebook(self, event=None):
        self.delete("bg_elements")

        width = self.winfo_width()
        height = self.winfo_height()

        if width <= 1 or height <= 1:
            return

        # Spiral binding - responsive width
        binding_width = max(40, min(50, int(width * 0.05)))
        binding_edge = binding_width + 15

        self.create_rectangle(0, 0, binding_width, height, fill="#7D6550", outline="", tags="bg_elements")
        self.create_rectangle(binding_width, 0, binding_edge, height, fill="#9C7E60", outline="", tags="bg_elements")
        self.create_line(binding_edge, 0, binding_edge, height, fill="#B8A080", width=2, tags="bg_elements")

        # Spiral rings
        for y in range(25, height, 38):
            cx = binding_width - 7
            self.create_oval(cx - 15, y - 9, cx + 15, y + 9, fill="#4A3A2A", outline="", tags="bg_elements")
            self.create_oval(cx - 13, y - 7, cx + 13, y + 7, fill="#808080", outline="#1a1a1a", width=2, tags="bg_elements")
            self.create_arc(cx - 10, y - 4, cx + 10, y + 4, start=40, extent=100, style=tk.ARC,
                            outline="#B0B0B0", width=2, tags="bg_elements")
            self.create_oval(cx - 7, y - 4, cx + 7, y + 4, fill="#5A4A3A", outline="", tags="bg_elements")

        paper_start = binding_edge + 5
        margin = max(20, int(width * 0.03))

        # Light paper center
        self.create_rectangle(paper_start + margin, margin,
                              width - margin, height - margin,
                              fill=self.paper_light, outline="", tags="bg_elements")

        self.create_rectangle(paper_start + margin, margin,
                              width - margin, height - margin,
                              fill="", outline="#B8A890", width=1, tags="bg_elements")

        # Horizontal lines
        for y in range(margin + self.line_spacing + 20, height - margin, self.line_spacing):
            self.create_line(paper_start + margin + 10, y,
                             width - margin - 10, y,
                             fill=self.line_color, width=1, tags="bg_elements")

        # Red margin
        margin_x = paper_start + margin + max(30, int(width * 0.04))
        self.create_line(margin_x, margin + 10, margin_x, height - margin - 10,
                         fill=self.margin_color, width=2, tags="bg_elements")
        self.create_line(margin_x + 4, margin + 10, margin_x + 4, height - margin - 10,
                         fill=self.margin_color, width=1, tags="bg_elements")

        # Header line
        self.create_line(paper_start + margin + 10, margin + 50,
                         width - margin - 10, margin + 50,
                         fill="#B0A090", width=2, tags="bg_elements")

        # Coffee stain - positioned relative to corner
        stain_x = width - max(80, int(width * 0.1))
        stain_y = height - max(90, int(height * 0.12))
        self.create_oval(stain_x - 35, stain_y - 35, stain_x + 35, stain_y + 35,
                         fill="", outline="#D8C8B0", width=3, tags="bg_elements")

        self.tag_lower("bg_elements")


class AddTaskButton(tk.Canvas):
    """Square Add Task button"""

    def __init__(self, parent, command=None, **kwargs):
        super().__init__(parent, width=140, height=50,
                         highlightthickness=0, bg="#F5ECD7", **kwargs)

        self.command = command
        self.is_hovered = False
        self.is_pressed = False

        self.draw_button()

        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
        self.bind("<ButtonRelease-1>", self.on_release)

    def draw_button(self):
        self.delete("all")

        offset = 3 if self.is_pressed else 0
        color = "#C55A3B" if self.is_hovered else "#D4694A"

        # Shadow
        if not self.is_pressed:
            self.create_rectangle(6, 6, 136, 46, fill="#3D3020", outline="")

        # Main button
        self.create_rectangle(offset + 2, offset + 2, offset + 132, offset + 42,
                              fill=color, outline="#1a1a1a", width=3)

        # Plus icon
        cx = 25 + offset
        cy = 22 + offset
        self.create_line(cx - 8, cy, cx + 8, cy, fill="#FFFFFF", width=3)
        self.create_line(cx, cy - 8, cx, cy + 8, fill="#FFFFFF", width=3)

        # Text
        self.create_text(offset + 82, offset + 24, text="ADD TASK",
                         font=("Impact", 14, "bold"), fill="#FFFFFF")

    def on_enter(self, event):
        self.is_hovered = True
        self.draw_button()
        self.config(cursor="hand2")

    def on_leave(self, event):
        self.is_hovered = False
        self.is_pressed = False
        self.draw_button()

    def on_click(self, event):
        self.is_pressed = True
        self.draw_button()

    def on_release(self, event):
        if self.is_pressed:
            self.is_pressed = False
            self.draw_button()
            if self.command:
                self.command()


class StickyNotePopup(tk.Toplevel):
    """Sticky note popup for adding tasks with subtasks"""

    def __init__(self, parent, on_add_task, colors, **kwargs):
        super().__init__(parent)

        self.on_add_task = on_add_task
        self.colors = colors
        self.note_color = "#FFFACD"
        self.subtasks = []  # List of subtask names

        self.overrideredirect(True)
        self.attributes("-topmost", True)

        # Center on parent
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_x()
        py = parent.winfo_y()

        # Increased height for subtasks
        w, h = 420, 720
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2

        # Make sure it fits on screen
        screen_height = self.winfo_screenheight()
        if y + h > screen_height - 50:
            y = max(10, screen_height - h - 50)

        self.geometry(f"{w}x{h}+{x}+{y}")

        self.create_note()

        # Dragging
        self._drag_data = {"x": 0, "y": 0}

    def start_drag(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def on_drag(self, event):
        x = self.winfo_x() + (event.x - self._drag_data["x"])
        y = self.winfo_y() + (event.y - self._drag_data["y"])
        self.geometry(f"+{x}+{y}")

    def create_note(self):
        # Main canvas
        self.canvas = tk.Canvas(self, width=420, height=720,
                                highlightthickness=0, bg="#E0D4BC")
        self.canvas.pack()

        # Bind drag to canvas
        self.canvas.bind("<Button-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.on_drag)

        # Shadow
        self.canvas.create_polygon(
            15, 18, 408, 22, 415, 708, 10, 702,
            fill="#6D5D4D", outline=""
        )

        # Note body with folded corner
        self.canvas.create_polygon(
            5, 8, 395, 5, 400, 660, 360, 700, 5, 698,
            fill=self.note_color, outline="#1a1a1a", width=3
        )

        # Folded corner
        self.canvas.create_polygon(
            360, 700, 400, 660, 398, 698,
            fill="#E8DC9C", outline="#1a1a1a", width=2
        )

        # Tape at top
        self.canvas.create_polygon(
            160, -5, 260, -3, 258, 25, 162, 22,
            fill="#D0D0D0", outline="#AAAAAA", width=1
        )

        # Pin holes
        self.canvas.create_oval(185, 2, 195, 12, fill="#E8DC9C", outline="#999999")
        self.canvas.create_oval(225, 2, 235, 12, fill="#E8DC9C", outline="#999999")

        # Title
        self.canvas.create_text(202, 52, text="✏️ NEW TASK",
                                font=("Impact", 28, "bold"), fill="#8B7355")
        self.canvas.create_text(200, 50, text="✏️ NEW TASK",
                                font=("Impact", 28, "bold"), fill="#5D4D3D")

        # Decorative line
        self.canvas.create_line(50, 80, 350, 80, fill="#D4A574", width=2, dash=(5, 3))

        # Content frame with scrollable area
        content_container = tk.Frame(self.canvas, bg=self.note_color)
        self.canvas.create_window(200, 390, window=content_container, width=370, height=580)

        # Create scrollable content
        self.content_canvas = tk.Canvas(content_container, bg=self.note_color,
                                        highlightthickness=0, height=580)
        scrollbar = ttk.Scrollbar(content_container, orient="vertical",
                                  command=self.content_canvas.yview)

        self.content_frame = tk.Frame(self.content_canvas, bg=self.note_color)

        self.content_frame.bind("<Configure>",
                                lambda e: self.content_canvas.configure(scrollregion=self.content_canvas.bbox("all")))

        self.content_canvas.create_window((0, 0), window=self.content_frame, anchor="nw", width=350)
        self.content_canvas.configure(yscrollcommand=scrollbar.set)

        self.content_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Mousewheel for content
        self.content_canvas.bind("<Enter>",
                                 lambda e: self.content_canvas.bind_all("<MouseWheel>", self._on_content_mousewheel))
        self.content_canvas.bind("<Leave>",
                                 lambda e: self.content_canvas.unbind_all("<MouseWheel>"))

        # Build content
        self.build_content()

    def _on_content_mousewheel(self, event):
        self.content_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def build_content(self):
        content = self.content_frame

        # Task name
        name_frame = tk.Frame(content, bg=self.note_color)
        name_frame.pack(fill=tk.X, pady=(10, 12), padx=5)

        tk.Label(name_frame, text="WHAT TO DO:",
                 font=("Comic Sans MS", 11, "bold"),
                 bg=self.note_color, fg="#5D4D3D").pack(anchor="w")

        entry_border = tk.Frame(name_frame, bg="#1a1a1a", padx=2, pady=2)
        entry_border.pack(fill=tk.X, pady=(5, 0))

        self.task_entry = tk.Entry(entry_border, font=("Comic Sans MS", 12),
                                   bg=self.note_color, fg="#2D2015",
                                   relief=tk.FLAT, insertbackground="#2D2015")
        self.task_entry.pack(fill=tk.X, padx=3, pady=3, ipady=5)
        self.task_entry.focus_set()

        # Subtasks section
        subtask_frame = tk.Frame(content, bg=self.note_color)
        subtask_frame.pack(fill=tk.X, pady=(0, 12), padx=5)

        tk.Label(subtask_frame, text="📋 STEPS (optional):",
                 font=("Comic Sans MS", 11, "bold"),
                 bg=self.note_color, fg="#5D4D3D").pack(anchor="w")

        # Add subtask row
        add_subtask_row = tk.Frame(subtask_frame, bg=self.note_color)
        add_subtask_row.pack(fill=tk.X, pady=(5, 5))

        subtask_entry_border = tk.Frame(add_subtask_row, bg="#1a1a1a", padx=1, pady=1)
        subtask_entry_border.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.subtask_entry = tk.Entry(subtask_entry_border, font=("Comic Sans MS", 10),
                                      bg=self.note_color, fg="#2D2015",
                                      relief=tk.FLAT, insertbackground="#2D2015")
        self.subtask_entry.pack(fill=tk.X, padx=2, pady=2, ipady=3)
        self.subtask_entry.bind("<Return>", lambda e: self.add_subtask())

        # Add subtask button
        add_sub_btn = tk.Canvas(add_subtask_row, width=32, height=28,
                                bg=self.note_color, highlightthickness=0, cursor="hand2")
        add_sub_btn.pack(side=tk.LEFT, padx=(5, 0))
        add_sub_btn.create_rectangle(2, 2, 30, 26, fill="#4A8B4A", outline="#1a1a1a", width=2)
        add_sub_btn.create_text(16, 14, text="+", font=("Arial", 14, "bold"), fill="#FFFFFF")
        add_sub_btn.bind("<Button-1>", lambda e: self.add_subtask())

        # Subtasks list container
        self.subtasks_list_frame = tk.Frame(subtask_frame, bg=self.note_color)
        self.subtasks_list_frame.pack(fill=tk.X, pady=(5, 0))

        # Points
        points_frame = tk.Frame(content, bg=self.note_color)
        points_frame.pack(fill=tk.X, pady=(0, 12), padx=5)

        tk.Label(points_frame, text="STARS:",
                 font=("Comic Sans MS", 11, "bold"),
                 bg=self.note_color, fg="#5D4D3D").pack(side=tk.LEFT)

        self.points_var = tk.IntVar(value=10)

        points_inner = tk.Frame(points_frame, bg=self.note_color)
        points_inner.pack(side=tk.LEFT, padx=(10, 0))

        dec_btn = tk.Canvas(points_inner, width=28, height=28,
                            bg=self.note_color, highlightthickness=0, cursor="hand2")
        dec_btn.pack(side=tk.LEFT)
        dec_btn.create_oval(2, 2, 26, 26, fill="#D4694A", outline="#1a1a1a", width=2)
        dec_btn.create_text(14, 14, text="-", font=("Arial", 14, "bold"), fill="#FFFFFF")
        dec_btn.bind("<Button-1>", lambda e: self.adjust_points(-1))

        points_border = tk.Frame(points_inner, bg="#1a1a1a", padx=1, pady=1)
        points_border.pack(side=tk.LEFT, padx=5)

        self.points_label = tk.Label(points_border, textvariable=self.points_var,
                                     font=("Impact", 16), width=4,
                                     bg=self.note_color, fg="#2D2015")
        self.points_label.pack(padx=3, pady=2)

        inc_btn = tk.Canvas(points_inner, width=28, height=28,
                            bg=self.note_color, highlightthickness=0, cursor="hand2")
        inc_btn.pack(side=tk.LEFT)
        inc_btn.create_oval(2, 2, 26, 26, fill="#4A8B4A", outline="#1a1a1a", width=2)
        inc_btn.create_text(14, 14, text="+", font=("Arial", 14, "bold"), fill="#FFFFFF")
        inc_btn.bind("<Button-1>", lambda e: self.adjust_points(1))

        # Deadline type
        type_frame = tk.Frame(content, bg=self.note_color)
        type_frame.pack(fill=tk.X, pady=(0, 8), padx=5)

        tk.Label(type_frame, text="DEADLINE TYPE:",
                 font=("Comic Sans MS", 11, "bold"),
                 bg=self.note_color, fg="#5D4D3D").pack(anchor="w")

        type_buttons = tk.Frame(type_frame, bg=self.note_color)
        type_buttons.pack(anchor="w", pady=(5, 0))

        self.deadline_type = tk.StringVar(value="schedule")

        schedule_border = tk.Frame(type_buttons, bg="#1a1a1a", padx=2, pady=2)
        schedule_border.pack(side=tk.LEFT, padx=(0, 10))

        self.schedule_radio = tk.Radiobutton(schedule_border, text="📅 SCHEDULE",
                                             variable=self.deadline_type, value="schedule",
                                             command=self.toggle_deadline_type,
                                             font=("Comic Sans MS", 10, "bold"),
                                             bg=self.note_color, fg="#2D2015",
                                             selectcolor="#FFD700",
                                             activebackground=self.note_color,
                                             indicatoron=0, padx=10, pady=4,
                                             cursor="hand2")
        self.schedule_radio.pack()

        timer_border = tk.Frame(type_buttons, bg="#1a1a1a", padx=2, pady=2)
        timer_border.pack(side=tk.LEFT)

        self.timer_radio = tk.Radiobutton(timer_border, text="⏱️ TIMER",
                                          variable=self.deadline_type, value="timer",
                                          command=self.toggle_deadline_type,
                                          font=("Comic Sans MS", 10, "bold"),
                                          bg=self.note_color, fg="#2D2015",
                                          selectcolor="#FFD700",
                                          activebackground=self.note_color,
                                          indicatoron=0, padx=10, pady=4,
                                          cursor="hand2")
        self.timer_radio.pack()

        # Deadline container
        self.deadline_container = tk.Frame(content, bg=self.note_color)
        self.deadline_container.pack(fill=tk.X, pady=(5, 12), padx=5)

        # Schedule frame
        self.schedule_frame = tk.Frame(self.deadline_container, bg=self.note_color)

        date_row = tk.Frame(self.schedule_frame, bg=self.note_color)
        date_row.pack(fill=tk.X, pady=(0, 5))

        tk.Label(date_row, text="DATE:",
                 font=("Comic Sans MS", 10, "bold"),
                 bg=self.note_color, fg="#5D4D3D").pack(side=tk.LEFT)

        self.calendar = CalendarDropdown(date_row, bg_color=self.note_color)
        self.calendar.pack(side=tk.LEFT, padx=(10, 0))

        time_row = tk.Frame(self.schedule_frame, bg=self.note_color)
        time_row.pack(fill=tk.X)

        tk.Label(time_row, text="TIME:",
                 font=("Comic Sans MS", 10, "bold"),
                 bg=self.note_color, fg="#5D4D3D").pack(side=tk.LEFT)

        time_inner = tk.Frame(time_row, bg=self.note_color)
        time_inner.pack(side=tk.LEFT, padx=(10, 0))

        self.schedule_hour = self.create_spinbox(time_inner, 0, 23, 12, "H")
        tk.Label(time_inner, text=":", font=("Impact", 16),
                 bg=self.note_color, fg="#2D2015").pack(side=tk.LEFT, padx=2)
        self.schedule_minute = self.create_spinbox(time_inner, 0, 59, 0, "M")

        # Timer frame
        self.timer_frame = tk.Frame(self.deadline_container, bg=self.note_color)

        tk.Label(self.timer_frame, text="COUNTDOWN:",
                 font=("Comic Sans MS", 10, "bold"),
                 bg=self.note_color, fg="#5D4D3D").pack(anchor="w")

        timer_border = tk.Frame(self.timer_frame, bg="#1a1a1a", padx=2, pady=2)
        timer_border.pack(anchor="w", pady=(5, 0))

        timer_inner = tk.Frame(timer_border, bg=self.note_color)
        timer_inner.pack(padx=6, pady=6)

        self.timer_hours = self.create_spinbox(timer_inner, 0, 99, 0, "H")
        tk.Label(timer_inner, text=":", font=("Impact", 18),
                 bg=self.note_color, fg="#2D2015").pack(side=tk.LEFT, padx=3)
        self.timer_minutes = self.create_spinbox(timer_inner, 0, 59, 30, "M")
        tk.Label(timer_inner, text=":", font=("Impact", 18),
                 bg=self.note_color, fg="#2D2015").pack(side=tk.LEFT, padx=3)
        self.timer_seconds = self.create_spinbox(timer_inner, 0, 59, 0, "S")

        # Show schedule by default
        self.schedule_frame.pack(fill=tk.X)

        # Buttons row
        btn_frame = tk.Frame(content, bg=self.note_color)
        btn_frame.pack(fill=tk.X, pady=(15, 10), padx=5)

        # Center the buttons
        btn_inner = tk.Frame(btn_frame, bg=self.note_color)
        btn_inner.pack()

        # Add button
        add_btn = self.create_button(btn_inner, "✓ ADD TASK", "#4A8B4A", self.add_task)
        add_btn.pack(side=tk.LEFT, padx=(0, 15))

        # Cancel button
        cancel_btn = self.create_button(btn_inner, "✕ CANCEL", "#B85050", self.cancel)
        cancel_btn.pack(side=tk.LEFT)

    def add_subtask(self):
        """Add a subtask to the list"""
        subtask_name = self.subtask_entry.get().strip()
        if not subtask_name:
            return

        if len(self.subtasks) >= 10:
            return  # Max 10 subtasks

        self.subtasks.append(subtask_name)
        self.subtask_entry.delete(0, tk.END)
        self.refresh_subtasks_list()

    def remove_subtask(self, index):
        """Remove a subtask from the list"""
        if 0 <= index < len(self.subtasks):
            self.subtasks.pop(index)
            self.refresh_subtasks_list()

    def refresh_subtasks_list(self):
        """Refresh the display of subtasks"""
        for widget in self.subtasks_list_frame.winfo_children():
            widget.destroy()

        for i, subtask in enumerate(self.subtasks):
            row = tk.Frame(self.subtasks_list_frame, bg="#F5ECD7")
            row.pack(fill=tk.X, pady=2)

            # Step number
            tk.Label(row, text=f"  {i + 1}.",
                     font=("Comic Sans MS", 9, "bold"),
                     bg="#F5ECD7", fg="#6D5D4D",
                     width=3).pack(side=tk.LEFT)

            # Subtask name
            tk.Label(row, text=subtask,
                     font=("Comic Sans MS", 10),
                     bg="#F5ECD7", fg="#2D2015",
                     anchor="w").pack(side=tk.LEFT, fill=tk.X, expand=True)

            # Remove button
            remove_btn = tk.Canvas(row, width=20, height=20,
                                   bg="#F5ECD7", highlightthickness=0, cursor="hand2")
            remove_btn.pack(side=tk.RIGHT, padx=2)
            remove_btn.create_oval(2, 2, 18, 18, fill="#B85050", outline="#1a1a1a", width=1)
            remove_btn.create_text(10, 10, text="×", font=("Arial", 10, "bold"), fill="#FFFFFF")
            remove_btn.bind("<Button-1>", lambda e, idx=i: self.remove_subtask(idx))

    def create_spinbox(self, parent, from_, to, value, label):
        frame = tk.Frame(parent, bg=self.note_color)
        frame.pack(side=tk.LEFT)

        var = tk.IntVar(value=value)

        up_btn = tk.Canvas(frame, width=28, height=16,
                           bg=self.note_color, highlightthickness=0, cursor="hand2")
        up_btn.pack()
        up_btn.create_rectangle(2, 2, 26, 14, fill="#4A8B4A", outline="#1a1a1a", width=1)
        up_btn.create_text(14, 8, text="▲", font=("Arial", 7), fill="#FFFFFF")
        up_btn.bind("<Button-1>", lambda e: self.spin_adjust(var, 1, from_, to))

        entry_border = tk.Frame(frame, bg="#1a1a1a", padx=1, pady=1)
        entry_border.pack()

        entry = tk.Entry(entry_border, textvariable=var,
                         font=("Impact", 12), width=3,
                         bg=self.note_color, fg="#2D2015",
                         relief=tk.FLAT, justify="center")
        entry.pack(padx=2, pady=1)

        down_btn = tk.Canvas(frame, width=28, height=16,
                             bg=self.note_color, highlightthickness=0, cursor="hand2")
        down_btn.pack()
        down_btn.create_rectangle(2, 2, 26, 14, fill="#D4694A", outline="#1a1a1a", width=1)
        down_btn.create_text(14, 8, text="▼", font=("Arial", 7), fill="#FFFFFF")
        down_btn.bind("<Button-1>", lambda e: self.spin_adjust(var, -1, from_, to))

        tk.Label(frame, text=label, font=("Arial", 7, "bold"),
                 bg=self.note_color, fg="#5D4D3D").pack()

        frame.var = var
        return frame

    def spin_adjust(self, var, delta, min_val, max_val):
        new_val = var.get() + delta
        if new_val > max_val:
            new_val = min_val
        elif new_val < min_val:
            new_val = max_val
        var.set(new_val)

    def create_button(self, parent, text, color, command):
        btn = tk.Canvas(parent, width=120, height=40,
                        bg=self.note_color, highlightthickness=0, cursor="hand2")

        def draw(pressed=False):
            btn.delete("all")
            offset = 3 if pressed else 0

            if not pressed:
                btn.create_rectangle(5, 5, 118, 38, fill="#3D3020", outline="")

            btn.create_rectangle(offset + 2, offset + 2, offset + 114, offset + 35,
                                 fill=color, outline="#1a1a1a", width=2)

            btn.create_text(offset + 59, offset + 19, text=text,
                            font=("Impact", 11, "bold"), fill="#FFFFFF")

        draw()

        def on_press(e):
            draw(True)

        def on_release(e):
            draw()
            command()

        btn.bind("<Button-1>", on_press)
        btn.bind("<ButtonRelease-1>", on_release)

        return btn

    def adjust_points(self, delta):
        new_val = self.points_var.get() + delta
        if 1 <= new_val <= 100:
            self.points_var.set(new_val)

    def toggle_deadline_type(self):
        if self.deadline_type.get() == "schedule":
            self.timer_frame.pack_forget()
            self.schedule_frame.pack(fill=tk.X)
        else:
            self.schedule_frame.pack_forget()
            self.timer_frame.pack(fill=tk.X)

    def add_task(self):
        name = self.task_entry.get().strip()
        if not name:
            self.shake_window()
            return

        points = self.points_var.get()
        is_timer = self.deadline_type.get() == "timer"

        if is_timer:
            hours = self.timer_hours.var.get()
            minutes = self.timer_minutes.var.get()
            seconds = self.timer_seconds.var.get()

            total_seconds = hours * 3600 + minutes * 60 + seconds

            if total_seconds <= 0:
                self.shake_window()
                return

            deadline = datetime.now() + timedelta(seconds=total_seconds)
        else:
            date_str = self.calendar.get()
            hour = self.schedule_hour.var.get()
            minute = self.schedule_minute.var.get()

            try:
                parts = date_str.split("-")
                year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                deadline = datetime(year, month, day, hour, minute, 0)
            except:
                self.shake_window()
                return

            if deadline < datetime.now():
                self.shake_window()
                return

        # Create subtasks list with IDs
        subtasks_data = []
        for i, subtask_name in enumerate(self.subtasks):
            subtasks_data.append({
                'id': i + 1,
                'name': subtask_name,
                'completed': False
            })

        task = {
            'id': int(datetime.now().timestamp() * 1000),
            'name': name,
            'deadline': deadline.strftime('%Y-%m-%d %H:%M:%S'),
            'points': points,
            'status': 'pending',
            'is_timer': is_timer,
            'created': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'subtasks': subtasks_data
        }

        self.on_add_task(task)
        self.destroy()

    def cancel(self):
        """Cancel and close the popup"""
        self.destroy()

    def shake_window(self):
        x = self.winfo_x()
        y = self.winfo_y()

        for i in range(4):
            self.geometry(f"+{x + 10}+{y}")
            self.update()
            time.sleep(0.03)
            self.geometry(f"+{x - 10}+{y}")
            self.update()
            time.sleep(0.03)

        self.geometry(f"+{x}+{y}")


class NotebookButton(tk.Canvas):
    """Button with black outline"""

    def __init__(self, parent, text, command=None, width=150, height=45,
                 bg_color="#D4694A", hover_color="#C55A3B",
                 text_color="#FFFFFF", font_family="Impact",
                 font_size=13, **kwargs):

        self.paper_color = parent.cget("bg") if hasattr(parent, 'cget') else "#F5ECD7"

        super().__init__(parent, width=width + 12, height=height + 12,
                         highlightthickness=0, bg=self.paper_color, **kwargs)

        self.command = command
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.text = text.upper()
        self.font = (font_family, font_size, "bold")
        self.btn_width = width
        self.btn_height = height
        self.pressed = False

        self.draw_button(self.bg_color, False)

        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
        self.bind("<ButtonRelease-1>", self.on_release)

    def draw_button(self, color, pressed=False):
        self.delete("all")

        w = self.btn_width
        h = self.btn_height
        offset = 4 if pressed else 0

        if not pressed:
            self.create_rectangle(8, 8, w + 8, h + 8, fill="#3D3020", outline="")

        self.create_rectangle(offset + 2, offset + 2, w + offset + 2, h + offset + 2,
                              fill=color, outline="#1a1a1a", width=3)

        cx = w / 2 + offset + 2
        cy = h / 2 + offset + 2

        self.create_text(cx + 2, cy + 2, text=self.text, fill="#1a1a1a", font=self.font)
        self.create_text(cx, cy, text=self.text, fill=self.text_color, font=self.font)

    def on_enter(self, event):
        self.draw_button(self.hover_color, False)
        self.config(cursor="hand2")

    def on_leave(self, event):
        self.draw_button(self.bg_color, False)
        self.pressed = False

    def on_click(self, event):
        self.pressed = True
        self.draw_button(self.hover_color, True)

    def on_release(self, event):
        if self.pressed:
            self.draw_button(self.bg_color, False)
            if self.command:
                self.command()
        self.pressed = False


class StickyNote(tk.Canvas):
    """Sticky note stat card"""

    def __init__(self, parent, icon, label, value="0",
                 note_color="#F0E68C", width=130, height=110, **kwargs):
        self.paper_color = parent.cget("bg") if hasattr(parent, 'cget') else "#F5ECD7"

        super().__init__(parent, width=width + 15, height=height + 15,
                         highlightthickness=0, bg=self.paper_color, **kwargs)

        self.icon = icon
        self.label = label.upper()
        self.value = str(value)
        self.note_color = note_color
        self.note_width = width
        self.note_height = height

        self.draw_note()

    def draw_note(self):
        self.delete("all")

        w = self.note_width
        h = self.note_height

        self.create_polygon(10, 12, w + 8, 14, w + 12, h + 10, 8, h + 8,
                            fill="#5D4D3D", outline="")

        self.create_polygon(w - 18, h - 2, w, h - 22, w + 5, h + 3,
                            fill="#4D3D2D", outline="")

        self.create_polygon(2, 3, w - 2, 0, w, h - 22, w - 22, h, 0, h - 2,
                            fill=self.note_color, outline="#1a1a1a", width=2)

        corner_dark = self.adjust_color(self.note_color, -35)
        self.create_polygon(w - 22, h, w, h - 22, w - 2, h - 2,
                            fill=corner_dark, outline="#1a1a1a", width=1)

        self.create_oval(w / 2 - 8, -2, w / 2 + 8, 14, fill="#CC4444",
                         outline="#1a1a1a", width=2)
        self.create_oval(w / 2 - 4, 2, w / 2 + 4, 10, fill="#FF6666", outline="")

        self.create_text(w / 2, 38, text=self.icon, font=("Segoe UI Emoji", 20))

        self.create_text(w / 2 + 2, 66, text=self.value,
                         font=("Impact", 24, "bold"), fill="#5D4D3D")
        self.create_text(w / 2, 64, text=self.value,
                         font=("Impact", 24, "bold"), fill="#2D2015")

        self.create_text(w / 2, 90, text=self.label,
                         font=("Arial Black", 7), fill="#4D3D2D")

    def adjust_color(self, hex_color, amount):
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
        r = max(0, min(255, r + amount))
        g = max(0, min(255, g + amount))
        b = max(0, min(255, b + amount))
        return f"#{r:02x}{g:02x}{b:02x}"

    def set_value(self, value):
        self.value = str(value)
        self.draw_note()


class TaskItem(tk.Frame):
    """Task item display with subtasks"""

    def __init__(self, parent, task, on_complete, on_remove, on_toggle_subtask, colors, **kwargs):
        super().__init__(parent, bg=colors['paper_light'], **kwargs)

        self.task = task
        self.colors = colors
        self.on_complete = on_complete
        self.on_remove = on_remove
        self.on_toggle_subtask = on_toggle_subtask
        self.time_label = None
        self.time_frame = None
        self.subtasks_expanded = False
        self.subtasks_frame = None

        self.create_item()

    def create_item(self):
        container = tk.Frame(self, bg=self.colors['paper_light'])
        container.pack(fill=tk.X, padx=(60, 20), pady=10)

        top_row = tk.Frame(container, bg=self.colors['paper_light'])
        top_row.pack(fill=tk.X)

        # Checkbox
        checkbox = tk.Canvas(top_row, width=30, height=30,
                             bg=self.colors['paper_light'], highlightthickness=0)
        checkbox.pack(side=tk.LEFT, padx=(0, 12))

        checkbox.create_rectangle(3, 3, 27, 27, fill="#FFFEF5",
                                  outline="#1a1a1a", width=2)

        if self.task['status'] == 'failed':
            checkbox.create_line(7, 7, 23, 23, fill="#B83030", width=3)
            checkbox.create_line(23, 7, 7, 23, fill="#B83030", width=3)
        else:
            checkbox.config(cursor="hand2")
            checkbox.bind("<Button-1>", lambda e: self.on_complete(self.task))

        # Task name and expand button
        name_frame = tk.Frame(top_row, bg=self.colors['paper_light'])
        name_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        if self.task['status'] == 'failed':
            name_color = "#A85050"
            name_font = ("Comic Sans MS", 14, "bold")
        else:
            name_color = "#2D2015"
            name_font = ("Comic Sans MS", 14, "bold")

        name_label = tk.Label(name_frame, text=self.task['name'],
                              font=name_font,
                              bg=self.colors['paper_light'], fg=name_color,
                              anchor="w")
        name_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Subtask indicator and expand button
        subtasks = self.task.get('subtasks', [])
        if subtasks:
            completed = sum(1 for s in subtasks if s.get('completed'))
            total = len(subtasks)

            # Progress color
            if completed == total:
                progress_color = "#4A8B4A"
            elif completed > 0:
                progress_color = "#B86000"
            else:
                progress_color = "#6D5D4D"

            # Expand/collapse button with progress
            self.expand_btn = tk.Canvas(name_frame, width=80, height=24,
                                        bg=self.colors['paper_light'],
                                        highlightthickness=0, cursor="hand2")
            self.expand_btn.pack(side=tk.LEFT, padx=(10, 0))

            self.expand_btn.create_rectangle(2, 2, 78, 22,
                                             fill="#F5ECD7", outline="#1a1a1a", width=1)
            self.expand_btn.create_text(40, 12, text=f"📋 {completed}/{total}",
                                        font=("Comic Sans MS", 9, "bold"),
                                        fill=progress_color)

            self.expand_btn.bind("<Button-1>", self.toggle_subtasks)

        # Timer badge
        if self.task.get('is_timer'):
            timer_frame = tk.Frame(top_row, bg="#1a1a1a", padx=1, pady=1)
            timer_frame.pack(side=tk.LEFT, padx=(10, 0))

            timer_badge = tk.Label(timer_frame, text="⏱️ TIMER",
                                   font=("Arial Black", 8),
                                   bg="#FFD700", fg="#2D2015",
                                   padx=6, pady=2)
            timer_badge.pack()

        # Action buttons
        if self.task['status'] == 'pending':
            btn_frame = tk.Frame(top_row, bg=self.colors['paper_light'])
            btn_frame.pack(side=tk.RIGHT)

            complete_btn = tk.Canvas(btn_frame, width=38, height=38,
                                     bg=self.colors['paper_light'],
                                     highlightthickness=0, cursor="hand2")
            complete_btn.pack(side=tk.LEFT, padx=(0, 8))
            complete_btn.create_oval(2, 2, 36, 36, fill="#4A8B4A",
                                     outline="#1a1a1a", width=2)
            complete_btn.create_text(19, 19, text="✓", font=("Arial", 18, "bold"),
                                     fill="#FFFFFF")
            complete_btn.bind("<Button-1>", lambda e: self.on_complete(self.task))

            remove_btn = tk.Canvas(btn_frame, width=38, height=38,
                                   bg=self.colors['paper_light'],
                                   highlightthickness=0, cursor="hand2")
            remove_btn.pack(side=tk.LEFT)
            remove_btn.create_oval(2, 2, 36, 36, fill="#B85050",
                                   outline="#1a1a1a", width=2)
            remove_btn.create_text(19, 19, text="✕", font=("Arial", 16, "bold"),
                                   fill="#FFFFFF")
            remove_btn.bind("<Button-1>", lambda e: self.on_remove(self.task))

        # Info row
        info_row = tk.Frame(container, bg=self.colors['paper_light'])
        info_row.pack(fill=tk.X, pady=(6, 0), padx=(42, 0))

        deadline_label = tk.Label(info_row,
                                  text=f"📅 {self.task['deadline'][:16]}",
                                  font=("Comic Sans MS", 10),
                                  bg=self.colors['paper_light'], fg="#6D5D4D")
        deadline_label.pack(side=tk.LEFT, padx=(0, 20))

        # Time frame
        self.time_frame = tk.Frame(info_row, highlightthickness=1, highlightbackground="#1a1a1a")
        self.time_frame.pack(side=tk.LEFT, padx=(0, 20))

        self.time_label = tk.Label(self.time_frame, text="",
                                   font=("Comic Sans MS", 10, "bold"),
                                   padx=5, pady=2)
        self.time_label.pack()

        self.update_time_display()

        points_label = tk.Label(info_row,
                                text=f"★ +{self.task['points']} PTS",
                                font=("Comic Sans MS", 10, "bold"),
                                bg=self.colors['paper_light'], fg="#B8860B")
        points_label.pack(side=tk.LEFT)

        # Subtasks container (initially hidden)
        self.subtasks_container = tk.Frame(container, bg=self.colors['paper_light'])
        self.subtasks_container.pack(fill=tk.X, pady=(5, 0), padx=(42, 0))

    def toggle_subtasks(self, event=None):
        """Toggle subtasks visibility"""
        self.subtasks_expanded = not self.subtasks_expanded

        if self.subtasks_expanded:
            self.show_subtasks()
        else:
            self.hide_subtasks()

    def show_subtasks(self):
        """Show subtasks list"""
        if self.subtasks_frame:
            self.subtasks_frame.destroy()

        self.subtasks_frame = tk.Frame(self.subtasks_container, bg="#F5ECD7",
                                       highlightthickness=2, highlightbackground="#C9BDAA")
        self.subtasks_frame.pack(fill=tk.X, pady=(5, 0))

        # Header
        header = tk.Frame(self.subtasks_frame, bg="#E0D4BC")
        header.pack(fill=tk.X)

        tk.Label(header, text="📝 Steps to Complete:",
                 font=("Comic Sans MS", 10, "bold"),
                 bg="#E0D4BC", fg="#5D4D3D",
                 padx=10, pady=5).pack(side=tk.LEFT)

        # Collapse button
        collapse_btn = tk.Label(header, text="▲",
                                font=("Arial", 10, "bold"),
                                bg="#E0D4BC", fg="#6D5D4D",
                                padx=10, cursor="hand2")
        collapse_btn.pack(side=tk.RIGHT)
        collapse_btn.bind("<Button-1>", self.toggle_subtasks)

        # Subtasks list
        subtasks = self.task.get('subtasks', [])
        for subtask in subtasks:
            self.create_subtask_row(subtask)

    def create_subtask_row(self, subtask):
        """Create a subtask row"""
        row = tk.Frame(self.subtasks_frame, bg="#F5ECD7")
        row.pack(fill=tk.X, padx=10, pady=3)

        # Checkbox
        checkbox = tk.Canvas(row, width=22, height=22,
                             bg="#F5ECD7", highlightthickness=0,
                             cursor="hand2" if self.task['status'] == 'pending' else "")
        checkbox.pack(side=tk.LEFT, padx=(0, 8))

        checkbox.create_rectangle(2, 2, 20, 20, fill="#FFFEF5",
                                  outline="#1a1a1a", width=1)

        if subtask.get('completed'):
            checkbox.create_line(5, 11, 9, 16, fill="#4A8B4A", width=2)
            checkbox.create_line(9, 16, 17, 6, fill="#4A8B4A", width=2)
            name_color = "#8D7D6D"
            name_font = ("Comic Sans MS", 10, "overstrike")
        else:
            name_color = "#2D2015"
            name_font = ("Comic Sans MS", 10)

        if self.task['status'] == 'pending':
            checkbox.bind("<Button-1>", lambda e, s=subtask: self.toggle_subtask(s))

        # Subtask name
        name_label = tk.Label(row, text=subtask['name'],
                              font=name_font,
                              bg="#F5ECD7", fg=name_color,
                              anchor="w")
        name_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def toggle_subtask(self, subtask):
        """Toggle subtask completion"""
        self.on_toggle_subtask(self.task, subtask)

    def hide_subtasks(self):
        """Hide subtasks list"""
        if self.subtasks_frame:
            self.subtasks_frame.destroy()
            self.subtasks_frame = None

    def update_time_display(self):
        """Update only the time display"""
        if not self.time_label or not self.time_label.winfo_exists():
            return

        deadline = datetime.strptime(self.task['deadline'], '%Y-%m-%d %H:%M:%S')
        time_left = self.get_time_left(deadline)

        if "OVERDUE" in time_left:
            time_color = "#A83030"
            time_bg = "#FFDDDD"
        elif ("M LEFT" in time_left and "H" not in time_left) or "S LEFT" in time_left:
            time_color = "#B86000"
            time_bg = "#FFF0DD"
        else:
            time_color = "#2D6B2D"
            time_bg = "#DDFFDD"

        self.time_label.config(text=f"⏰ {time_left}", fg=time_color, bg=time_bg)
        self.time_frame.config(bg=time_bg)

    def get_time_left(self, deadline):
        now = datetime.now()
        if deadline < now:
            return "OVERDUE!"

        diff = deadline - now
        days = diff.days
        hours, remainder = divmod(diff.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        if days > 0:
            return f"{days}D {hours}H LEFT"
        elif hours > 0:
            return f"{hours}H {minutes}M LEFT"
        elif minutes > 0:
            return f"{minutes}M {seconds}S LEFT"
        else:
            return f"{seconds}S LEFT"


class ScrollableNotebook(tk.Frame):
    """Scrollable area with notebook lines"""

    def __init__(self, parent, **kwargs):
        self.paper_color = "#F5ECD7"
        self.line_color = "#C9BDAA"

        super().__init__(parent, bg=self.paper_color)

        self.canvas = tk.Canvas(self, bg=self.paper_color, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)

        self.scrollable_frame = tk.Frame(self.canvas, bg=self.paper_color)

        self.scrollable_frame.bind("<Configure>", lambda e: self.update_scroll_region())

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind("<Configure>", self.on_configure)

        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)
        self.scrollable_frame.bind("<Enter>", self._bind_mousewheel)
        self.scrollable_frame.bind("<Leave>", self._unbind_mousewheel)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _bind_mousewheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel_linux)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel_linux)

    def _unbind_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_mousewheel_linux(self, event):
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")

    def update_scroll_region(self):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.draw_lines()

    def on_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)
        self.draw_lines()

    def draw_lines(self):
        self.canvas.delete("bg_lines")
        width = self.canvas.winfo_width()
        height = max(self.canvas.winfo_height(), self.scrollable_frame.winfo_reqheight() + 200)
        for y in range(30, height, 30):
            self.canvas.create_line(0, y, width, y, fill=self.line_color, width=1, tags="bg_lines")
        self.canvas.tag_lower("bg_lines")

    def get_frame(self):
        return self.scrollable_frame

    def scroll_to_top(self):
        self.canvas.yview_moveto(0)


class NoiseApp:
    """Main Application"""

    DATA_FILE = "noise_data.json"
    APP_NAME = "Noise Task Manager"

    POINTS_COMPLETE = 10
    POINTS_INCOMPLETE = -5
    POINTS_EARLY_BONUS = 5

    ALERT_THRESHOLDS = [300, 60, 30]

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("NOISE - TASK NOTEBOOK")
        self.root.geometry("1050x850")
        self.root.minsize(800, 600)

        self.colors = {
            'paper': '#E0D4BC',
            'paper_light': '#F5ECD7',
            'lines': '#C9BDAA',
            'margin': '#CC7777',
            'text': '#2D2015',
            'text_light': '#6D5D4D',
            'accent': '#D4694A',
            'success': '#4A8B4A',
            'danger': '#B85050',
            'warning': '#C4982A',
            'sticky_yellow': '#F0E68C',
            'sticky_pink': '#EBBCB0',
            'sticky_green': '#C0DCAC',
            'sticky_blue': '#B0C4DC'
        }

        self.root.configure(bg=self.colors['paper'])

        self.tasks = []
        self.total_points = 0
        self.completed_tasks = 0
        self.failed_tasks = 0

        self.timer_update_id = None
        self.popup = None
        self.task_widgets = []

        self.widget = None
        self.widget_var = None
        self.alerted_tasks = {}

        self.load_data()
        self.setup_ui()

        self.running = True
        self.checker_thread = threading.Thread(target=self.deadline_checker, daemon=True)
        self.checker_thread.start()

        self.start_timer_updates()

        self.root.bind("<Configure>", self.on_window_resize)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_window_resize(self, event):
        if event.widget == self.root:
            self.notebook_bg.draw_notebook()

    def setup_ui(self):
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self.notebook_bg = NotebookBackground(self.root)
        self.notebook_bg.grid(row=0, column=0, sticky="nsew")

        self.main_frame = tk.Frame(self.notebook_bg, bg=self.colors['paper_light'])
        self.main_frame.place(relx=0.08, rely=0.03, relwidth=0.88, relheight=0.94)

        self.main_frame.grid_rowconfigure(3, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.setup_header()
        self.setup_stats_grid()
        self.setup_add_task_button()
        self.setup_task_list()
        self.setup_footer()

        self.refresh_task_list()

    def setup_header(self):
        header = tk.Frame(self.main_frame, bg=self.colors['paper_light'])
        header.grid(row=0, column=0, sticky="ew", pady=(10, 15), padx=(40, 15))
        header.grid_columnconfigure(0, weight=1)

        title_frame = tk.Frame(header, bg=self.colors['paper_light'])
        title_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        title_canvas = tk.Canvas(title_frame, width=400, height=75,
                                 bg=self.colors['paper_light'], highlightthickness=0)
        title_canvas.pack(anchor="w")

        title_canvas.create_line(5, 62, 380, 62, fill=self.colors['accent'], width=4)
        title_canvas.create_line(10, 67, 375, 67, fill=self.colors['accent'], width=2)

        title_canvas.create_text(6, 6, text="📓 NOISE", anchor="nw",
                                 font=("Impact", 42, "bold"), fill="#C4B8A0")
        title_canvas.create_text(4, 4, text="📓 NOISE", anchor="nw",
                                 font=("Impact", 42, "bold"), fill=self.colors['accent'])

        subtitle_canvas = tk.Canvas(title_frame, width=350, height=25,
                                    bg=self.colors['paper_light'], highlightthickness=0)
        subtitle_canvas.pack(anchor="w")

        subtitle_canvas.create_text(0, 0, text="~ my personal task notebook ~", anchor="nw",
                                    font=("Comic Sans MS", 12, "italic"),
                                    fill=self.colors['text_light'])

        btn_container = tk.Frame(header, bg=self.colors['paper_light'])
        btn_container.pack(side=tk.RIGHT)

        NotebookButton(btn_container, "⏱️ WIDGET",
                       command=self.toggle_widget,
                       width=110, height=42,
                       bg_color=self.colors['sticky_yellow'],
                       hover_color="#E0D68C",
                       font_size=11).pack(side=tk.LEFT, padx=(0, 10), pady=10)

        NotebookButton(btn_container, "⚙ SETTINGS",
                       command=self.show_settings,
                       width=125, height=42,
                       bg_color=self.colors['sticky_blue'],
                       hover_color="#98B0C8",
                       font_size=11).pack(side=tk.LEFT, pady=10)

    def setup_stats_grid(self):
        stats_frame = tk.Frame(self.main_frame, bg=self.colors['paper_light'])
        stats_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15), padx=(40, 15))

        inner = tk.Frame(stats_frame, bg=self.colors['paper_light'])
        inner.pack()

        stats_data = [
            ("🏆", "POINTS", self.colors['sticky_yellow']),
            ("✅", "DONE", self.colors['sticky_green']),
            ("📝", "TODO", self.colors['sticky_blue']),
            ("❌", "MISSED", self.colors['sticky_pink'])
        ]

        self.stat_notes = {}

        for icon, label, color in stats_data:
            note = StickyNote(inner, icon, label, "0",
                              note_color=color, width=125, height=105)
            note.pack(side=tk.LEFT, padx=12)
            self.stat_notes[label.lower()] = note

    def setup_add_task_button(self):
        btn_frame = tk.Frame(self.main_frame, bg=self.colors['paper_light'])
        btn_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10), padx=(40, 15))

        self.add_btn = AddTaskButton(btn_frame, command=self.show_add_popup)
        self.add_btn.pack(side=tk.LEFT)

        hint_label = tk.Label(btn_frame, text="← Click to add a new task",
                              font=("Comic Sans MS", 10, "italic"),
                              bg=self.colors['paper_light'],
                              fg=self.colors['text_light'])
        hint_label.pack(side=tk.LEFT, padx=(15, 0))

    def setup_task_list(self):
        list_frame = tk.Frame(self.main_frame, bg=self.colors['paper_light'])
        list_frame.grid(row=3, column=0, sticky="nsew", padx=(0, 15))
        list_frame.grid_rowconfigure(1, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        header = tk.Frame(list_frame, bg=self.colors['paper_light'])
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10), padx=(40, 0))

        title_canvas = tk.Canvas(header, width=200, height=32,
                                 bg=self.colors['paper_light'], highlightthickness=0)
        title_canvas.pack(side=tk.LEFT)

        title_canvas.create_polygon(0, 14, 185, 12, 187, 30, 2, 32,
                                    fill="#B8E0F0", outline="")
        title_canvas.create_text(1, 1, text="📋 MY TASKS", anchor="nw",
                                 font=("Impact", 18), fill="#A09080")
        title_canvas.create_text(0, 0, text="📋 MY TASKS", anchor="nw",
                                 font=("Impact", 18), fill=self.colors['text'])

        filter_frame = tk.Frame(header, bg=self.colors['paper_light'])
        filter_frame.pack(side=tk.RIGHT)

        self.filter_var = tk.StringVar(value="all")

        tab_colors = {
            "all": "#F0E68C",
            "pending": "#B0C4DC",
            "failed": "#EBBCB0"
        }

        filters = [("ALL", "all"), ("TODO", "pending"), ("MISSED", "failed")]

        for text, value in filters:
            bg = tab_colors[value]

            btn_frame_inner = tk.Frame(filter_frame, bg="#1a1a1a", padx=2, pady=2)
            btn_frame_inner.pack(side=tk.LEFT, padx=2)

            btn = tk.Radiobutton(btn_frame_inner, text=text,
                                 variable=self.filter_var, value=value,
                                 command=self.refresh_task_list,
                                 font=("Comic Sans MS", 10, "bold"),
                                 bg=bg, fg="#2D2015",
                                 selectcolor=bg,
                                 activebackground=bg,
                                 indicatoron=0, padx=12, pady=5,
                                 cursor="hand2", relief=tk.FLAT,
                                 highlightthickness=0)
            btn.pack()

        self.scroll_area = ScrollableNotebook(list_frame)
        self.scroll_area.grid(row=1, column=0, sticky="nsew")

        self.scrollable_frame = self.scroll_area.get_frame()

    def setup_footer(self):
        footer = tk.Frame(self.main_frame, bg=self.colors['paper_light'])
        footer.grid(row=4, column=0, sticky="ew", pady=(10, 5), padx=(40, 15))

        self.startup_var = tk.BooleanVar(value=self.check_startup())
        self.widget_var = tk.BooleanVar(value=False)

        startup_check = tk.Checkbutton(footer, text="🚀 Start with Windows",
                                       variable=self.startup_var,
                                       command=self.toggle_startup,
                                       font=("Comic Sans MS", 10, "bold"),
                                       bg=self.colors['paper_light'],
                                       fg=self.colors['text'],
                                       selectcolor=self.colors['sticky_yellow'],
                                       activebackground=self.colors['paper_light'],
                                       cursor="hand2")
        startup_check.pack(side=tk.LEFT)

        widget_check = tk.Checkbutton(footer, text="📌 Show Widget",
                                      variable=self.widget_var,
                                      command=self.toggle_widget,
                                      font=("Comic Sans MS", 10, "bold"),
                                      bg=self.colors['paper_light'],
                                      fg=self.colors['text'],
                                      selectcolor=self.colors['sticky_yellow'],
                                      activebackground=self.colors['paper_light'],
                                      cursor="hand2")
        widget_check.pack(side=tk.LEFT, padx=(20, 0))

        tk.Label(footer, text="- page v1.1 -",
                 font=("Comic Sans MS", 10, "italic"),
                 bg=self.colors['paper_light'],
                 fg=self.colors['text_light']).pack(side=tk.RIGHT)

    def toggle_widget(self):
        if self.widget and self.widget.winfo_exists():
            self.widget.close_widget()
        else:
            self.widget = DesktopWidget(self.root, self)
            self.widget_var.set(True)

    def show_add_popup(self):
        if self.popup and self.popup.winfo_exists():
            self.popup.destroy()

        self.popup = StickyNotePopup(self.root, self.add_task_from_popup, self.colors)

    def add_task_from_popup(self, task):
        self.tasks.append(task)
        self.save_data()
        self.refresh_task_list()
        self.play_sound('add')
        self.show_notification(f"Added: {task['name']}", "success")

    def toggle_subtask(self, task, subtask):
        """Toggle subtask completion status"""
        subtask['completed'] = not subtask['completed']
        self.save_data()
        self.refresh_task_list()

        # Play a small sound
        if subtask['completed']:
            self.play_sound('add')

    def complete_task(self, task):
        if task['status'] != 'pending':
            return

        # Check if there are incomplete subtasks
        subtasks = task.get('subtasks', [])
        incomplete = [s for s in subtasks if not s.get('completed')]

        if incomplete:
            # Ask for confirmation
            if not messagebox.askyesno("Incomplete Steps",
                                       f"This task has {len(incomplete)} incomplete step(s).\n\nComplete task anyway?"):
                return

        task['status'] = 'completed'

        deadline = datetime.strptime(task['deadline'], '%Y-%m-%d %H:%M:%S')
        points = task['points']

        # Bonus for completing all subtasks
        if subtasks and all(s.get('completed') for s in subtasks):
            points += 2  # Extra bonus for completing all steps
            bonus = f" (+2 all steps bonus!)"
        elif datetime.now() < deadline - timedelta(hours=1):
            points += self.POINTS_EARLY_BONUS
            bonus = f" (+{self.POINTS_EARLY_BONUS} early bonus!)"
        else:
            bonus = ""

        self.total_points += points
        self.completed_tasks += 1

        if task['id'] in self.alerted_tasks:
            del self.alerted_tasks[task['id']]

        self.save_data()
        self.refresh_task_list()
        self.update_stats()
        self.play_sound('complete')

        self.show_notification(f"Done! +{points} ★{bonus}", "success")

    def remove_task(self, task):
        if task['id'] in self.alerted_tasks:
            del self.alerted_tasks[task['id']]

        self.tasks = [t for t in self.tasks if t['id'] != task['id']]
        self.save_data()
        self.refresh_task_list()
        self.play_sound('remove')
        self.show_notification("Erased!", "info")

    def refresh_task_list(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        self.task_widgets = []

        filter_value = self.filter_var.get()

        active_tasks = [t for t in self.tasks if t['status'] != 'completed']

        if filter_value == "all":
            filtered = active_tasks
        elif filter_value == "pending":
            filtered = [t for t in active_tasks if t['status'] == 'pending']
        elif filter_value == "failed":
            filtered = [t for t in active_tasks if t['status'] == 'failed']
        else:
            filtered = active_tasks

        sorted_tasks = sorted(filtered,
                              key=lambda x: (x['status'] != 'pending', x['deadline']))

        if not sorted_tasks:
            empty_frame = tk.Frame(self.scrollable_frame, bg=self.colors['paper_light'])
            empty_frame.pack(fill=tk.BOTH, expand=True, pady=40)

            empty_canvas = tk.Canvas(empty_frame, width=400, height=150,
                                     bg=self.colors['paper_light'], highlightthickness=0)
            empty_canvas.pack()

            for y in range(30, 150, 30):
                empty_canvas.create_line(0, y, 400, y, fill=self.colors['lines'])

            empty_canvas.create_text(200, 45, text="📝",
                                     font=("Segoe UI Emoji", 40))
            empty_canvas.create_text(200, 100, text="Nothing here yet...",
                                     font=("Comic Sans MS", 16, "bold italic"),
                                     fill=self.colors['text_light'])
            empty_canvas.create_text(200, 130, text="Click 'Add Task' to get started!",
                                     font=("Comic Sans MS", 11, "italic"),
                                     fill="#A09080")
        else:
            for task in sorted_tasks:
                item = TaskItem(self.scrollable_frame, task,
                                self.complete_task, self.remove_task,
                                self.toggle_subtask, self.colors)
                item.pack(fill=tk.X, pady=0)

                if task['status'] == 'pending':
                    self.task_widgets.append(item)

                sep = tk.Canvas(self.scrollable_frame, height=2,
                                bg=self.colors['paper_light'], highlightthickness=0)
                sep.pack(fill=tk.X, padx=(60, 20))
                sep.create_line(0, 1, 2000, 1, fill=self.colors['lines'],
                                dash=(6, 4))

        self.scrollable_frame.update_idletasks()
        self.scroll_area.draw_lines()
        self.update_stats()
        self.scroll_area.scroll_to_top()

    def start_timer_updates(self):
        self.update_time_labels()

    def update_time_labels(self):
        if self.running:
            for widget in self.task_widgets:
                try:
                    if widget.winfo_exists():
                        widget.update_time_display()
                except:
                    pass

            self.timer_update_id = self.root.after(1000, self.update_time_labels)

    def update_stats(self):
        pending = len([t for t in self.tasks if t['status'] == 'pending'])

        self.stat_notes['points'].set_value(self.total_points)
        self.stat_notes['done'].set_value(self.completed_tasks)
        self.stat_notes['todo'].set_value(pending)
        self.stat_notes['missed'].set_value(self.failed_tasks)

    def check_timer_alerts(self):
        now = datetime.now()

        for task in self.tasks:
            if task['status'] != 'pending' or not task.get('is_timer'):
                continue

            deadline = datetime.strptime(task['deadline'], '%Y-%m-%d %H:%M:%S')
            diff = deadline - now

            if diff.total_seconds() <= 0:
                continue

            total_seconds = int(diff.total_seconds())
            task_id = task['id']

            if task_id not in self.alerted_tasks:
                self.alerted_tasks[task_id] = set()

            for threshold in self.ALERT_THRESHOLDS:
                if total_seconds <= threshold and threshold not in self.alerted_tasks[task_id]:
                    self.alerted_tasks[task_id].add(threshold)

                    if threshold >= 60:
                        time_str = f"{threshold // 60} minute{'s' if threshold >= 120 else ''}"
                    else:
                        time_str = f"{threshold} seconds"

                    self.root.after(0, lambda t=task, ts=time_str: self.show_timer_alert(t, ts))
                    break

    def show_timer_alert(self, task, time_left):
        self.play_sound('fail')

        self.root.deiconify()
        self.root.lift()
        self.root.attributes("-topmost", True)
        self.root.after(100, lambda: self.root.attributes("-topmost", False))

        alert = TimerAlertPopup(self.root, self, task, time_left)

    def deadline_checker(self):
        while self.running:
            try:
                now = datetime.now()
                failed = False

                for task in self.tasks:
                    if task['status'] == 'pending':
                        deadline = datetime.strptime(task['deadline'], '%Y-%m-%d %H:%M:%S')

                        if deadline < now:
                            task['status'] = 'failed'
                            self.total_points += self.POINTS_INCOMPLETE
                            self.failed_tasks += 1

                            if task['id'] in self.alerted_tasks:
                                del self.alerted_tasks[task['id']]

                            failed = True

                if failed:
                    self.save_data()
                    self.root.after(0, self.refresh_task_list)
                    self.root.after(0, lambda: self.show_notification(
                        "Oops! Time's up!", "danger"))
                    self.play_sound('fail')

                self.check_timer_alerts()

            except Exception as e:
                print(f"Error: {e}")

            time.sleep(1)

    def show_notification(self, message, type_="info"):
        colors = {
            "success": self.colors['sticky_green'],
            "warning": self.colors['sticky_yellow'],
            "danger": self.colors['sticky_pink'],
            "info": self.colors['sticky_blue']
        }

        notif = tk.Toplevel(self.root)
        notif.overrideredirect(True)
        notif.attributes("-topmost", True)

        x = self.root.winfo_x() + self.root.winfo_width() - 340
        y = self.root.winfo_y() + 100
        notif.geometry(f"320x90+{x}+{y}")

        note_color = colors.get(type_, self.colors['sticky_yellow'])

        note_canvas = tk.Canvas(notif, width=320, height=90,
                                bg=self.colors['paper'], highlightthickness=0)
        note_canvas.pack()

        note_canvas.create_polygon(12, 12, 310, 15, 315, 82, 8, 78,
                                   fill="#5D4D3D", outline="")

        note_canvas.create_polygon(5, 5, 305, 3, 308, 75, 3, 78,
                                   fill=note_color, outline="#1a1a1a", width=2)

        note_canvas.create_oval(150, 0, 170, 16, fill="#CC4444",
                                outline="#1a1a1a", width=2)
        note_canvas.create_oval(155, 4, 165, 12, fill="#FF6666", outline="")

        note_canvas.create_text(157, 47, text=message,
                                font=("Comic Sans MS", 13, "bold"),
                                fill="#2D2015")

        notif.after(3000, notif.destroy)

    def show_settings(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("SETTINGS")
        dialog.geometry("400x450")
        dialog.configure(bg=self.colors['paper_light'])
        dialog.transient(self.root)
        dialog.grab_set()

        dialog.geometry("+%d+%d" % (self.root.winfo_x() + 325,
                                    self.root.winfo_y() + 200))

        bg_canvas = tk.Canvas(dialog, bg=self.colors['paper_light'], highlightthickness=0)
        bg_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)

        for y in range(30, 480, 30):
            bg_canvas.create_line(0, y, 420, y, fill=self.colors['lines'])

        title_canvas = tk.Canvas(dialog, width=240, height=55,
                                 bg=self.colors['paper_light'], highlightthickness=0)
        title_canvas.pack(pady=20)

        title_canvas.create_polygon(20, 28, 220, 26, 222, 48, 22, 50,
                                    fill="#FFEB99", outline="")
        title_canvas.create_text(122, 25, text="⚙️ SETTINGS",
                                 font=("Impact", 26), fill=self.colors['text'])

        btn_frame = tk.Frame(dialog, bg=self.colors['paper_light'])
        btn_frame.pack(fill=tk.X, padx=70)

        NotebookButton(btn_frame, "🧹 CLEAR DONE",
                       command=lambda: [self.clear_completed(), dialog.destroy()],
                       width=175, height=48,
                       bg_color=self.colors['sticky_green'],
                       hover_color="#A8C898",
                       font_size=12).pack(pady=12)

        NotebookButton(btn_frame, "🗑️ ERASE ALL",
                       command=lambda: [self.clear_all_tasks(), dialog.destroy()],
                       width=175, height=48,
                       bg_color=self.colors['danger'],
                       hover_color="#A84040",
                       font_size=12).pack(pady=12)

        NotebookButton(btn_frame, "🔄 RESET STARS",
                       command=lambda: [self.reset_points(), dialog.destroy()],
                       width=175, height=48,
                       bg_color=self.colors['warning'],
                       hover_color="#B48820",
                       font_size=12).pack(pady=12)

        NotebookButton(btn_frame, "CLOSE",
                       command=dialog.destroy,
                       width=120, height=42,
                       bg_color=self.colors['sticky_blue'],
                       hover_color="#98B0C8",
                       font_size=11).pack(pady=25)

    def clear_completed(self):
        self.tasks = [t for t in self.tasks if t['status'] != 'completed']
        self.save_data()
        self.refresh_task_list()
        self.show_notification("Cleaned up!", "success")

    def clear_all_tasks(self):
        if messagebox.askyesno("Wait!", "Erase everything?"):
            self.tasks = []
            self.alerted_tasks = {}
            self.save_data()
            self.refresh_task_list()
            self.show_notification("All erased!", "success")

    def reset_points(self):
        if messagebox.askyesno("Sure?", "Reset all stars?"):
            self.total_points = 0
            self.completed_tasks = 0
            self.failed_tasks = 0
            self.save_data()
            self.update_stats()
            self.show_notification("Stars reset!", "success")

    def play_sound(self, sound_type):
        if not SOUND_AVAILABLE:
            return
        try:
            sounds = {
                'complete': winsound.MB_OK,
                'fail': winsound.MB_ICONHAND,
                'add': winsound.MB_ICONASTERISK,
                'remove': winsound.MB_OK
            }
            winsound.MessageBeep(sounds.get(sound_type, winsound.MB_OK))
        except:
            pass

    def check_startup(self):
        if not WINREG_AVAILABLE:
            return False
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Run",
                                 0, winreg.KEY_READ)
            try:
                winreg.QueryValueEx(key, self.APP_NAME)
                return True
            except:
                return False
            finally:
                winreg.CloseKey(key)
        except:
            return False

    def toggle_startup(self):
        if not WINREG_AVAILABLE:
            self.show_notification("Windows only!", "warning")
            return

        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Run",
                                 0, winreg.KEY_SET_VALUE)

            if self.startup_var.get():
                exe = sys.executable if getattr(sys, 'frozen', False) else sys.argv[0]
                winreg.SetValueEx(key, self.APP_NAME, 0, winreg.REG_SZ, f'"{os.path.abspath(exe)}"')
                self.show_notification("Added to startup!", "success")
            else:
                try:
                    winreg.DeleteValue(key, self.APP_NAME)
                    self.show_notification("Removed!", "info")
                except:
                    pass

            winreg.CloseKey(key)
        except:
            self.show_notification("Error!", "danger")

    def save_data(self):
        data = {
            'tasks': self.tasks,
            'total_points': self.total_points,
            'completed_tasks': self.completed_tasks,
            'failed_tasks': self.failed_tasks
        }
        try:
            with open(self.DATA_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Save error: {e}")

    def load_data(self):
        try:
            if os.path.exists(self.DATA_FILE):
                with open(self.DATA_FILE, 'r') as f:
                    data = json.load(f)
                    self.tasks = data.get('tasks', [])
                    self.total_points = data.get('total_points', 0)
                    self.completed_tasks = data.get('completed_tasks', 0)
                    self.failed_tasks = data.get('failed_tasks', 0)

                    # Ensure all tasks have subtasks field
                    for task in self.tasks:
                        if 'subtasks' not in task:
                            task['subtasks'] = []
        except Exception as e:
            print(f"Load error: {e}")

    def on_closing(self):
        self.running = False
        if self.timer_update_id:
            self.root.after_cancel(self.timer_update_id)
        if self.popup and self.popup.winfo_exists():
            self.popup.destroy()
        if self.widget and self.widget.winfo_exists():
            self.widget.destroy()
        self.save_data()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = NoiseApp()
    app.run()