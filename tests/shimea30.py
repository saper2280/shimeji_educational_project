from PyQt5.QtWidgets import QApplication, QLabel, QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap
import sys, os

class ShimeaWindow(QWidget):
    def __init__(self):
        super().__init__()
        # Делаем окно без рамки, поверх всех окон
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        # Прозрачный фон окна
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Делаем окно во весь экран вручную, вместо showFullScreen
        screen_geometry = QApplication.primaryScreen().geometry()
        self.setGeometry(screen_geometry)

        # Загружаем персонажа
        img_path = r"C:/Users/lyzam/OneDrive - Gymnázium Josefa Jungmanna/Plocha/maturita/shimea-educational-project/src/data/vecteezy_soldier-png-graphic-clipart-design_19806301.png"
        pixmap = QPixmap(img_path).scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        self.image_label = QLabel(self)
        self.image_label.setPixmap(pixmap)
        self.image_label.setFixedSize(pixmap.size())
        # Обязательно делаем фон картинки прозрачным
        self.image_label.setStyleSheet("background: transparent;")

        # Устанавливаем позицию после показа окна
        QTimer.singleShot(0, self.set_start_pos)

    def set_start_pos(self):
        x = (self.width() - self.image_label.width()) // 2
        y = self.height() - self.image_label.height() - 50
        self.image_label.move(x, y)
        print("Image at:", x, y)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = ShimeaWindow()
    w.show()
    sys.exit(app.exec_())
