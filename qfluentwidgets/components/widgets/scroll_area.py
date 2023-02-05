# coding:utf-8
from collections import deque
from enum import Enum
from math import cos, pi

from PyQt6.QtCore import QDateTime, QEasingCurve, Qt, QTimer, QPoint, pyqtSignal, QPropertyAnimation
from PyQt6.QtGui import QWheelEvent
from PyQt6.QtWidgets import QApplication, QScrollArea, QScrollBar

from ...common.smooth_scroll import SmoothScroll, SmoothMode


class ScrollArea(QScrollArea):
    """ A scroll area which can scroll smoothly """

    def __init__(self, parent=None, orient=Qt.Orientation.Vertical):
        """
        Parameters
        ----------
        parent: QWidget
            parent widget

        orient: Orientation
            scroll orientation
        """
        super().__init__(parent)
        self.smoothScroll = SmoothScroll(self)

    def setSmoothMode(self, mode):
        """ set smooth mode

        Parameters
        ----------
        mode: SmoothMode
            smooth scroll mode
        """
        self.smoothScroll.setSmoothMode(mode)

    def wheelEvent(self, e):
        self.smoothScroll.wheelEvent(e)

class SmoothScrollBar(QScrollBar):
    """ Smooth scroll bar """

    scrollFinished = pyqtSignal()

    def __init__(self, parent=None):
        QScrollBar.__init__(self, parent)
        self.ani = QPropertyAnimation()
        self.ani.setTargetObject(self)
        self.ani.setPropertyName(b"value")
        self.ani.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.ani.setDuration(500)
        self.ani.finished.connect(self.scrollFinished)

    def setValue(self, value):
        if value == self.value():
            return

        # stop running animation
        self.ani.stop()
        self.scrollFinished.emit()

        self.ani.setStartValue(self.value())
        self.ani.setEndValue(value)
        self.ani.start()

    def scrollValue(self, value):
        """ scroll the specified distance """
        value += self.value()
        self.scrollTo(value)

    def scrollTo(self, value):
        """ scroll to the specified position """
        value = min(self.maximum(), max(self.minimum(), value))
        self.setValue(value)

    def mousePressEvent(self, e):
        self.ani.stop()
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        self.ani.stop()
        super().mouseReleaseEvent(e)

    def mouseMoveEvent(self, e):
        self.ani.stop()
        super().mouseMoveEvent(e)


class SmoothScrollArea(QScrollArea):
    """ Smooth scroll area """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.hScrollBar = SmoothScrollBar()
        self.vScrollBar = SmoothScrollBar()
        self.hScrollBar.setOrientation(Qt.Orientation.Horizontal)
        self.vScrollBar.setOrientation(Qt.Orientation.Vertical)
        self.setVerticalScrollBar(self.vScrollBar)
        self.setHorizontalScrollBar(self.hScrollBar)

    def setScrollAnimation(self, orient, duration, easing=QEasingCurve.Type.OutCubic):
        """ set scroll animation

        Parameters
        ----------
        orient: Orient
            scroll orientation

        duration: int
            scroll duration

        easing: QEasingCurve
            animation type
        """
        bar = self.hScrollBar if orient == Qt.Orientation.Horizontal else self.vScrollBar
        bar.ani.setDuration(duration)
        bar.ani.setEasingCurve(easing)

    def wheelEvent(self, e):
        if e.modifiers() == Qt.KeyboardModifier.NoModifier:
            self.vScrollBar.scrollValue(-e.angleDelta().y())
        else:
            self.hScrollBar.scrollValue(-e.angleDelta().x())