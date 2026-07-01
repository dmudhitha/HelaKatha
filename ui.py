import sys
from PyQt6.QtCore import Qt, QPoint, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame, QGraphicsOpacityEffect,
    QDialog, QPushButton, QGridLayout, QScrollArea, QFileDialog, QCheckBox, QTabWidget
)
from PyQt6.QtGui import QFont, QColor, QCursor, QScreen, QIcon, QPixmap, QPainter, QPen, QFontDatabase

# Modern QSS style definitions using a sleek dark theme (Catppuccin Mocha inspired)
WINDOW_STYLE = """
QFrame#container {
    background-color: rgba(30, 30, 46, 240); /* #1e1e2e with transparency */
    border: 1px solid rgba(137, 180, 250, 100); /* soft blue border */
    border-radius: 10px;
}
"""

PREVIEW_STYLE = """
QLabel {
    color: #bac2de; /* lighter grey */
    font-size: 11px;
    font-weight: bold;
    padding: 2px 5px;
    background-color: rgba(49, 50, 68, 150); /* #313244 */
    border-radius: 4px;
}
"""

CANDIDATE_ACTIVE_STYLE = """
QFrame#candidate_row {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #89b4fa, stop:1 #b4befe); /* blue-lavender gradient */
    border-radius: 6px;
}
QLabel#num_badge {
    color: #1e1e2e;
    background-color: #ffffff;
    font-weight: bold;
    border-radius: 3px;
    padding: 1px 5px;
}
QLabel#word_text {
    color: #1e1e2e;
    font-weight: bold;
}
"""

CANDIDATE_INACTIVE_STYLE = """
QFrame#candidate_row {
    background-color: transparent;
    border-radius: 6px;
}
QFrame#candidate_row:hover {
    background-color: rgba(49, 50, 68, 180);
}
QLabel#num_badge {
    color: #cdd6f4;
    background-color: #313244;
    font-weight: bold;
    border-radius: 3px;
    padding: 1px 5px;
}
QLabel#word_text {
    color: #cdd6f4;
}
"""

OSD_STYLE = """
QFrame#osd_container {
    background-color: rgba(17, 17, 27, 220); /* #11111b dark transparent */
    border: 2px solid %BORDER_COLOR%;
    border-radius: 15px;
}
QLabel#title {
    color: %TEXT_COLOR%;
    font-size: 18px;
    font-weight: bold;
}
QLabel#subtitle {
    color: #a6adc8;
    font-size: 12px;
}
"""

HELP_DIALOG_STYLE = """
QDialog {
    background-color: #1e1e2e;
    border: 1px solid #313244;
    border-radius: 8px;
}
QLabel#title {
    color: #89b4fa;
    font-size: 16px;
    font-weight: bold;
}
QLabel#section_title {
    color: #f38ba8;
    font-size: 12px;
    font-weight: bold;
    margin-top: 10px;
}
QLabel#cell_header {
    color: #a6adc8;
    font-weight: bold;
    border-bottom: 1px solid #313244;
    padding: 4px;
}
QLabel#cell_data {
    color: #cdd6f4;
    background-color: #181825;
    border-radius: 3px;
    padding: 4px;
}
QPushButton#close_btn {
    background-color: #89b4fa;
    color: #11111b;
    border: none;
    border-radius: 4px;
    padding: 6px 16px;
    font-weight: bold;
}
QPushButton#close_btn:hover {
    background-color: #b4befe;
}
"""

def create_status_icon(enabled):
    """
    Draws a beautiful system tray icon dynamically using QPainter.
    Includes the Sinhala syllable 'සි' in the center and a small indicator dot.
    Green dot for Enabled, Red dot for Disabled.
    """
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    # 1. Draw rounded purple background circle
    painter.setBrush(QColor("#7c4dff")) # vibrant violet
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(4, 4, 56, 56)
    
    # 2. Draw 'සි' (Si) character in white
    painter.setPen(QColor("#ffffff"))
    font = QFont("Ubuntu", 28, QFont.Weight.Bold)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "සි")
    
    # 3. Draw status dot (bottom-right)
    if enabled:
        painter.setBrush(QColor("#a6e3a1")) # soft green
    else:
        painter.setBrush(QColor("#f38ba8")) # soft red
    painter.drawEllipse(44, 44, 16, 16)
    
    painter.end()
    return QIcon(pixmap)


