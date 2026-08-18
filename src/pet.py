"""
Desktop pet — main runtime.

Spawns N windowless, transparent widgets that crawl around the desktop, treating
open application windows (and the screen edges) as obstacles. Right-click any
pet for the menu.

Run: python src/pet.py
"""
from __future__ import annotations

import math
import os
import random
import sys
import time
import winreg
from pathlib import Path
from typing import List, Optional

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, QPointF, QRectF, QTimer, QSize, QElapsedTimer
from PySide6.QtGui import QAction, QActionGroup, QImage, QPixmap, QPainter, QColor, QCursor, QFont, QPalette, QIcon
from PySide6.QtWidgets import QApplication, QLabel, QMenu, QSystemTrayIcon, QWidget

_BASE = Path(sys._MEIPASS).resolve() if getattr(sys, "frozen", False) else Path(__file__).resolve().parent.parent
ASSETS = _BASE / "assets"

# --- Theme system -----------------------------------------------------------

_REG_THEME_KEY = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
_THEME_PREF_VAL = "DesktopPet_ThemePref"


def _read_theme_pref() -> Optional[str]:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_THEME_KEY, 0,
                            winreg.KEY_QUERY_VALUE) as k:
            val, _ = winreg.QueryValueEx(k, _THEME_PREF_VAL)
            return str(val).strip()
    except OSError:
        return None


def _write_theme_pref(pref: Optional[str]) -> None:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_THEME_KEY, 0,
                            winreg.KEY_SET_VALUE) as k:
            if pref is None:
                winreg.DeleteValue(k, _THEME_PREF_VAL)
            else:
                winreg.SetValueEx(k, _THEME_PREF_VAL, 0, winreg.REG_SZ, pref)
    except OSError:
        pass


def _read_system_theme() -> str:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_THEME_KEY, 0,
                            winreg.KEY_QUERY_VALUE) as k:
            val, _ = winreg.QueryValueEx(k, _REG_THEME_VAL)
            return "light" if val else "dark"
    except OSError:
        return "light"


_REG_THEME_VAL = "AppsUseLightTheme"


# Each palette covers popup menus, the settings dialog, the app stylesheet,
# and the tray icon tint.
_THEMES = {
    "light": {
        "menu_bg":        "#fafafa",
        "menu_border":    "#c9c9c9",
        "menu_item_sel":  "#e8f0fe",
        "menu_item_txt":  "#101010",
        "menu_sep":       "#e2e2e2",
        "dlg_bg":         "#ffffff",
        "dlg_fg":         "#1f1f1f",
        "dlg_btn_bg":     "#f3f3f3",
        "dlg_btn_fg":     "#1f1f1f",
        "dlg_btn_hov":    "#e5e5e5",
        "dlg_btn_prs":    "#d0d0d0",
        "dlg_chk_bg":     "#f0f0f0",
        "dlg_chk_fg":     "#1f1f1f",
        "dlg_border":     "#dcdcdc",
        "ctrl_bg":        "#ffffff",
        "ctrl_fg":        "#1f1f1f",
        "ctrl_border":    "#bdbdbd",
        "ctrl_sel":       "#0078d4",
        "ctrl_sel_fg":    "#ffffff",
        "icon_tint":      "rgba(0,0,0,30)",
    },
    "dark": {
        "menu_bg":        "#252526",
        "menu_border":    "#3f3f46",
        "menu_item_sel":  "#094771",
        "menu_item_txt":  "#cccccc",
        "menu_sep":       "#3f3f46",
        "dlg_bg":         "#2d2d30",
        "dlg_fg":         "#cccccc",
        "dlg_btn_bg":     "#3d3d42",
        "dlg_btn_fg":     "#cccccc",
        "dlg_btn_hov":    "#4d4d52",
        "dlg_btn_prs":    "#5d5d62",
        "dlg_chk_bg":     "#333337",
        "dlg_chk_fg":     "#cccccc",
        "dlg_border":     "#3f3f46",
        "ctrl_bg":        "#333337",
        "ctrl_fg":        "#cccccc",
        "ctrl_border":    "#555555",
        "ctrl_sel":       "#0078d4",
        "ctrl_sel_fg":    "#ffffff",
        "icon_tint":      "rgba(255,255,255,25)",
    },
}


def _build_menu_qss(palette: dict) -> str:
    return f"""
QMenu {{
    background-color: {palette["menu_bg"]};
    border: 1px solid {palette["menu_border"]};
    border-radius: 6px;
    padding: 6px;
}}
QMenu::item {{
    padding: 8px 32px 8px 14px;
    border-radius: 4px;
    color: {palette["menu_item_txt"]};
}}
QMenu::item:selected {{
    background-color: {palette["menu_item_sel"]};
}}
QMenu::item:disabled {{
    color: #888888;
}}
QMenu::separator {{
    height: 1px;
    background: {palette["menu_sep"]};
    margin: 6px 10px;
}}
"""


def _build_dlg_qss(palette: dict) -> str:
    # NOTE: Qt style sheets do NOT support CSS `!important`; colour declarations
    # must be plain `color: ...` (widget-level stylesheet wins over app-level
    # and over the system palette).
    return f"""
QDialog {{
    background-color: {palette["dlg_bg"]};
}}
QPushButton {{
    background-color: {palette["dlg_btn_bg"]};
    color: {palette["dlg_btn_fg"]};
    border: 1px solid {palette["dlg_border"]};
    border-radius: 4px;
    padding: 6px 16px;
    min-width: 70px;
}}
QPushButton:hover {{
    background-color: {palette["dlg_btn_hov"]};
}}
QPushButton:pressed {{
    background-color: {palette["dlg_btn_prs"]};
}}
QPushButton:default {{
    background-color: {palette["ctrl_sel"]};
    color: {palette["ctrl_sel_fg"]};
    border-color: {palette["ctrl_sel"]};
}}
QLabel {{
    color: {palette["dlg_fg"]};
}}
QCheckBox {{
    spacing: 6px;
    color: {palette["dlg_chk_fg"]};
}}
QCheckBox::indicator {{
    width: 16px; height: 16px;
    border: 1px solid {palette["ctrl_border"]};
    border-radius: 3px;
    background: {palette["ctrl_bg"]};
}}
QCheckBox::indicator:checked {{
    background-color: {palette["ctrl_sel"]};
    border-color: {palette["ctrl_sel"]};
}}
QRadioButton {{
    spacing: 6px;
    color: {palette["dlg_chk_fg"]};
}}
QComboBox {{
    background-color: {palette["ctrl_bg"]};
    color: {palette["ctrl_fg"]};
    border: 1px solid {palette["ctrl_border"]};
    border-radius: 4px;
    padding: 4px 10px;
    min-width: 90px;
}}
QComboBox::dropDown {{
    border: none;
}}
QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {palette["ctrl_fg"]};
    margin-right: 4px;
}}
QComboBox QAbstractItemView {{
    background-color: {palette["ctrl_bg"]};
    color: {palette["ctrl_fg"]};
    selection-background-color: {palette["ctrl_sel"]};
    selection-color: {palette["ctrl_sel_fg"]};
    border: 1px solid {palette["ctrl_border"]};
}}
"""

