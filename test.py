from PyQt5.QtWidgets import QApplication
from pyqtgraph.Qt import QtCore
import pyqtgraph as pg
import numpy as np
from matplotlib import cm
from QtMatplotlib import QtPlotter
import time


waypoints = np.stack([np.arange(10), np.arange(10), np.arange(10)]).T

qt_plotter = QtPlotter()
qt_plotter.scatter(waypoints[:, 0], waypoints[:, 1], c=waypoints[:, 2], live=True, plot_num=0)
# time.sleep(1)
waypoints = np.stack([np.arange(10), np.arange(10) + 1, np.arange(10)[::-1]]).T
qt_plotter.scatter(waypoints[:, 0], waypoints[:, 1], c=waypoints[:, 2], live=True, plot_num=1)