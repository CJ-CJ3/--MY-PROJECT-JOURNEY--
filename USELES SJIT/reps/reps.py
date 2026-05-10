import tkinter as tk
from tkinter import messagebox, simpledialog
import pygame
import os
import random
import math
import json


SAVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reps_save.json")
FONT = "Gill Sans Ultra Bold"


def load_save():
    default = {"count": 0, "goal": 0, "cookies": 0}
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f:
                data = json.load(f)
            for key in default:
                if key not in data:
                    data[key] = default[key]
            return data
        except (json.JSONDecodeError, IOError):
            return default
    return default


def write_save(count, goal, cookies):
    try:
        with open(SAVE_FILE, "w") as f:
            json.dump({"count": count, "goal": goal, "cookies": cookies}, f, indent=2)
    except IOError:
        pass


class Star:
    def __init__(self, canvas, width, height):
        self.canvas = canvas
        self.x = random.randint(0, width)
        self.y = random.randint(0, height)
        self.base_size = random.uniform(0.5, 2.5)
        self.size = self.base_size
        self.speed = random.uniform(0.02, 0.08)
        self.phase = random.uniform(0, math.pi * 2)
        self.time = 0
        colors = ["#ffffff", "#ffe4c4", "#add8e6", "#fffacd", "#e6e6fa"]
        self.color = random.choice(colors)
        self.id = canvas.create_oval(
            self.x - self.size, self.y - self.size,
            self.x + self.size, self.y + self.size,
            fill=self.color, outline=""
        )

    def twinkle(self):
        self.time += self.speed
        factor = 0.5 + 0.5 * math.sin(self.time + self.phase)
        self.size = self.base_size * (0.3 + 0.7 * factor)
        self.canvas.coords(
            self.id,
            self.x - self.size, self.y - self.size,
            self.x + self.size, self.y + self.size
        )


class Asteroid:
    def __init__(self, canvas, width, height):
        self.canvas = canvas
        self.w = width
        self.h = height
        self.radius = random.uniform(12, 45)
        self.x = random.uniform(-50, width + 50)
        self.y = random.uniform(-50, height + 50)
        self.dx = random.uniform(-0.4, 0.4)
        self.dy = random.uniform(-0.3, 0.3)
        self.angle = random.uniform(0, math.pi * 2)
        self.spin = random.uniform(-0.005, 0.005)
        self.num_points = random.randint(7, 12)
        self.offsets = [random.uniform(0.6, 1.0) for _ in range(self.num_points)]

        base = random.randint(40, 80)
        self.fill = f"#{base:02x}{max(base-10,0):02x}{max(base-15,0):02x}"
        edge = base + 25
        self.outline = f"#{edge:02x}{max(edge-5,0):02x}{max(edge-10,0):02x}"

        self.craters = []
        for _ in range(random.randint(0, 3)):
            cr = random.uniform(0.15, 0.35) * self.radius
            ca = random.uniform(0, math.pi * 2)
            cd = random.uniform(0.2, 0.5) * self.radius
            dark = max(base - 20, 10)
            cc = f"#{dark:02x}{max(dark-5,0):02x}{max(dark-8,0):02x}"
            self.craters.append((cr, ca, cd, cc))

        self.id = canvas.create_polygon(
            self._get_points(),
            fill=self.fill, outline=self.outline, width=1.5
        )
        self.crater_ids = []
        self._draw_craters()

    def _get_points(self):
        points = []
        for i in range(self.num_points):
            a = self.angle + (2 * math.pi * i / self.num_points)
            r = self.radius * self.offsets[i]
            points.extend([self.x + math.cos(a) * r, self.y + math.sin(a) * r])
        return points

    def _draw_craters(self):
        for cid in self.crater_ids:
            self.canvas.delete(cid)
        self.crater_ids = []
        for cr, ca, cd, cc in self.craters:
            cx = self.x + math.cos(self.angle + ca) * cd
            cy = self.y + math.sin(self.angle + ca) * cd
            cid = self.canvas.create_oval(
                cx - cr, cy - cr, cx + cr, cy + cr,
                fill=cc, outline=""
            )
            self.crater_ids.append(cid)

    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.angle += self.spin
        margin = self.radius + 60
        if self.x < -margin:
            self.x = self.w + margin
        elif self.x > self.w + margin:
            self.x = -margin
        if self.y < -margin:
            self.y = self.h + margin
        elif self.y > self.h + margin:
            self.y = -margin
        try:
            self.canvas.coords(self.id, self._get_points())
            self._draw_craters()
        except tk.TclError:
            pass