_current_theme: str = "light"


def current_theme() -> str:
    return _current_theme


def _effective_theme() -> str:
    pref = _read_theme_pref()
    return pref if pref else _read_system_theme()


def apply_theme(theme: Optional[str] = None,
                app: Optional[QApplication] = None) -> None:
    global _current_theme
    if theme is None:
        theme = _effective_theme()
    else:
        _write_theme_pref(theme)
    _current_theme = theme
    palette = _THEMES[theme]
    menu_qss = _build_menu_qss(palette)
    dlg_qss  = _build_dlg_qss(palette)
    if app is None:
        app = QApplication.instance()
    if app is not None:
        # App-level QSS so new dialogs/menus pick up the theme automatically.
        # The settings dialog additionally carries its own widget-level QSS
        # (set in SettingsDialog.__init__) which wins over this one, and is
        # refreshed below when the theme changes.
        app.setStyleSheet(dlg_qss)
    for p in controller.pets:
        for child in p.children():
            if isinstance(child, QMenu):
                child.setStyleSheet(menu_qss)
    # Update already-open settings dialog so theme switch is instant
    if _settings_dialog is not None and _settings_dialog.isVisible():
        _settings_dialog.setStyleSheet(dlg_qss)
    _update_tray_icon(palette["icon_tint"])


def _tint_pixmap(pix: QPixmap, tint: str) -> QPixmap:
    import re
    m = re.search(r'rgba\((\d+),(\d+),(\d+),(\d+)\)', tint)
    if not m:
        return pix
    r2, g2, b2, a2 = int(m[1]), int(m[2]), int(m[3]), int(m[4])
    result = pix.copy()
    painter = QPainter(result)
    painter.setCompositionMode(QPainter.CompositionMode_SourceAtop)
    painter.fillRect(result.rect(), QColor(r2, g2, b2, a2))
    painter.end()
    return result


_tray_icon_refs: list = []


def _update_tray_icon(tint: str) -> None:
    global _tray_icon_refs
    # QPixmap requires a QGuiApplication; skip if we're still in pre-app init
    if QApplication.instance() is None:
        return
    # Tray icon uses the app icon (colored round icon); tint no longer applied
    idle_raw = QPixmap(str(ASSETS / "tray_icon.png"))
    if idle_raw.isNull():
        idle_raw = QPixmap(str(ASSETS / "pet_idle.png"))
        idle_raw = _tint_pixmap(idle_raw, tint)
    _tray_icon_refs.append(idle_raw)
    tray = getattr(app_ref, "tray", None)
    if tray is not None:
        tray.setIcon(idle_raw)


app_ref = type("", (), {"tray": None})()


def apply_menu_style(menu: QMenu) -> None:
    """Apply the current theme's menu style to a popup menu."""
    palette = _THEMES[_current_theme]
    menu.setStyleSheet(_build_menu_qss(palette))


# --- Autostart (registry) -----------------------------------------------------

_AUTOSTART_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_AUTOSTART_NAME = "DesktopPet"


def _autostart_key(mode: int):
    return winreg.OpenKey(winreg.HKEY_CURRENT_USER, _AUTOSTART_KEY, 0, mode)


def is_autostart() -> bool:
    try:
        with _autostart_key(winreg.KEY_QUERY_VALUE) as key:
            winreg.QueryValueEx(key, _AUTOSTART_NAME)
        return True
    except OSError:
        return False


def set_autostart(enabled: bool) -> bool:
    """Add/remove this program to the current user's Run key."""
    try:
        if enabled:
            exe = os.path.normpath(sys.executable)
            with _autostart_key(winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, _AUTOSTART_NAME, 0, winreg.REG_SZ, f'"{exe}"')
        else:
            try:
                with _autostart_key(winreg.KEY_SET_VALUE) as key:
                    winreg.DeleteValue(key, _AUTOSTART_NAME)
            except FileNotFoundError:
                pass
        return True
    except OSError:
        return False


# --- Feed cooldown -------------------------------------------------------------

FEED_COOLDOWN_MS = 10 * 60 * 1000   # 10 minutes

# --- Idle wandering ------------------------------------------------------------

# How often (ms) an idle pet re-picks a fresh slow direction on its own.
IDLE_REDIR_MS = 2600.0
# Idle speed as a fraction of the pet's max speed (kept slow + gentle).
IDLE_SPEED_MIN = 0.20
IDLE_SPEED_MAX = 0.35

# Speed (px/s) used when chasing the mouse cursor.
FOLLOW_SPEED = 280.0

# --- Sprite loading -----------------------------------------------------------

def load_walk_frames():
    """Load right-facing and left-facing walk strips; each cell is a square."""
    def load(name: str) -> List[QPixmap]:
        strip = QPixmap(str(ASSETS / name))
        frames: List[QPixmap] = []
        if strip.isNull():
            return frames
        n = strip.width() // strip.height()
        for i in range(n):
            frames.append(strip.copy(i * strip.height(), 0, strip.height(), strip.height()))
        return frames
    return load("pet_walk.png"), load("pet_walk_left.png")


WALK_FRAMES: List[QPixmap] = []    # right-facing walk frames
WALK_FRAMES_L: List[QPixmap] = []  # left-facing walk frames
IDLE_FRAME: Optional[QPixmap] = None  # front-facing standing pose
FRAME_SIZE = 256  # updated when frames load


# --- Speech bubble -----------------------------------------------------------

