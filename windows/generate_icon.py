import sys
import os
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont

def make_ico():
    app = QApplication(sys.argv)
    
    # Generate a 256x256 high-resolution icon
    size = 256
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    # 1. Draw rounded purple background circle
    painter.setBrush(QColor("#7c4dff")) # vibrant violet
    painter.setPen(Qt.PenStyle.NoPen)
    padding = size // 16
    painter.drawEllipse(padding, padding, size - 2 * padding, size - 2 * padding)
    
    # 2. Draw 'සි' (Si) character in white
    painter.setPen(QColor("#ffffff"))
    font = QFont("Segoe UI", size // 2, QFont.Weight.Bold)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "සි")
    painter.end()
    
    # Save as ICO file
    output_path = os.path.join(os.path.dirname(__file__), "icon.ico")
    pixmap.save(output_path, "ICO")
    print(f"Icon generated successfully at: {output_path}")

if __name__ == "__main__":
    make_ico()