class CandidateRow(QFrame):
    """
    A single row in the candidate window representing one Sinhala word suggestion.
    """
    def __init__(self, index, parent=None):
        super().__init__(parent)
        self.setObjectName("candidate_row")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(10)
        
        # Number badge (1-5)
        self.num_badge = QLabel(str(index + 1), self)
        self.num_badge.setObjectName("num_badge")
        self.num_badge.setFixedSize(18, 18)
        self.num_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Word text label
        self.word_text = QLabel("", self)
        self.word_text.setObjectName("word_text")
        self.word_text.setFont(QFont("Ubuntu", 13))
        
        layout.addWidget(self.num_badge)
        layout.addWidget(self.word_text)
        layout.addStretch()
        
        self.set_active(False)

    def set_text(self, text):
        self.word_text.setText(text)

    def set_font_family(self, family):
        if family:
            self.word_text.setFont(QFont(family, 13))
        else:
            self.word_text.setFont(QFont("Ubuntu", 13))

    def set_active(self, active):
        if active:
            self.setStyleSheet(CANDIDATE_ACTIVE_STYLE)
        else:
            self.setStyleSheet(CANDIDATE_INACTIVE_STYLE)


class CandidateWindow(QWidget):
    """
    The borderless, floating suggestion box that follows the cursor.
    It does not accept keyboard focus so typing is not interrupted.
    """
    def __init__(self):
        super().__init__()
        
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowDoesNotAcceptFocus |
            Qt.WindowType.X11BypassWindowManagerHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        self.container = QFrame(self)
        self.container.setObjectName("container")
        self.container.setStyleSheet(WINDOW_STYLE)
        
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(6, 6, 6, 6)
        self.main_layout.setSpacing(4)
        
        self.preview_label = QLabel(self)
        self.preview_label.setStyleSheet(PREVIEW_STYLE)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setFont(QFont("Monospace", 9))
        self.main_layout.addWidget(self.preview_label)
        
        self.rows = []
        for i in range(5):
            row = CandidateRow(i, self)
            self.rows.append(row)
            self.main_layout.addWidget(row)
            
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.container)
        
        self.hide()

    def set_font_family(self, family):
        for row in self.rows:
            row.set_font_family(family)

    def update_candidates(self, buffer_text, candidates):
        if not buffer_text:
            self.hide()
            return
            
        self.preview_label.setText(f"Typing: {buffer_text}")
        
        for i in range(5):
            if i < len(candidates):
                self.rows[i].set_text(candidates[i])
                self.rows[i].set_active(i == 0)
                self.rows[i].show()
            else:
                self.rows[i].hide()
                
        self.adjustSize()
        self.follow_mouse()
        self.show()

    def follow_mouse(self):
        cursor_pos = QCursor.pos()
        x = cursor_pos.x() + 15
        y = cursor_pos.y() + 20
        
        screen = QApplication.primaryScreen().geometry()
        window_width = self.width()
        window_height = self.height()
        
        if x + window_width > screen.right():
            x = cursor_pos.x() - window_width - 10
        if y + window_height > screen.bottom():
            y = cursor_pos.y() - window_height - 10
            
        self.move(x, y)