class ShootingStar:
    def __init__(self, canvas, width, height):
        self.canvas = canvas
        self.width = width
        self.height = height
        self.active = False
        self.trail_ids = []

    def launch(self):
        self.active = True
        self.x = random.randint(0, self.width)
        self.y = random.randint(0, int(self.height * 0.3))
        angle = random.uniform(0.3, 0.8)
        speed = random.uniform(8, 15)
        self.dx = math.cos(angle) * speed
        self.dy = math.sin(angle) * speed
        self.life = random.randint(20, 40)
        self.trail_ids = []

    def update(self):
        if not self.active:
            return
        self.x += self.dx
        self.y += self.dy
        self.life -= 1
        trail = self.canvas.create_line(
            self.x, self.y,
            self.x - self.dx * 2, self.y - self.dy * 2,
            fill="#ffffff", width=1.5
        )
        self.trail_ids.append((trail, 8))
        new = []
        for tid, frames in self.trail_ids:
            frames -= 1
            if frames <= 0:
                self.canvas.delete(tid)
            else:
                v = int(255 * frames / 8)
                try:
                    self.canvas.itemconfig(tid, fill=f"#{v:02x}{v:02x}{v:02x}")
                except tk.TclError:
                    pass
                new.append((tid, frames))
        self.trail_ids = new
        if self.life <= 0 or self.x > self.width or self.y > self.height:
            self.active = False
            for tid, _ in self.trail_ids:
                self.canvas.delete(tid)
            self.trail_ids = []


class CookieExplosion:
    def __init__(self, canvas, x, y):
        self.canvas = canvas
        self.particles = []
        emojis = ["🍪", "⭐", "✨", "🌟", "💫"]
        for _ in range(15):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(3, 10)
            pid = canvas.create_text(
                x, y, text=random.choice(emojis),
                font=(FONT, random.randint(14, 28)),
            )
            self.particles.append({
                "id": pid, "x": x, "y": y,
                "dx": math.cos(angle) * speed,
                "dy": math.sin(angle) * speed,
                "life": random.randint(25, 50)
            })

    def update(self):
        alive = []
        for p in self.particles:
            p["x"] += p["dx"]
            p["y"] += p["dy"]
            p["dy"] += 0.15
            p["dx"] *= 0.98
            p["life"] -= 1
            if p["life"] > 0:
                try:
                    self.canvas.coords(p["id"], p["x"], p["y"])
                except tk.TclError:
                    pass
                alive.append(p)
            else:
                try:
                    self.canvas.delete(p["id"])
                except tk.TclError:
                    pass
        self.particles = alive
        return len(alive) > 0


class RepsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("REPS")
        self.root.geometry("420x680")
        self.root.resizable(False, False)
        self.root.configure(bg="#020208")

        self.W = 420
        self.H = 680

        # Audio
        pygame.mixer.init()
        self.reset_sound = None
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "i-got-this.mp3")
        if os.path.exists(path):
            self.reset_sound = path

        # Load saved state
        save = load_save()
        self.count = save["count"]
        self.goal = save["goal"]
        self.cookies = save["cookies"]
        self.explosions = []
        self.celebrating = False

        self._build_space()
        self._build_ui()
        self._restore_state()
        self._animate()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        write_save(self.count, self.goal, self.cookies)
        pygame.mixer.quit()
        self.root.destroy()

    def _save(self):
        write_save(self.count, self.goal, self.cookies)

    def _build_space(self):
        self.canvas = tk.Canvas(
            self.root, width=self.W, height=self.H,
            bg="#020208", highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        for i in range(self.H):
            r = i / self.H
            red = int(2 + 8 * r)
            grn = int(2 + 4 * r)
            blu = int(8 + 18 * r + 8 * math.sin(r * math.pi))
            self.canvas.create_line(
                0, i, self.W, i,
                fill=f"#{red:02x}{grn:02x}{blu:02x}"
            )

        self.stars = [Star(self.canvas, self.W, self.H) for _ in range(150)]
        self.asteroids = [Asteroid(self.canvas, self.W, self.H) for _ in range(8)]
        self.shooting_star = ShootingStar(self.canvas, self.W, self.H)
        self.shoot_timer = random.randint(80, 250)

    def _build_ui(self):
        cx = self.W // 2

        # Cookie counter — top center
        self.cookie_text = self.canvas.create_text(
            cx, 35,
            text=f"🍪  {self.cookies}",
            font=(FONT, 20),
            fill="#f5a623",
        )

        # Goal indicator — below cookies
        self.goal_text = self.canvas.create_text(
            cx, 75,
            text="",
            font=(FONT, 16),
            fill="#5a5aaa",
        )

        # Glow ring
        self.glow_ring = self.canvas.create_oval(
            cx - 95, 195, cx + 95, 385,
            outline="#e94560", width=1, dash=(2, 4)
        )

        # Counter circle
        self.counter_bg = self.canvas.create_oval(
            cx - 80, 210, cx + 80, 370,
            fill="#08081a", outline="#15153a", width=2
        )

        # Count number
        self.count_text = self.canvas.create_text(
            cx, 280,
            text=str(self.count),
            font=(FONT, 58),
            fill="#ffffff",
        )

        # "click away"
        self.click_away = self.canvas.create_text(
            cx, 350,
            text="click away",
            font=(FONT, 10),
            fill="#6a6a9a",
        )

        # Progress bar
        bw, bh = 240, 10
        bx = cx - bw // 2
        by = 405

        self.canvas.create_rectangle(
            bx, by, bx + bw, by + bh,
            fill="#08081a", outline="#15153a", width=1
        )
        self.progress_fill = self.canvas.create_rectangle(
            bx + 1, by + 1, bx + 1, by + bh - 1,
            fill="#e94560", outline=""
        )
        self.bar_x = bx
        self.bar_y = by
        self.bar_w = bw
        self.bar_h = bh

        self.pct_text = self.canvas.create_text(
            cx, by + bh + 14, text="",
            font=(FONT, 8),
            fill="#4a4a7a",
        )

        # Click button
        self._make_click_btn(cx, 460, 200, 65, "#e94560", "#ff6b81", "💪 CLICK!")

        # Bottom buttons
        bot_y = 570
        sw, sh = 120, 40
        gap = 20

        # Set Goal
        self._rounded_rect(
            cx - sw - gap // 2, bot_y,
            cx - gap // 2, bot_y + sh,
            10, fill="#0f3460", outline="#1a4a8a", width=1, tag="goal_btn"
        )
        self.canvas.create_text(
            cx - sw // 2 - gap // 2, bot_y + sh // 2,
            text="🎯 Goal",
            font=(FONT, 11),
            fill="#ffffff", tags="goal_btn"
        )
        self.canvas.tag_bind("goal_btn", "<Button-1>", lambda e: self.set_goal())
        self.canvas.tag_bind("goal_btn", "<Enter>", lambda e: self.canvas.config(cursor="hand2"))
        self.canvas.tag_bind("goal_btn", "<Leave>", lambda e: self.canvas.config(cursor=""))

        # Reset
        self._rounded_rect(
            cx + gap // 2, bot_y,
            cx + sw + gap // 2, bot_y + sh,
            10, fill="#533483", outline="#7a4abf", width=1, tag="reset_btn"
        )
        self.canvas.create_text(
            cx + sw // 2 + gap // 2, bot_y + sh // 2,
            text="🔄 Reset",
            font=(FONT, 11),
            fill="#ffffff", tags="reset_btn"
        )
        self.canvas.tag_bind("reset_btn", "<Button-1>", lambda e: self.reset())
        self.canvas.tag_bind("reset_btn", "<Enter>", lambda e: self.canvas.config(cursor="hand2"))
        self.canvas.tag_bind("reset_btn", "<Leave>", lambda e: self.canvas.config(cursor=""))

        self._raise_ui()

    def _restore_state(self):
        if self.goal > 0:
            self.canvas.itemconfig(self.goal_text, text=f"🎯  {self.goal}", fill="#e94560")
        self._update_progress()

    def _make_click_btn(self, cx, y, w, h, fill, outline, text):
        self.canvas.delete("click_btn")
        self._rounded_rect(
            cx - w // 2, y, cx + w // 2, y + h,
            16, fill=fill, outline=outline, width=2, tag="click_btn"
        )
        self.canvas.create_text(
            cx, y + h // 2, text=text,
            font=(FONT, 17),
            fill="#ffffff", tags="click_btn"
        )
        self.canvas.tag_bind("click_btn", "<Button-1>", lambda e: self.on_click())
        self.canvas.tag_bind("click_btn", "<Enter>", lambda e: self.canvas.config(cursor="hand2"))
        self.canvas.tag_bind("click_btn", "<Leave>", lambda e: self.canvas.config(cursor=""))

    def _rounded_rect(self, x1, y1, x2, y2, r, **kw):
        tag = kw.pop("tag", "")
        pts = [
            x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
            x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
            x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
        ]
        return self.canvas.create_polygon(pts, smooth=True, tags=tag, **kw)

    def _raise_ui(self):
        for tag in ["click_btn", "goal_btn", "reset_btn"]:
            self.canvas.tag_raise(tag)
        for item in [self.cookie_text, self.goal_text, self.glow_ring,
                      self.counter_bg, self.count_text, self.click_away,
                      self.progress_fill, self.pct_text]:
            self.canvas.tag_raise(item)

    # ── Animation ──
    def _animate(self):
        for s in self.stars:
            s.twinkle()
        for a in self.asteroids:
            a.update()
            self.canvas.tag_raise(a.id)
            for cid in a.crater_ids:
                self.canvas.tag_raise(cid)

        self.shoot_timer -= 1
        if self.shoot_timer <= 0 and not self.shooting_star.active:
            self.shooting_star.launch()
            self.shoot_timer = random.randint(120, 350)
        self.shooting_star.update()

        self.explosions = [e for e in self.explosions if e.update()]
        self._pulse_glow()
        self._raise_ui()
        self.root.after(33, self._animate)

    def _pulse_glow(self):
        t = pygame.time.get_ticks() / 1000.0 if pygame.get_init() else 0
        pulse = 0.5 + 0.5 * math.sin(t * 2)
        w = 1 + int(2 * pulse)

        if self.celebrating:
            color = "#2ecc71"
        elif self.goal > 0:
            color = "#e94560"
        else:
            color = "#2a2a5a"

        try:
            self.canvas.itemconfig(self.glow_ring, outline=color, width=w)
        except tk.TclError:
            pass

    # ── Audio ──
    def play_reset_sound(self):
        if self.reset_sound:
            try:
                pygame.mixer.music.stop()
                pygame.mixer.music.load(self.reset_sound)
                pygame.mixer.music.play()
            except Exception:
                pass

    # ── Auto Reset After Celebration ──
    def _auto_reset(self):
        """Reset count back to 0 after celebration, play audio."""
        self.celebrating = False
        self.count = 0

        # ▶️ Play "i got this" on auto reset
        self.play_reset_sound()

        self.canvas.itemconfig(self.count_text, text="0", fill="#ffffff")
        self.canvas.itemconfig(self.counter_bg, fill="#08081a", outline="#15153a")
        self.canvas.itemconfig(self.click_away, text="click away", fill="#6a6a9a")
        self._update_progress()
        self._save()

    def _flash_celebration(self, flashes_left):
        """Flash the counter green/white to celebrate before auto-reset."""
        if flashes_left <= 0:
            self._auto_reset()
            return

        if flashes_left % 2 == 0:
            self.canvas.itemconfig(self.count_text, fill="#2ecc71")
            self.canvas.itemconfig(self.counter_bg, fill="#0a1a0a", outline="#1a3a1a")
        else:
            self.canvas.itemconfig(self.count_text, fill="#ffffff")
            self.canvas.itemconfig(self.counter_bg, fill="#08081a", outline="#15153a")

        self.root.after(200, lambda: self._flash_celebration(flashes_left - 1))

    # ── Logic ──
    def on_click(self):
        if self.celebrating:
            return

        self.count += 1
        self.canvas.itemconfig(self.count_text, text=str(self.count))
        self._update_progress()
        self._save()

        # Pulse
        cx = self.W // 2
        self.canvas.coords(self.counter_bg, cx - 85, 205, cx + 85, 375)
        self.root.after(80, lambda: self.canvas.coords(
            self.counter_bg, cx - 80, 210, cx + 80, 370))

        # Check goal
        if self.goal > 0 and self.count >= self.goal:
            self.cookies += 1
            self.celebrating = True
            self.canvas.itemconfig(self.cookie_text, text=f"🍪  {self.cookies}")
            self.canvas.itemconfig(self.click_away, text="🍪 cookie earned!", fill="#2ecc71")

            # Explosion
            self.explosions.append(CookieExplosion(self.canvas, cx, 280))
            self._save()

            # Flash 6 times then auto-reset with audio
            self._flash_celebration(6)

    def set_goal(self):
        if self.celebrating:
            return
        goal = simpledialog.askinteger(
            "🎯", "Enter your click goal:",
            minvalue=1, maxvalue=99999, parent=self.root
        )
        if goal is not None:
            self.goal = goal
            self.count = 0
            self.canvas.itemconfig(self.count_text, text="0", fill="#ffffff")
            self.canvas.itemconfig(self.counter_bg, fill="#08081a", outline="#15153a")
            self.canvas.itemconfig(self.goal_text, text=f"🎯  {self.goal}", fill="#e94560")
            self.canvas.itemconfig(self.click_away, text="click away", fill="#6a6a9a")
            self._update_progress()
            self._save()

    def reset(self):
        if self.celebrating:
            return
        self.play_reset_sound()
        self.count = 0
        self.canvas.itemconfig(self.count_text, text="0", fill="#ffffff")
        self.canvas.itemconfig(self.counter_bg, fill="#08081a", outline="#15153a")
        self.canvas.itemconfig(self.click_away, text="click away", fill="#6a6a9a")
        self._update_progress()
        self._save()

    def _update_progress(self):
        if self.goal > 0:
            pct = min(self.count / self.goal, 1.0)
            fw = max(int(self.bar_w * pct), 0)
            self.canvas.coords(
                self.progress_fill,
                self.bar_x + 1, self.bar_y + 1,
                self.bar_x + 1 + fw, self.bar_y + self.bar_h - 1
            )
            color = "#2ecc71" if pct >= 1.0 else "#f5a623" if pct >= 0.75 else "#e94560"
            self.canvas.itemconfig(self.progress_fill, fill=color)
            self.canvas.itemconfig(self.pct_text, text=f"{int(pct * 100)}%", fill=color)
        else:
            self.canvas.coords(
                self.progress_fill,
                self.bar_x + 1, self.bar_y + 1,
                self.bar_x + 1, self.bar_y + self.bar_h - 1
            )
            self.canvas.itemconfig(self.pct_text, text="", fill="#4a4a7a")


if __name__ == "__main__":
    root = tk.Tk()
    RepsApp(root)
    root.mainloop()