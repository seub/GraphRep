#!/usr/bin/env python
# -*- coding: utf-8 -*-

from canvas import Canvas
import sys
from PySide6.QtWidgets import QApplication

def main():
    app = QApplication(sys.argv)
    cv = Canvas()
    app.exec()

if __name__ == '__main__':
    main()