class NotificationOSD(QWidget):
    """
    On-Screen Display notification shown in the center of the screen
    when the HelaKatha input tool is toggled ON or OFF.
    """
    def __init__(self):
        super().__init__()
        
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowDoesNotAcceptFocus |
            Qt.WindowType.X11BypassWindowManagerHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        self.container = QFrame(self)
        self.container.setObjectName("osd_container")
        
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(6)
        
        self.title_label = QLabel("", self)
        self.title_label.setObjectName("title")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.subtitle_label = QLabel("Press Ctrl + Space to Toggle", self)
        self.subtitle_label.setObjectName("subtitle")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(self.title_label)
        layout.addWidget(self.subtitle_label)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.container)
        
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        
        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(250)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.finished.connect(self.on_animation_finished)
        
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.start_fade_out)

    def show_message(self, enabled):
        self.timer.stop()
        self.animation.stop()
        
        if enabled:
            title = "HelaKatha: ENABLED"
            border_color = "rgba(166, 227, 161, 150)" # soft green
            text_color = "#a6e3a1"
        else:
            title = "HelaKatha: DISABLED"
            border_color = "rgba(243, 139, 168, 150)" # soft red
            text_color = "#f38ba8"
            
        self.title_label.setText(title)
        
        style = OSD_STYLE.replace("%BORDER_COLOR%", border_color).replace("%TEXT_COLOR%", text_color)
        self.container.setStyleSheet(style)
        
        self.adjustSize()
        self.center_on_screen()
        self.opacity_effect.setOpacity(1.0)
        self.show()
        
        self.timer.start(1200)

    def center_on_screen(self):
        screen_geometry = QApplication.primaryScreen().geometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

    def start_fade_out(self):
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.start()

    def on_animation_finished(self):
        if self.opacity_effect.opacity() == 0.0:
            self.hide()

LANGBAR_STYLE = """
QFrame#lang_container {
    background-color: rgba(30, 30, 46, 220); /* #1e1e2e transparent */
    border: 1px solid rgba(137, 180, 250, 150); /* blue border */
    border-radius: 14px;
}
QLabel#lang_text {
    color: #89b4fa; /* blue */
    font-size: 13px;
    font-weight: bold;
}
"""

class LanguageBar(QWidget):
    """
    A tiny floating widget on the screen displaying 'සි' or 'EN'.
    Clicking it toggles the input mode. It is draggable anywhere on the screen.
    """
    clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowDoesNotAcceptFocus |
            Qt.WindowType.X11BypassWindowManagerHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.container = QFrame(self)
        self.container.setObjectName("lang_container")
        self.container.setStyleSheet(LANGBAR_STYLE)
        
        layout = QHBoxLayout(self.container)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.label = QLabel("සි", self)
        self.label.setObjectName("lang_text")
        self.label.setFont(QFont("Ubuntu", 11, QFont.Weight.Bold))
        layout.addWidget(self.label)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.container)
        
        self.drag_start_pos = QPoint()
        self.drag_position = QPoint()
        self.is_dragging = False
        self.setFixedSize(50, 32)
        
        self.position_default()
        self.show()

    def position_default(self):
        screen = QApplication.primaryScreen().geometry()
        x = screen.width() - self.width() - 40
        y = screen.height() - self.height() - 80
        self.move(x, y)

    def set_mode(self, enabled):
        if enabled:
            self.label.setText("සි")
            self.container.setStyleSheet(
                LANGBAR_STYLE.replace("#89b4fa", "#a6e3a1").replace("rgba(137, 180, 250, 150)", "rgba(166, 227, 161, 150)")
            )
        else:
            self.label.setText("EN")
            self.container.setStyleSheet(
                LANGBAR_STYLE.replace("#89b4fa", "#bac2de").replace("rgba(137, 180, 250, 150)", "rgba(180, 190, 254, 80)")
            )

    # Draggable Window & Click Logic
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_pos = event.globalPosition().toPoint()
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.is_dragging = False
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            delta = (event.globalPosition().toPoint() - self.drag_start_pos).manhattanLength()
            if delta > 3:
                self.is_dragging = True
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.is_dragging:
                self.clicked.emit()
            event.accept()


