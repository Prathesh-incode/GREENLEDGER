"""
╔══════════════════════════════════════════════════════════╗
║           G R E E N L E D G E R  v2.0                   ║
║   Credit-Based Incentive Platform | Waste Tracking       ║
╚══════════════════════════════════════════════════════════╝

A digital incentive-based household waste segregation tracker.
- Households log biodegradable & non-biodegradable waste
- Green Score formula rewards proper segregation
- Green Credits stored in Digital Green Wallet
- Public leaderboard shows community waste (not points)
- Redeem credits at local shops
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json, os, math, time
from pathlib import Path
from datetime import datetime, timedelta
import random

# ─────────────────────────────────────────────
#  DATA STORE  (JSON file simulates a database)
# ─────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_FILE = str(DATA_DIR / "greenledger_data.json")

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"houses": {}, "public_log": []}

def save_data(data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ─────────────────────────────────────────────
#  GREEN SCORE  FORMULA
# ─────────────────────────────────────────────
def calculate_green_score(bio_kg, non_bio_kg):
    """
    Formula:
      base_score     = segregation_ratio × 60         (0–60)
      efficiency     = max(0, 1 - non_bio/total) × 20 (0–20)
      reduction_bonus= e^(-total/5) × 20              (0–20)  rewards low total waste
      ─────────────────────────────────────────────────────
      raw_score      = base_score + efficiency + reduction_bonus
      green_score    = min(100, round(raw_score, 2))
      green_credits  = green_score // 5   (0–20 credits per entry)
    """
    total = bio_kg + non_bio_kg
    if total == 0:
        return 0.0, 0

    seg_ratio = bio_kg / total
    base_score = seg_ratio * 60

    # Efficiency: penalise heavy non-bio
    non_bio_ratio = non_bio_kg / total
    efficiency = (1 - non_bio_ratio) * 20

    # Reduction bonus: fewer total kg → higher reward
    reduction_bonus = math.exp(-total / 5) * 20

    raw = base_score + efficiency + reduction_bonus
    green_score = min(100.0, round(raw, 2))
    green_credits = int(green_score // 5)
    return green_score, green_credits

# ─────────────────────────────────────────────
#  COLOUR / STYLE PALETTE
# ─────────────────────────────────────────────
BG        = "#0D1F0F"   # very dark forest green
PANEL     = "#132B16"   # panel background
CARD      = "#1A3B1E"   # card background
ACCENT1   = "#4ADE80"   # bright mint green
ACCENT2   = "#22C55E"   # mid green
ACCENT3   = "#86EFAC"   # light green
GOLD      = "#FCD34D"   # reward gold
SOFT_TEXT = "#A7F3D0"   # soft mint text
WHITE     = "#F0FFF4"   # near-white
RED_WARN  = "#EF4444"
AMBER     = "#F59E0B"
BLUE      = "#38BDF8"

FONT_TITLE  = ("Trebuchet MS", 22, "bold")
FONT_HEAD   = ("Trebuchet MS", 14, "bold")
FONT_SUB    = ("Trebuchet MS", 11, "bold")
FONT_BODY   = ("Trebuchet MS", 10)
FONT_SMALL  = ("Trebuchet MS", 9)
FONT_BIG    = ("Trebuchet MS", 32, "bold")
FONT_HUGE   = ("Trebuchet MS", 48, "bold")

# ─────────────────────────────────────────────
#  ANIMATED SPLASH
# ─────────────────────────────────────────────
class SplashScreen(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.overrideredirect(True)
        w, h = 520, 300
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.configure(bg=BG)

        canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        # Leaf decoration
        for i in range(12):
            x = random.randint(20, 500)
            y = random.randint(20, 280)
            r = random.randint(4, 12)
            canvas.create_oval(x-r, y-r, x+r, y+r,
                                fill=random.choice([ACCENT2, CARD, ACCENT1]),
                                outline="")

        canvas.create_text(260, 100, text="🌱", font=("Segoe UI Emoji", 48))
        canvas.create_text(260, 165, text="GreenLedger", font=FONT_HUGE, fill=ACCENT1)
        canvas.create_text(260, 210, text="Waste Less. Earn More. Live Green.", font=FONT_SUB, fill=SOFT_TEXT)

        self.bar_canvas = tk.Canvas(self, bg=BG, height=6, highlightthickness=0)
        self.bar_canvas.pack(fill="x", padx=40, pady=10)
        self._progress = 0
        self._animate_bar()

    def _animate_bar(self):
        self._progress += 2
        self.bar_canvas.delete("all")
        w = self.bar_canvas.winfo_width() or 440
        filled = int(w * self._progress / 100)
        self.bar_canvas.create_rectangle(0, 0, w, 6, fill=PANEL, outline="")
        self.bar_canvas.create_rectangle(0, 0, filled, 6, fill=ACCENT1, outline="")
        if self._progress < 100:
            self.after(18, self._animate_bar)
        else:
            self.after(300, self.destroy)

# ─────────────────────────────────────────────
#  MAIN APPLICATION
# ─────────────────────────────────────────────
class GreenLedgerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GreenLedger – Digital Waste Incentive Platform")
        self.configure(bg=BG)
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h = 1100, 720
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.minsize(900, 640)
        self.resizable(True, True)

        self.data = load_data()
        self.current_house = tk.StringVar(value="")
        self.current_user_data = None

        # Splash
        splash = SplashScreen(self)
        self.withdraw()
        self.wait_window(splash)

        self._seed_demo_data()
        self._build_ui()
        self.deiconify()

    # ── seed some demo neighbour data ──────────────
    def _seed_demo_data(self):
        demos = [
            ("House-01", [
                ("2025-06-01", 1.2, 0.3),
                ("2025-06-02", 0.9, 0.2),
                ("2025-06-03", 1.5, 0.4),
            ]),
            ("House-02", [
                ("2025-06-01", 0.5, 0.8),
                ("2025-06-02", 0.7, 0.6),
            ]),
            ("House-03", [
                ("2025-06-01", 1.8, 0.1),
                ("2025-06-02", 1.6, 0.2),
                ("2025-06-03", 1.4, 0.1),
            ]),
            ("House-04", [
                ("2025-06-01", 0.3, 0.9),
            ]),
            ("House-05", [
                ("2025-06-01", 1.1, 0.3),
                ("2025-06-02", 1.0, 0.2),
            ]),
        ]
        changed = False
        for house_id, entries in demos:
            if house_id not in self.data["houses"]:
                changed = True
                score_total, credits_total = 0, 0
                log = []
                for date, bio, nbio in entries:
                    gs, gc = calculate_green_score(bio, nbio)
                    score_total += gs
                    credits_total += gc
                    log.append({"date": date, "bio_kg": bio, "non_bio_kg": nbio,
                                 "green_score": gs, "credits_earned": gc})
                self.data["houses"][house_id] = {
                    "password": "demo",
                    "total_score": score_total,
                    "wallet_credits": credits_total,
                    "redeemed_credits": 0,
                    "log": log
                }
        if changed:
            save_data(self.data)

    # ─────────────────────────────────────────────
    #  BUILD UI SKELETON
    # ─────────────────────────────────────────────
    def _build_ui(self):
        # Top bar
        self._build_topbar()

        # Content area (sidebar + main)
        self.content = tk.Frame(self, bg=BG)
        self.content.pack(fill="both", expand=True)

        self._build_sidebar()

        self.main_frame = tk.Frame(self.content, bg=BG)
        self.main_frame.pack(side="left", fill="both", expand=True, padx=8, pady=8)

        # Pages
        self.pages = {}
        for PageClass in [LoginPage, DashboardPage, LogWastePage,
                           HistoryPage, WalletPage, CommunityPage, LeaderboardPage]:
            page = PageClass(self.main_frame, self)
            self.pages[PageClass.__name__] = page

        self.show_page("LoginPage")

    def _build_topbar(self):
        bar = tk.Frame(self, bg=PANEL, height=56)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        tk.Label(bar, text="🌱 GreenLedger", font=FONT_TITLE,
                 bg=PANEL, fg=ACCENT1).pack(side="left", padx=20, pady=8)
        tk.Label(bar, text="Waste Less · Earn More · Live Green",
                 font=FONT_SMALL, bg=PANEL, fg=SOFT_TEXT).pack(side="left", padx=4)

        self.lbl_house = tk.Label(bar, text="", font=FONT_SUB,
                                   bg=PANEL, fg=GOLD)
        self.lbl_house.pack(side="right", padx=20)

        tk.Label(bar, text="●", bg=PANEL, fg=ACCENT2).pack(side="right", padx=2)
        self.lbl_status = tk.Label(bar, text="Not logged in",
                                    font=FONT_SMALL, bg=PANEL, fg=SOFT_TEXT)
        self.lbl_status.pack(side="right", padx=4)

    def _build_sidebar(self):
        sb = tk.Frame(self.content, bg=PANEL, width=188)
        sb.pack(side="left", fill="y", padx=(4, 0), pady=4)
        sb.pack_propagate(False)

        tk.Label(sb, text="NAVIGATION", font=FONT_SMALL,
                 bg=PANEL, fg=SOFT_TEXT).pack(pady=(20, 6), padx=16, anchor="w")

        nav_items = [
            ("🏠", "Dashboard",    "DashboardPage"),
            ("📋", "Log Waste",    "LogWastePage"),
            ("📅", "History",      "HistoryPage"),
            ("💚", "Green Wallet", "WalletPage"),
            ("🌍", "Community",    "CommunityPage"),
            ("🏆", "Leaderboard",  "LeaderboardPage"),
        ]
        self.nav_buttons = {}
        for icon, label, page in nav_items:
            btn = tk.Button(sb, text=f"  {icon}  {label}",
                            font=FONT_BODY, bg=PANEL, fg=WHITE,
                            activebackground=CARD, activeforeground=ACCENT1,
                            relief="flat", anchor="w", cursor="hand2",
                            command=lambda p=page: self.require_login(p))
            btn.pack(fill="x", padx=8, pady=2, ipady=8)
            self.nav_buttons[page] = btn

        # separator
        tk.Frame(sb, bg=CARD, height=1).pack(fill="x", padx=12, pady=12)

        logout_btn = tk.Button(sb, text="  🚪  Logout",
                               font=FONT_BODY, bg=PANEL, fg=RED_WARN,
                               activebackground=CARD, relief="flat",
                               anchor="w", cursor="hand2",
                               command=self._logout)
        logout_btn.pack(fill="x", padx=8, pady=2, ipady=8)

        # credits mini-widget
        tk.Frame(sb, bg=CARD, height=1).pack(fill="x", padx=12, pady=8)
        self.sb_credits_lbl = tk.Label(sb, text="", font=FONT_SMALL,
                                        bg=PANEL, fg=GOLD, justify="center")
        self.sb_credits_lbl.pack(padx=8, pady=4)

    def _logout(self):
        self.current_house.set("")
        self.current_user_data = None
        self.lbl_status.config(text="Not logged in")
        self.lbl_house.config(text="")
        self.sb_credits_lbl.config(text="")
        self.show_page("LoginPage")

    def show_page(self, name):
        for page in self.pages.values():
            page.pack_forget()
        page = self.pages[name]
        page.pack(fill="both", expand=True)
        page.on_show()
        # Highlight nav
        for pname, btn in self.nav_buttons.items():
            btn.config(bg=CARD if pname == name else PANEL,
                       fg=ACCENT1 if pname == name else WHITE)

    def require_login(self, page):
        if not self.current_house.get():
            messagebox.showwarning("Login Required", "Please login first.")
            return
        self.show_page(page)

    def refresh_header(self):
        h = self.current_house.get()
        if h and h in self.data["houses"]:
            ud = self.data["houses"][h]
            self.lbl_status.config(text="Logged in")
            self.lbl_house.config(text=f"🏡 {h}")
            self.sb_credits_lbl.config(
                text=f"💚 Credits\n{ud['wallet_credits'] - ud['redeemed_credits']} available")


# ─────────────────────────────────────────────
#  BASE PAGE
# ─────────────────────────────────────────────
class BasePage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app

    def on_show(self): pass

    def card(self, parent, title="", **kwargs):
        outer = tk.Frame(parent, bg=ACCENT2, padx=1, pady=1)
        inner = tk.Frame(outer, bg=CARD, **kwargs)
        inner.pack(fill="both", expand=True, padx=1, pady=1)
        if title:
            tk.Label(inner, text=title, font=FONT_SUB,
                     bg=CARD, fg=ACCENT1).pack(anchor="w", padx=14, pady=(10, 4))
        return outer, inner


# ─────────────────────────────────────────────
#  LOGIN / REGISTER PAGE
# ─────────────────────────────────────────────
class LoginPage(BasePage):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._build()

    def on_show(self): pass

    def _build(self):
        # Centre panel
        wrapper = tk.Frame(self, bg=BG)
        wrapper.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(wrapper, text="🌱", font=("Segoe UI Emoji", 52),
                 bg=BG).pack(pady=(0, 4))
        tk.Label(wrapper, text="GreenLedger", font=FONT_BIG,
                 bg=BG, fg=ACCENT1).pack()
        tk.Label(wrapper, text="Login or register your household",
                 font=FONT_BODY, bg=BG, fg=SOFT_TEXT).pack(pady=(4, 18))

        card_outer = tk.Frame(wrapper, bg=ACCENT2, padx=2, pady=2)
        card_outer.pack(ipadx=30, ipady=20)
        card_in = tk.Frame(card_outer, bg=CARD)
        card_in.pack(fill="both", expand=True, padx=1, pady=1)

        def field(lbl):
            tk.Label(card_in, text=lbl, font=FONT_SMALL, bg=CARD, fg=SOFT_TEXT).pack(anchor="w", padx=20, pady=(10, 2))
            e = tk.Entry(card_in, font=FONT_BODY, bg=PANEL, fg=WHITE,
                         insertbackground=ACCENT1, relief="flat",
                         width=28)
            e.pack(padx=20, ipady=6)
            return e

        self.e_house = field("House ID (e.g. House-07 or your name)")
        self.e_pass  = field("Password")
        self.e_pass.config(show="●")

        # Tab: Login / Register
        self.mode = tk.StringVar(value="login")
        tab_frame = tk.Frame(card_in, bg=CARD)
        tab_frame.pack(pady=(14, 4))
        tk.Radiobutton(tab_frame, text="Login", variable=self.mode,
                       value="login", bg=CARD, fg=WHITE,
                       selectcolor=PANEL, activebackground=CARD,
                       font=FONT_BODY).pack(side="left", padx=8)
        tk.Radiobutton(tab_frame, text="Register New House", variable=self.mode,
                       value="register", bg=CARD, fg=WHITE,
                       selectcolor=PANEL, activebackground=CARD,
                       font=FONT_BODY).pack(side="left", padx=8)

        tk.Button(card_in, text="Continue →",
                  font=FONT_SUB, bg=ACCENT2, fg=BG,
                  activebackground=ACCENT1, relief="flat",
                  cursor="hand2", command=self._submit).pack(pady=14, ipadx=20, ipady=6)

        self.err_lbl = tk.Label(card_in, text="", font=FONT_SMALL,
                                 bg=CARD, fg=RED_WARN)
        self.err_lbl.pack()

    def _submit(self):
        hid = self.e_house.get().strip()
        pwd = self.e_pass.get().strip()
        if not hid or not pwd:
            self.err_lbl.config(text="Both fields are required.")
            return

        if self.mode.get() == "register":
            if hid in self.app.data["houses"]:
                self.err_lbl.config(text="House ID already exists. Try login.")
                return
            self.app.data["houses"][hid] = {
                "password": pwd,
                "total_score": 0.0,
                "wallet_credits": 0,
                "redeemed_credits": 0,
                "log": []
            }
            save_data(self.app.data)
            messagebox.showinfo("Welcome!", f"House '{hid}' registered! 🎉")
        else:
            if hid not in self.app.data["houses"]:
                self.err_lbl.config(text="House not found. Register first.")
                return
            if self.app.data["houses"][hid]["password"] != pwd:
                self.err_lbl.config(text="Wrong password.")
                return

        self.app.current_house.set(hid)
        self.app.current_user_data = self.app.data["houses"][hid]
        self.app.refresh_header()
        self.err_lbl.config(text="")
        self.app.show_page("DashboardPage")


# ─────────────────────────────────────────────
#  DASHBOARD
# ─────────────────────────────────────────────
class DashboardPage(BasePage):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._built = False

    def on_show(self):
        for w in self.winfo_children():
            w.destroy()
        self._build()

    def _build(self):
        hid = self.app.current_house.get()
        if not hid:
            return
        ud = self.app.data["houses"][hid]
        avail = ud["wallet_credits"] - ud["redeemed_credits"]
        logs = ud["log"]
        total_bio   = sum(e["bio_kg"] for e in logs)
        total_nbio  = sum(e["non_bio_kg"] for e in logs)
        total_waste = total_bio + total_nbio

        # Title
        tk.Label(self, text=f"Welcome back, {hid} 👋",
                 font=FONT_TITLE, bg=BG, fg=WHITE).pack(anchor="w", padx=8, pady=(8, 4))
        tk.Label(self, text=datetime.now().strftime("%A, %d %B %Y"),
                 font=FONT_SMALL, bg=BG, fg=SOFT_TEXT).pack(anchor="w", padx=8)

        # Stat cards row
        row = tk.Frame(self, bg=BG)
        row.pack(fill="x", padx=8, pady=10)

        stats = [
            ("🌿", "Green Score",  f"{ud['total_score']:.1f}", "pts", ACCENT1),
            ("💚", "Credits Earned", str(ud["wallet_credits"]), "total", ACCENT2),
            ("💰", "Available Credits", str(avail), "credits", GOLD),
            ("🗑️", "Entries Logged",  str(len(logs)), "days", SOFT_TEXT),
        ]
        for icon, label, value, unit, color in stats:
            c = tk.Frame(row, bg=CARD, padx=16, pady=14)
            c.pack(side="left", expand=True, fill="both", padx=5)
            tk.Label(c, text=icon, font=("Segoe UI Emoji", 22), bg=CARD).pack()
            tk.Label(c, text=value, font=("Trebuchet MS", 26, "bold"),
                     bg=CARD, fg=color).pack()
            tk.Label(c, text=unit, font=FONT_SMALL, bg=CARD, fg=SOFT_TEXT).pack()
            tk.Label(c, text=label, font=FONT_SMALL, bg=CARD, fg=WHITE).pack(pady=(4, 0))

        # Middle section: waste summary + reward status
        mid = tk.Frame(self, bg=BG)
        mid.pack(fill="both", expand=True, padx=8, pady=4)

        # Waste breakdown
        left_card = tk.Frame(mid, bg=CARD, padx=16, pady=14)
        left_card.pack(side="left", fill="both", expand=True, padx=(0, 5))
        tk.Label(left_card, text="📊 Waste Overview", font=FONT_HEAD,
                 bg=CARD, fg=ACCENT1).pack(anchor="w")
        tk.Frame(left_card, bg=ACCENT2, height=1).pack(fill="x", pady=6)

        def stat_row(icon, label, val, color):
            r = tk.Frame(left_card, bg=CARD)
            r.pack(fill="x", pady=3)
            tk.Label(r, text=icon, font=("Segoe UI Emoji", 14), bg=CARD).pack(side="left")
            tk.Label(r, text=f"  {label}", font=FONT_BODY, bg=CARD, fg=WHITE).pack(side="left")
            tk.Label(r, text=f"{val:.2f} kg", font=FONT_SUB, bg=CARD, fg=color).pack(side="right")

        stat_row("🟢", "Biodegradable",     total_bio,   ACCENT1)
        stat_row("🔴", "Non-Biodegradable", total_nbio,  RED_WARN)
        stat_row("⚖️", "Total Waste",        total_waste, SOFT_TEXT)

        # Segregation meter
        if total_waste > 0:
            ratio = total_bio / total_waste
            tk.Label(left_card, text="\nSegregation Efficiency",
                     font=FONT_SMALL, bg=CARD, fg=SOFT_TEXT).pack(anchor="w", pady=(8, 2))
            meter_bg = tk.Canvas(left_card, bg=PANEL, height=16,
                                  highlightthickness=0)
            meter_bg.pack(fill="x", pady=2)
            meter_bg.update()
            w = meter_bg.winfo_width()
            filled = int(w * ratio)
            color = ACCENT1 if ratio > 0.7 else AMBER if ratio > 0.4 else RED_WARN
            meter_bg.create_rectangle(0, 0, w, 16, fill=PANEL, outline="")
            meter_bg.create_rectangle(0, 0, filled, 16, fill=color, outline="")
            meter_bg.create_text(w//2, 8, text=f"{ratio*100:.0f}%",
                                  fill=BG, font=FONT_SMALL)

        # Reward status
        right_card = tk.Frame(mid, bg=CARD, padx=16, pady=14)
        right_card.pack(side="left", fill="both", expand=True, padx=(5, 0))
        tk.Label(right_card, text="🎁 Reward Status", font=FONT_HEAD,
                 bg=CARD, fg=ACCENT1).pack(anchor="w")
        tk.Frame(right_card, bg=ACCENT2, height=1).pack(fill="x", pady=6)

        tiers = [
            (100, "🥇 Platinum – 30% Discount + Priority Pickup"),
            (75,  "🥈 Gold     – 25% Discount at partners"),
            (50,  "🥉 Silver   – 20% Discount at local shops"),
            (25,  "🎖️ Bronze   – 10% Discount"),
            (10,  "🌱 Starter  – 5% Discount"),
            (0,   "🌀 Keep logging to earn rewards!"),
        ]
        current_tier = tiers[-1][1]
        for threshold, label in tiers:
            if avail >= threshold:
                current_tier = label
                break

        tk.Label(right_card, text="Current Tier", font=FONT_SMALL,
                 bg=CARD, fg=SOFT_TEXT).pack(anchor="w")
        tk.Label(right_card, text=current_tier, font=FONT_SUB,
                 bg=CARD, fg=GOLD, wraplength=260, justify="left").pack(anchor="w", pady=6)
        tk.Frame(right_card, bg=PANEL, height=1).pack(fill="x", pady=6)

        # Progress to next tier
        next_tiers = [(t, l) for t, l in tiers if t > avail]
        if next_tiers:
            next_t, next_l = next_tiers[-1]
            needed = next_t - avail
            tk.Label(right_card, text=f"Need {needed} more credits for:",
                     font=FONT_SMALL, bg=CARD, fg=SOFT_TEXT).pack(anchor="w")
            tk.Label(right_card, text=next_l, font=FONT_SMALL,
                     bg=CARD, fg=ACCENT3, wraplength=260, justify="left").pack(anchor="w")

        # Quick action
        tk.Frame(right_card, bg=PANEL, height=1).pack(fill="x", pady=10)
        tk.Button(right_card, text="➕  Log Today's Waste",
                  font=FONT_SUB, bg=ACCENT2, fg=BG,
                  activebackground=ACCENT1, relief="flat",
                  cursor="hand2",
                  command=lambda: self.app.show_page("LogWastePage")
                  ).pack(fill="x", ipady=8)

        # Recent activity
        bot = tk.Frame(self, bg=CARD, padx=16, pady=10)
        bot.pack(fill="x", padx=8, pady=8)
        tk.Label(bot, text="📅 Recent Activity", font=FONT_HEAD,
                 bg=CARD, fg=ACCENT1).pack(anchor="w")
        tk.Frame(bot, bg=ACCENT2, height=1).pack(fill="x", pady=4)

        if not logs:
            tk.Label(bot, text="No entries yet. Start logging waste to earn Green Credits!",
                     font=FONT_BODY, bg=CARD, fg=SOFT_TEXT).pack(pady=8)
        else:
            header = tk.Frame(bot, bg=PANEL)
            header.pack(fill="x", pady=(0, 2))
            for col, w in [("Date", 120), ("Bio (kg)", 90), ("Non-Bio (kg)", 110),
                            ("Green Score", 110), ("Credits", 80)]:
                tk.Label(header, text=col, font=FONT_SMALL, bg=PANEL,
                         fg=SOFT_TEXT, width=w//8).pack(side="left", padx=4)

            for entry in reversed(logs[-5:]):
                row = tk.Frame(bot, bg=CARD)
                row.pack(fill="x", pady=1)
                vals = [entry["date"], f"{entry['bio_kg']:.2f}",
                        f"{entry['non_bio_kg']:.2f}",
                        f"{entry['green_score']:.1f}",
                        f"+{entry['credits_earned']}"]
                colors = [WHITE, ACCENT1, RED_WARN, ACCENT3, GOLD]
                for v, c in zip(vals, colors):
                    tk.Label(row, text=v, font=FONT_SMALL, bg=CARD,
                             fg=c, width=10).pack(side="left", padx=4)


# ─────────────────────────────────────────────
#  LOG WASTE PAGE
# ─────────────────────────────────────────────
class LogWastePage(BasePage):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._build()

    def on_show(self):
        self.e_bio.delete(0, "end")
        self.e_nbio.delete(0, "end")
        self.result_frame.pack_forget()

    def _build(self):
        tk.Label(self, text="📋 Log Waste Entry", font=FONT_TITLE,
                 bg=BG, fg=WHITE).pack(anchor="w", padx=8, pady=(8, 2))
        tk.Label(self, text="Record your household waste to earn Green Credits",
                 font=FONT_SMALL, bg=BG, fg=SOFT_TEXT).pack(anchor="w", padx=8)

        wrapper = tk.Frame(self, bg=BG)
        wrapper.pack(fill="both", expand=True, padx=8, pady=10)

        # Form card
        form_card = tk.Frame(wrapper, bg=CARD, padx=24, pady=20)
        form_card.pack(side="left", fill="y", padx=(0, 10))

        tk.Label(form_card, text="Enter Waste Weights", font=FONT_HEAD,
                 bg=CARD, fg=ACCENT1).pack(anchor="w")
        tk.Frame(form_card, bg=ACCENT2, height=1).pack(fill="x", pady=8)

        # Date
        tk.Label(form_card, text="Date", font=FONT_SMALL, bg=CARD, fg=SOFT_TEXT).pack(anchor="w")
        self.e_date = tk.Entry(form_card, font=FONT_BODY, bg=PANEL, fg=WHITE,
                                insertbackground=ACCENT1, relief="flat", width=24)
        self.e_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.e_date.pack(ipady=6, pady=(0, 10))

        # Bio
        bio_frame = tk.Frame(form_card, bg=CARD)
        bio_frame.pack(fill="x", pady=4)
        tk.Label(bio_frame, text="🟢", font=("Segoe UI Emoji", 16), bg=CARD).pack(side="left")
        tk.Label(bio_frame, text=" Biodegradable Waste (kg)",
                 font=FONT_BODY, bg=CARD, fg=ACCENT1).pack(side="left")
        self.e_bio = tk.Entry(form_card, font=("Trebuchet MS", 18), bg=PANEL,
                               fg=ACCENT1, insertbackground=ACCENT1,
                               relief="flat", width=18, justify="center")
        self.e_bio.pack(ipady=10, pady=(0, 6))

        tk.Label(form_card, text="Examples: food scraps, vegetable peels, garden waste",
                 font=FONT_SMALL, bg=CARD, fg=SOFT_TEXT, wraplength=240).pack(anchor="w")

        tk.Frame(form_card, bg=PANEL, height=1).pack(fill="x", pady=10)

        # Non-bio
        nbio_frame = tk.Frame(form_card, bg=CARD)
        nbio_frame.pack(fill="x", pady=4)
        tk.Label(nbio_frame, text="🔴", font=("Segoe UI Emoji", 16), bg=CARD).pack(side="left")
        tk.Label(nbio_frame, text=" Non-Biodegradable Waste (kg)",
                 font=FONT_BODY, bg=CARD, fg=RED_WARN).pack(side="left")
        self.e_nbio = tk.Entry(form_card, font=("Trebuchet MS", 18), bg=PANEL,
                                fg=RED_WARN, insertbackground=RED_WARN,
                                relief="flat", width=18, justify="center")
        self.e_nbio.pack(ipady=10, pady=(0, 6))

        tk.Label(form_card, text="Examples: plastics, glass, metal, e-waste",
                 font=FONT_SMALL, bg=CARD, fg=SOFT_TEXT, wraplength=240).pack(anchor="w")

        tk.Frame(form_card, bg=PANEL, height=1).pack(fill="x", pady=14)

        tk.Button(form_card, text="  ✅  Submit & Calculate  ",
                  font=FONT_HEAD, bg=ACCENT2, fg=BG,
                  activebackground=ACCENT1, relief="flat", cursor="hand2",
                  command=self._submit).pack(fill="x", ipady=10)

        # Info panel
        info_card = tk.Frame(wrapper, bg=CARD, padx=20, pady=20)
        info_card.pack(side="left", fill="both", expand=True)

        tk.Label(info_card, text="ℹ️ How Scoring Works", font=FONT_HEAD,
                 bg=CARD, fg=ACCENT1).pack(anchor="w")
        tk.Frame(info_card, bg=ACCENT2, height=1).pack(fill="x", pady=8)

        tips = [
            ("🌿", "Segregation Base",  "Up to 60 pts for proper bio/non-bio ratio"),
            ("♻️", "Efficiency Bonus",  "Up to 20 pts for minimising non-bio waste"),
            ("📉", "Reduction Bonus",   "Up to 20 pts for keeping total waste low"),
            ("💚", "Green Credits",     "1 credit per 5 Green Score points"),
            ("🎁", "Rewards",           "Use credits for shop discounts!"),
        ]
        for icon, head, desc in tips:
            r = tk.Frame(info_card, bg=PANEL, padx=12, pady=8)
            r.pack(fill="x", pady=3)
            tk.Label(r, text=icon, font=("Segoe UI Emoji", 18), bg=PANEL).pack(side="left", padx=(0, 8))
            t = tk.Frame(r, bg=PANEL)
            t.pack(side="left")
            tk.Label(t, text=head, font=FONT_SUB, bg=PANEL, fg=ACCENT3).pack(anchor="w")
            tk.Label(t, text=desc, font=FONT_SMALL, bg=PANEL, fg=SOFT_TEXT,
                     wraplength=260, justify="left").pack(anchor="w")

        # Result area
        self.result_frame = tk.Frame(self, bg=CARD, padx=24, pady=20)

    def _submit(self):
        try:
            bio  = float(self.e_bio.get())
            nbio = float(self.e_nbio.get())
        except ValueError:
            messagebox.showerror("Input Error", "Enter valid numbers (e.g. 1.2)")
            return
        if bio < 0 or nbio < 0:
            messagebox.showerror("Input Error", "Values cannot be negative.")
            return
        if bio == 0 and nbio == 0:
            messagebox.showwarning("No Waste", "Please enter at least some waste weight.")
            return

        date_str = self.e_date.get().strip() or datetime.now().strftime("%Y-%m-%d")
        gs, gc = calculate_green_score(bio, nbio)

        hid = self.app.current_house.get()
        ud  = self.app.data["houses"][hid]
        ud["log"].append({
            "date": date_str,
            "bio_kg": bio,
            "non_bio_kg": nbio,
            "green_score": gs,
            "credits_earned": gc
        })
        ud["total_score"]    += gs
        ud["wallet_credits"] += gc
        save_data(self.app.data)
        self.app.refresh_header()

        # Show result
        self.result_frame.pack(fill="x", padx=8, pady=8)
        for w in self.result_frame.winfo_children():
            w.destroy()

        tk.Label(self.result_frame, text="✅ Entry Recorded!", font=FONT_HEAD,
                 bg=CARD, fg=ACCENT1).pack(anchor="w")
        tk.Frame(self.result_frame, bg=ACCENT2, height=1).pack(fill="x", pady=6)

        row = tk.Frame(self.result_frame, bg=CARD)
        row.pack(fill="x")
        for label, value, color in [
            ("Green Score", f"{gs:.2f} pts", ACCENT1),
            ("Credits Earned", f"+{gc} 💚", GOLD),
            ("Total Credits", str(ud["wallet_credits"]), ACCENT3),
        ]:
            c = tk.Frame(row, bg=PANEL, padx=20, pady=10)
            c.pack(side="left", expand=True, fill="both", padx=4)
            tk.Label(c, text=value, font=("Trebuchet MS", 20, "bold"),
                     bg=PANEL, fg=color).pack()
            tk.Label(c, text=label, font=FONT_SMALL, bg=PANEL, fg=SOFT_TEXT).pack()

        # Tip
        if gs < 40:
            tip = "💡 Try to segregate more biodegradable waste to boost your score!"
        elif gs < 70:
            tip = "💡 Great effort! Reducing total waste will earn you more credits."
        else:
            tip = "🌟 Excellent segregation! Keep it up and earn more rewards!"
        tk.Label(self.result_frame, text=tip, font=FONT_SMALL,
                 bg=CARD, fg=SOFT_TEXT, wraplength=600).pack(pady=8, anchor="w")


# ─────────────────────────────────────────────
#  HISTORY PAGE
# ─────────────────────────────────────────────
class HistoryPage(BasePage):
    def __init__(self, parent, app):
        super().__init__(parent, app)

    def on_show(self):
        for w in self.winfo_children():
            w.destroy()
        self._build()

    def _build(self):
        tk.Label(self, text="📅 Waste History", font=FONT_TITLE,
                 bg=BG, fg=WHITE).pack(anchor="w", padx=8, pady=(8, 2))

        hid = self.app.current_house.get()
        ud  = self.app.data["houses"].get(hid, {})
        logs = ud.get("log", [])

        # Summary bar
        if logs:
            total_bio   = sum(e["bio_kg"] for e in logs)
            total_nbio  = sum(e["non_bio_kg"] for e in logs)
            total_score = sum(e["green_score"] for e in logs)
            avg_score   = total_score / len(logs)

            sbar = tk.Frame(self, bg=PANEL, padx=12, pady=8)
            sbar.pack(fill="x", padx=8, pady=6)
            for label, value, color in [
                ("Entries", str(len(logs)), WHITE),
                ("Total Bio", f"{total_bio:.2f} kg", ACCENT1),
                ("Total Non-Bio", f"{total_nbio:.2f} kg", RED_WARN),
                ("Avg Score", f"{avg_score:.1f}", ACCENT3),
            ]:
                c = tk.Frame(sbar, bg=PANEL)
                c.pack(side="left", padx=20)
                tk.Label(c, text=value, font=FONT_HEAD, bg=PANEL, fg=color).pack()
                tk.Label(c, text=label, font=FONT_SMALL, bg=PANEL, fg=SOFT_TEXT).pack()

        # Table
        table_card = tk.Frame(self, bg=CARD)
        table_card.pack(fill="both", expand=True, padx=8, pady=4)

        cols = ["#", "Date", "Bio (kg)", "Non-Bio (kg)", "Total (kg)",
                "Green Score", "Credits", "Seg. Ratio"]
        widths = [40, 110, 90, 110, 90, 110, 80, 100]

        # Header
        hdr = tk.Frame(table_card, bg=PANEL)
        hdr.pack(fill="x")
        for col, w in zip(cols, widths):
            tk.Label(hdr, text=col, font=FONT_SMALL, bg=PANEL,
                     fg=ACCENT1, width=w//7, anchor="w").pack(side="left", padx=4, pady=6)

        # Scrollable body
        canvas = tk.Canvas(table_card, bg=CARD, highlightthickness=0)
        scrollbar = ttk.Scrollbar(table_card, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=CARD)

        scroll_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        if not logs:
            tk.Label(scroll_frame, text="No entries yet.",
                     font=FONT_BODY, bg=CARD, fg=SOFT_TEXT).pack(pady=20)
        else:
            for i, e in enumerate(reversed(logs), 1):
                total = e["bio_kg"] + e["non_bio_kg"]
                ratio = e["bio_kg"] / total if total else 0
                bg = CARD if i % 2 == 0 else PANEL
                row = tk.Frame(scroll_frame, bg=bg)
                row.pack(fill="x")
                vals = [str(i), e["date"],
                        f"{e['bio_kg']:.2f}", f"{e['non_bio_kg']:.2f}",
                        f"{total:.2f}", f"{e['green_score']:.1f}",
                        f"+{e['credits_earned']}", f"{ratio*100:.0f}%"]
                f_cols = [WHITE, SOFT_TEXT, ACCENT1, RED_WARN,
                           WHITE, ACCENT3, GOLD, BLUE]
                for v, c, w in zip(vals, f_cols, widths):
                    tk.Label(row, text=v, font=FONT_SMALL, bg=bg,
                             fg=c, width=w//7, anchor="w").pack(side="left", padx=4, pady=4)


# ─────────────────────────────────────────────
#  WALLET PAGE
# ─────────────────────────────────────────────
class WalletPage(BasePage):
    def __init__(self, parent, app):
        super().__init__(parent, app)

    def on_show(self):
        for w in self.winfo_children():
            w.destroy()
        self._build()

    def _build(self):
        tk.Label(self, text="💚 Green Wallet", font=FONT_TITLE,
                 bg=BG, fg=WHITE).pack(anchor="w", padx=8, pady=(8, 2))

        hid = self.app.current_house.get()
        ud  = self.app.data["houses"].get(hid, {})
        total    = ud.get("wallet_credits", 0)
        redeemed = ud.get("redeemed_credits", 0)
        avail    = total - redeemed

        wrapper = tk.Frame(self, bg=BG)
        wrapper.pack(fill="both", expand=True, padx=8, pady=8)

        # Wallet card
        wallet = tk.Frame(wrapper, bg=CARD, padx=24, pady=20)
        wallet.pack(side="left", fill="y", padx=(0, 10))

        tk.Label(wallet, text="💚", font=("Segoe UI Emoji", 48), bg=CARD).pack()
        tk.Label(wallet, text=str(avail), font=("Trebuchet MS", 56, "bold"),
                 bg=CARD, fg=ACCENT1).pack()
        tk.Label(wallet, text="Available Credits", font=FONT_HEAD,
                 bg=CARD, fg=SOFT_TEXT).pack()

        tk.Frame(wallet, bg=PANEL, height=1).pack(fill="x", pady=10)

        for label, value in [("Total Earned", str(total)), ("Redeemed", str(redeemed))]:
            r = tk.Frame(wallet, bg=PANEL, padx=12, pady=6)
            r.pack(fill="x", pady=2)
            tk.Label(r, text=label, font=FONT_SMALL, bg=PANEL, fg=SOFT_TEXT).pack(side="left")
            tk.Label(r, text=value, font=FONT_SUB, bg=PANEL, fg=GOLD).pack(side="right")

        # Redeem section
        right = tk.Frame(wrapper, bg=BG)
        right.pack(side="left", fill="both", expand=True)

        # Discount tiers
        tiers_card = tk.Frame(right, bg=CARD, padx=20, pady=16)
        tiers_card.pack(fill="x", pady=(0, 8))
        tk.Label(tiers_card, text="🎁 Discount Tiers", font=FONT_HEAD,
                 bg=CARD, fg=ACCENT1).pack(anchor="w")
        tk.Frame(tiers_card, bg=ACCENT2, height=1).pack(fill="x", pady=6)

        tiers = [
            (100, "30%", "Platinum – Priority pickup + 30% discount"),
            (75,  "25%", "Gold – 25% at all partner shops"),
            (50,  "20%", "Silver – 20% at local shops"),
            (25,  "10%", "Bronze – 10% discount"),
            (10,  "5%",  "Starter – 5% discount"),
        ]
        for req, disc, label in tiers:
            r = tk.Frame(tiers_card, bg=PANEL if avail >= req else CARD, padx=12, pady=6)
            r.pack(fill="x", pady=2)
            status = "✅" if avail >= req else f"🔒 Need {req}"
            tk.Label(r, text=status, font=FONT_SMALL,
                     bg=r["bg"], fg=ACCENT1 if avail >= req else SOFT_TEXT).pack(side="left")
            tk.Label(r, text=f"  {label}", font=FONT_SMALL,
                     bg=r["bg"], fg=WHITE if avail >= req else SOFT_TEXT).pack(side="left")
            tk.Label(r, text=disc, font=FONT_SUB,
                     bg=r["bg"], fg=GOLD if avail >= req else SOFT_TEXT).pack(side="right")

        # Redeem
        redeem_card = tk.Frame(right, bg=CARD, padx=20, pady=16)
        redeem_card.pack(fill="x")
        tk.Label(redeem_card, text="🛒 Redeem Credits", font=FONT_HEAD,
                 bg=CARD, fg=ACCENT1).pack(anchor="w")
        tk.Frame(redeem_card, bg=ACCENT2, height=1).pack(fill="x", pady=6)

        tk.Label(redeem_card, text="How many credits to redeem?",
                 font=FONT_SMALL, bg=CARD, fg=SOFT_TEXT).pack(anchor="w")
        self.e_redeem = tk.Entry(redeem_card, font=FONT_HEAD, bg=PANEL, fg=GOLD,
                                  insertbackground=GOLD, relief="flat", width=10)
        self.e_redeem.pack(anchor="w", pady=4, ipady=6)

        tk.Button(redeem_card, text="Redeem →",
                  font=FONT_SUB, bg=GOLD, fg=BG,
                  activebackground=AMBER, relief="flat", cursor="hand2",
                  command=self._redeem).pack(anchor="w", ipadx=20, ipady=6)

        self.redeem_msg = tk.Label(redeem_card, text="", font=FONT_SMALL,
                                    bg=CARD, fg=ACCENT1)
        self.redeem_msg.pack(anchor="w", pady=4)

    def _redeem(self):
        hid = self.app.current_house.get()
        ud  = self.app.data["houses"][hid]
        avail = ud["wallet_credits"] - ud["redeemed_credits"]
        try:
            amount = int(self.e_redeem.get())
        except ValueError:
            self.redeem_msg.config(text="Enter a valid number.", fg=RED_WARN)
            return
        if amount <= 0:
            self.redeem_msg.config(text="Amount must be positive.", fg=RED_WARN)
            return
        if amount > avail:
            self.redeem_msg.config(text=f"Only {avail} credits available.", fg=RED_WARN)
            return
        ud["redeemed_credits"] += amount
        save_data(self.app.data)
        self.redeem_msg.config(text=f"✅ {amount} credits redeemed! Show this screen at your shop.", fg=ACCENT1)
        self.app.refresh_header()
        self.on_show()


# ─────────────────────────────────────────────
#  COMMUNITY PAGE (public waste data, no points)
# ─────────────────────────────────────────────
class CommunityPage(BasePage):
    def __init__(self, parent, app):
        super().__init__(parent, app)

    def on_show(self):
        for w in self.winfo_children():
            w.destroy()
        self._build()

    def _build(self):
        tk.Label(self, text="🌍 Community Waste Board", font=FONT_TITLE,
                 bg=BG, fg=WHITE).pack(anchor="w", padx=8, pady=(8, 2))
        tk.Label(self, text="Public data: All households' waste amounts (points are private)",
                 font=FONT_SMALL, bg=BG, fg=SOFT_TEXT).pack(anchor="w", padx=8)

        # Stats bar
        houses = self.app.data["houses"]
        all_logs = []
        for hid, ud in houses.items():
            for e in ud.get("log", []):
                all_logs.append({**e, "house": hid})

        total_bio  = sum(e["bio_kg"] for e in all_logs)
        total_nbio = sum(e["non_bio_kg"] for e in all_logs)
        total_waste = total_bio + total_nbio

        sbar = tk.Frame(self, bg=PANEL, padx=12, pady=10)
        sbar.pack(fill="x", padx=8, pady=8)
        tk.Label(sbar, text="📊 Community Statistics",
                 font=FONT_SUB, bg=PANEL, fg=ACCENT1).pack(anchor="w")
        row = tk.Frame(sbar, bg=PANEL)
        row.pack(fill="x", pady=6)
        stats = [
            ("🏘️", "Households", str(len(houses))),
            ("📋", "Total Entries", str(len(all_logs))),
            ("🟢", "Total Bio Waste", f"{total_bio:.2f} kg"),
            ("🔴", "Total Non-Bio", f"{total_nbio:.2f} kg"),
            ("⚖️", "Total Waste", f"{total_waste:.2f} kg"),
        ]
        for icon, label, value in stats:
            c = tk.Frame(row, bg=CARD, padx=14, pady=8)
            c.pack(side="left", expand=True, fill="both", padx=4)
            tk.Label(c, text=icon, font=("Segoe UI Emoji", 18), bg=CARD).pack()
            tk.Label(c, text=value, font=FONT_HEAD, bg=CARD, fg=ACCENT1).pack()
            tk.Label(c, text=label, font=FONT_SMALL, bg=CARD, fg=SOFT_TEXT).pack()

        # House-wise breakdown (PUBLIC: only waste, NO points)
        table_card = tk.Frame(self, bg=CARD)
        table_card.pack(fill="both", expand=True, padx=8, pady=4)

        tk.Label(table_card, text="🏡 Per-Household Waste (Points Hidden)",
                 font=FONT_HEAD, bg=CARD, fg=ACCENT1).pack(anchor="w", padx=14, pady=(10, 4))

        hdr = tk.Frame(table_card, bg=PANEL)
        hdr.pack(fill="x", padx=4)
        cols = ["House ID", "Entries", "Bio Waste (kg)", "Non-Bio (kg)", "Total (kg)", "Seg %"]
        widths = [130, 70, 120, 120, 110, 80]
        for col, w in zip(cols, widths):
            tk.Label(hdr, text=col, font=FONT_SMALL, bg=PANEL,
                     fg=ACCENT1, width=w//7, anchor="w").pack(side="left", padx=4, pady=6)

        canvas = tk.Canvas(table_card, bg=CARD, highlightthickness=0)
        sb2 = ttk.Scrollbar(table_card, orient="vertical", command=canvas.yview)
        sf = tk.Frame(canvas, bg=CARD)
        sf.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=sf, anchor="nw")
        canvas.configure(yscrollcommand=sb2.set)
        canvas.pack(side="left", fill="both", expand=True, padx=4)
        sb2.pack(side="right", fill="y")

        for i, (hid, ud) in enumerate(sorted(houses.items())):
            logs = ud.get("log", [])
            bio   = sum(e["bio_kg"] for e in logs)
            nbio  = sum(e["non_bio_kg"] for e in logs)
            total = bio + nbio
            seg   = (bio / total * 100) if total else 0
            bg = CARD if i % 2 == 0 else PANEL
            row = tk.Frame(sf, bg=bg)
            row.pack(fill="x")
            vals = [hid, str(len(logs)), f"{bio:.2f}", f"{nbio:.2f}", f"{total:.2f}", f"{seg:.0f}%"]
            fc   = [WHITE, SOFT_TEXT, ACCENT1, RED_WARN, WHITE, BLUE]
            for v, c, w in zip(vals, fc, widths):
                tk.Label(row, text=v, font=FONT_SMALL, bg=bg,
                         fg=c, width=w//7, anchor="w").pack(side="left", padx=4, pady=4)


# ─────────────────────────────────────────────
#  LEADERBOARD (score shown, but anonymised for others)
# ─────────────────────────────────────────────
class LeaderboardPage(BasePage):
    def __init__(self, parent, app):
        super().__init__(parent, app)

    def on_show(self):
        for w in self.winfo_children():
            w.destroy()
        self._build()

    def _build(self):
        tk.Label(self, text="🏆 Green Leaderboard", font=FONT_TITLE,
                 bg=BG, fg=WHITE).pack(anchor="w", padx=8, pady=(8, 2))
        tk.Label(self, text="Rankings based on total Green Score (your exact credits are private)",
                 font=FONT_SMALL, bg=BG, fg=SOFT_TEXT).pack(anchor="w", padx=8)

        hid = self.app.current_house.get()
        houses = self.app.data["houses"]

        ranked = sorted(
            [(h, d["total_score"]) for h, d in houses.items()],
            key=lambda x: x[1], reverse=True
        )

        # Podium (top 3)
        podium_frame = tk.Frame(self, bg=BG)
        podium_frame.pack(fill="x", padx=8, pady=10)

        medals = ["🥇", "🥈", "🥉"]
        heights = [120, 90, 75]
        colors  = [GOLD, "#C0C0C0", "#CD7F32"]

        for rank, (h, score) in enumerate(ranked[:3], 1):
            c = tk.Frame(podium_frame, bg=CARD, padx=16, pady=10,
                          height=heights[rank-1])
            c.pack(side="left", expand=True, fill="y", padx=6)
            is_me = h == hid
            tk.Label(c, text=medals[rank-1], font=("Segoe UI Emoji", 28), bg=CARD).pack()
            tk.Label(c, text=h + (" ← You" if is_me else ""),
                     font=FONT_SUB if not is_me else ("Trebuchet MS", 11, "bold"),
                     bg=CARD, fg=colors[rank-1] if not is_me else ACCENT1).pack()
            tk.Label(c, text=f"{score:.1f} pts", font=FONT_HEAD,
                     bg=CARD, fg=ACCENT3).pack()
            tk.Label(c, text=f"Rank #{rank}", font=FONT_SMALL,
                     bg=CARD, fg=SOFT_TEXT).pack()

        # Full table
        table_card = tk.Frame(self, bg=CARD)
        table_card.pack(fill="both", expand=True, padx=8, pady=4)

        tk.Label(table_card, text="Full Rankings", font=FONT_HEAD,
                 bg=CARD, fg=ACCENT1).pack(anchor="w", padx=14, pady=(10, 4))

        hdr = tk.Frame(table_card, bg=PANEL)
        hdr.pack(fill="x", padx=4)
        for col, w in [("Rank", 60), ("House", 160), ("Green Score", 120),
                        ("Entries", 80), ("Your Rank", 90)]:
            tk.Label(hdr, text=col, font=FONT_SMALL, bg=PANEL,
                     fg=ACCENT1, width=w//7, anchor="w").pack(side="left", padx=4, pady=6)

        canvas = tk.Canvas(table_card, bg=CARD, highlightthickness=0)
        sb = ttk.Scrollbar(table_card, orient="vertical", command=canvas.yview)
        sf = tk.Frame(canvas, bg=CARD)
        sf.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=sf, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True, padx=4)
        sb.pack(side="right", fill="y")

        for rank, (h, score) in enumerate(ranked, 1):
            logs = houses[h].get("log", [])
            is_me = h == hid
            bg = PANEL if is_me else (CARD if rank % 2 == 0 else BG)
            row = tk.Frame(sf, bg=bg)
            row.pack(fill="x")
            prefix = ["🥇", "🥈", "🥉"][rank-1] if rank <= 3 else f"#{rank}"
            vals = [prefix, h + (" ← You" if is_me else ""),
                    f"{score:.1f}", str(len(logs)), "You!" if is_me else "—"]
            fc   = [GOLD if rank <= 3 else SOFT_TEXT,
                    ACCENT1 if is_me else WHITE,
                    ACCENT3, SOFT_TEXT, GOLD]
            for v, c, w in zip(vals, fc, [60, 160, 120, 80, 90]):
                tk.Label(row, text=v, font=FONT_SMALL if not is_me else FONT_SUB,
                         bg=bg, fg=c, width=w//7, anchor="w").pack(side="left", padx=4, pady=5)


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = GreenLedgerApp()
    app.mainloop()
