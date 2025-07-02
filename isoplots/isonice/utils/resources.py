import logging
import threading
import time

import numpy as np
import psutil
from nicegui import ui


Logger = logging.getLogger("utils/resources")


class Resources:
    def __init__(self, interval=2, units=None):
        """
        Tracks system resources

        Parameters
        ----------
        interval : int, default=2
            Interval frequency to check resources
        units : float, default=1024**3
            Units to display as. Defaults to GB
        """
        self.interval = 2
        self.units = units or 1024**3
        print(self.units)

        sys = psutil.virtual_memory()
        self.total = sys.total / self.units

        fontColor = '#ffffff'

        self.echart = ui.echart({
            'title': {
                'text': 'Memory (GB)',
                'left': 'center',
                'top': 10,
                'textStyle': {
                    'color': fontColor,
                    'fontSize': 12
                }
            },
            'xAxis': {'type': 'category', 'data': ['']},
            'yAxis': {
                'type': 'value',
                'max': self.total,
            },
            'legend': {
                'selectedMode': False,
                'orient': 'vertical',
                'bottom': 0,
                'itemGap': 2,
                'textStyle': {
                    'color': fontColor
                }
            },
            'series': [{
                    'type': 'bar',
                    'stack': 'total',
                    'name': 'App',
                    'data': [0],
                    'label': {
                        'show': True
                    }
                }, {
                    'type': 'bar',
                    'stack': 'total',
                    'name': 'System',
                    'data': [0],
                    'label': {
                        'show': True
                    }
                }, {
                    'type': 'bar',
                    'stack': 'total',
                    'name': 'Free',
                    'data': [0],
                    'label': {
                        'show': True
                    }
                },
            ],
        }).classes("h-full")

    def _track(self):
        """
        """
        process = psutil.Process()
        while not self.stopEvent.is_set():
            sys = psutil.virtual_memory()
            app = process.memory_info().rss / self.units

            used = sys.used / self.units
            free = self.total - (used + app)

            self.echart.options['series'][0]['data'][0] = np.round(app, 2)
            self.echart.options['series'][1]['data'][0] = np.round(used, 2)
            self.echart.options['series'][2]['data'][0] = np.round(free, 2)
            self.echart.update()

            time.sleep(self.interval)

    def start(self):
        """
        """
        self.stopEvent = threading.Event()
        self.thread = threading.Thread(
            target = self._track,
            daemon = True
        )
        self.thread.start()

    def stop(self):
        """
        """
        self.stopEvent.set()
