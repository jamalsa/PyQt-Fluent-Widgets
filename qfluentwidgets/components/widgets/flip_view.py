# coding:utf-8
from typing import List, Union

from PyQt5.QtCore import Qt, pyqtSignal, QModelIndex, QSize, pyqtProperty, QRectF, QPropertyAnimation
from PyQt5.QtGui import QPixmap, QPainter, QColor, QImage, QWheelEvent
from PyQt5.QtWidgets import QStyleOptionViewItem, QWidget, QListWidget, QStyledItemDelegate, QListWidgetItem

from ...common.overload import singledispatchmethod
from ...common.style_sheet import isDarkTheme, FluentStyleSheet
from ...common.icon import drawIcon, FluentIcon
from .scroll_bar import SmoothScrollBar
from .button import ToolButton


class ScrollButton(ToolButton):
    """ Scroll button """

    def _postInit(self):
        self._opacity = 0
        self.opacityAni = QPropertyAnimation(self, b'opacity', self)
        self.opacityAni.setDuration(150)

    @pyqtProperty(float)
    def opacity(self):
        return self._opacity

    @opacity.setter
    def opacity(self, o: float):
        self._opacity = o
        self.update()

    def isTransparent(self):
        return self.opacity == 0

    def fadeIn(self):
        self.opacityAni.setStartValue(self.opacity)
        self.opacityAni.setEndValue(1)
        self.opacityAni.start()

    def fadeOut(self):
        self.opacityAni.setStartValue(self.opacity)
        self.opacityAni.setEndValue(0)
        self.opacityAni.start()

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setOpacity(self.opacity)

        # draw background
        if not isDarkTheme():
            painter.setBrush(QColor(252, 252, 252, 217))
        else:
            painter.setBrush(QColor(44, 44, 44, 245))

        painter.drawRoundedRect(self.rect(), 4, 4)

        # draw icon
        if isDarkTheme():
            color = QColor(255, 255, 255)
            opacity = 0.773 if self.isHover or self.isPressed else 0.541
        else:
            color = QColor(0, 0, 0)
            opacity = 0.616 if self.isHover or self.isPressed else 0.45

        painter.setOpacity(self.opacity * opacity)

        s = 6 if self.isPressed else 8
        w, h = self.width(), self.height()
        x, y = (w - s) / 2, (h - s) / 2
        drawIcon(self._icon, painter, QRectF(x, y, s, s), fill=color.name())