class HelpDialog(QDialog):
    """
    A beautiful dark-themed help dialog showing phonetic mapping instructions
    and configuration settings for custom Unicode/Legacy fonts.
    """
    # Custom signal emitted when font settings change: (font_path, font_family, is_legacy)
    font_settings_changed = pyqtSignal(str, str, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("HelaKatha Guide & Settings")
        self.setFixedSize(500, 600)
        self.setStyleSheet(HELP_DIALOG_STYLE)
        
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowTitleHint | Qt.WindowType.WindowCloseButtonHint)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # We use a QTabWidget for Guide vs Settings
        self.tabs = QTabWidget(self)
        self.tabs.setStyleSheet("""
            QTabWidget::panel {
                border: 1px solid rgba(137, 180, 250, 80);
                background-color: rgba(30, 30, 46, 120);
                border-radius: 8px;
            }
            QTabBar::tab {
                background: rgba(45, 45, 68, 200);
                color: #bac2de;
                border: 1px solid rgba(137, 180, 250, 50);
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 8px 20px;
                margin-right: 4px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: rgba(137, 180, 250, 50);
                color: #89b4fa;
                border: 1px solid rgba(137, 180, 250, 120);
                border-bottom: none;
            }
            QTabBar::tab:hover {
                background: rgba(137, 180, 250, 30);
                color: #f5c2e7;
            }
        """)
        
        # ---------------- TAB 1: GUIDE ----------------
        guide_widget = QWidget()
        guide_layout = QVBoxLayout(guide_widget)
        guide_layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QLabel("HelaKatha Transliteration Guide", self)
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        guide_layout.addWidget(title)
        
        # Scrollable area for guide
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: transparent;")
        grid = QGridLayout(content_widget)
        grid.setSpacing(8)
        
        # Helper function to add headers
        def add_header(row, col1_text, col2_text):
            h1 = QLabel(col1_text)
            h1.setObjectName("cell_header")
            h2 = QLabel(col2_text)
            h2.setObjectName("cell_header")
            grid.addWidget(h1, row, 0)
            grid.addWidget(h2, row, 1)
            
        # Helper function to add data
        def add_row(row, key, val):
            k_lbl = QLabel(key)
            k_lbl.setObjectName("cell_data")
            k_lbl.setFont(QFont("Monospace", 10))
            
            v_lbl = QLabel(val)
            v_lbl.setObjectName("cell_data")
            v_lbl.setFont(QFont("Ubuntu", 11))
            
            grid.addWidget(k_lbl, row, 0)
            grid.addWidget(v_lbl, row, 1)

        curr_row = 0
        
        # SECTION: Controls
        lbl = QLabel("App Controls")
        lbl.setObjectName("section_title")
        grid.addWidget(lbl, curr_row, 0, 1, 2)
        curr_row += 1
        add_header(curr_row, "Action", "Hotkey")
        curr_row += 1
        add_row(curr_row, "Toggle Input On/Off", "Ctrl + Space")
        curr_row += 1
        add_row(curr_row, "Choose Word #1", "Space  or  Enter")
        curr_row += 1
        add_row(curr_row, "Choose Word #1-5", "Number Keys 1 - 5")
        curr_row += 1
        add_row(curr_row, "Cancel/Dismiss Box", "Esc")
        curr_row += 2
        
        # SECTION: Vowels
        lbl = QLabel("Vowel Mappings")
        lbl.setObjectName("section_title")
        grid.addWidget(lbl, curr_row, 0, 1, 2)
        curr_row += 1
        add_header(curr_row, "English Key", "Sinhala Vowel / Modifier")
        curr_row += 1
        add_row(curr_row, "a", "අ / (none)")
        curr_row += 1
        add_row(curr_row, "aa  or  a)", "ආ / ා (aela-pilla)")
        curr_row += 1
        add_row(curr_row, "ae  or  A", "ඇ / ැ (aeda-pilla)")
        curr_row += 1
        add_row(curr_row, "Aa  or  A)", "ඈ / ෑ")
        curr_row += 1
        add_row(curr_row, "i", "ඉ / ි (is-pilla)")
        curr_row += 1
        add_row(curr_row, "ii  or  ee", "ඊ / ී")
        curr_row += 1
        add_row(curr_row, "u", "උ / ු (papilla)")
        curr_row += 1
        add_row(curr_row, "uu  or  oo", "ඌ / ූ")
        curr_row += 1
        add_row(curr_row, "e", "එ / ෙ (kombuva)")
        curr_row += 1
        add_row(curr_row, "ee  or  ea", "ඒ / ේ")
        curr_row += 1
        add_row(curr_row, "o", "ඔ / ො")
        curr_row += 1
        add_row(curr_row, "oo  or  o)", "ඕ / ෝ")
        curr_row += 1
        add_row(curr_row, "au", "ඖ / ෞ")
        curr_row += 2
        
        # SECTION: Consonants
        lbl = QLabel("Consonant Examples")
        lbl.setObjectName("section_title")
        grid.addWidget(lbl, curr_row, 0, 1, 2)
        curr_row += 1
        add_header(curr_row, "English Key", "Sinhala Unicode")
        curr_row += 1
        add_row(curr_row, "k  /  g", "ක  /  ග")
        curr_row += 1
        add_row(curr_row, "t  /  th", "ට  /  ත")
        curr_row += 1
        add_row(curr_row, "d  /  dh", "ඩ  /  ද")
        curr_row += 1
        add_row(curr_row, "n  /  N", "න  /  ණ")
        curr_row += 1
        add_row(curr_row, "p  /  b", "ප  /  බ")
        curr_row += 1
        add_row(curr_row, "m  /  y  /  r", "ම  /  ය  /  ර")
        curr_row += 1
        add_row(curr_row, "l  /  L", "ල  /  ළ")
        curr_row += 1
        add_row(curr_row, "s  /  h  /  f", "ස  /  හ  /  ෆ")
        curr_row += 1
        add_row(curr_row, "sh  /  Sh", "ශ  /  ෂ")
        curr_row += 1
        add_row(curr_row, "ch  /  Ch", "ච  /  ඡ")
        curr_row += 1
        add_row(curr_row, "kh / gh / bh", "ඛ / ඝ / භ")
        curr_row += 2
        
        # SECTION: Special ligatures
        lbl = QLabel("Special Modifiers & Touchings")
        lbl.setObjectName("section_title")
        grid.addWidget(lbl, curr_row, 0, 1, 2)
        curr_row += 1
        add_header(curr_row, "Phonetic Type", "Example Keys -> Result")
        curr_row += 1
        add_row(curr_row, "Anusvara (ං)", "x  or  laxka -> ලංකා")
        curr_row += 1
        add_row(curr_row, "Rakaransha (්‍ර)", "kr -> ක්‍ර  /  sri -> ශ්‍රී")
        curr_row += 1
        add_row(curr_row, "Yansaya (්‍ය)", "kYa -> ක්‍ර‍ය (ක්‍ය)")
        curr_row += 1
        add_row(curr_row, "Repaya (ර්‍)", "R  or  dharma -> ධර්ම")
        curr_row += 1
        add_row(curr_row, "Sanya (Prenasal)", "zg -> ඟ  /  zd -> ඬ  /  zdh -> ඳ")
        curr_row += 1
        add_row(curr_row, "Gayanukitha (ෘ)", "kru -> කෘ  /  kruu -> කෲ")
        
        scroll.setWidget(content_widget)
        guide_layout.addWidget(scroll)
        
        self.tabs.addTab(guide_widget, "Phonetic Guide")
        
        # ---------------- TAB 2: SETTINGS ----------------
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setContentsMargins(20, 20, 20, 20)
        settings_layout.setSpacing(15)
        
        lbl_title = QLabel("Font Settings", self)
        lbl_title.setObjectName("title")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        settings_layout.addWidget(lbl_title)
        
        # Info text
        info_lbl = QLabel(
            "By default, this app uses the system font and types in Unicode.\n"
            "If you want to type in a legacy/normal font (e.g. FM Abhaya) or use a "
            "custom TrueType font (.ttf) for rendering Sinhala candidates, import it here.",
            self
        )
        info_lbl.setObjectName("cell_data")
        info_lbl.setWordWrap(True)
        info_lbl.setStyleSheet("color: #a6adc8; font-size: 11px;")
        settings_layout.addWidget(info_lbl)
        
        # Current Config Box
        self.config_box = QFrame()
        self.config_box.setStyleSheet("""
            QFrame {
                background-color: rgba(45, 45, 68, 150);
                border: 1px solid rgba(137, 180, 250, 50);
                border-radius: 6px;
            }
        """)
        config_layout = QGridLayout(self.config_box)
        config_layout.setSpacing(10)
        
        config_layout.addWidget(QLabel("Active Font:"), 0, 0)
        self.font_name_lbl = QLabel("Default (System Font)")
        self.font_name_lbl.setStyleSheet("font-weight: bold; color: #f5c2e7;")
        config_layout.addWidget(self.font_name_lbl, 0, 1)
        
        config_layout.addWidget(QLabel("Font Path:"), 1, 0)
        self.font_path_lbl = QLabel("None")
        self.font_path_lbl.setWordWrap(True)
        self.font_path_lbl.setStyleSheet("color: #a6adc8; font-size: 10px;")
        config_layout.addWidget(self.font_path_lbl, 1, 1)
        
        settings_layout.addWidget(self.config_box)
        
        # Legacy toggle Checkbox
        self.legacy_check = QCheckBox("Active Font is Legacy / Normal (e.g. FM Abhaya)", self)
        self.legacy_check.setCursor(Qt.CursorShape.PointingHandCursor)
        self.legacy_check.setStyleSheet("""
            QCheckBox {
                color: #cdd6f4;
                font-size: 11px;
            }
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
            }
        """)
        self.legacy_check.stateChanged.connect(self.on_settings_changed)
        settings_layout.addWidget(self.legacy_check)
        
        # Action Buttons
        btn_layout = QHBoxLayout()
        
        self.import_btn = QPushButton("Import Font (.ttf)", self)
        self.import_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.import_btn.setStyleSheet("""
            QPushButton {
                background-color: #89b4fa;
                color: #1e1e2e;
                font-weight: bold;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #b4befe;
            }
        """)
        self.import_btn.clicked.connect(self.import_font_clicked)
        btn_layout.addWidget(self.import_btn)
        
        self.reset_btn = QPushButton("Reset to Default", self)
        self.reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #f38ba8;
                color: #1e1e2e;
                font-weight: bold;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #f9e2af;
            }
        """)
        self.reset_btn.clicked.connect(self.reset_font_clicked)
        btn_layout.addWidget(self.reset_btn)
        
        settings_layout.addLayout(btn_layout)
        settings_layout.addStretch()
        
        self.tabs.addTab(settings_widget, "Font Settings")
        layout.addWidget(self.tabs)
        
        # Main Close Button
        close_btn = QPushButton("Done", self)
        close_btn.setObjectName("close_btn")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_layout.addWidget(close_btn)
        close_layout.addStretch()
        layout.addLayout(close_layout)
        
        # State variables for settings
        self.current_font_path = ""
        self.current_font_family = ""
        self.current_is_legacy = False

    def load_initial_settings(self, path, family, is_legacy):
        """
        Populate UI elements on dialog show.
        """
        self.current_font_path = path
        self.current_font_family = family
        self.current_is_legacy = is_legacy
        
        # Temporarily block signals so checking doesn't trigger on_settings_changed immediately
        self.legacy_check.blockSignals(True)
        self.legacy_check.setChecked(is_legacy)
        self.legacy_check.blockSignals(False)
        
        if path:
            self.font_path_lbl.setText(path)
            self.font_name_lbl.setText(family if family else "Custom Font")
        else:
            self.font_path_lbl.setText("None")
            self.font_name_lbl.setText("Default (System Font)")

    def import_font_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select TrueType Font", "", "TrueType Fonts (*.ttf);;All Files (*)"
        )
        if file_path:
            # Register font and retrieve family name
            font_id = QFontDatabase.addApplicationFont(file_path)
            if font_id != -1:
                families = QFontDatabase.applicationFontFamilies(font_id)
                if families:
                    family_name = families[0]
                    self.current_font_path = file_path
                    self.current_font_family = family_name
                    
                    self.font_path_lbl.setText(file_path)
                    self.font_name_lbl.setText(family_name)
                    
                    # Force legacy mode checkbox if font filename starts with "FM" (common convention)
                    import os
                    basename = os.path.basename(file_path).upper()
                    if basename.startswith("FM") or "ABHAYA" in basename:
                        self.legacy_check.setChecked(True)
                        self.current_is_legacy = True
                    
                    self.on_settings_changed()
            else:
                self.font_name_lbl.setText("Error loading font")

    def reset_font_clicked(self):
        self.current_font_path = ""
        self.current_font_family = ""
        self.current_is_legacy = False
        
        self.legacy_check.setChecked(False)
        self.font_path_lbl.setText("None")
        self.font_name_lbl.setText("Default (System Font)")
        
        self.on_settings_changed()

    def on_settings_changed(self):
        self.current_is_legacy = self.legacy_check.isChecked()
        self.font_settings_changed.emit(
            self.current_font_path,
            self.current_font_family,
            self.current_is_legacy
        )
