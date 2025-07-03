from PyQt6.QtWidgets import QApplication
from PyQt6 import QtCore
import pyqtgraph as pg
import numpy as np
import matplotlib.pyplot as plt
import multiprocessing as mp
import sys
import time

pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

class QtPlotter:
    def __init__(self, timer_delay=1, win_title="QtMatplotlib"):
        self.timer_delay = timer_delay
        self.win_title = win_title
        self.total_plot_num = 0
        self.send_dict = {'add': {}, 'update': []}
        self.window_exist = False
        
    def xlabel(self, label: str):
        self._send_axis_update(x_label=label)

    def ylabel(self, label: str):
        self._send_axis_update(y_label=label)

    def xlim(self, left: float, right: float):
        self._send_axis_update(xlim=(left, right))

    def ylim(self, bottom: float, top: float):
        self._send_axis_update(ylim=(bottom, top))
        
    def scatter(self, x, y, c=None, s=10, name="", live=False, plot_num=None):
        plot_num = self._add_plot(plot_num, live, 'scatter', size=s, name=name)
        self.send_dict['update'].append({
            'plot_num': plot_num,
            'plot_type': 'scatter',
            'x': x,
            'y': y,
            'colors': c
        })
        self._update_plot(live)

    def plot(self, *args, live=False, plot_num=None, name="", **kwargs):
        """
        Usage like matplotlib.pyplot.plot():
        - plot(y)
        - plot(x, y)
        - plot(x, y, color='r', linewidth=2)
        """
        if len(args) == 1:
            y = np.asarray(args[0])
            x = np.arange(len(y))
        elif len(args) == 2:
            x = np.asarray(args[0])
            y = np.asarray(args[1])
        else:
            raise ValueError("plot() accepts either plot(y) or plot(x, y)")

        color = kwargs.get("color", 'k')  # default: black
        width = kwargs.get("linewidth", 2)

        pen_kwargs={'color': color, 'width': width}

        plot_num = self._add_plot(plot_num, live, 'line', pen=pen_kwargs, name=name)
        self.send_dict['update'].append({
            'plot_num': plot_num,
            'plot_type': 'line',
            'x': x,
            'y': y,
            'pen': pen_kwargs
        })
        self._update_plot(live)

    def _init_process(self):
        self.queue = mp.Queue()
        self.plot_process = QtPlotterProcess()
        self.process = mp.Process(target=self.plot_process.run, args=(
            self.queue,
            self.timer_delay,
            self.win_title
        ))
        self.process.start()
        self.window_exist = True
    
    def _add_plot(self, plot_num, live, plot_type, **kwargs):
        if not live or not self.window_exist:
            self._init_process()
        self.send_dict = {'add': [], 'update': []}
        if plot_num is None or plot_num == self.total_plot_num:
            self.total_plot_num += 1
            self.send_dict['add'].append({'plot_type': plot_type, **kwargs})
            return self.total_plot_num - 1
        elif 0 <= plot_num < self.total_plot_num:
            return plot_num
        else:
            raise ValueError("Invalid plot_num")
    
    def _update_plot(self, live):
        self.queue.put(self.send_dict)
        if not live:
            self.process.join()
            self.total_plot_num -= 1
            
    def _send_axis_update(self, **kwargs):
        self.queue.put({'axis': kwargs})
            
    

