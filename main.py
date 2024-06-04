import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QColorDialog, QSlider, QVBoxLayout, QWidget, QPushButton, QLabel
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPainter, QPen, QColor, QImage, QPalette


class OverlayWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        screen_size = QApplication.desktop().availableGeometry()
        self.setGeometry(screen_size)
        self.show()

        self.drawing = False
        self.last_pos = QPoint()
        self.image = QImage(self.size(), QImage.Format_ARGB32)
        self.image.fill(Qt.transparent)

        self.pen_color = QColor(0, 0, 0)
        self.pen_thickness = 5

        self.create_settings_window()

    def create_settings_window(self):
        settings_window = QWidget(self)
        layout = QVBoxLayout(settings_window)

        thickness_label = QLabel("Thickness", settings_window)
        self.thickness_slider = QSlider(Qt.Horizontal, settings_window)
        self.thickness_slider.setMinimum(1)
        self.thickness_slider.setMaximum(20)
        self.thickness_slider.setValue(self.pen_thickness)
        self.thickness_slider.setTickPosition(QSlider.TicksBelow)
        self.thickness_slider.setTickInterval(1)
        self.thickness_slider.valueChanged.connect(self.change_thickness)

        color_button = QPushButton("Color", settings_window)
        color_button.clicked.connect(self.choose_color)

        layout.addWidget(thickness_label)
        layout.addWidget(self.thickness_slider)
        layout.addWidget(color_button)

        settings_window.setLayout(layout)

        palette = settings_window.palette()
        palette.setColor(QPalette.Background, Qt.lightGray)
        settings_window.setAutoFillBackground(True)
        settings_window.setPalette(palette)

        settings_window.setWindowTitle("Settings")
        settings_window.setWindowFlags(Qt.WindowStaysOnTopHint)
        settings_window.setGeometry(50, 50, 200, 150)
        settings_window.show()

    def choose_color(self):
        color = QColorDialog.getColor(initial=self.pen_color, parent=self)
        if color.isValid():
            self.pen_color = color

    def change_thickness(self, value):
        self.pen_thickness = value

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.last_pos = event.pos()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and self.drawing:
            painter = QPainter(self.image)
            pen = QPen(self.pen_color, self.pen_thickness, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(self.last_pos, event.pos())
            self.last_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = False

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawImage(self.rect(), self.image, self.image.rect())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    overlay = OverlayWindow()
    sys.exit(app.exec_())