class SpeechBubble(QWidget):
    """One speech bubble per pet — avoids cross-pet bubble bleed."""

    def __init__(self, parent: "Pet") -> None:
        super().__init__(parent)
        self.setWindowFlags(
            Qt.Tool
            | Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self._pet = parent
        self._label = QLabel("", self)
        self._label.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        self._label.setStyleSheet(
            "color: #222; background-color: rgba(255,255,255,220); "
            "padding: 6px 10px; border-radius: 10px;"
        )
        self._label.adjustSize()

    def set_text(self, text: str, emoji: str = "") -> None:
        if emoji:
            self._label.setText(emoji)
        else:
            self._label.setText(text)
        self._label.adjustSize()
        sz = self._label.sizeHint()
        self.resize(sz.width() + 20, sz.height() + 20)
        self._label.move(10, 10)
        self._label.resize(self.width() - 20, self.height() - 20)
        self._reposition()

    def _reposition(self) -> None:
        """Position bubble directly above the pet on screen (absolute coords)."""
        pet_rect = self._pet.current_rect()
        x = pet_rect.center().x() - self.width() / 2
        y = pet_rect.top() - self.height() - 6
        self.move(int(x), int(y))

    def show(self) -> None:
        self._reposition()
        super().show()

    def hide(self) -> None:
        super().hide()


# --- The pet widget -----------------------------------------------------------

class Pet(QWidget):
    """One crawling pet window. Click-through except on right-click."""

    # Movement modes
    MODE_IDLE = "idle"   # stand still-ish, slowly drift, face front
    MODE_WALK = "walk"   # directed horizontal walk, bounces at edges
    MODE_FOLLOW = "follow"  # chase the mouse cursor

    # Class-level cache for virtual desktop rect (shared across all pets)
    _screen_cache: Optional[QRectF] = None
    _screen_cache_ms: float = -100000.0

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(
            Qt.Tool
            | Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)

        # Geometry
        self._scale = 0.5
        self._frame_index = 0
        self._frame_accum = 0.0
        self._frame_period_ms = 130.0

        # Off-screen backbuffer
        self._off_buf: QPixmap = QPixmap()

        # Physics
        self._pos = QPointF(200.0, 200.0)
        self._vel = QPointF(0.0, 0.0)
        self._max_speed = 70.0
        self._target_dir_timer = 0
        self._target: Optional[QPointF] = None  # gather/scatter seek target (top-left)
        self._facing = 1          # +1 = facing right, -1 = facing left (hysteresis)
        self._follow_index = 0       # index among pets, for swarm spread around cursor
        self._follow_phase = 0.0     # rotating angle on the swarm ring
        self._follow_dir = 1          # +1/-1 orbit direction when loitering at cursor

        # Movement mode
        self._mode = Pet.MODE_IDLE
        # Mode before follow was enabled (restored when follow is turned off)
        self._mode_before_follow = Pet.MODE_IDLE

        # Left-button drag state
        self._dragging = False
        self._drag_offset = QPointF(0.0, 0.0)
        self._drag_restore_mode = Pet.MODE_IDLE

        # Per-pet speech bubble
        self._speech: Optional[SpeechBubble] = None
        self._speech_timer = QTimer(self)
        self._speech_timer.setSingleShot(True)
        self._speech_timer.timeout.connect(self._clear_speech)

        # Per-pet feed cooldown
        self._last_feed_ms = -FEED_COOLDOWN_MS   # allow immediate feed at start
        self._feed_bounce_timer = QTimer(self)
        self._feed_bounce_timer.setSingleShot(True)
        self._feed_bounce_timer.timeout.connect(self._feed_bounce_end)
        self._feed_scale_before = 0.5

        # Wall-clock for cooldowns
        self._clock = QElapsedTimer()
        self._clock.start()

        # Caches so we don't re-scan the screen / top-level windows every tick
        self._obstacles_cache: List[QRectF] = []
        self._obstacles_cache_ms = -100000

        # Timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(int(self._frame_period_ms))

        self._resize_to_scale()
        self.move(int(self._pos.x()), int(self._pos.y()))

    # --- public ---------------------------------------------------------------

    def set_scale(self, scale: float) -> None:
        self._scale = max(0.15, min(1.6, scale))
        self._resize_to_scale()

    def scale(self) -> float:
        return self._scale

    def current_rect(self) -> QRectF:
        s = FRAME_SIZE * self._scale
        return QRectF(self._pos.x(), self._pos.y(), s, s)

    def mode(self) -> str:
        return self._mode

    def set_mode(self, mode: str) -> None:
        self._mode = mode
        self._target = None
        self._vel = QPointF(0, 0)
        self._frame_index = 0
        self._target_dir_timer = 0
        self.update()

    def is_feed_on_cooldown(self) -> bool:
        elapsed = self._clock.elapsed()
        return (elapsed - self._last_feed_ms) < FEED_COOLDOWN_MS

    def set_speech(self, text: str, emoji: bool = False) -> None:
        if self._speech is None:
            self._speech = SpeechBubble(self)
        if emoji:
            self._speech.set_text("", emoji=text)
        else:
            self._speech.set_text(text)
        self._speech.show()
        self._speech_timer.start(2200)

    def feed(self) -> bool:
        """Feed this pet. Returns True if fed, False if not allowed/on cooldown."""
        # 走动中 / 被拖拽时不能喂食
        if self._mode == Pet.MODE_WALK:
            self.set_speech("走路呢，先不吃了")
            return False
        if self._dragging:
            self.set_speech("别拽我！")
            return False
        if self.is_feed_on_cooldown():
            self.set_speech("我已经吃饱了")
            return False
        self._last_feed_ms = self._clock.elapsed()
        phrases = ["吃饱了", "好饱啊", "嗝~", "再来一碗", "吃撑了", "美味~"]
        self.set_speech(random.choice(phrases))
        self._feed_scale_before = self.scale()
        self.set_scale(min(1.5, self.scale() + 0.08))
        self._feed_bounce_timer.start(3000)
        return True

    # --- internal -------------------------------------------------------------

    def _resize_to_scale(self) -> None:
        s = int(FRAME_SIZE * self._scale)
        self.resize(s, s)
        self._off_buf = QPixmap(s, s)
        self._max_speed = 40 + 80 * self._scale

    def _feed_bounce_end(self) -> None:
        self.set_scale(self._feed_scale_before)

    def _clear_speech(self) -> None:
        if self._speech is not None:
            self._speech.hide()

    def _pick_walk_direction(self, screen_rect: QRectF) -> None:
        """Pick a purely horizontal direction (left or right)."""
        if random.random() < 0.5:
            self._vel = QPointF(-self._max_speed * random.uniform(0.6, 1.0), 0)
            self._facing = -1
        else:
            self._vel = QPointF(self._max_speed * random.uniform(0.6, 1.0), 0)
            self._facing = 1

    def _pick_idle_direction(self) -> None:
        """Pick a fresh slow direction at a random angle (omni-directional)."""
        ang = random.uniform(0, 2 * math.pi)
        sp = self._max_speed * random.uniform(IDLE_SPEED_MIN, IDLE_SPEED_MAX)
        self._vel = QPointF(math.cos(ang) * sp, math.sin(ang) * sp)

    def _bounce(self, new_pos: QPointF, w: float, h: float,
                screen: QRectF, obstacles: List[QRectF]) -> bool:
        """Resolve collisions with screen edges and window obstacles in place.

        Reflects self._vel and clamps new_pos. Returns True if a bounce happened.
        """
        bounced = False

        # Screen edges (all four sides)
        if new_pos.x() + w > screen.right():
            new_pos.setX(screen.right() - w)
            self._vel.setX(-abs(self._vel.x()))
            bounced = True
        elif new_pos.x() < screen.left():
            new_pos.setX(screen.left())
            self._vel.setX(abs(self._vel.x()))
            bounced = True
        if new_pos.y() + h > screen.bottom():
            new_pos.setY(screen.bottom() - h)
            self._vel.setY(-abs(self._vel.y()))
            bounced = True
        elif new_pos.y() < screen.top():
            new_pos.setY(screen.top())
            self._vel.setY(abs(self._vel.y()))
            bounced = True

        # Window obstacles
        moved = QRectF(new_pos.x(), new_pos.y(), w, h)
        for ob in obstacles:
            if not moved.intersects(ob):
                continue
            ix = min(moved.right() - ob.left(), ob.right() - moved.left())
            iy = min(moved.bottom() - ob.top(), ob.bottom() - moved.top())
            if ix <= iy:
                if moved.center().x() < ob.center().x():
                    new_pos.setX(ob.left() - w)
                else:
                    new_pos.setX(ob.right())
                self._vel.setX(-self._vel.x())
            else:
                if moved.center().y() < ob.center().y():
                    new_pos.setY(ob.top() - h)
                else:
                    new_pos.setY(ob.bottom())
                self._vel.setY(-self._vel.y())
            bounced = True

        return bounced

    def _step_walk(self, dt: float, screen: QRectF, obstacles: List[QRectF]) -> None:
        if self._vel.isNull():
            self._pick_walk_direction(screen)
        w, h = self.current_rect().width(), self.current_rect().height()
        new_pos = QPointF(self._pos.x() + self._vel.x() * dt,
                          self._pos.y() + self._vel.y() * dt)
        bounced = self._bounce(new_pos, w, h, screen, obstacles)
        if bounced:
            self._target_dir_timer = 0
        self._pos = new_pos
        self.move(int(self._pos.x()), int(self._pos.y()))

    def _step_idle(self, dt: float, screen: QRectF, obstacles: List[QRectF]) -> None:
        self._target_dir_timer += self._frame_period_ms
        if self._vel.isNull() or self._target_dir_timer > IDLE_REDIR_MS:
            self._pick_idle_direction()
            self._target_dir_timer = 0
        w, h = self.current_rect().width(), self.current_rect().height()
        new_pos = QPointF(self._pos.x() + self._vel.x() * dt,
                          self._pos.y() + self._vel.y() * dt)
        bounced = self._bounce(new_pos, w, h, screen, obstacles)
        if bounced:
            self._pick_idle_direction()
            self._target_dir_timer = 0
        self._pos = new_pos
        self.move(int(self._pos.x()), int(self._pos.y()))

    def _step_toward(self, target: QPointF, dt: float, speed: float,
                     screen: QRectF, obstacles: List[QRectF]) -> None:
        dx = target.x() - self._pos.x()
        dy = target.y() - self._pos.y()
        mag = math.hypot(dx, dy)
        if mag <= max(4.0, speed * dt):
            # Close enough, or a full step would overshoot the target: snap to it
            # and stop. Snapping (instead of oscillating around the target) is what
            # fixes the gather bug where pets flipped facing back and forth.
            self._pos = QPointF(target.x(), target.y())
            self._target = None
            self._vel = QPointF(0.0, 0.0)
            self.move(int(self._pos.x()), int(self._pos.y()))
            return
        self._vel = QPointF(dx / mag * speed, dy / mag * speed)
        w, h = self.current_rect().width(), self.current_rect().height()
        new_pos = QPointF(self._pos.x() + self._vel.x() * dt,
                          self._pos.y() + self._vel.y() * dt)
        self._bounce(new_pos, w, h, screen, obstacles)
        self._pos = new_pos
        self.move(int(self._pos.x()), int(self._pos.y()))

    def _step_follow(self, dt: float, screen: QRectF, obstacles: List[QRectF]) -> None:
        """Chase the cursor: each pet heads straight for the pointer, arriving at
        a small personal slot on a tight ring around it (so pets don't all stack
        on the exact cursor pixel), then stops and KEEPS FACING the mouse. If the
        mouse moves, the pet resumes chasing; if it keeps moving, the pet keeps
        facing and chasing."""
        cur = QCursor.pos()
        # 紧凑小环：贴近鼠标但不完全重叠
        ring_r = (36.0 + 26.0 * self._follow_index) * self._scale
        ox = math.cos(self._follow_phase) * ring_r
        oy = math.sin(self._follow_phase) * ring_r
        tx = cur.x() - self.width() / 2 + ox
        ty = cur.y() - self.height() / 2 + oy
        dx = tx - self._pos.x()
        dy = ty - self._pos.y()
        mag = math.hypot(dx, dy)
        if mag < 1.5:
            # 已到槽位：完全静止（鼠标不动时稳定停下）
            self._vel = QPointF(0.0, 0.0)
        elif mag < 70.0:
            # 接近槽位：平滑减速跟随——鼠标静止则渐停，鼠标移动则持续追随
            sp = min(FOLLOW_SPEED, mag * 4.0)
            self._vel = QPointF(dx / mag * sp, dy / mag * sp)
        else:
            self._vel = QPointF(dx / mag * FOLLOW_SPEED, dy / mag * FOLLOW_SPEED)
        # 面向鼠标：以鼠标相对位置为准（追的过程中和静止时都保持面向）
        mx = cur.x() - (self._pos.x() + self.width() / 2)
        if abs(mx) > 3.0:
            self._facing = 1 if mx > 0 else -1
        w, h = self.current_rect().width(), self.current_rect().height()
        new_pos = QPointF(self._pos.x() + self._vel.x() * dt,
                          self._pos.y() + self._vel.y() * dt)
        self._bounce(new_pos, w, h, screen, obstacles)
        self._pos = new_pos
        self.move(int(self._pos.x()), int(self._pos.y()))

    def _tick(self) -> None:
        # 拖拽中：完全静止（不移动、不换帧）
        if self._dragging:
            return
        screen = self._screen_rect()
        obstacles = self._obstacle_rects()
        dt = self._frame_period_ms / 1000.0

        if self._target is not None:
            self._step_toward(self._target, dt, 220.0, screen, obstacles)
        elif self._mode == Pet.MODE_FOLLOW:
            self._step_follow(dt, screen, obstacles)
        elif self._mode == Pet.MODE_WALK:
            self._step_walk(dt, screen, obstacles)
        else:
            self._step_idle(dt, screen, obstacles)

        # Facing hysteresis: only flip when there's a real horizontal velocity,
        # so near-vertical approaches don't flicker left/right every frame.
        if abs(self._vel.x()) > 3.0:
            self._facing = 1 if self._vel.x() > 0 else -1

        # Advance animation frame (only when actually moving)
        # Follow mode also animates while chasing so the pet visibly walks toward
        # the mouse instead of sliding in a fixed pose.
        moving = (abs(self._vel.x()) > 0.1 or abs(self._vel.y()) > 0.1)
        if moving and self._mode in (Pet.MODE_WALK, Pet.MODE_FOLLOW):
            self._frame_accum += self._frame_period_ms
            if self._frame_accum >= self._frame_period_ms:
                n = len(WALK_FRAMES) if WALK_FRAMES else 0
                if n > 0:
                    self._frame_index = (self._frame_index + 1) % n
                self._frame_accum = 0
        # move() alone does NOT trigger paintEvent for frameless/transparent
        # windows, so we must explicitly request a repaint every tick.
        self.update()

    # --- geometry helpers -----------------------------------------------------

    @staticmethod
    def _virtual_rect() -> QRectF:
        """Union of every screen's available geometry = the whole virtual desktop,
        so pets can roam and appear across ALL monitors, not just the primary."""
        now = time.time() * 1000.0
        if Pet._screen_cache is not None and now - Pet._screen_cache_ms <= 1000:
            return Pet._screen_cache
        screens = QApplication.screens()
        if not screens:
            rect = QRectF(0, 0, 1920, 1080)
        else:
            r = screens[0].availableGeometry()
            for sc in screens[1:]:
                r = r.united(sc.availableGeometry())
            rect = QRectF(r.x(), r.y(), r.width(), r.height())
        Pet._screen_cache = rect
        Pet._screen_cache_ms = now
        return rect

    def _screen_rect(self) -> QRectF:
        return Pet._virtual_rect()

    def _obstacle_rects(self) -> List[QRectF]:
        now = self._clock.elapsed()
        if now - self._obstacles_cache_ms <= 400:
            return self._obstacles_cache
        rects: List[QRectF] = []
        for w in QApplication.topLevelWidgets():
            if w is self or isinstance(w, Pet):
                continue
            if not w.isVisible():
                continue
            if isinstance(w, (SpeechBubble,)):
                continue
            try:
                w.winId()
            except Exception:
                continue
            geo = w.frameGeometry()
            if geo.width() < 50 or geo.height() < 50:
                continue
            if w.isMinimized():
                continue
            if w.windowType() in (Qt.Tool, Qt.SplashScreen):
                continue
            rects.append(QRectF(geo))
        self._obstacles_cache = rects
        self._obstacles_cache_ms = now
        return rects

    # --- painting -------------------------------------------------------------

    def paintEvent(self, _event) -> None:
        if not WALK_FRAMES:
            return

        buf = self._off_buf
        buf.fill(Qt.transparent)
        buf_painter = QPainter(buf)
        # SmoothPixmapTransform keeps the sprite crisp when scaled; Antialiasing
        # is dropped (negligible for a small cartoon sprite, saves a repaint).
        buf_painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        # Idle: front-facing pose; Walk: side-view
        # Follow mode: while CHASING the mouse the pet shows the walk animation
        # (side frames, facing the mouse). Once it has arrived and is standing
        # still, always show the front-facing pose — a frozen side profile looks
        # wrong next to the pointer.
        vertical_follow = False
        if self._mode == Pet.MODE_FOLLOW:
            moving = (abs(self._vel.x()) > 0.1 or abs(self._vel.y()) > 0.1)
            vertical_follow = not moving
        if (self._mode == Pet.MODE_IDLE or vertical_follow) and IDLE_FRAME is not None:
            buf_painter.drawPixmap(buf.rect(), IDLE_FRAME)
        else:
            frames = WALK_FRAMES_L if self._facing < 0 else WALK_FRAMES
            if frames:
                buf_painter.drawPixmap(buf.rect(), frames[self._frame_index % len(frames)])

        buf_painter.end()

        painter = QPainter(self)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        painter.drawPixmap(self.rect(), buf)

    # --- input ----------------------------------------------------------------

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        # 左键长按拖拽（跟随模式下禁止拖拽）
        if event.button() == Qt.LeftButton and self._mode != Pet.MODE_FOLLOW:
            self._dragging = True
            self._drag_restore_mode = self._mode
            gpos = event.globalPosition()
            self._drag_offset = QPointF(gpos.x() - self._pos.x(),
                                        gpos.y() - self._pos.y())
            self._vel = QPointF(0.0, 0.0)
            self._target = None
            # 拖拽期间停掉 tick，人物完全静止
            self._timer.stop()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        if self._dragging and (event.buttons() & Qt.LeftButton):
            gpos = event.globalPosition()
            self._pos = QPointF(gpos.x() - self._drag_offset.x(),
                                gpos.y() - self._drag_offset.y())
            # 拖拽时也限制在虚拟桌面内，避免拖出屏幕找不到
            screen = Pet._virtual_rect()
            w, h = self.current_rect().width(), self.current_rect().height()
            x = max(screen.left(), min(self._pos.x(), screen.right() - w))
            y = max(screen.top(), min(self._pos.y(), screen.bottom() - h))
            self._pos = QPointF(x, y)
            self.move(int(self._pos.x()), int(self._pos.y()))
            # move() 不触发无边框透明窗口重绘，需显式刷新
            self.update()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        if self._dragging and event.button() == Qt.LeftButton:
            self._dragging = False
            if QApplication.instance() is not None:
                self._timer.start()
            # 恢复拖拽前的状态（idle 回待机、walk 继续走）
            self.set_mode(self._drag_restore_mode)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent) -> None:
        # Pause this pet's animation while its menu is open, so the popup shows
        # without a competing repaint hitch (the "右键卡一下" stutter).
        self._timer.stop()
        menu = build_context_menu(self)
        menu.aboutToHide.connect(self._resume_after_menu)
        menu.exec(event.globalPos())

    def _resume_after_menu(self) -> None:
        if not controller.paused and QApplication.instance() is not None:
            self._timer.start()


