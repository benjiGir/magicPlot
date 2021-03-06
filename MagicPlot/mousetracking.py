# -*- coding: utf-8 -*-

"""
Created on 2014/12/05

Author: Renaud CARRIERE

Modified on 2020/04/23

Author: Benjamin Girard

Copyright: SoftBank Robotics 2020
"""
from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication
import pyqtgraph as pg

dict_values = {}

class Crosshair(pg.PlotItem):
    '''
    Class Crosshair

    PlotItem qui vient s'ajouter sur le graphique principale, affichant un repère synchronisé avec
    les mouvements de la souris dans le champs de vision du graphique.
    Permet de récupérer les coordonnées et d'obtenir les valeurs d'un point sur le graphique.

    :param
        plot: PlotItem contennant les données des courbes affichées
    '''

    def __init__(self, plot):
        super(Crosshair, self).__init__()

        self.data_list = []
        self.data_list_x_sorted = []
        self.plot = plot
        self.dict_values = {}

        self.v_line = pg.InfiniteLine(
            angle=90, movable=False, pen=pg.mkPen('#000'))
        self.h_line = pg.InfiniteLine(
            angle=0, movable=False, pen=pg.mkPen('#000'))

        self.label_x = pg.TextItem(
            border=pg.mkPen('#ffaa55'),
            fill=pg.mkBrush(0, 0, 0, 210), anchor=(0.5, 1.0))
        self.label_y = pg.TextItem(
            border=pg.mkPen('#ffaa55'),
            fill=pg.mkBrush(0, 0, 0, 210), anchor=(0.0, 0.5))

        self.label = pg.LabelItem(justify="right")

        self.plot.addItem(self.v_line, ignoreBounds=True)
        self.plot.addItem(self.h_line, ignoreBounds=True)
        self.plot.addItem(self.label_x, ignoreBounds=True)
        self.plot.addItem(self.label_y, ignoreBounds=True)

        self.view_box = self.plot.getViewBox()
        self.vb_range = self.view_box.viewRange()

        self.v_line.hide()
        self.h_line.hide()
        self.label_x.hide()
        self.label_y.hide()

        self.min_x = None
        self.max_x = None
        self.min_y = None
        self.max_y = None

        self.y_text_list = []
        self.ycircle_list = []

        self.plot.scene().sigMouseMoved.connect(self.mouse_moved)
        self.plot.scene().sigMouseClicked.connect(self.mouse_clicked)

    def update(self):

        curve_id = 0
        for plot_data_item in self.plot.listDataItems():
            (self.x_data, y_data) = plot_data_item.getData()
            self.x_data = self.x_data.tolist()
            x_data_log = [10**val for val in self.x_data]
            y_data = y_data.tolist()
            color = plot_data_item.curve.opts['pen'].color().getRgb()

            self.data_list.append(
                {
                    'color': color,
                    'data': {round(self.x_data[cpt], 2): {'x': self.x_data[cpt],
                                                          'xlog': x_data_log[cpt],
                                                          'y': y_data[cpt]}
                             for cpt in range(len(x_data_log))},
                    'txt_pos': {'x': None, 'y': None}
                }
            )

            self.data_list_x_sorted.append(
                sorted(self.data_list[curve_id]['data'].keys())
            )

            curve_id += 1

        if len(self.data_list) > 0:
            list_x = [data['x'] for data in self.data_list[0]['data'].values()]
            list_y = [data['y'] for data in self.data_list[0]['data'].values()]
            try:
                self.min_x = min(list_x)
                self.max_x = max(list_x)
                self.min_y = min(list_y)
                self.max_y = max(list_y)
            except ValueError:
                self.min_x = None
                self.max_x = None
                self.min_y = None
                self.max_y = None

        else:
            self.min_x = None
            self.max_x = None
            self.min_y = None
            self.max_y = None

        for data in self.data_list:
            self.y_text_list.append(
                pg.TextItem(
                    border=pg.mkPen(
                        color=(data['color'][0],
                               data['color'][1],
                               data['color'][2])),
                    fill=pg.mkBrush(0, 0, 0, 210),
                    anchor=(-0.1, 0.5)
                )
            )
            html_cross = '<span style="color: #%s; \
            font-size: 12px;"><mark><b>X</b>' \
            % pg.colorStr(pg.mkColor('#ffaa55'))[:-2]
            html_cross += '</mark></span>'

            self.ycircle_list.append(
                pg.TextItem(html=html_cross,
                            anchor=(0.45, 0.5)))

        for item in self.y_text_list:
            self.plot.addItem(item)
            item.hide()

        for item in self.ycircle_list:
            self.plot.addItem(item)
            item.hide()

    def mouse_moved(self, pos):
        if self.plot.sceneBoundingRect().contains(pos):
            mouse_point = self.view_box.mapSceneToView(pos)
            self.mouse_pos_x = mouse_point.x()
            self.mouse_pos_y = mouse_point.y()

            self.moved()
            self.vb_range = self.view_box.viewRange()

    def mouse_clicked(self):
        modifiers = QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ShiftModifier:
            x_value = self.mouse_pos_x
            y_value = self.mouse_pos_y
            x_log = 10 ** x_value

            roi = pg.ROI(pos=(x_value, y_value),
                         size=(0.005, 0.07),
                         movable=False,
                         removable=True)

            roi.setAcceptedMouseButtons(QtCore.Qt.LeftButton)

            arrow = pg.ArrowItem(pos=(0.0005, 0.1))
            arrow.setParentItem(roi)

            self.text = pg.TextItem(color="#000",
                text='Frequence: {:.2e} Hz \nNiveau: {:.2f} dBµV'.format(x_log, y_value),
                anchor=(0, 1))
            self.text.setParentItem(roi)
            

            roi.sigClicked.connect(self.roi_click)
            roi.sigRemoveRequested.connect(self.roi_remove)

            self.plot.addItem(roi)

            self.dict_values[roi] = {
                'Frequence': f"{x_log:.2e}",
                'Level': f"{y_value:.2f}"
            }

    def roi_remove(self, roi):
        self.plot.removeItem(roi)
        self.dict_values.pop(roi)

    def roi_click(self, roi):
        for item in self.plot.items:
            if isinstance(item, pg.ROI):
                item.setZValue(0)
        roi.setZvalue(1)

    def moved(self):

        x_value = self.mouse_pos_x
        x_value_log = round((10**x_value))
        y_value = self.mouse_pos_y

        if x_value >= self.vb_range[0][0] and\
                x_value <= self.vb_range[0][1] and\
                y_value >= self.vb_range[1][0] and\
                y_value <= self.vb_range[1][1]:

            self.v_line.show()
            self.h_line.show()

            self.v_line.setPos(x_value)
            self.h_line.setPos(y_value)

            self.set_line_text(x_value, y_value, x_value_log)

        else:
            self.v_line.hide()
            self.h_line.hide()
            for item in self.ycircle_list:
                item.hide()

            self.label_x.hide()
            self.label_y.hide()
            for item in self.y_text_list:
                item.hide()

    def set_line_text(self, x_value, y_value, x_value_log=None):

        textx = "{:.2e}".format(x_value_log)
        texty = '%.3f' % y_value

        html = '<span style="color: #%s; \
                 font-size: 12px;"><mark>' %\
            pg.colorStr(pg.mkColor('#ffaa55'))[:-2]
        self.label_x.setHtml('%s%s%s' % (html, textx, '</mark></span>'))
        self.label_y.setHtml('%s%s%s' % (html, texty, '</mark></span>'))

        self.label_x.show()
        self.label_y.show()

        self.label_x.setPos(x_value, self.vb_range[1][0])
        self.label_y.setPos(self.vb_range[0][0], y_value)
