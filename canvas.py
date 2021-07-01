import sys, random
import numpy as np
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QColor, QImage, QPainter, QPen
from PySide6.QtCore import Qt

class Canvas(QWidget):
    
    def __init__(self):
        super(Canvas, self).__init__()
        self.init(800, 800)

    def __del__(self):
        self.painter.end()
        
    def init(self, sizeX, sizeY):
        self.resetView(sizeX, sizeY)
        self.initPaintTools(sizeX, sizeY)

        self.setFocusPolicy(Qt.WheelFocus)
        self.setMouseTracking(True)
        self.setEnabled(True)

        self.resize(self.sizeX, self.sizeY)
        self.setWindowTitle('Graph Rep')
        self.show()

    def initPaintTools(self, sizeX, sizeY):
        self.image = QImage(self.sizeX, self.sizeY, QImage.Format_RGB32)
        self.painter = QPainter()
        self.painter.begin(self.image)
        self.painter.setRenderHint(QPainter.Antialiasing, True)
        self.painter.eraseRect(0, 0, sizeX, sizeY)
        self.pen = QPen()
        self.painter.setPen(self.pen)
        self.painter.setClipRect(0, 0, sizeX, sizeY)

    def resetView(self, sizeX, sizeY):
        self.xMin, self.yMax= -1.1, 1.1
        self.sizeX, self.sizeY = sizeX, sizeY
        self.scaleX, self.scaleY = sizeX/2.2, sizeY/2.2

    def xMax(self):
        return self.xMin + self.sizeX/self.scaleX

    def yMin(self):
        return self.yMax - self.sizeY/self.scaleY

    def isInside(self, z):
        x, y = z.real, z.imag
        return (x >= self.xMin) and (x <= self.xMax()) and (y >= self.yMin()) and (y <= self.yMax)

    def rescale(self, sizeX, sizeY):
        self.initPaintTools(sizeX, sizeY)
        xFactor, yFactor = sizeX*1.0/self.sizeX, sizeY*1.0/self.sizeY
        self.sizeX, self.sizeY = sizeX, sizeY
        self.scaleX, self.scaleY = xFactor * self.scaleX, yFactor * self.scaleY

    def redrawback(self):
        self.image.fill('white')

    def complexToPixel(self, z):
        x, y = z.real, z.imag
        xOut = np.rint((x - self.xMin)*self.scaleX)
        yOut = np.rint((self.yMax - y)*self.scaleY)
        return xOut, yOut

    def pixelToComplex(self, x, y):
        a = self.xMin + (x/self.scaleX)
        b = self.yMax - (y/self.scaleY)
        return a+b*1j

    def imageFirstCorner(self):
        w, h =self.width(), self.height()
        X = int((w-h)/2) if w>h else 0
        Y = int((h-w)/2) if h>w else 0
        return X, Y

    def imageMaxSize(self):
        return min(self.width(), self.height())

    def paintEvent(self, event):
        self.redrawback()
        self.playground()

        if (self.image.width() != self.imageMaxSize()):
            print("Error in Canvas.paintEvent: image size doesn't fit canvas size")
        canvasPainter = QPainter()
        canvasPainter.begin(self)
        canvasPainter.setClipRegion(event.region())
        X, Y = self.imageFirstCorner()
        canvasPainter.drawImage(X, Y, self.image)
        canvasPainter.end()



    def drawPoint(self, z, color=QColor('black'), width=1):
        x, y = self.complexToPixel(z)
        self.pen.setWidth(width)
        self.pen.setColor(color)
        self.painter.setPen(self.pen)
        self.painter.drawPoint(x,y)    

    def drawSegment(self, z1, z2, color=QColor('black'), width=1):
        x1, y1 = self.complexToPixel(z1)
        x2, y2 = self.complexToPixel(z2)
        self.pen.setWidth(width)
        self.pen.setColor(color)
        self.painter.setPen(self.pen)
        self.painter.drawLine(x1, y1, x2, y2)

    def drawCircle(self, c, r, color = QColor('black'), width=1):
        firstCorner = c + r*(-1+1j)
        secondCorner = c + r*(1-1j)
        x1, y1 = self.complexToPixel(firstCorner)
        x2, y2 = self.complexToPixel(secondCorner)
        self.pen.setColor(color)
        self.pen.setWidth(width)
        self.painter.setPen(self.pen)
        self.painter.drawEllipse(x1, y1, x2 - x1, y2 - y1)

    def playground(self):
        self.drawPoint(0, color=QColor('red'), width=6)
        self.drawSegment(-0.5, 1j, color=QColor('blue'), width=3)
        self.drawCircle(0, 1, QColor('black'), 2)