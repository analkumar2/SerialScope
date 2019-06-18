# -*- coding: utf-8 -*-

__author__ = "Dilawar Singh"
__copyright__ = "Copyright 2019-, Dilawar Singh"
__maintainer__ = "Dilawar Singh"
__email__ = "dilawars@ncbs.res.in"

import numpy as np
from collections import defaultdict
from ArduinoScope import config as C

logger = C.logger


class Channel():
    def __init__(self, graph, **kwargs):
        self.graph = graph
        self.xScale = 1.0
        self.yScale = 1.0
        self.lines = []
        self.color = kwargs.get('color', 'white')
        self.nData = 0
        self.offset = kwargs.get('offset', 0.0)
        self.freeze = False
        self.prev = (0.0, 0.0)
        self.curr = self.prev
        self.xRange = (0, 0.2)
        self.yRange = (0, 255)
        self.xStep = 10e-3
        self.axLine = None
        self.gridLines = []
        self.gridColor = kwargs.get('grid_color', 'gray25')

    def canvas(self):
        return self.graph.TKCanvas

    def draw_axis(self):
        # Horizontal axis.
        yLoc = self.offset
        if self.axLine is not None:
            self.canvas().delete(self.axLine)
        self.axLine = self.graph.DrawLine((self.xRange[0], yLoc),
                                          (self.xRange[1], yLoc),
                                          color=self.color)
        return self.axLine

    def draw_grid(self):
        """
        Draw grid on axis.
        """

        # delete old grid if any.
        for l in self.gridLines:
            self.canvas().delete(l)
        self.gridLines.clear()

        # draw new grid.
        xs = np.arange(self.xRange[0], self.xRange[1], self.xStep)
        for x in xs:
            gl = self.graph.DrawLine((x, self.offset + self.yRange[0]),
                                     (x, self.offset + self.yRange[1]),
                                     color=self.gridColor)
            self.gridLines.append(gl)

        # draw y grid. 1 section == 1 volt.
        ys = np.arange(self.yRange[0], self.yRange[1], 255/5)
        for y in ys:
            gl = self.graph.DrawLine((self.xRange[0], self.offset+y),
                    (self.xRange[1], self.offset+y),
                    color=self.gridColor)
            self.gridLines.append(gl)


    def draw_value(self):
        t1, y1 = self.curr
        t0, y0 = self.prev
        #  logger.debug(f"Drawing value {t1} {y1}")
        l = self.graph.DrawLine(
            (t0 * self.xScale, self.offset + (y0 * self.yScale)),
            (t1 * self.xScale, self.offset + (y1 * self.yScale)),
            color=self.color)
        self.lines.append(l)

    def add_value(self, t1, y1):
        """
        Add value to channel, draw it and update the canvas.
        Make sure to delete old lines when we roll-over to next frame.
        """
        self.nData += 1
        t0, y0 = self.prev
        t1 = t1 % C.T_
        self.curr = t1, y1
        if t0 >= t1:
            # This is NOT obvious. But when freeze is set True by a key-press, we wait
            # till maximum time for which we can plot in the screen is passed. Then
            # we freeze. Note that moving this logic to end of this block will
            # defeat the purpose. If you doubt me; just move the following two lines
            # around.
            if self.freeze:
                return
            for l in self.lines:
                self.canvas().delete(l)
            self.lines.clear()
            self.prev = (t1, y1)
            return

        self.draw_value()
        self.prev = self.curr
        if self.nData % 20 == 0:
            self.canvas().update()


class ScopeGUI():
    """
    Helper class for Scope GUI.
    """

    def __init__(self, window):
        self.window = window
        self.freezeChannels = False
        self.nFrame = 0
        self.nData = 0
        self.prev = 0.0, 0.0, 0.0
        self.curr = self.prev
        self.elems = defaultdict(list)
        self.colos = {'chanA.line': 'cyan', 'chanB.line': 'white'}
        self.channels = dict(A=Channel(self.window.FindElement("graph"),
                                       color="cyan", offset=-255),
                             B=Channel(self.window.FindElement("graph"),
                                       color="yellow", offset=51))
        self.nGrids = dict(x=20, y=10)
        self.bottomLeft = (0, -255)
        self.topRight = (C.T_, 255)
        self.rect = (self.bottomLeft, self.topRight)
        self.init_channels()

    def freeze(self, channel=None):
        if channel is None:
            for c in self.channels:
                self.channels[c].freeze = True
        else:
            self.channels[channel].freeze = True

    def unFreeze(self, channel=None):
        if channel is None:
            for c in self.channels:
                self.channels[c].freeze = False
        else:
            self.channels[channel].freeze = False


    def init_channels(self):
        for c in self.channels:
            ch = self.channels[c]
            ax = ch.draw_axis()
            self.elems['channel.axis'].append(ax)
            grid = ch.draw_grid()
            self.elems['channel.grid'].append(grid)

    def graph(self):
        return self.window.FindElement("graph")

    def canvas(self):
        return self.graph().TkCanvas

    def attach_label(self):
        if 'label' in self.elems:
            self.graph.TKCanvas.delete(self.elems['label'])

    def draw_axes(self):
        self.graph.Erase()
        for ch in self.channels:
            self.channels[ch].draw_axis()

    def add_values(self, t1, a1, b1):
        self.channels["A"].add_value(t1, a1)
        self.channels["B"].add_value(t1, b1)