# --- Menu & controller ------------------------------------------------------

class PetController:
    def __init__(self) -> None:
        self.pets: List[Pet] = []
        self.paused: bool = False
        self.size_label_to_scale = {
            "小 (50%)": 0.30,
            "中 (75%)": 0.45,
            "大 (100%)": 0.55,
            "巨大 (150%)": 0.85,
        }

    def spawn(self, count: int) -> None:
        screen = Pet._virtual_rect()
        for _ in range(count):
            pet = Pet()
            x = screen.x() + random.uniform(50, screen.width() - 200)
            y = screen.y() + random.uniform(50, screen.height() - 200)
            pet._pos = QPointF(x, y)
            pet.set_mode(Pet.MODE_IDLE)
            pet.move(int(x), int(y))
            pet.show()
            self.pets.append(pet)

    def remove_all(self) -> None:
        for p in self.pets:
            p.hide()
            p.deleteLater()
        self.pets.clear()

    def set_count(self, count: int) -> None:
        while len(self.pets) < count:
            self.spawn(1)
        while len(self.pets) > count:
            p = self.pets.pop()
            p.hide()
            p.deleteLater()

    def set_size(self, scale: float) -> None:
        for p in self.pets:
            p.set_scale(scale)

    def set_mode_all(self, mode: str) -> None:
        for p in self.pets:
            p.set_mode(mode)

    def toggle_walk(self) -> None:
        """Toggle all pets between idle and walk."""
        if all(p.mode() == Pet.MODE_WALK for p in self.pets):
            self.set_mode_all(Pet.MODE_IDLE)
        else:
            self.set_mode_all(Pet.MODE_WALK)

    def toggle_follow(self) -> None:
        """Toggle all pets between following the cursor and their previous mode.

        When follow is turned ON, each pet remembers its current mode; when it is
        turned OFF, each pet is restored to that remembered mode (idle pets go
        back to idle, walking pets keep walking)."""
        if self.pets and all(p.mode() == Pet.MODE_FOLLOW for p in self.pets):
            for p in self.pets:
                p.set_mode(getattr(p, "_mode_before_follow", Pet.MODE_IDLE))
        else:
            n = len(self.pets)
            for i, p in enumerate(self.pets):
                p._follow_index = i
                p._follow_phase = (2.0 * math.pi * i) / n if n else 0.0
                p._follow_dir = 1 if i % 2 == 0 else -1
                p._mode_before_follow = p.mode()
                p.set_mode(Pet.MODE_FOLLOW)

    def set_follow(self, enabled: bool) -> None:
        """Force follow mode on/off (idempotent, used by the settings dialog)."""
        following = bool(self.pets) and all(p.mode() == Pet.MODE_FOLLOW for p in self.pets)
        if enabled and not following:
            self.toggle_follow()
        elif not enabled and following:
            self.toggle_follow()

    def set_click_through(self, enabled: bool) -> None:
        """Let mouse events pass through the pet windows (interaction then happens
        via the tray icon menu)."""
        for p in self.pets:
            p.setAttribute(Qt.WA_TransparentForMouseEvents, enabled)

    def feed_one(self, pet: Pet) -> None:
        pet.feed()

    def feed_all(self) -> None:
        for p in self.pets:
            p.feed()

    def gather(self) -> None:
        screen = QApplication.primaryScreen().availableGeometry()
        cx = screen.x() + screen.width() / 2
        cy = screen.y() + screen.height() / 2
        if not self.pets:
            return
        for i, p in enumerate(self.pets):
            angle = (2 * math.pi * i) / len(self.pets)
            tx = cx + math.cos(angle) * 120 - p.width() / 2
            ty = cy + math.sin(angle) * 120 - p.height() / 2
            p._target = QPointF(tx, ty)

    def scatter(self) -> None:
        screen = QApplication.primaryScreen().availableGeometry()
        corners = [
            (screen.x() + 80, screen.y() + 80),
            (screen.x() + screen.width() - 200, screen.y() + 80),
            (screen.x() + 80, screen.y() + screen.height() - 200),
            (screen.x() + screen.width() - 200, screen.y() + screen.height() - 200),
        ]
        for i, p in enumerate(self.pets):
            tx, ty = corners[i % 4]
            tx -= p.width() / 2
            ty -= p.height() / 2
            p._target = QPointF(tx, ty)

    def toggle_pause(self) -> None:
        self.paused = not self.paused
        for p in self.pets:
            if self.paused:
                p._timer.stop()
            else:
                p._timer.start()


