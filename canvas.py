import sys, random
import numpy as np

from PySide6.QtCore import QDir, QRect, QSize, Qt
from PySide6.QtGui import QColor, QImage, QKeyEvent, QMouseEvent, QPainter, QPen, QWheelEvent
from PySide6.QtSvg import QSvgGenerator
from PySide6.QtWidgets import QApplication, QFileDialog, QWidget

from toolkit import qnorm, mod2pi
from h2geometry import H2Isometry, H2Point, H2Segment


class Canvas(QWidget):
    
    def __init__(self):
        super(Canvas, self).__init__()
        self.init(800, 800)

    def __del__(self):
        self.painter.end()
        
    def init(self, sizeX, sizeY):
        self.title = 'Graph Rep'
        self.resetView(sizeX, sizeY)
        self.initPaintTools(sizeX, sizeY)
        self.setFocusPolicy(Qt.WheelFocus)
        self.setMouseTracking(True)
        self.setEnabled(True)
        self.resize(self.sizeX, self.sizeY)
        self.setWindowTitle(self.title)
        self.show()

        self.pointsClicked = []
        self.H2pointsClicked = []

    def initPaintTools(self, sizeX, sizeY):
        self.image = QImage(self.sizeX, self.sizeY, QImage.Format_RGB32)
        self.painter = QPainter()
        self.initPaintImage(sizeX, sizeY)

    def initPaintImage(self, sizeX, sizeY):
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
        self.transform = H2Isometry(1.0, 0.0)
        self.changingTransform = False

    def xMax(self):
        return self.xMin + self.sizeX/self.scaleX

    def yMin(self):
        return self.yMax - self.sizeY/self.scaleY

    def isInside(self, z):
        x, y = z.real, z.imag
        return (x >= self.xMin) and (x <= self.xMax()) and (y >= self.yMin()) and (y <= self.yMax)

    def rescale(self, sizeX, sizeY):
        self.painter.end()
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

    def zoom(self, coeff, centerX=-1, centerY=-1):
        if centerX==-1 and centerY==-1:
            centerX = np.rint(self.sizeX/2.0)
            centerY = np.rint(self.sizeX/2.0)
        x, y = self.xMin + centerX/self.scaleX, self.yMax - centerY/self.scaleY
        self.xMin = x - (x - self.xMin)/coeff
        self.yMax = y + (self.yMax - y)/coeff
        self.scaleX, self.scaleY = coeff*self.scaleX, coeff*self.scaleY

    def shift(self, x, y):
        self.xMin += x/self.scaleX
        self.yMax += y/self.scaleY

    def mouseShift(self, x, y):
        self.xMin = self.xMinSave + (self.mouseXSave - x)/self.scaleX
        self.yMax = self.yMaxSave - (self.mouseYSave - y)/self.scaleY

    def paint(self):
        self.redrawback()
        self.playground()

    def paintEvent(self, event):
        self.paint()
        # if (self.image.width() != self.imageMaxSize()):
        #     print("Warning in Canvas.paintEvent: image doesn't fit canvas (image size = {}, canvas size = {})".format(self.image.width(), self.imageMaxSize()))
        canvasPainter = QPainter()
        canvasPainter.begin(self)
        canvasPainter.setClipRegion(event.region())
        X, Y = self.imageFirstCorner()
        canvasPainter.drawImage(X, Y, self.image)
        canvasPainter.end()

    def saveSvg(self):
        path = QDir.currentPath()+'/export.svg'
        print(path)
        generator = QSvgGenerator()
        generator.setFileName(path)
        generator.setSize(QSize(self.sizeX, self.sizeY))
        generator.setViewBox(QRect(0, 0, self.sizeX, self.sizeY))
        generator.setTitle(self.title)

        self.painter.end()
        self.painter.begin(generator)
        self.paint()
        self.painter.end()
        self.initPaintImage(self.sizeX, self.sizeY)

    def mouseOverImage(self, event:QMouseEvent):
        x, y = event.x(), event.y()
        X0, Y0 = self.imageFirstCorner()
        if (x < X0) or (x > X0 + self.imageMaxSize()) or (y < Y0) or (y > Y0 + self.imageMaxSize()):
            return False, 0, 0
        else:
            return True, x - X0, y - Y0

    def mousePressEvent(self, event:QMouseEvent):
        inside, x, y = self.mouseOverImage(event)
        if inside:
            z = self.pixelToComplex(x,y)
            print('z = {:.2}'.format(z))
            self.pointsClicked.append(z)
            if qnorm(z)<1:
                self.H2pointsClicked.append(self.pixelToH2(x, y))
            self.update()
        if event.button() == Qt.LeftButton:
            self.pointSave = self.pixelToComplex(x, y)
            if QApplication.keyboardModifiers() == Qt.ShiftModifier:
                self.xMinSave, self.yMaxSave = self.xMin, self.yMax
            else:
                if qnorm(self.pointSave) < 1.0:
                    self.changingTransform = True
                    self.transformSave = self.transform

    def resizeEvent(self, QResizeEvent):
        newSize = min(self.width(), self.height())
        self.rescale(newSize, newSize)
        self.update()

    def moveEvent(self, QMoveEvent):
        self.update()

    def mouseMoveEvent(self, event:QMouseEvent):
        inside, x, y = self.mouseOverImage(event)
        if inside:
            self.mouseX, self.mouseY = x, y
            if (event.buttons() == Qt.LeftButton):
                if (QApplication.keyboardModifiers() == Qt.ShiftModifier):
                    self.mouseShift(x, y)
                elif self.changingTransform:
                    z = self.pixelToComplex(x, y)
                    if (qnorm(z)< 1.0):
                        transformChange = H2Isometry(1,0)
                        if (QApplication.keyboardModifiers() == Qt.ControlModifier):
                            u = z - self.pointSave
                            if (u.imag*u.imag > 0):
                                u = u/np.abs(u)
                                v = u - qnorm(self.pointSave)
                                transformChange = H2Isometry(np.conj(u)*v*v/qnorm(v), -self.pointSave*(1.0-u)/v)
                        else:
                            if qnorm(z - self.pointSave) > 0:
                                transformChange.setByMappingPoint(H2Point(self.pointSave), H2Point(z))
                        self.transform = transformChange*self.transformSave
        self.update()

    def mouseReleaseEvent(self, event:QMouseEvent):
        inside, x, y = self.mouseOverImage(event)
        if inside:
            self.changingTransform = False
            self.update()

    def enterEvent(self, QEvent):
        self.setFocus()
        self.changingTransform = False
    
    def leaveEvent(self, QEvent):
        self.changingTransform = False

    def wheelEvent(self, event:QWheelEvent):
        coeff = np.power(1.2, event.angleDelta().y()/120)
        self.zoom(coeff, event.position().x(), event.position().y())
        self.update()

    def keyPressEvent(self, event:QKeyEvent):
        # When Python 3.10 is released, we can use match-case like here: https://stackoverflow.com/a/30881320
        key=event.key()
        if key==Qt.Key_Left :
            self.xMinSave, self.xMaxSave = self.xMin, self.yMax
            self.shift(-20, 0)
        elif key==Qt.Key_Right :
            self.xMinSave, self.xMaxSave = self.xMin, self.yMax
            self.shift(20, 0)
        elif key==Qt.Key_Up :
            self.xMinSave, self.xMaxSave = self.xMin, self.yMax
            self.shift(0, 20)
        elif key==Qt.Key_Down :
            self.xMinSave, self.xMaxSave = self.xMin, self.yMax
            self.shift(0, -20)
        elif key==Qt.Key_Plus :
            self.zoom(2)
        elif key==Qt.Key_Minus :
            self.zoom(0.5)
        elif key==Qt.Key_Control :
            if self.changingTransform and qnorm(self.pixelToComplex(self.mouseX, self.mouseY)) < 1.0:
                self.pointSave = self.pixelToComplex(self.mouseX, self.mouseY)
                self.transformSave = self.transform
        elif key==Qt.Key_Shift :
            self.mouseXSave, self.mouseYSave = self.mouseX, self.mouseY
            self.xMinSave, self.yMaxSave = self.xMin, self.yMax
        elif key==Qt.Key_S :
            self.saveSvg()
        self.update()

    def keyReleaseEvent(self, event:QKeyEvent):
        key = event.key()
        if key==Qt.Key_Control :
            if self.changingTransform and qnorm(self.pixelToComplex(self.mouseX, self.mouseY)) < 1.0 :
                self.pointSave = self.pixelToComplex(self.mouseX, self.mouseY)
                self.transformSave = self.transform;
        self.update()

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

    def drawSmallerArc(self, c, r, z1, z2, color, width):
        outside, straight, z1New, z2New = self.straightApprox(c, r, z1, z2)
        if outside:
            pass
        elif straight:
            self.drawSegment(z1New, z2New, color, width)
        else:
            angle1, angle2 = np.angle(z1 - c), np.angle(z2 - c)
            if ((z2-c)*np.conj(z1-c)).imag < 0:
                angle1, angle2 = angle2, angle1
            corner1, corner2 = c + r*(-1.0+1j), c + r*(1.0-1j)
            x1, y1 = self.complexToPixel(corner1)
            x2, y2 = self.complexToPixel(corner2)
            qtAngle = np.rint(mod2pi(angle1)*16*360/(2*np.pi))
            qtSpan = np.rint(mod2pi(angle2 - angle1)*16*360/(2*np.pi))
            self.pen.setColor(color)
            self.pen.setWidth(width)
            self.painter.setPen(self.pen)
            #print('c = {:2}, r = {:2}, z1 = {:2}, z2 = {:2}'.format(c, r, z1, z2))
            #print('x1 = {}, y1 = {}, x2 - x1 = {}, y2 - y1 = {}, qtAngle = {}, qtSpan = {}'.format(x1, y1, x2 - x1, y2 - y1, qtAngle, qtSpan))
            self.painter.drawArc(x1, y1, x2 - x1, y2 - y1, qtAngle, qtSpan)

    def straightApprox(self, c, r, z1, z2):
        inside, outside, many, z1New, z2New = self.arcIntersectsCanvasBoundary(c, r, z1, z2)
        straight = False
        if many:
            #print('many')
            pass
        elif outside:
            #print('outside')
            pass
        elif self.isAlmostSmallStraightArc(c, r, z1, z2):
            #print('almost small straight')
            z1New, z2New = z1, z2 # I'm tempted to comment this line but it corresponds to what I had
            straight = True
        elif self.isAlmostInfiniteRadius(r):
            #print('almost infinite radius')
            straight = True
        else:
            #print('normal arc')
            pass
        return outside, straight, z1New, z2New

    def liesOnSmallerArc(self, z, center, endpoint1, endpoint2):
        u, u1, u2 = z - center, endpoint1 - center, endpoint2 - center
        v, v2 = u*np.conj(u1), u2*np.conj(u1)
        if np.imag(v2) > 0:
            return (v.imag >= 0) and (v.real >= v2.real)
        else:
            return (v.imag <= 0) and (v.real >= v2.real)

    def isAlmostInfiniteRadius(self, r):
        angleMin = np.pi/(180*16)
        scale = max(self.scaleX, self.scaleY)
        pxError = 8.0
        return np.isnan(r) or (r*scale*angleMin > pxError)

    def isAlmostSmallStraightArc(self, c, r, z1, z2):
        z2New = (z2 - c)*np.conj(z1 - c)/(r*r)
        X2, Y2 = z2New.real, z2New.imag
        mX, mY = 0.5*(1.0 + X2), 0.5*(1.0 - X2)
        if np.isnan(mX) or np.isnan(mY) or mX<=0 or mY<=0:
            return True
        else:
            arcMidX, arcMidY = np.sqrt(mX), np.sqrt(mY)
            arcMidY = arcMidY if (Y2 > 0) else -arcMidY
            arcMid = arcMidX + arcMidY*1j
            lineMid = 0.5*(1.0 + z2New)
            scale = max(self.scaleX, self.scaleY)
            pxDeltaSq = np.rint(qnorm(arcMid - lineMid)*r*r*scale*scale)
            pxTolSq = 0
            return pxDeltaSq <= pxTolSq

    def circleIntersectsCanvasBoundary(self, c, r):
        intersections = []
        xMin, xMax, yMin, yMax = self.xMin, self.xMax(), self.yMin(), self.yMax
        xc, yc = c.real, c.imag
        for x in [xMin, xMax]:
            D = r*r - (x-xc)*(x-xc)
            if D >= 0:
                D = np.sqrt(D)
                for y in [yc+D, yc-D]:
                    if (y >= yMin) and (y <= yMax):
                        intersections.append(x+y*1j)
        for y in [yMin, yMax]:
            D = r*r - (y-yc)*(y-yc)
            if D >= 0:
                D = np.sqrt(D)
                for x in [xc+D, xc-D]:
                    if (x >= xMin) and (x <= xMax):
                        intersections.append(x+y*1j)
        return intersections

    def arcIntersectsCanvasBoundary(self, c, r, z1, z2):
        inside, outside, many = False, False, False
        z1New, z2New = z1, z2
        isIn1, isIn2 = self.isInside(z1), self.isInside(z2)
        if isIn1 and isIn2:
            inside = True
        else:
            intersections = self.circleIntersectsCanvasBoundary(c, r)
            nbInter = len(intersections)
            if (nbInter == 0):
                if (not isIn1) and (not isIn2):
                    outside = True
                else:
                    print("Problem in arcIntersectsCanvasBoundary")
            elif (nbInter == 2):
                inter1, inter2 = intersections[0], intersections[1]
                if isIn1 and (not isIn2):
                    if self.liesOnSmallerArc(inter1, c, z1, z2):
                        z2New = inter1
                    elif self.liesOnSmallerArc(inter2, c, z1, z2):
                        z2New = inter2
                    else:
                        print("Problem in arcIntersectsCanvasBoundary")
                elif isIn2 and (not isIn1):
                    if self.liesOnSmallerArc(inter1, c, z2, z1):
                        z1New = inter1
                    elif self.liesOnSmallerArc(inter2, c, z2, z1):
                        z1New = inter2
                    else:
                        print("Problem in arcIntersectsCanvasBoundary")
                else:
                    if self.liesOnSmallerArc(inter1, c, z1, z2) and self.liesOnSmallerArc(inter2, c, z1, z2):
                        if self.liesOnSmallerArc(inter1, c, z1, inter2):
                            z1New, z2New = inter1, inter2
                        elif self.liesOnSmallerArc(inter2, c, z1, inter1):
                            z1New, z2New = inter2, inter1
                        else:
                            print("Problem in arcIntersectsCanvasBoundary")
                    else:
                        outside = True
            elif (nbInter % 2) == 1:
                print("Problem in arcIntersectsCanvasBoundary")
            else:
                # In this case, the full circle has 4 or more intersections with the canvas boundary, which is possible, but implies that it does not look straight
                many = True
        return inside, outside, many, z1New, z2New

    def pixelToH2(self, x, y):
        p = H2Point(self.pixelToComplex(x,y))
        return self.transform.inverse().kick(p)

    def drawH2Point(self, p, color='black', width=1):
        z = self.transform.kick(p).z
        self.drawPoint(z, color, width)


    def drawH2Segment(self, p1, p2, color='black', width=1):
        s = H2Segment(p1, p2)
        straight, c, r, z1, z2 = (self.transform.kickSegment(s)).getCircleAndEndpoints()
        if straight:
            self.drawSegment(z1, z2, color, width)
        else:
            self.drawSmallerArc(c, r, z1, z2, color, width)

    def playground(self):
        self.drawPoint(0, color='black', width=2)
        self.drawSegment(np.exp(2*1j*np.pi/3), 1, color=QColor('red'), width=1)
        self.drawCircle(0, 1, QColor('black'), 1)
        for i in range(len(self.pointsClicked)):
            zi = self.pointsClicked[i]
            self.drawPoint(zi, color='blue', width=2)
            if i>0:
                ziL = self.pointsClicked[i-1]
                self.drawSegment(zi, ziL, color='green')
        for i in range(len(self.H2pointsClicked)):
            pi = self.H2pointsClicked[i]
            self.drawH2Point(pi, color='yellow', width=2)
            if i>0:
                piL = self.H2pointsClicked[i-1]
                self.drawH2Segment(pi, piL, color='orange')