class QtPlotterProcess:

    def __init__(self):
        pass

    def run(self, queue, timer_delay, win_title, show_fps=False):
        self.queue = queue
        self.app = QApplication([])
        self.win = pg.GraphicsLayoutWidget(title=win_title)
        self.win.show()
        self.figure = self.win.addPlot(title='')
        self.figure.enableAutoRange('xy', True)
        self.figure.setAspectLocked(True)
        self.colormap = plt.get_cmap('viridis')
        self.axis_config = {
            "x_label": "",
            "y_label": "",
            "xlim": None,
            "ylim": None
        }

        self.plots = []
        self.data = []

        # Timer
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_figure)
        self.timer.start(timer_delay)

        self.figure.scene().sigMouseMoved.connect(self._on_mouse_move)
        self.label = pg.LabelItem(justify='left')
        self.win.addItem(self.label, row=1, col=0)
        self.figure.showGrid(x=True, y=True, alpha=0.3)
        
        self.show_fps = show_fps
        if show_fps:
            self.fps_text = pg.TextItem(text='', anchor=(1, 1), color=(150, 150, 150), 
                                        fill=pg.mkBrush(255, 255, 255, 180))
            self.figure.addItem(self.fps_text)
            self.fps_text.setZValue(1000)
            self.elapsed_timer = QtCore.QElapsedTimer()
            self.elapsed_timer.start()
            self.frame_count = 0

        sys.exit(self.app.exec())
        
    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.Type.Close:
            self.app.quit()
            return True
        return False
    
    def _apply_axis_config(self):
        if self.axis_config["x_label"]:
            self.figure.setLabel("bottom", self.axis_config["x_label"])
        if self.axis_config["y_label"]:
            self.figure.setLabel("left", self.axis_config["y_label"])
        if self.axis_config["xlim"]:
            self.figure.setXRange(*self.axis_config["xlim"], padding=0)
        if self.axis_config["ylim"]:
            self.figure.setYRange(*self.axis_config["ylim"], padding=0)
    
    def _update_fps_text(self):
        self.frame_count += 1
        elapsed = self.elapsed_timer.elapsed()
        if elapsed > 1000:
            fps = self.frame_count * 1000.0 / elapsed
            self.fps_text.setText(f"FPS: {fps:.1f}")
            self.elapsed_timer.restart()
            self.frame_count = 0


    def _on_mouse_move(self, evt):
        pos = self.figure.vb.mapSceneToView(evt)
        x, y = pos.x(), pos.y()
        self.label.setText(f"x {x:.2f}, y {y:.2f}")

    def _get_brushes(self, z):
        z_normalized = (z - z.min()) / (z.max() - z.min())
        brushes = [pg.mkBrush(*[int(c * 255) for c in self.colormap(value)[:3]]) for value in z_normalized]
        return brushes
    
    def add_plot(self, plot_type, size=10, pen=None, name=""):
        if plot_type == 'scatter':
            item = pg.ScatterPlotItem(size=size, brush=pg.mkBrush(0, 0, 0), name=name)
        elif plot_type == 'line':
            mk_pen = pg.mkPen(**pen) if pen else pg.mkPen(0, 0, 0)
            item = pg.PlotDataItem(pen=mk_pen, name=name)
        else:
            raise ValueError(f"Unknown plot_type: {plot_type}")
        self.figure.addItem(item)
        self.plots.append(item)
        self.data.append([])
        return len(self.plots) - 1
            
    def update_plot(self, plot_num, plot_type, **kwargs):
        item = self.plots[plot_num]
        
        if plot_type == 'scatter':
            item.setData(pos=np.column_stack((kwargs['x'], kwargs['y'])))
            if kwargs.get('colors') is not None:
                item.setBrush(self._get_brushes(kwargs['colors']))
                
        elif plot_type == 'line':
            item.setData(x=kwargs['x'], y=kwargs['y'])
            if 'pen' in kwargs and kwargs['pen'] is not None:
                item.setPen(pg.mkPen(**kwargs['pen']))
            
        self.data[plot_num] = (kwargs['x'], kwargs['y'])

    def update_figure(self):
        # print("Updating figure...", time.time())
        while not self.queue.empty():
            data = self.queue.get()
            
            if 'axis' in data:
                for key, value in data['axis'].items():
                    self.axis_config[key] = value
                self._apply_axis_config()

            # Handle new plots
            for add_dict in data.get('add', []):
                self.add_plot(add_dict['plot_type'],
                            size=add_dict.get('size', 10),
                            pen=add_dict.get('pen', None),
                            name=add_dict.get('name', ""))

            # Handle updates
            for update_dict in data.get('update', []):
                self.update_plot(update_dict['plot_num'],
                                update_dict['plot_type'],
                                x=update_dict['x'],
                                y=update_dict['y'],
                                colors=update_dict.get('colors', None))

        if self.show_fps:
            self._update_fps_text()