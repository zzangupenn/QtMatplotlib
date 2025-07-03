import numpy as np
from QtMatplotlib import QtPlotter
import time




qt_plotter = QtPlotter()
# for _ in range(1):
#     waypoints = np.stack([np.arange(10), np.arange(10), np.arange(10)]).T
#     qt_plotter.scatter(waypoints[:, 0], waypoints[:, 1], c=waypoints[:, 2], s=10, live=True, plot_num=0)
#     time.sleep(0.5)
#     waypoints = np.stack([np.arange(10), np.arange(10) + 1, np.arange(10)[::-1]]).T
#     qt_plotter.scatter(waypoints[:, 0], waypoints[:, 1], c=waypoints[:, 2], s=10, live=True, plot_num=0)
#     time.sleep(0.5)

# qt_plotter.plot(np.sin(np.linspace(0, 10, 100)), live=True)

# x and y
# qt_plotter.plot(np.linspace(0, 10, 100), np.sin(np.linspace(0, 10, 100)), live=True)

# # With color and linewidth
# qt_plotter.plot(np.linspace(0, 10, 100), np.cos(np.linspace(0, 10, 100)), color='r', linewidth=4, live=True)


# Example of animating a sine wave using QtPlotter
fps = 60  # frames per second
qt = QtPlotter(timer_delay=10, win_title="Sine Wave Animation")

x = np.linspace(0, 2 * np.pi, 500)
amplitude = np.sin(x)
plot_num = None  # initialize to None to create new plot on first call

for i in range(200):  # animate 200 frames
    phase_shift = i * 0.1
    y = np.sin(x + phase_shift)

    # plot_num=0 after first call to reuse the same plot
    plot_num = 0
    qt.plot(x, y, color='blue', linewidth=2, live=True, plot_num=plot_num)
    time.sleep(1 / fps)  # control frame rate