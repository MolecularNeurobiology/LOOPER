# -*- coding: utf-8 -*-
"""
Trace Viewer


For use with the Ray Lab automated autoresuscitation system and PCC software,
and Breathe Easy with BASSPRO and STAGG.

Copyright (C) 2022  Christopher Scott Ward
Additional contributions from Savanah Lusk, Dipak Patel, Russel Ray

***
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
***

=Features=
*load and view Signal Data
*load and view Data Annotations
*load and view Derived Parameters
*test BASSPRO settings for breath detection
*save graphs
*run batch export of graphs


"""

__version__ = '0.0.1'

#%% import libraries

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtCore import QAbstractTableModel, QModelIndex 
from PyQt5.QtWidgets import QMainWindow, QApplication, QLabel, QPushButton 
from PyQt5.QtWidgets import QTextEdit, QTableView, QHBoxLayout, QVBoxLayout
from PyQt5.QtWidgets import QFileDialog, QComboBox, QDialog, QRadioButton
from PyQt5.QtWidgets import QButtonGroup, QDoubleSpinBox
import pandas
import sys
import re
import os
import traceback
from pyqtgraph import PlotWidget, plot
import pyqtgraph
# custom modules
import python_module
import SHAM


#%% define functions

def html_text_color(text,color):
    text_output = f'<span style="color:{color}">{text}</span><br>'

    return text_output









#%% define classes

# settings subguis?
class PandasModel(QAbstractTableModel):
    """
    A model to interface a Qt view with pandas dataframe
    
    code adapted from example located at
    https://doc.qt.io/qtforpython/examples/example_external__pandas.html
    
    """

    def __init__(self, dataframe: pandas.DataFrame, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self._dataframe = dataframe.copy()



    def rowCount(self, parent=QModelIndex()) -> int:
        """ Override method from QAbstractTableModel

        Return row count of the pandas DataFrame
        """
        if parent == QModelIndex():
            return len(self._dataframe)

        return 0



    def columnCount(self, parent=QModelIndex()) -> int:
        """Override method from QAbstractTableModel

        Return column count of the pandas DataFrame
        """
        if parent == QModelIndex():
            return len(self._dataframe.columns)
        return 0

    
    def setData(self, index, value, role):
        if role == Qt.EditRole:
            self._dataframe.iloc[index.row(),index.column()] = value
            return True


    def data(self, index: QModelIndex, role=Qt.ItemDataRole):
        """Override method from QAbstractTableModel

        Return data cell from the pandas DataFrame
        """
        if not index.isValid():
            return None

        if role == Qt.DisplayRole or role == Qt.EditRole:
            value = str(self._dataframe.iloc[index.row(), index.column()])
            return value

        return None


    
    def flags(self,index):
        # presumable needed in order to provide editable table functionality
        
        # use of | performs a bitwise 'or' comparison. in this case it
        # results in creation of a Qt.ItemFlag ...
        return Qt.ItemIsSelectable|Qt.ItemIsEnabled|Qt.ItemIsEditable
    
    

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole
        ):
        """Override method from QAbstractTableModel

        Return dataframe index as vertical header data and columns as horizontal header data.
        """
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._dataframe.columns[section])

            if orientation == Qt.Vertical:
                return str(self._dataframe.index[section])
            
        return None






class SettingEditor(QDialog):
    def __init__(self,parent,attribute,df_name,title):
        super(SettingEditor,self).__init__()
        
        self.parent = parent
        self.attribute = attribute
        self.df_name = df_name
        
        # set up window
        self.setWindowTitle(title)
        self.df = getattr(getattr(parent,attribute),df_name)
        layout = QVBoxLayout()
        self.setLayout(layout) 
        # setup table
        self.view = QTableView(self)
        self.df_model = PandasModel(self.df)
        
        # adjust aesthetics
        self.view.horizontalHeader().setStretchLastSection(True)
        self.view.setAlternatingRowColors(True)
        # adjust behaviors
        self.view.setSelectionBehavior(QTableView.SelectRows)

        # display the data model
        self.view.setModel(self.df_model)
        layout.addWidget(self.view)
        
        # apply button
        self.apply_button = QPushButton('Apply and Close',self)
        self.apply_button.clicked.connect(self.apply_button_action)
        layout.addWidget(self.apply_button)
        
        # close button
        self.cancel_button = QPushButton('Cancel and Close',self)
        self.cancel_button.clicked.connect(self.cancel_button_action)
        layout.addWidget(self.cancel_button)
        
        # adjust aesthetics
        self.adjust_aesthetics()
        
        
        self.show()
    
    def apply_button_action(self):
        setattr(
            getattr(
                self.parent,
                self.attribute
                ),
            self.df_name,
            self.df_model._dataframe
            )
        self.close()
        
    def cancel_button_action(self):
        self.close()
        
    def adjust_aesthetics(self):
        # hide/show/modify columns/rows as needed depending on settings
        for i in range(len(list(self.df.columns))):
            if list(self.df.columns)[i] in ['Display','Category']:
                self.view.hideColumn(i)  
                