controller = PetController()


def _walk_label() -> str:
    is_walking = bool(controller.pets) and all(
        p.mode() == Pet.MODE_WALK for p in controller.pets
    )
    return "停止 ■" if is_walking else "走动 ▶"


def build_context_menu(pet: Pet) -> QMenu:
    menu = QMenu()
    apply_menu_style(menu)

    # Size submenu
    size_menu = menu.addMenu("调整大小")
    apply_menu_style(size_menu)
    size_group = QActionGroup(size_menu)
    size_group.setExclusive(True)
    for label, scale in controller.size_label_to_scale.items():
        act = QAction(label, size_menu)
        act.setCheckable(True)
        act.setChecked(abs(pet.scale() - scale) < 0.05)
        act.triggered.connect(lambda _c=False, s=scale: controller.set_size(s))
        size_group.addAction(act)
        size_menu.addAction(act)

    # Count submenu
    count_menu = menu.addMenu("切换数量")
    apply_menu_style(count_menu)
    count_group = QActionGroup(count_menu)
    count_group.setExclusive(True)
    for n in (1, 3, 5, 8):
        act = QAction(f"{n} 只", count_menu)
        act.setCheckable(True)
        act.setChecked(len(controller.pets) == n)
        act.triggered.connect(lambda _c=False, c=n: controller.set_count(c))
        count_group.addAction(act)
        count_menu.addAction(act)

    menu.addSeparator()

    # 走动 toggle
    walk_act = QAction(_walk_label(), menu)
    walk_act.setCheckable(True)
    is_walking = all(p.mode() == Pet.MODE_WALK for p in controller.pets)
    walk_act.setChecked(is_walking)
    walk_act.triggered.connect(lambda: controller.toggle_walk())
    menu.addAction(walk_act)

    # 跟随鼠标 toggle
    follow_act = QAction("跟随鼠标 🖱", menu)
    follow_act.setCheckable(True)
    is_following = bool(controller.pets) and all(
        p.mode() == Pet.MODE_FOLLOW for p in controller.pets
    )
    follow_act.setChecked(is_following)
    follow_act.triggered.connect(lambda: controller.toggle_follow())
    menu.addAction(follow_act)

    menu.addSeparator()

    # 喂饭（每只独立冷却；吃饱/走动中/被拖拽时禁用并标注）
    feed_act = QAction(menu)
    if pet.is_feed_on_cooldown():
        feed_act.setText("喂饭 🍚 (已吃饱)")
        feed_act.setEnabled(False)
    elif pet.mode() == Pet.MODE_WALK:
        feed_act.setText("喂饭 🍚 (走动中)")
        feed_act.setEnabled(False)
    elif pet._dragging:
        feed_act.setText("喂饭 🍚 (拖拽中)")
        feed_act.setEnabled(False)
    else:
        feed_act.setText("喂饭 🍚")
        feed_act.triggered.connect(lambda: controller.feed_one(pet))
    menu.addAction(feed_act)

    menu.addSeparator()

    menu.addAction("聚拢").triggered.connect(controller.gather)
    menu.addAction("分散").triggered.connect(controller.scatter)

    menu.addSeparator()

    pause_act = menu.addAction("暂停 / 继续")
    pause_act.setCheckable(True)
    pause_act.setChecked(controller.paused)
    pause_act.triggered.connect(lambda _c: controller.toggle_pause())

    menu.addSeparator()
    menu.addAction("设置… ⚙").triggered.connect(open_settings)
    menu.addAction("退出程序").triggered.connect(QApplication.instance().quit)

    return menu


