import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QColorDialog, QSlider, QVBoxLayout, QWidget, QPushButton, QLabel
from PyQt5.QtCore import Qt, QPoint, QRect
from PyQt5.QtGui import QPainter, QPen, QColor, QImage, QPalette, QBrush


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
        self.drawing_line = False
        self.drawing_rect = False
        self.drawing_filled_rect = False
        self.start_pos = QPoint()
        self.end_pos = QPoint()
        self.image = QImage(self.size(), QImage.Format_ARGB32)
        self.image.fill(Qt.transparent)

        self.pen_color = QColor(0, 255, 0)
        self.pen_thickness = 5

        self.undo_stack = [self.image.copy()]

        self.settings_window = None
        self.create_settings_window()

    def create_settings_window(self):
        if self.settings_window is None:
            self.settings_window = QWidget(self)
            layout = QVBoxLayout(self.settings_window)

            thickness_label = QLabel("Thickness", self.settings_window)
            self.thickness_slider = QSlider(Qt.Horizontal, self.settings_window)
            self.thickness_slider.setMinimum(1)
            self.thickness_slider.setMaximum(20)
            self.thickness_slider.setValue(self.pen_thickness)
            self.thickness_slider.setTickPosition(QSlider.TicksBelow)
            self.thickness_slider.setTickInterval(1)
            self.thickness_slider.valueChanged.connect(self.change_thickness)

            color_button = QPushButton("Color", self.settings_window)
            color_button.clicked.connect(self.choose_color)

            layout.addWidget(thickness_label)
            layout.addWidget(self.thickness_slider)
            layout.addWidget(color_button)

            self.settings_window.setLayout(layout)

            palette = self.settings_window.palette()
            palette.setColor(QPalette.Background, Qt.lightGray)
            self.settings_window.setAutoFillBackground(True)
            self.settings_window.setPalette(palette)

            self.settings_window.setWindowTitle("Settings")
            self.settings_window.setWindowFlags(Qt.WindowStaysOnTopHint)
            self.settings_window.setGeometry(50, 50, 200, 150)
            self.settings_window.show()

    def toggle_settings_window(self):
        if self.settings_window is not None:
            if self.settings_window.isVisible():
                self.settings_window.hide()
            else:
                self.settings_window.show()

    def choose_color(self):
        color = QColorDialog.getColor(initial=self.pen_color, parent=self)
        if color.isValid():
            self.pen_color = color

    def change_thickness(self, value):
        self.pen_thickness = value

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if event.modifiers() == Qt.ControlModifier:
                self.drawing_rect = True
            else:
                self.drawing = True
            self.start_pos = event.pos()
            self.end_pos = self.start_pos
        elif event.button() == Qt.RightButton:
            if event.modifiers() == Qt.ControlModifier:
                self.drawing_filled_rect = True
            else:
                self.drawing_line = True
            self.start_pos = event.pos()
            self.end_pos = self.start_pos

    def mouseMoveEvent(self, event):
        if self.drawing and event.buttons() & Qt.LeftButton:
            painter = QPainter(self.image)
            pen = QPen(self.pen_color, self.pen_thickness, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(self.start_pos, event.pos())
            self.start_pos = event.pos()
            self.update()
        elif self.drawing_line and event.buttons() & Qt.RightButton:
            self.end_pos = event.pos()
            self.update()
        elif (self.drawing_rect or self.drawing_filled_rect) and event.buttons() & (Qt.LeftButton | Qt.RightButton):
            self.end_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.drawing:
            self.drawing = False
            self.save_state()
        elif event.button() == Qt.RightButton and self.drawing_line:
            self.drawing_line = False
            painter = QPainter(self.image)
            pen = QPen(self.pen_color, self.pen_thickness, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(self.start_pos, self.end_pos)
            self.update()
            self.save_state()
        elif event.button() == Qt.LeftButton and self.drawing_rect:
            self.drawing_rect = False
            painter = QPainter(self.image)
            pen = QPen(self.pen_color, self.pen_thickness, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            rect = self.get_rect(self.start_pos, self.end_pos)
            painter.drawRect(rect)
            self.update()
            self.save_state()
        elif event.button() == Qt.RightButton and self.drawing_filled_rect:
            self.drawing_filled_rect = False
            painter = QPainter(self.image)
            painter.setPen(Qt.NoPen)
            brush = QBrush(self.pen_color)
            painter.setBrush(brush)
            rect = self.get_rect(self.start_pos, self.end_pos)
            painter.drawRect(rect)
            self.update()
            self.save_state()

    def get_rect(self, start, end):
        return QRect(min(start.x(), end.x()), min(start.y(), end.y()), abs(start.x() - end.x()), abs(start.y() - end.y()))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() == Qt.Key_S:
            self.toggle_settings_window()
        elif event.key() == Qt.Key_Z and event.modifiers() == Qt.ControlModifier:
            self.undo()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawImage(self.rect(), self.image, self.image.rect())
        if self.drawing_line:
            pen = QPen(self.pen_color, self.pen_thickness, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(self.start_pos, self.end_pos)
        elif self.drawing_rect or self.drawing_filled_rect:
            rect = self.get_rect(self.start_pos, self.end_pos)
            if self.drawing_rect:
                pen = QPen(self.pen_color, self.pen_thickness, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                painter.setPen(pen)
                painter.drawRect(rect)
            elif self.drawing_filled_rect:
                painter.setPen(Qt.NoPen)
                brush = QBrush(self.pen_color)
                painter.setBrush(brush)
                painter.drawRect(rect)

    def save_state(self):
        self.undo_stack.append(self.image.copy())
        if len(self.undo_stack) > 10:
            self.undo_stack.pop(0)

    def undo(self):
        if len(self.undo_stack) > 1:
            self.undo_stack.pop()
            self.image = self.undo_stack[-1].copy()
            self.update()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    overlay = OverlayWindow()
    sys.exit(app.exec_())