# main window
class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow,self).__init__()

        self.setWindowTitle('Trace Viewer - v{}'.format(__version__))
        self.setGeometry(10,10,1200,960)
        self.move(100,100)
        self.Label_1=QLabel(
            '<h1>Trace Viewer - v{}</h1>'.format(__version__),
            parent=self
            )
        self.Label_1.setAlignment(Qt.AlignCenter)
        
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
  
        # constants
        self.data_mode = 'autores'
        
        self.signal_file_path = ''
        self.signal_data = pandas.DataFrame()
        
        self.breath_list_path = ''
        self.breath_list_data = pandas.DataFrame()
        
        self.beat_list_path = ''
        self.beat_list_data = pandas.DataFrame()
        
        self.autores_results_path = ''
        self.autores_results_data = {
            'Baseline':pandas.DataFrame(),
            'Challenge':pandas.DataFrame()
            }
        
        self.text1 = QTextEdit(self)
        self.text1.insertHtml(
            html_text_color(
                f'<strong><em>Trace Viewer - VERSION {__version__}</em></strong>',
                'black'
                )
            )
        
        # graphs
        self.graph = {}
        self.plotted = {}
        self.graph_counter = 0
        self.plotted_counter = 0
        self.x_min = 0
        self.x_max = 30
        
        self.pen_style_dict = {
            'Solid':Qt.SolidLine,
            'Dashed':Qt.DashLine,
            'Dotted':Qt.DotLine
            }
        
        # layouts
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)
        
        self.upper_layout = QHBoxLayout()
        self.upper_layout.addWidget(self.Label_1)
        self.layout.addLayout(self.upper_layout)
        
        self.middle_layout = QHBoxLayout()
        self.layout.addLayout(self.middle_layout)
        
        self.lower_layout = QHBoxLayout()
        self.layout.addLayout(self.lower_layout)
        
        self.graph_layout = QVBoxLayout()                
        self.controls_layout = QHBoxLayout()
        self.controls_layout_A = QVBoxLayout()
        self.controls_layout_B = QVBoxLayout()
        self.middle_layout.addLayout(self.graph_layout)
        self.middle_layout.addLayout(self.controls_layout)
        self.controls_layout.addLayout(self.controls_layout_A)
        self.controls_layout.addLayout(self.controls_layout_B)
        
        # add feedback window
        self.lower_layout.addWidget(self.text1)
        

        
        # select data type
        #    toggle data source
        self.controls_layout_A_radio = QVBoxLayout()
        self.controls_layout_A.setAlignment(Qt.AlignTop)
        self.controls_layout_A.addLayout(self.controls_layout_A_radio, stretch=0)
        self.controls_layout_A_radio.setAlignment(Qt.AlignTop)

        # select graph destination
        #    combo box with entry for each graph
        self.time_start_label = QLabel('Graph Time: Minimum')
        self.controls_layout_A.addWidget(self.time_start_label)
        self.time_start_value = QDoubleSpinBox(self)
        self.time_start_value.setValue(self.x_min)
        self.time_start_value.setMinimum(0)
        self.time_start_value.setMaximum(999999)
        self.time_start_value.setSingleStep(1)
        self.controls_layout_A.addWidget(self.time_start_value)
        self.time_window_label = QLabel('Graph Time: Window')
        self.controls_layout_A.addWidget(self.time_window_label)
        self.time_window_value = QDoubleSpinBox(self)
        self.time_window_value.setValue(self.x_max-self.x_min)
        self.time_window_value.setMinimum(0)
        self.time_window_value.setMaximum(999999)
        self.time_window_value.setSingleStep(1)
        self.controls_layout_A.addWidget(self.time_window_value)
        
        self.graph_selector = QComboBox(self)
        self.controls_layout_A_radio.addWidget(self.graph_selector)
        
        self.data_radio_group = QButtonGroup()
        self.data_label = QLabel('Select Data Type')
        self.controls_layout_A_radio.addWidget(self.data_label)
        
        self.signal_radio = QRadioButton('Signal')
        self.data_radio_group.addButton(self.signal_radio)
        self.signal_radio.data = 'Signal'
        self.signal_radio.toggled.connect(self.select_data_action)
        self.controls_layout_A_radio.addWidget(self.signal_radio)
        
        self.breath_beat_radio = QRadioButton('Breath/Beat')
        self.data_radio_group.addButton(self.breath_beat_radio)
        self.breath_beat_radio.data = 'Breath/Beat'
        self.breath_beat_radio.toggled.connect(self.select_data_action)
        self.controls_layout_A_radio.addWidget(self.breath_beat_radio)
        
        self.derived_filter_radio = QRadioButton('Derived Filter')
        self.data_radio_group.addButton(self.derived_filter_radio)
        self.derived_filter_radio.data = 'Derived Filter'
        self.derived_filter_radio.toggled.connect(self.select_data_action)
        self.controls_layout_A_radio.addWidget(self.derived_filter_radio)
        
        self.derived_measure_radio = QRadioButton('Derived Measure')
        self.data_radio_group.addButton(self.derived_measure_radio)
        self.derived_measure_radio.data = 'Derived Measure'
        self.derived_measure_radio.toggled.connect(self.select_data_action)
        self.controls_layout_A_radio.addWidget(self.derived_measure_radio)
        
        #    signal
        self.signal_label = QLabel('Select Signal:')
        self.controls_layout_A.addWidget(self.signal_label)
        self.signal_selector = QComboBox(self)
        self.controls_layout_A.addWidget(self.signal_selector)
        
        #    breath/beat
        self.breath_beat_label = QLabel('Select: Breath/Beat/Timestamp')
        self.controls_layout_A.addWidget(self.breath_beat_label)
        self.breath_beat_selector = QComboBox(self)
        self.controls_layout_A.addWidget(self.breath_beat_selector)
        self.breath_beat_offset_label = QLabel('marker offset')
        self.controls_layout_A.addWidget(self.breath_beat_offset_label)
        self.breath_beat_offset = QDoubleSpinBox(self)
        self.breath_beat_offset.setValue(0)
        self.breath_beat_offset.setSingleStep(0.1)
        self.breath_beat_offset.setMinimum(-999)
        self.breath_beat_offset.setMaximum(999)
        self.controls_layout_A.addWidget(self.breath_beat_offset)
        
        #    filter - with filter value
        self.derived_filter_label = QLabel('Select Derived Filter')
        self.controls_layout_A.addWidget(self.derived_filter_label)
        self.derived_filter_selector = QComboBox(self)
        self.derived_filter_selector.activated.connect(
            self.update_derived_filter_selections
            )
        self.controls_layout_A.addWidget(self.derived_filter_selector)
        self.derived_filter_value_label = QLabel('Select Value To Mark')
        self.controls_layout_A.addWidget(self.derived_filter_value_label)
        self.derived_filter_value = QComboBox(self)
        self.controls_layout_A_radio.addWidget(self.derived_filter_value)
        self.derived_filter_offset_label = QLabel('marker offset')
        self.controls_layout_A.addWidget(self.derived_filter_offset_label)
        self.derived_filter_offset = QDoubleSpinBox(self)
        self.derived_filter_offset.setValue(0)
        self.derived_filter_offset.setSingleStep(0.1)
        self.derived_filter_offset.setMinimum(-999)
        self.derived_filter_offset.setMaximum(999)
        self.controls_layout_A.addWidget(self.derived_filter_offset)
        
        #    derived measure
        self.derived_measure_label = QLabel('Select Derived Measure')
        self.controls_layout_A.addWidget(self.derived_measure_label)
        self.derived_measure_selector = QComboBox(self)
        self.controls_layout_A.addWidget(self.derived_measure_selector)
        
        #    add constant lines (baseline, minPIF, minPEF)
        
        # set initial conditions
        self.signal_radio.setChecked(True)
        self.signal_radio.toggle()
        
        
        # select style
        self.style_layout = QVBoxLayout()
        self.style_layout.setAlignment(Qt.AlignTop)
        self.controls_layout_A.addLayout(self.style_layout)
        #    line style - none, solid, dashed
        self.line_style_label = QLabel('Line Style')
        self.style_layout.addWidget(self.line_style_label)
        self.line_style_select = QComboBox(self)
        self.line_style_select.addItem('None')
        self.line_style_select.addItem('Solid')
        self.line_style_select.addItem('Dashed')
        self.line_style_select.addItem('Dotted')
        self.style_layout.addWidget(self.line_style_select)
        #    line width - pt size
        self.line_width_label = QLabel('Line Width')
        self.style_layout.addWidget(self.line_width_label)
        self.line_width_value = QDoubleSpinBox(self)
        self.line_width_value.setValue(1)
        self.line_width_value.setMinimum(0)
        self.line_width_value.setSingleStep(0.1)
        self.style_layout.addWidget(self.line_width_value)
        #    line color - rgb
        self.line_color_label = QLabel('Line Color')
        self.style_layout.addWidget(self.line_color_label)
        self.line_color_value = QComboBox(self)
        self.line_color_value.addItem('r - red')
        self.line_color_value.addItem('g - green')
        self.line_color_value.addItem('b - blue')
        self.line_color_value.addItem('c - cyan')
        self.line_color_value.addItem('m - magenta')
        self.line_color_value.addItem('y - yellow')
        self.line_color_value.addItem('k - black')
        self.line_color_value.addItem('w - white')
        self.style_layout.addWidget(self.line_color_value)
        #    marker style - none, ... shapes
        self.marker_style_label = QLabel('Marker Style')
        self.style_layout.addWidget(self.marker_style_label)
        self.marker_style_value = QComboBox(self)
        self.marker_style_value.addItems(
            [
                "None",
                "o_circle",
                "s_square",
                "t_triangle",
                "d_diamond",
                "+_plus",
                "p_pentagon",
                "h_hexagon",
                "star",
                "x_cross",
                "crosshair"
                ]
            )
        self.style_layout.addWidget(self.marker_style_value)
        #    marker size - pt size
        self.marker_size_label = QLabel('Marker Size')
        self.style_layout.addWidget(self.marker_size_label)
        self.marker_size_value = QDoubleSpinBox(self)
        self.marker_size_value.setValue(1)
        self.marker_size_value.setMinimum(0)
        self.marker_size_value.setSingleStep(0.1)
        self.style_layout.addWidget(self.marker_size_value)
        #    marker color - rgb
        self.marker_color_label = QLabel('Marker Color')
        self.style_layout.addWidget(self.marker_color_label)
        self.marker_color_value = QComboBox(self)
        self.marker_color_value.addItem('r - red')
        self.marker_color_value.addItem('g - green')
        self.marker_color_value.addItem('b - blue')
        self.marker_color_value.addItem('c - cyan')
        self.marker_color_value.addItem('m - magenta')
        self.marker_color_value.addItem('y - yellow')
        self.marker_color_value.addItem('k - black')
        self.marker_color_value.addItem('w - white')
        self.style_layout.addWidget(self.marker_color_value)
        #    marker border-size - pt size
        self.border_size_label = QLabel('Border Size')
        self.style_layout.addWidget(self.border_size_label)
        self.border_size_value = QDoubleSpinBox(self)
        self.border_size_value.setValue(1)
        self.border_size_value.setMinimum(0)
        self.border_size_value.setSingleStep(0.1)
        self.style_layout.addWidget(self.border_size_value)
        #    marker border-color - rgb
        self.border_color_label = QLabel('Border Color')
        self.style_layout.addWidget(self.border_color_label)
        self.border_color_value = QComboBox(self)
        self.border_color_value.addItem('r - red')
        self.border_color_value.addItem('g - green')
        self.border_color_value.addItem('b - blue')
        self.border_color_value.addItem('c - cyan')
        self.border_color_value.addItem('m - magenta')
        self.border_color_value.addItem('y - yellow')
        self.border_color_value.addItem('k - black')
        self.border_color_value.addItem('w - white')
        self.style_layout.addWidget(self.border_color_value)
        # add to graph
        self.add_to_graph = QPushButton('Add to Graph')
        self.add_to_graph.clicked.connect(self.add_to_graph_action)
        self.controls_layout_A.addWidget(self.add_to_graph)
        
        
        # load standard settings
        
        
        # controls
        #   select input modes
        self.mode_radio_group = QButtonGroup()
        self.mode_radio_standard = QRadioButton('standard pleth')
        self.mode_radio_group.addButton(self.mode_radio_standard)
        self.mode_radio_standard.toggled.connect(self.mode_radio_action)
        self.mode_radio_standard.mode = 'standard'
        self.controls_layout_B.addWidget(self.mode_radio_standard)
        self.mode_radio_autores = QRadioButton('autoresuscitation')
        self.mode_radio_group.addButton(self.mode_radio_autores)
        self.mode_radio_autores.mode = 'autores'
        self.mode_radio_autores.setChecked(True)
        self.mode_radio_autores.toggled.connect(self.mode_radio_action)
        self.controls_layout_B.addWidget(self.mode_radio_autores)
        #   select data sources for charts
        # select signal file
        self.select_signal_file = QPushButton('Select Signal File')
        self.select_signal_file.clicked.connect(self.select_signal_file_action)
        self.controls_layout_B.addWidget(self.select_signal_file)
        self.signal_file_label = QLabel(
            f'Signals: {os.path.basename(self.signal_file_path)}'
        )
        self.controls_layout_B.addWidget(self.signal_file_label)
        # select breath list file
        self.select_breath_list_file = QPushButton('Select Breath List')
        self.select_breath_list_file.clicked.connect(
            self.select_breath_list_file_action
            )
        self.controls_layout_B.addWidget(self.select_breath_list_file)
        self.breath_list_label = QLabel(
            f'Breath List: {os.path.basename(self.breath_list_path)}'
            )
        self.controls_layout_B.addWidget(self.breath_list_label)
        # select beat list file
        self.select_beat_list_file = QPushButton('Select Beat List')
        self.select_beat_list_file.clicked.connect(
            self.select_beat_list_file_action
            )
        self.controls_layout_B.addWidget(self.select_beat_list_file)
        self.beat_list_label = QLabel(
            f'Beat List: {os.path.basename(self.breath_list_path)}'
            )
        self.controls_layout_B.addWidget(self.beat_list_label)
        # select autores output
        self.select_autores_results_path = QPushButton('Select Autores Results')
        self.select_autores_results_path.clicked.connect(
            self.select_autores_results_action
            )
        self.controls_layout_B.addWidget(self.select_autores_results_path)
        
        # add graph button
        self.add_graph_button = QPushButton('Add Graph')
        self.add_graph_button.clicked.connect(self.add_graph)
        self.controls_layout_B.addWidget(self.add_graph_button)
        
        self.add_graph()
    
    #   select # of charts
    #   select formatting for charts, data
    #   select annotations for plotting
    #   select timestamp sources
    #   (dynamically populated) timestamps to jump to
    
    #   add/edit timestamps (add this feature?)
    
    #   load BASSPRO Settings
    #   edit BASSPRO Settings
    
    
    
    # graphs
    @pyqtSlot()
    def select_data_action(self):
        #    signal
        self.signal_label.hide()
        self.signal_selector.hide()
        
        #    breath/beat
        self.breath_beat_label.hide()
        self.breath_beat_selector.hide()
        self.breath_beat_offset_label.hide()
        self.breath_beat_offset.hide()
        
        #    filter - with filter value
        self.derived_filter_label.hide()
        self.derived_filter_selector.hide()
        self.derived_filter_value_label.hide()
        self.derived_filter_value.hide()
        self.derived_filter_offset_label.hide()
        self.derived_filter_offset.hide()
        
        #    derived measure
        self.derived_measure_label.hide()
        self.derived_measure_selector.hide()
    
        # show controls based on user selection
        self.data_type = self.sender()
        
        if self.data_type.isChecked():
            if self.data_type.data == 'Signal':
                self.signal_label.show()
                self.signal_selector.show()
            elif self.data_type.data == 'Breath/Beat':
                #    breath/beat
                self.breath_beat_label.show()
                self.breath_beat_selector.show()
                self.breath_beat_offset_label.show()
                self.breath_beat_offset.show()
            elif self.data_type.data == 'Derived Filter':
                #    filter - with filter value
                self.derived_filter_label.show()
                self.derived_filter_selector.show()
                self.derived_filter_value_label.show()
                self.derived_filter_value.show()
                self.derived_filter_offset_label.show()
                self.derived_filter_offset.show()
            elif self.data_type.data == 'Derived Measure':
                #    derived measure
                self.derived_measure_label.show()
                self.derived_measure_selector.show()
                
        
        
    
    @pyqtSlot()
    def update_derived_filter_selections(self):
        pass
    
    @pyqtSlot()
    def add_graph(self):
        # pyqtgraph crosshair example would be usefull as a graph variation
        self.graph_counter += 1
        graph_layout = QHBoxLayout()
        graph_left_layout = QVBoxLayout()
        graph_right_layout = QVBoxLayout()
        graph_layout.addLayout(graph_left_layout)
        graph_layout.addLayout(graph_right_layout)
        
        self.graph_layout.addLayout(graph_layout)
        graph = {}
        graph['graph_label'] = QLabel(f'Graph: {self.graph_counter}')
        graph_left_layout.addWidget(graph['graph_label'])
        graph['graph'] = pyqtgraph.PlotWidget()
        graph['graph'].addLegend()
        graph_left_layout.addWidget(graph['graph'])
        graph['graph'].setXRange(self.x_min,self.x_max)
        graph['graph'].setBackground('w')
        graph['remove_graph_button'] = QPushButton(
            f'Remove Graph {self.graph_counter}'
            )
        graph['remove_graph_button'].clicked.connect(
            lambda: remove_graph(self,graph,graph_layout)
            )
        graph_right_layout.addWidget(graph['remove_graph_button'])
        self.graph[self.graph_counter] = graph
        self.graph_selector.addItem(f'Graph: {self.graph_counter}')
        def remove_graph(self,graph,graph_layout):
            for k in list(graph.keys()):
                graph[k].setParent(None)
            graph_layout.removeItem(graph_left_layout)
            graph_layout.removeItem(graph_right_layout)
            self.graph_layout.removeItem(graph_layout)
            
            print(self.graph_selector.findText(graph['graph_label'].text()))
            self.graph_selector.removeItem(
                self.graph_selector.findText(graph['graph_label'].text())
                )
            if self.graph_layout.count() == 0:
                self.add_graph()
        
        
        
    def update_graph(self):
        
        pass
        # setData method on lines can update when changing 
    
    def add_to_graph_action(self):
        try:
            
            self.x_min = self.time_start_value.value()
            self.x_max = self.time_start_value.value() + \
                self.time_window_value.value()
            
            graph = self.graph[
                int(self.graph_selector.currentText().split(' ')[1])
                ]['graph']
            
            if self.data_type.data == 'Signal':
                data_filter = (self.signal_data['ts']>=self.x_min) & \
                    (self.signal_data['ts']<=self.x_max)
                x_val = self.signal_data['ts'][data_filter]
                y_val = self.signal_data[
                    self.signal_selector.currentText()
                    ][data_filter]
                print(x_val)
                print(y_val)
                
            elif self.data_type.data == 'Breath/Beat':
                if self.breath_beat_selector.currentText() == 'Breath':
                    data_filter = (self.breath_list_data['Timestamp_Inspiration']>=self.x_min) & \
                        (self.breath_list_data['Timestamp_Inspiration']<=self.x_max)
                    x_val = self.breath_list_data['Timestamp_Inspiration'][data_filter]
                elif self.breath_beat_selector.currentText() == 'Beat':
                    data_filter = (self.beat_list_data['ts']>=self.x_min) & \
                        (self.beat_list_data['ts']<=self.x_max)
                    x_val = self.beat_list_data['ts'][data_filter]
                else: # timestamp column from autores
                    x_val = self.autores_results_data['Challenge'][
                        self.breath_beat_selector.currentText()
                        ]
                y_val = [self.breath_beat_offset.value() for i in list(x_val)]
            elif self.data_type.data == 'Derived Filter':
                data_filter = (self.breath_list_data['Timestamp_Inspiration']>=self.x_min) & \
                    (self.breath_list_data['Timestamp_Inspiration']<=self.x_max) & \
                    (
                        self.breath_list_data['self.derived_filter_selector'] == \
                        self.breath_list_data['self.derived_filter_value']
                        )
                x_val = self.breath_list_data['Timestamp_Inspiration'][data_filter]
                y_val = [self.derived_filter_offset.value() for i in list(x_val)]
            elif self.data_type.data == 'Derived Measure':
                if self.derived_measure_selector.currentText() == "HR":
                    data_filter = (self.beat_list_data['ts']>=self.x_min) & \
                        (self.beat_list_data['ts']<=self.x_max)
                    x_val = self.beat_list_data['ts'][data_filter]
                    y_val = self.beat_list_data[
                        self.derived_measure_selector.currentText()
                        ][data_filter]
                else:
                    data_filter = (self.breath_list_data['Timestamp_Inspiration']>=self.x_min) & \
                        (self.breath_list_data['Timestamp_Inspiration']<=self.x_max)
                    x_val = self.breath_list_data['Timestamp_Inspiration'][data_filter]
                    y_val = self.breath_list_data[
                        self.derived_measure_selector.currentText()
                        ][data_filter]
            elif self.data_type.date == 'Constant':
                x_val = [self.x_min,self.x_max]
                y_val = [self.constant_value.value(),self.constant_value.value()]
            
            self.plotted_counter +=1
            # !!! refactoring to avoid plotting twice would be good
            self.plotted[self.plotted_counter] = graph.plot(list(x_val),list(y_val))
            # set line style
            # !!!
            if self.line_style_select.currentText() == 'None':
                pen = None
            else:
                pen = pyqtgraph.mkPen(
                    self.line_color_value.currentText()[0],
                    width=self.line_width_value.value(),
                    style=self.pen_style_dict[self.line_style_select.currentText()]
                    )
            # set marker style
            if self.marker_style_value.currentText() == 'None':
                self.plotted[self.plotted_counter].setData(
                    x=list(x_val) ,y=list(y_val) ,pen = pen, symbol = None
                    )
                
            else:
                self.plotted[self.plotted_counter].setData(
                    x=list(x_val),
                    y=list(y_val),
                    pen = pen,
                    symbol = self.marker_style_value.currentText().split('_')[0],
                    symbolBrush = self.marker_color_value.currentText()[0],
                    symbolPen = pyqtgraph.mkPen(
                        self.border_color_value.currentText()[0],
                        width=self.border_size_value.value()
                        ),
                    symbolSize = self.marker_size_value.value()
                    )
            
            graph.update()
            print('plot?')
            
        except Exception:
            self.log_text(
                f'unable to prepare graph element: {Exception}<br/>{traceback.format_exc()}',
                'red'
                )
            print('no plot?')
        
        
    
    # methods
    @pyqtSlot()
    def mode_radio_action(self):
        mode_radio = self.sender()
        if mode_radio.isChecked():
            self.data_mode = mode_radio.mode
            self.log_text(f'Data Mode : {self.data_mode}','blue')
    
    
    def log_text(self,text,color):
        self.text1.insertHtml(html_text_color(text,color))
        self.text1.repaint()
        
        
    
    @pyqtSlot()
    def select_signal_file_action(self):
        self.signal_file_path = QFileDialog.getOpenFileName(
            caption = 'select Signal File',
            filter = ('Text (*.txt)')
            )[0]
        self.log_text(f'selecting signal file: {self.signal_file_path}','blue'
            )
        self.signal_file_label.setText(f'Signal: {os.path.basename(self.signal_file_path)}')
        
        if self.signal_file_path == '' or self.signal_file_path is None:
            self.log_text(
                '<strong>No file selected!</strong',
                'red'
                )
            
        else:
            self.log_text(
                'loading signal data...',
                'black'
                )
            
            try:
                # extract muid/plyuid/ruid
                
                self.signal_data = python_module.load_signal_data(
                    self.signal_file_path
                    )
                self.signal_selector.clear()
                self.signal_selector.addItems(
                    [i for i in list(self.signal_data.columns) if i not in \
                         ['ts','comment']
                         ]
                        )
                
                
                self.log_text(
                    f'signal data loaded: {self.signal_data.columns}',
                    'black'
                    )
            except Exception:
                self.log_text(
                    f'unable to load file: {Exception} <br/> {sys.exc_info()}',
                    'red'
                    )
    def select_breath_list_file_action(self):
        self.breath_list_path = QFileDialog.getOpenFileName(
            caption = 'select Breath List',
            filter = ('csv (*.csv)')
            )[0]
        self.log_text(f'selecting Breath List: {self.breath_list_path}','blue'
            )
        self.breath_list_label.setText(f'Breath List: {os.path.basename(self.breath_list_path)}')
        
        if self.breath_list_path == '' or self.breath_list_path is None:
            self.log_text(
                '<strong>No file selected!</strong',
                'red'
                )
            
        else:
            self.log_text(
                'loading Breath List...',
                'black'
                )
            try:
                self.breath_list_data = pandas.read_csv(self.breath_list_path)
                self.log_text(
                    f'Breath List data loaded: {self.breath_list_data.columns}',
                    'black'
                    )
                self.breath_beat_selector.addItem('Breath')
                # additional combo box population needed
                # !!!
            except Exception:
                self.log_text(
                    f'unable to load file: {Exception} <br/> {sys.exc_info()}',
                    'red'
                    )
    
    def select_beat_list_file_action(self):
        self.beat_list_path = QFileDialog.getOpenFileName(
            caption = 'select Beat List',
            filter = ('csv (*.csv)')
            )[0]
        self.log_text(f'selecting Beat List: {os.path.basename(self.beat_list_path)}','blue'
            )
        self.beat_list_label.setText('Beat List: {self.beat_list_path}')
        
        if self.beat_list_path == '' or self.beat_list_path is None:
            self.log_text(
                '<strong>No file selected!</strong',
                'red'
                )
            
        else:
            self.log_text(
                'loading Beat List...',
                'black'
                )
            try:
                self.beat_list_data = pandas.read_csv(self.beat_list_path)
                self.log_text(
                    f'Beat List data loaded: {self.beat_list_data.columns}',
                    'black'
                    )
                self.breath_beat_selector.addItem('Beat')
            except Exception:
                self.log_text(
                    f'unable to load file: {Exception} <br/> {sys.exc_info()}',
                    'red'
                    )
    
    
    
    def select_autores_results_action(self):
        self.autores_results_path = QFileDialog.getOpenFileName(
            caption = 'select Autores Results',
            filter = ('Excel (*.xlsx)')
            )[0]
        self.log_text(f'selecting Autores Results: {self.autores_results_path}','blue'
            )
        self.autores_results_label.setText('Autores Results: {self.autores_results_path}')
        
        if self.autores_results_path == '' or self.autores_results_path is None:
            self.log_text(
                '<strong>No file selected!</strong',
                'red'
                )
            
        else:
            self.log_text(
                'loading Autores Results...',
                'black'
                )
            try:
                self.autores_results_data = {
                    'Baseline':pandas.read_excel(self.autores_results_path,'Baseline'),
                    'Challenge':pandas.read_excel(self.autores_results_path,'Challenge')
                    }
                self.log_text(
                    f'Autores data loaded: {self.autores_results_dats.Challenge.columns}',
                    'black'
                    )
            except Exception:
                self.log_text(
                    f'unable to load file: {Exception} <br/> {sys.exc_info()}',
                    'red'
                    )
    
    
    
    
#%% define main

def main():
    defaultfont = QtGui.QFont('Arial', 8)
    QtWidgets.QApplication.setStyle("fusion")
    QtWidgets.QApplication.setFont(defaultfont)
    app=QApplication(sys.argv)
    MW = MainWindow()
    MW.show()
    sys.exit(app.exec_())



#%% run main()

if __name__ == '__main__':
    main()