# --- System tray ------------------------------------------------------------

def build_tray(app: QApplication) -> QSystemTrayIcon:
    tray = QSystemTrayIcon()
    idle_icon = QPixmap(str(ASSETS / "tray_icon.png"))
    if idle_icon.isNull():
        idle_icon = QPixmap(str(ASSETS / "pet_idle.png"))
    idle_icon = idle_icon.scaled(
        64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation
    )
    tray.setIcon(idle_icon)
    tray.setToolTip("桌面宠物 — 右键点击宠物进行操作")

    def tray_menu() -> QMenu:
        m = QMenu()
        apply_menu_style(m)
        # 所有宠物都在走动/被拖拽时，一键喂饭置灰
        all_busy = bool(controller.pets) and all(
            p.mode() == Pet.MODE_WALK or p._dragging for p in controller.pets
        )
        if all_busy:
            feed_all_act = QAction("一键喂饭 🍚 (忙碌中)", m)
            feed_all_act.setEnabled(False)
            m.addAction(feed_all_act)
        else:
            m.addAction("一键喂饭 🍚").triggered.connect(controller.feed_all)
        walk_act = QAction(_walk_label(), m)
        walk_act.setCheckable(True)
        is_walking = all(p.mode() == Pet.MODE_WALK for p in controller.pets)
        walk_act.setChecked(is_walking)
        walk_act.triggered.connect(lambda: controller.toggle_walk())
        m.addAction(walk_act)
        follow_act = QAction("跟随鼠标 🖱", m)
        follow_act.setCheckable(True)
        is_following = bool(controller.pets) and all(
            p.mode() == Pet.MODE_FOLLOW for p in controller.pets
        )
        follow_act.setChecked(is_following)
        follow_act.triggered.connect(lambda: controller.toggle_follow())
        m.addAction(follow_act)
        m.addSeparator()
        m.addAction("聚拢").triggered.connect(controller.gather)
        m.addAction("分散").triggered.connect(controller.scatter)
        m.addSeparator()
        m.addAction("设置… ⚙").triggered.connect(open_settings)
        m.addAction("退出程序").triggered.connect(app.quit)
        return m

    def on_activated(reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            m = tray_menu()
            apply_menu_style(m)
            m.exec(QCursor.pos())

    tray.activated.connect(on_activated)
    tray.setContextMenu(tray_menu())
    tray.show()
    return tray


# --- Settings dialog ----------------------------------------------------------

_settings_dialog: Optional[QtWidgets.QDialog] = None


def open_settings() -> None:
    """Show the settings dialog (single instance, modal, centered on the cursor)."""
    global _settings_dialog
    if _settings_dialog is not None and _settings_dialog.isVisible():
        _settings_dialog.raise_()
        _settings_dialog.activateWindow()
        return
    _settings_dialog = SettingsDialog()
    _settings_dialog.show()


class SettingsDialog(QtWidgets.QDialog):
    """Window with the everyday controls: movement, follow, pause, feed,
    gather/scatter, pet count/size, click-through and autostart."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("桌面宠物 — 设置")
        self.setMinimumWidth(380)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.setWindowIcon(QIcon(str(ASSETS / "app.ico")))
        self._loading = False
        # Widget-level stylesheet: wins over app-level QSS and the system
        # palette, so text stays readable in both light and dark themes.
        self.setStyleSheet(_build_dlg_qss(_THEMES[_current_theme]))

        lay = QtWidgets.QVBoxLayout(self)
        lay.setSpacing(8)

        # ── 外观 ──────────────────────────────────────────────────────────────
        self.theme_lbl = QtWidgets.QLabel("主题")
        font = self.theme_lbl.font()
        font.setBold(True)
        font.setPointSize(11)
        self.theme_lbl.setFont(font)
        lay.addWidget(self.theme_lbl)

        self.theme_group = QtWidgets.QButtonGroup(self)
        self.theme_group.setExclusive(True)
        theme_row = QtWidgets.QHBoxLayout()
        theme_row.setSpacing(6)
        self.theme_system = QtWidgets.QRadioButton("跟随系统")
        self.theme_light  = QtWidgets.QRadioButton("浅色模式")
        self.theme_dark   = QtWidgets.QRadioButton("深色模式")
        for rb in (self.theme_system, self.theme_light, self.theme_dark):
            self.theme_group.addButton(rb)
            theme_row.addWidget(rb)
        theme_row.addStretch(1)
        lay.addLayout(theme_row)
        lay.addSpacing(6)

        # ── 行为开关 ──────────────────────────────────────────────────────────
        self.walk_chk   = QtWidgets.QCheckBox("走动 ▶ / 停止 ■")
        self.follow_chk = QtWidgets.QCheckBox("跟随鼠标 🖱")
        self.pause_chk = QtWidgets.QCheckBox("暂停 / 继续")
        self.through_chk = QtWidgets.QCheckBox("点击穿透（宠物不挡鼠标，操作走托盘菜单）")
        for chk in (self.walk_chk, self.follow_chk, self.pause_chk, self.through_chk):
            lay.addWidget(chk)

        # 数量 / 大小
        row1 = QtWidgets.QHBoxLayout()
        row1.addWidget(QtWidgets.QLabel("宠物数量:"))
        self.count_combo = QtWidgets.QComboBox()
        for n in (1, 3, 5, 8):
            self.count_combo.addItem(f"{n} 只", n)
        row1.addWidget(self.count_combo)
        row1.addSpacing(16)
        row1.addWidget(QtWidgets.QLabel("大小:"))
        self.size_combo = QtWidgets.QComboBox()
        for label, scale in controller.size_label_to_scale.items():
            self.size_combo.addItem(label, scale)
        row1.addWidget(self.size_combo)
        row1.addStretch(1)
        lay.addLayout(row1)

        # 动作按钮
        row2 = QtWidgets.QHBoxLayout()
        self.gather_btn = QtWidgets.QPushButton("聚拢")
        self.scatter_btn = QtWidgets.QPushButton("分散")
        self.feed_btn = QtWidgets.QPushButton("一键喂饭 🍚")
        for b in (self.gather_btn, self.scatter_btn, self.feed_btn):
            row2.addWidget(b)
        lay.addLayout(row2)

        # 开机自启
        self.autostart_chk = QtWidgets.QCheckBox("开机自动启动")
        lay.addWidget(self.autostart_chk)

        lay.addSpacing(4)
        row3 = QtWidgets.QHBoxLayout()
        self.quit_btn = QtWidgets.QPushButton("退出程序")
        self.about_btn = QtWidgets.QPushButton("关于")
        close_btn = QtWidgets.QPushButton("关闭")
        close_btn.setDefault(True)
        row3.addWidget(self.quit_btn)
        row3.addStretch(1)
        row3.addWidget(self.about_btn)
        row3.addWidget(close_btn)
        lay.addLayout(row3)

        # 信号
        self.theme_group.buttonClicked.connect(self._on_theme)
        self.walk_chk.toggled.connect(self._on_walk)
        self.follow_chk.toggled.connect(self._on_follow)
        self.pause_chk.toggled.connect(self._on_pause)
        self.through_chk.toggled.connect(self._on_through)
        self.count_combo.currentIndexChanged.connect(self._on_count)
        self.size_combo.currentIndexChanged.connect(self._on_size)
        self.gather_btn.clicked.connect(controller.gather)
        self.scatter_btn.clicked.connect(controller.scatter)
        self.feed_btn.clicked.connect(controller.feed_all)
        self.autostart_chk.toggled.connect(self._on_autostart)
        self.quit_btn.clicked.connect(QApplication.instance().quit)
        self.about_btn.clicked.connect(self._on_about)
        close_btn.clicked.connect(self.accept)

        self._sync()

    def _sync(self) -> None:
        """Refresh controls from live state (suppressing signal loops)."""
        self._loading = True
        # Theme
        pref = _read_theme_pref()
        if pref is None:
            self.theme_system.setChecked(True)
        elif pref == "light":
            self.theme_light.setChecked(True)
        else:
            self.theme_dark.setChecked(True)

        pets = controller.pets
        self.walk_chk.setChecked(bool(pets) and all(p.mode() == Pet.MODE_WALK for p in pets))
        self.follow_chk.setChecked(bool(pets) and all(p.mode() == Pet.MODE_FOLLOW for p in pets))
        self.pause_chk.setChecked(controller.paused)
        self.through_chk.setChecked(bool(pets) and any(
            p.testAttribute(Qt.WA_TransparentForMouseEvents) for p in pets))
        n = len(controller.pets)
        idx = self.count_combo.findData(n)
        if idx >= 0:
            self.count_combo.setCurrentIndex(idx)
        cur = pets[0].scale() if pets else 0.5
        best = min(range(self.size_combo.count()),
                   key=lambda i: abs(float(self.size_combo.itemData(i)) - cur))
        self.size_combo.setCurrentIndex(best)
        self.autostart_chk.setChecked(is_autostart())
        self.feed_btn.setEnabled(not (bool(pets) and all(
            p.mode() == Pet.MODE_WALK or p._dragging for p in pets)))
        self._loading = False

    # --- handlers ---

    def _on_theme(self) -> None:
        if self._loading:
            return
        checked = self.theme_group.checkedButton()
        if checked == self.theme_system:
            apply_theme(None)
        elif checked == self.theme_light:
            apply_theme("light")
        else:
            apply_theme("dark")

    def _on_walk(self, checked: bool) -> None:
        if self._loading:
            return
        controller.set_mode_all(Pet.MODE_WALK if checked else Pet.MODE_IDLE)
        self._refresh_flags()

    def _on_follow(self, checked: bool) -> None:
        if self._loading:
            return
        controller.set_follow(checked)
        self._refresh_flags()

    def _on_pause(self, checked: bool) -> None:
        if self._loading:
            return
        if checked != controller.paused:
            controller.toggle_pause()

    def _on_through(self, checked: bool) -> None:
        if self._loading:
            return
        controller.set_click_through(checked)

    def _on_count(self, idx: int) -> None:
        if self._loading:
            return
        n = self.count_combo.itemData(idx)
        if n is None:
            return
        controller.set_count(int(n))
        self._refresh_flags()

    def _on_size(self, idx: int) -> None:
        if self._loading:
            return
        s = self.size_combo.itemData(idx)
        if s is None:
            return
        controller.set_size(float(s))

    def _on_autostart(self, checked: bool) -> None:
        if self._loading:
            return
        if not set_autostart(checked):
            QtWidgets.QMessageBox.warning(self, "桌面宠物", "无法写入开机自启注册表项。")

    def _refresh_flags(self) -> None:
        """Keep walk/follow/pause/feed states consistent after a mode change."""
        self._loading = True
        pets = controller.pets
        self.walk_chk.setChecked(bool(pets) and all(p.mode() == Pet.MODE_WALK for p in pets))
        self.follow_chk.setChecked(bool(pets) and all(p.mode() == Pet.MODE_FOLLOW for p in pets))
        self.feed_btn.setEnabled(not (bool(pets) and all(
            p.mode() == Pet.MODE_WALK or p._dragging for p in pets)))
        self._loading = False

    def _on_about(self) -> None:
        """Show the about dialog."""
        icon = QPixmap(str(ASSETS / "app_icon.png"))
        if icon.isNull():
            icon = QPixmap(str(ASSETS / "pet_idle.png"))
        icon_small = icon.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        lbl_icon = QtWidgets.QLabel()
        lbl_icon.setPixmap(icon_small)
        lbl_icon.setFixedSize(64, 64)

        title = QtWidgets.QLabel("桌面宠物")
        title.setFont(QtGui.QFont("微软雅黑", 14, QtGui.QFont.Bold))

        version = QtWidgets.QLabel("版本 1.0")
        desc = QtWidgets.QLabel(
            "一只戴眼镜的小宠物在桌面上陪伴你。\n"
            "右键点击宠物进行操作，或通过托盘菜单控制。"
        )
        desc.setWordWrap(True)

        byline = QtWidgets.QLabel("by.庠肉")
        byline.setStyleSheet("color: #1E90FF; font-weight: bold;")

        right_col = QtWidgets.QWidget()
        right_vbox = QtWidgets.QVBoxLayout(right_col)
        right_vbox.setSpacing(4)
        right_vbox.addWidget(title)
        right_vbox.addWidget(version)
        right_vbox.addWidget(desc)
        right_vbox.addWidget(byline)
        right_vbox.addStretch(1)

        hbox = QtWidgets.QHBoxLayout()
        hbox.setSpacing(16)
        hbox.addWidget(lbl_icon)
        hbox.addWidget(right_col, 1)

        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("关于")
        dlg.setWindowIcon(QIcon(str(ASSETS / "app.ico")))
        dlg.setMinimumWidth(340)
        dlg_vbox = QtWidgets.QVBoxLayout(dlg)
        dlg_vbox.addLayout(hbox)
        ok_btn = QtWidgets.QPushButton("确定")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(dlg.accept)
        btn_row = QtWidgets.QHBoxLayout()
        btn_row.addStretch(1)
        btn_row.addWidget(ok_btn)
        dlg_vbox.addLayout(btn_row)
        dlg.setStyleSheet(_build_dlg_qss(_THEMES[_current_theme]))
        dlg.exec()


# --- Entry point ------------------------------------------------------------

def main() -> int:
    # Disable automatic DPI scaling so pets keep the same size across all monitors
    QtWidgets.QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
    
    app = QApplication.instance() or QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setFont(QFont("Microsoft YaHei UI", 10))

    # Apply the saved/user theme on startup (before any window is shown)
    apply_theme(app=app)

    global WALK_FRAMES, WALK_FRAMES_L, IDLE_FRAME, FRAME_SIZE
    WALK_FRAMES, WALK_FRAMES_L = load_walk_frames()
    if not WALK_FRAMES or not WALK_FRAMES_L:
        QtWidgets.QMessageBox.critical(
            None, "桌面宠物",
            "找不到素材，请确认 assets/ 目录里有 pet_walk.png 和 pet_walk_left.png"
        )
        return 1
    FRAME_SIZE = WALK_FRAMES[0].width()
    IDLE_FRAME = QPixmap(str(ASSETS / "pet_idle.png"))
    if IDLE_FRAME.isNull():
        IDLE_FRAME = None

    # 启动时3只，默认idle（缓慢游走），正面朝人
    controller.spawn(3)
    tray = build_tray(app)
    app.tray = tray

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