class FlipImageDelegate(QStyledItemDelegate):
    """ Flip view image delegate """

    def __init__(self, parent=None):
        super().__init__(parent)

    def itemSize(self):
        return self.parent().itemSize

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        painter.save()
        painter.setRenderHints(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)

        size = self.itemSize()  # type: QSize

        # draw image
        r = self.parent().devicePixelRatioF()
        image = index.data(Qt.UserRole)  # type: QImage
        image = image.scaled(size* r, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        x = option.rect.x() + int((option.rect.width() - size.width()) / 2)
        y = option.rect.y() + int((option.rect.height() - size.height()) / 2)
        painter.drawImage(QRectF(x, y, size.width(), size.height()), image)

        painter.restore()


class FlipView(QListWidget):
    """ Flip view """

    currentIndexChanged = pyqtSignal(int)

    @singledispatchmethod
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.orientation = Qt.Horizontal
        self._postInit()

    @__init__.register
    def _(self, orientation: Qt.Orientation, parent=None):
        super().__init__(parent=parent)
        self.orientation = orientation
        self._postInit()

    def _postInit(self):
        self.isHover = False
        self._currentIndex = -1
        self._itemSize = QSize(480, 270)  # 16:9

        self.delegate = FlipImageDelegate(self)
        self.scrollBar = SmoothScrollBar(self.orientation, self)

        self.scrollBar.setScrollAnimation(500)
        self.scrollBar.setForceHidden(True)

        self.setUniformItemSizes(True)
        self.setGridSize(self.itemSize)
        self.setFixedSize(self.itemSize)
        self.setItemDelegate(self.delegate)
        self.setMovement(QListWidget.Static)
        self.setVerticalScrollMode(self.ScrollPerPixel)
        self.setHorizontalScrollMode(self.ScrollPerPixel)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        FluentStyleSheet.FLIP_VIEW.apply(self)

        if self.isHorizontal():
            self.setFlow(QListWidget.LeftToRight)
            self.preButton = ScrollButton(FluentIcon.CARE_LEFT_SOLID, self)
            self.nextButton = ScrollButton(FluentIcon.CARE_RIGHT_SOLID, self)
            self.preButton.setFixedSize(16, 38)
            self.nextButton.setFixedSize(16, 38)
        else:
            self.preButton = ScrollButton(FluentIcon.CARE_UP_SOLID, self)
            self.nextButton = ScrollButton(FluentIcon.CARE_DOWN_SOLID, self)
            self.preButton.setFixedSize(38, 16)
            self.nextButton.setFixedSize(38, 16)

        # connect signal to slot
        self.preButton.clicked.connect(self.scrollPrevious)
        self.nextButton.clicked.connect(self.scrollNext)

    def isHorizontal(self):
        return self.orientation == Qt.Horizontal

    def setItemSize(self, size: QSize):
        """ set the size of item """
        if size == self.itemSize:
            return

        self._itemSize = size
        self.setGridSize(size)

        for i in range(self.count()):
            item = self.item(i)
            item.setSizeHint(size)

        self.viewport().update()

    def getItemSize(self):
        """ get the size of item """
        return self._itemSize

    def scrollPrevious(self):
        """ scroll to previous item """
        self.setCurrentIndex(self.currentIndex() - 1)

    def scrollNext(self):
        """ scroll to next item """
        self.setCurrentIndex(self.currentIndex() + 1)

    def setCurrentIndex(self, index: int):
        """ set current index """
        if not 0 <= index < self.count() or index == self.currentIndex():
            return

        self.scrollToIndex(index)

        # update the visibility of scroll button
        if index == 0:
            self.preButton.fadeOut()
        elif self.preButton.isTransparent() and self.isHover:
            self.preButton.fadeIn()

        if index == self.count() - 1:
            self.nextButton.fadeOut()
        elif self.nextButton.isTransparent() and self.isHover:
            self.nextButton.fadeIn()

        # fire signal
        self.currentIndexChanged.emit(index)

    def scrollToIndex(self, index):
        if not 0 <= index < self.count():
            return

        self._currentIndex = index

        if self.isHorizontal():
            value = self.itemSize.width() * index
        else:
            value = self.itemSize.height() * index

        self.scrollBar.scrollTo(value)

    def currentIndex(self):
        return self._currentIndex

    def image(self, index: int):
        if not 0 <= index < self.count():
            return QImage()

        return self.item(index).data(Qt.UserRole)

    def addImage(self, image: Union[QImage, QPixmap, str]):
        """ add image """
        self.addImages([image])

    def addImages(self, images: List[Union[QImage, QPixmap, str]]):
        """ add images """
        if not images:
            return

        N = self.count()
        self.addItems([''] * len(images))

        for i in range(N, self.count()):
            image = images[i - N]

            # convert image to QImage
            if isinstance(image, str):
                image = QImage(image)
            elif isinstance(image, QPixmap):
                image = image.toImage()

            item = self.item(i)
            item.setData(Qt.UserRole, image)
            item.setSizeHint(self.itemSize)

        if self.currentIndex() < 0:
            self._currentIndex = 0

    def resizeEvent(self, e):
        w, h = self.width(), self.height()
        bw, bh = self.preButton.width(), self.preButton.height()

        if self.isHorizontal():
            self.preButton.move(2, int(h / 2 - bh / 2))
            self.nextButton.move(w - bw - 2, int(h / 2 - bh / 2))
        else:
            self.preButton.move(int(w / 2 - bw / 2), 2)
            self.nextButton.move(int(w / 2 - bw / 2), h - bh - 2)

    def enterEvent(self, e):
        super().enterEvent(e)
        self.isHover = True
        self.preButton.fadeIn()
        self.nextButton.fadeIn()

    def leaveEvent(self, e):
        super().leaveEvent(e)
        self.isHover = False
        self.preButton.fadeOut()
        self.nextButton.fadeOut()

    def showEvent(self, e):
        self.scrollBar.duration = 0
        self.scrollToIndex(self.currentIndex())
        self.scrollBar.duration = 500

    def wheelEvent(self, e: QWheelEvent):
        if self.scrollBar.ani.state() == QPropertyAnimation.Running:
            return

        if e.angleDelta().y() < 0:
            self.scrollNext()
        else:
            self.scrollPrevious()

    itemSize = pyqtProperty(QSize, getItemSize, setItemSize)


class HorizontalFlipView(FlipView):
    """ Horizontal flip view """

    def __init__(self, parent=None):
        super().__init__(Qt.Horizontal, parent)


class VerticalFlipView(FlipView):
    """ Vertical flip view """

    def __init__(self, parent=None):
        super().__init__(Qt.Vertical, parent)