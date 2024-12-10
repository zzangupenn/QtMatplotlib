from PyQt5.QtWidgets import QApplication
from pyqtgraph.Qt import QtCore
import pyqtgraph as pg
import numpy as np
import matplotlib.pyplot as plt
import multiprocessing as mp
import sys
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

class QtPlotterProcess:
    
    def __init__(self):
        pass
        
    def run(self, queue, timer_delay, win_title):
        self.queue = queue
        self.app = QApplication([])
        self.win = pg.GraphicsLayoutWidget(show=True, title=win_title)
        self.plot = self.win.addPlot(title='')
        self.plot.enableAutoRange('xy', True)
        self.plot.setAspectLocked(True)
        self.colormap = plt.get_cmap('viridis')
        
        self.plots = []
        self.data = []
        
        # Timer to change colors every second
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plots)
        self.timer.start(timer_delay)  # Update every 1000 ms (1 second)
        self.plot.scene().sigMouseMoved.connect(self.on_mouse_move)
        self.label = pg.LabelItem(justify='left')
        self.win.addItem(self.label, row=1, col=0)
        self.plot.showGrid(x=True, y=True, alpha=0.3)
        
        sys.exit(self.app.exec_())
        
    def on_mouse_move(self, evt):
        """Handle mouse move events to display coordinates."""
        pos = self.plot.vb.mapSceneToView(evt)
        x, y = pos.x(), pos.y()
        self.label.setText(f"x {x:.2f}, y {y:.2f}")
        
    def get_brushes(self, z):
        z_normalized = (z - z.min()) / (z.max() - z.min())
        brushes = [pg.mkBrush(*[int(c * 255) for c in self.colormap(value)[:3]]) for value in z_normalized]
        return brushes
        
    def add_scatter_plot(self, size=10, name=""):
        brush = pg.mkBrush((0, 0, 0))
        scatter_plot = pg.ScatterPlotItem(size=size, brush=brush, name=name)
        self.plots.append(scatter_plot)
        self.data.append([])
        self.plot.addItem(scatter_plot)
        return len(self.plots) - 1
        
    def update_scatter(self, plot_num, data_in, colors=None):
        if colors is not None:
            brushes = self.get_brushes(colors)
        self.plots[plot_num].setData(pos=np.column_stack((data_in[:, 0], data_in[:, 1])))
        self.data[plot_num] = data_in
        if colors is not None:
            self.plots[plot_num].setBrush(brushes)    
        # color_bar = pg.ColorBarItem(values=(colors.min(), colors.max()), cmap=self.colormap)
        # color_bar.setImageItem(None)  # No image, just a color bar
        # self.win.addItem(color_bar, row=0, col=1)
    
    def update_plots(self):
        while not self.queue.empty():
            data = self.queue.get()
            if len(data['add']) > 0:
                self.add_scatter_plot(data['add']['size'], data['add']['name'])
            if len(data['update']) > 0:
                for update_dict in data['update']:
                    self.update_scatter(update_dict['plot_num'], update_dict['data_in'], update_dict['colors'])
        

class QtPlotter:
    def __init__(self, timer_delay=50, win_title="QtMatplotlib"):
        self.timer_delay = timer_delay
        self.win_title = win_title
        self.total_plot_num = 0
        self.send_dict = {'add': {}, 'update': []}
        self.window_exist = False

    def init_process(self):
        self.queue = mp.Queue()
        self.plot_process = QtPlotterProcess()
        self.process = mp.Process(target=self.plot_process.run, args=(self.queue, 
                                                                 self.timer_delay,
                                                                 self.win_title))
        self.process.start()
        self.window_exist = True

    def add_scatter_plot(self, size=10, name=""):
        self.total_plot_num += 1
        self.send_dict['add'] = {'size': size, 'name': name}
        return self.total_plot_num - 1
            
    def update_scatter(self, plot_num, data_in, colors=None):
        self.send_dict['update'].append({'plot_num': plot_num, 'data_in': data_in, 'colors': colors})
    
    def scatter(self, x, y, c=None, s=10, name="", live=False, plot_num=None):
        if not live or self.window_exist is False:
            self.init_process()
        self.send_dict = {'add': {}, 'update': []}
        if plot_num is None:
            plot_num = self.add_scatter_plot(size=s, name=name)
        else:
            if plot_num >= self.total_plot_num + 1:
                raise ValueError("plot_num must be less than the total number of plots")
            elif plot_num < 0:
                raise ValueError("plot_num must be greater than or equal to 0")
            elif plot_num == self.total_plot_num:
                self.add_scatter_plot(size=s, name=name)
        self.update_scatter(plot_num, np.column_stack((x, y)), colors=c)
        self.queue.put(self.send_dict)
        if not live:
            self.process.join()
            self.total_plot_num -= 1
        
        
            
    





