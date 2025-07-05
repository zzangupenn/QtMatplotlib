import numpy as np

class QtMatplotlib:
    def __init__(self, timer_delay=1, win_title="QtMatplotlib", show_fps=False):
        import pyqtgraph as pg
        self.pg = pg
        import PyQt6
        self.PyQt6 = PyQt6
        self.timer_delay = timer_delay
        self.win_title = win_title
        self.total_plot_num = 0
        self.send_dict = {'add': {}, 'update': []}
        self.window_exist = False
        self.show_fps = show_fps
        
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
    
    def plot(self, x=None, y=None, live=False, plot_num=None, name="", **kwargs):
        """
        Usage like matplotlib.pyplot.plot():
        - plot(y)
        - plot(x, y)
        - plot(x, y, color='r', linewidth=2)
        """
        if x is None and y is None:
            raise ValueError("plot() requires either x or y")

        if x is None:
            x = np.arange(len(y))
            y = np.asarray(y)
        elif y is None:
            y = np.asarray(x)
            x = np.arange(len(x))

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
        import multiprocessing as mp
        ctx = mp.get_context("spawn")  # force spawn context
        self.queue = ctx.Queue()
        self.plot_process = QtPlotterProcess()
        self.start_event = ctx.Event()
        self.process = ctx.Process(target=self.plot_process.run, args=(
            self.queue,
            self.timer_delay,
            self.win_title,
            self.start_event,
            self.show_fps,
        ))
        self.process.daemon = True  # 🔧 ensures it dies with the parent
        self.process.start()
        self.start_event.wait()
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
        if not self.window_exist:
            self._init_process()
        self.queue.put({'axis': kwargs})
            
    

class QtPlotterProcess:

    def __init__(self):
        pass

    def run(self, queue, timer_delay, win_title, start_event, show_fps):
        import pyqtgraph as pg
        self.pg = pg
        self.pg.setConfigOption('background', '#191919')
        self.pg.setConfigOption('foreground', 'w')
        import PyQt6
        self.PyQt6 = PyQt6
        self.queue = queue
        self.app = self.PyQt6.QtWidgets.QApplication([])
        self.win = self.pg.GraphicsLayoutWidget(title=win_title)
        self.win.show()
        self.figure = self.win.addPlot(title='')
        self.figure.enableAutoRange('xy', True)
        # self.figure.setAspectLocked(True)
        import matplotlib.pyplot as plt
        self.colormap = plt.get_cmap('viridis')
        self.axis_config = {
            "x_label": None,
            "y_label": None,
            "xlim": None,
            "ylim": None
        }

        self.plots = []
        self.data = []

        # Timer
        self.timer = self.PyQt6.QtCore.QTimer()
        self.timer.timeout.connect(self.update_figure)
        self.timer.start(timer_delay)

        self.figure.scene().sigMouseMoved.connect(self._on_mouse_move)
        self.label = self.pg.LabelItem(justify='left')
        self.win.addItem(self.label, row=1, col=0)
        self.figure.showGrid(x=True, y=True, alpha=0.3)
        
        self.show_fps = show_fps
        if show_fps:
            self.fps_text = self.pg.TextItem(text='', anchor=(1, 1), color=(150, 150, 150), 
                                        fill=self.pg.mkBrush(255, 255, 255, 180))
            self.figure.addItem(self.fps_text)
            self.fps_text.setZValue(1000)
            self.elapsed_timer = self.PyQt6.QtCore.QElapsedTimer()
            self.elapsed_timer.start()
            self.frame_count = 0
        import sys
        start_event.set()
        sys.exit(self.app.exec())
    
    def _apply_axis_config(self):
        if self.axis_config["x_label"]:
            self.figure.setLabel("bottom", self.axis_config["x_label"])
        if self.axis_config["y_label"]:
            self.figure.setLabel("left", self.axis_config["y_label"])
        if self.axis_config["xlim"]:
            self.figure.enableAutoRange(x=False)
            self.figure.setXRange(self.axis_config["xlim"][0], self.axis_config["xlim"][1])
        if self.axis_config["ylim"]:
            self.figure.enableAutoRange(y=False)
            self.figure.setYRange(self.axis_config["ylim"][0], self.axis_config["ylim"][1])

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
        brushes = [self.pg.mkBrush(*[int(c * 255) for c in self.colormap(value)[:3]]) for value in z_normalized]
        return brushes
    
    def add_plot(self, plot_type, size=10, pen=None, name=""):
        if plot_type == 'scatter':
            item = self.pg.ScatterPlotItem(size=size, brush=self.pg.mkBrush(0, 0, 0), name=name)
        elif plot_type == 'line':
            mk_pen = self.pg.mkPen(**pen) if pen else self.pg.mkPen(0, 0, 0)
            item = self.pg.PlotDataItem(pen=mk_pen, name=name)
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
                item.setPen(self.pg.mkPen(**kwargs['pen']))
            
        self.data[plot_num] = (kwargs['x'], kwargs['y'])

    def update_figure(self):
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