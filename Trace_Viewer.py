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
 -works for pleth and pneumo data
*customize plots (i.e. line vs point, color, size, shape)
*add/remove lines
*(in progress) modify existing lines
*(in progress, mostly complete) load and view Data Annotations
*(in progress) load and view Derived Parameters
*(not yet started) test BASSPRO settings for breath detection
*(not yet started) user can interactively run BASSPRO to fill in 
 filtered/updated signals
*save graphs
 -exportable and savable through native pyqtgraph dialog
*(not yet started) launch with quick presentation of default view 
 -(i.e. graph 1 flow + breaths, graph 2 ecg + beats)
*(not yet started) run batch export of graphs
*(not yet started) create/load/test basic settings for BASSPRO

"""

__version__ = '0.0.2'

#%% import libraries

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot, Qt, QSize
from PyQt5.QtCore import QAbstractTableModel, QModelIndex 
from PyQt5.QtWidgets import QMainWindow, QApplication, QLabel, QPushButton 
from PyQt5.QtWidgets import QTextEdit, QTableView, QHBoxLayout, QVBoxLayout
from PyQt5.QtWidgets import QFileDialog, QComboBox, QDialog, QRadioButton
from PyQt5.QtWidgets import QButtonGroup, QDoubleSpinBox, QCheckBox
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



def remove_line(graph=None,line=None,remove=None):
    graph = graph
    line = line
    remove = remove
    graph['graph'].removeItem(line)
    remove.setParent = None
    remove.deleteLater()

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
            'Challenge':pandas.DataFrame(),
            'Timestamps':pandas.DataFrame()
            }
        self.autores_timesetamp_df = pandas.DataFrame()
        
        self.jump_to_dict= {}
        
        
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
        

        
        # add graph button
        self.add_graph_button = QPushButton('Add Graph')
        self.add_graph_button.clicked.connect(self.add_graph)
        self.controls_layout_A.addWidget(self.add_graph_button)
        
        # select data type
        #    toggle data source
        self.controls_layout_A_radio = QVBoxLayout()
        self.controls_layout_A.setAlignment(Qt.AlignTop)
        self.controls_layout_A.addLayout(self.controls_layout_A_radio, stretch=0)
        self.controls_layout_A_radio.setAlignment(Qt.AlignTop)
        
        # select graph destination
        #    combo box with entry for each graph

        
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
        
        self.breath_beat_radio = QRadioButton('Breath/Beat/TimeStamp')
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
        
        self.constant_radio = QRadioButton('Constant')
        self.data_radio_group.addButton(self.constant_radio)
        self.constant_radio.data = 'Constant'
        self.constant_radio.toggled.connect(self.select_data_action)
        self.controls_layout_A_radio.addWidget(self.constant_radio)
        
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
        self.controls_layout_A.addWidget(self.derived_filter_value)
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
        self.constant_measure_label = QLabel('Select Constant Value')
        self.controls_layout_A.addWidget(self.constant_measure_label)
        self.constant_value = QDoubleSpinBox(self)
        self.controls_layout_A.addWidget(self.constant_value)
        self.constant_value.setMinimum(-999999)
        self.constant_value.setMaximum(999999)
        self.constant_value.setSingleStep(0.1)
        self.constant_value.setValue(0)
        # !!! in the future - allow auto loading of key constants (baseline, pif pef, etc.)
        
        
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
        self.line_style_select.setCurrentText('Solid')
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
        self.line_color_value.setCurrentText('b - blue')
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
        self.marker_size_value.setMinimum(0)
        self.marker_size_value.setMaximum(100)
        self.marker_size_value.setValue(10)
        self.marker_size_value.setSingleStep(1)
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
        self.border_size_value.setMinimum(0)
        self.border_size_value.setMaximum(100)
        self.border_size_value.setValue(1)
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
        self.border_color_value.setCurrentText('k - black')
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
        self.autores_results_label = QLabel(
            f'Autores Results: {os.path.basename(self.autores_results_path)}'
            )
        self.controls_layout_B.addWidget(self.autores_results_label)
        
        # jump to Combo Boxes
        self.jump_to_layout = QVBoxLayout()
        self.controls_layout_B.addLayout(self.jump_to_layout)
        
        self.jump_to_source_label = QLabel('Source for "Jump To" List')
        self.jump_to_layout.addWidget(self.jump_to_source_label)
        self.jump_to_source_combo = QComboBox(self)
        self.jump_to_source_combo.activated.connect(self.update_jump_to_list)
        self.jump_to_layout.addWidget(self.jump_to_source_combo)
        self.jump_to_prev_layout = QHBoxLayout()
        self.jump_to_current_layout = QHBoxLayout()
        self.jump_to_next_layout = QHBoxLayout()
        #
        self.jump_to_layout.addLayout(self.jump_to_prev_layout)
        self.jump_to_layout.addLayout(self.jump_to_current_layout)
        self.jump_to_layout.addLayout(self.jump_to_next_layout)
        self.jump_to_prev_button = QPushButton('/\\')
        self.jump_to_prev_button.setStyleSheet("padding: 5px;")
        self.jump_to_prev_button.clicked.connect(self.jump_to_prev_action)
        self.jump_to_current_button = QPushButton('(O)')
        self.jump_to_current_button.setStyleSheet("padding: 5px;")
        self.jump_to_current_button.clicked.connect(self.jump_to_current_action)
        self.jump_to_next_button = QPushButton('\\/')
        self.jump_to_next_button.setStyleSheet("padding: 5px;")
        self.jump_to_next_button.clicked.connect(self.jump_to_next_action)
        #
        self.jump_to_prev_label = QLabel('')
        self.jump_to_current_combo = QComboBox(self)
        self.jump_to_current_combo.activated.connect(self.jump_to_current_action)
        self.jump_to_next_label = QLabel('')
        #
        self.jump_to_prev_layout.addWidget(self.jump_to_prev_button)
        self.jump_to_prev_layout.addWidget(self.jump_to_prev_label)
        self.jump_to_current_layout.addWidget(self.jump_to_current_button)
        self.jump_to_current_layout.addWidget(self.jump_to_current_combo)
        self.jump_to_next_layout.addWidget(self.jump_to_next_button)
        self.jump_to_next_layout.addWidget(self.jump_to_next_label)
        
        

        # self.autores_trial_label = QLabel('Autores Trial')
        # self.autores_trial_combo = QComboBox(self)
        # self.autores_trial_combo.activated.connect(self.jump_to_autores_trial_action)
        # self.jump_to_autores_trial.addWidget(self.autores_trial_label)
        # self.jump_to_autores_trial.addWidget(self.autores_trial_combo)
        
        # self.autores_ts_label = QLabel('Autores TimeStamp')
        # self.autores_ts_combo = QComboBox(self)
        # self.autores_ts_combo.activated.connect(self.jump_to_autores_ts_action)
        # self.jump_to_autores_ts.addWidget(self.autores_ts_label)
        # self.jump_to_autores_ts.addWidget(self.autores_ts_combo)
        
        
        # time navigation controls
        self.graph_time_layout = QHBoxLayout()
        self.graph_time_minimum_layout = QVBoxLayout()
        self.time_start_label = QLabel('Graph Time: Minimum')
        self.graph_time_minimum_layout.addWidget(self.time_start_label)
        self.time_start_value = QDoubleSpinBox(self)
        self.time_start_value.setValue(self.x_min)
        self.time_start_value.setMinimum(0)
        self.time_start_value.setMaximum(999999)
        self.time_start_value.setSingleStep(1)
        self.graph_time_minimum_layout.addWidget(self.time_start_value)
        self.graph_time_window_layout = QVBoxLayout()
        self.time_window_label = QLabel('Graph Time: Window')
        self.graph_time_window_layout.addWidget(self.time_window_label)
        self.time_window_value = QDoubleSpinBox(self)
        self.time_window_value.setValue(self.x_max-self.x_min)
        self.time_window_value.setMinimum(0)
        self.time_window_value.setMaximum(999999)
        self.time_window_value.setSingleStep(1)
        self.graph_time_window_layout.addWidget(self.time_window_value)
        self.graph_time_layout.addLayout(self.graph_time_minimum_layout)
        self.graph_time_layout.addLayout(self.graph_time_window_layout)
        self.controls_layout_B.addLayout(self.graph_time_layout)
        # buttons to move time
        self.move_button_layout_1 = QHBoxLayout()
        self.move_button_layout_2 = QHBoxLayout()
        self.controls_layout_B.addLayout(self.move_button_layout_1)
        self.controls_layout_B.addLayout(self.move_button_layout_2)
        # move button_layout_1
        self.move_beginning = QPushButton(' [< ')
        self.move_beginning.setStyleSheet("padding: 5px;")
        self.move_beginning.clicked.connect(self.move_beginning_action)
        self.move_button_layout_1.addWidget(self.move_beginning)
        self.show_all = QPushButton(' [<>] ')
        self.show_all.setStyleSheet("padding: 5px;")
        self.show_all.clicked.connect(self.show_all_action)
        self.move_button_layout_1.addWidget(self.show_all)
        self.window_reset = QPushButton(' <R> ')
        self.window_reset.setStyleSheet("padding: 5px;")
        self.window_reset.clicked.connect(self.window_reset_action)
        self.move_button_layout_1.addWidget(self.window_reset)
        self.zoom_in = QPushButton(' + ')
        self.zoom_in.setStyleSheet("padding: 5px;")
        self.zoom_in.clicked.connect(self.zoom_in_action)
        self.move_button_layout_1.addWidget(self.zoom_in)
        self.zoom_out = QPushButton(' - ')
        self.zoom_out.setStyleSheet("padding: 5px;")
        self.zoom_out.clicked.connect(self.zoom_out_action)
        self.move_button_layout_1.addWidget(self.zoom_out)
        self.move_end = QPushButton(' >] ')
        self.move_end.setStyleSheet("padding: 5px;")
        self.move_end.clicked.connect(self.move_end_action)
        self.move_button_layout_1.addWidget(self.move_end)
        # move_button_layout_2
        self.move_backward = QPushButton('<<<')
        self.move_backward.setStyleSheet("padding: 5px;")
        self.move_backward.clicked.connect(self.move_backward_action)
        self.move_button_layout_2.addWidget(self.move_backward)
        self.move_backward_half = QPushButton(' < ')
        self.move_backward_half.setStyleSheet("padding: 5px;")
        self.move_backward_half.clicked.connect(self.move_backward_half_action)
        self.move_button_layout_2.addWidget(self.move_backward_half)
        self.refresh_button = QPushButton('Refresh')
        self.refresh_button.setStyleSheet("padding: 5px;")
        self.refresh_button.clicked.connect(self.update_graph)
        self.move_button_layout_2.addWidget(self.refresh_button)
        self.move_forward_half = QPushButton(' > ')
        self.move_forward_half.setStyleSheet("padding: 5px;")
        self.move_forward_half.clicked.connect(self.move_forward_half_action)
        self.move_button_layout_2.addWidget(self.move_forward_half)
        self.move_forward = QPushButton('>>>')
        self.move_forward.setStyleSheet("padding: 5px;")
        self.move_forward.clicked.connect(self.move_forward_action)
        self.move_button_layout_2.addWidget(self.move_forward)
        
        
        # set up the environment
        self.add_graph()
        # set initial conditions
        self.signal_radio.setChecked(True)
        self.signal_radio.toggle()
        
    #   select # of charts
    #   select formatting for charts, data
    #   select annotations for plotting
    #   select timestamp sources
    #   (dynamically populated) timestamps to jump to
    
    #   add/edit timestamps (add this feature?)
    
    #   load BASSPRO Settings
    #   edit BASSPRO Settings
    
    
    @pyqtSlot()
    def move_backward_action(self):
        
        self.x_min -= self.time_window_value.value()
        self.time_start_value.setValue(self.x_min)
        self.update_graph()
        
    
    
    @pyqtSlot()
    def move_forward_action(self):
        
        self.x_min += self.time_window_value.value()
        self.time_start_value.setValue(self.x_min)
        self.update_graph()
    
    
    
    @pyqtSlot()
    def move_backward_half_action(self):
        
        self.x_min -= self.time_window_value.value()/2
        self.time_start_value.setValue(self.x_min)
        self.update_graph()
        
    
    
    @pyqtSlot()
    def move_forward_half_action(self):
        
        self.x_min += self.time_window_value.value()/2
        self.time_start_value.setValue(self.x_min)
        self.update_graph()
    
    
    
    @pyqtSlot()
    def move_beginning_action(self):
        self.x_min = 0
        self.time_start_value.setValue(self.x_min)
        self.update_graph()
    


    @pyqtSlot()
    def move_end_action(self):
        self.x_min = 0
        if 'ts' in self.signal_data.columns:
            self.x_min = max(
                self.signal_data['ts'].max() -self.time_window_value.value(),
                self.x_min
                )
        if 'ts' in self.beat_list_data.columns:
            self.x_min = max(
                self.beat_list_data['ts'].max() - \
                    self.time_window_value.value(),
                self.x_min
                )
        if 'Timestamp_Inspiration' in self.breath_list_data.columns:
            self.x_min = max(
                self.breath_list_data['Timestamp_Inspiration'].max() - \
                    self.time_window_value.value(),
                self.x_min
                )
        if len(self.autores_timesetamp_df) > 0:
            self.x_min = max(
                self.autores_timestamp_df.max().max() - \
                    self.time_window_value.value(),
                self.x_min
                )
        
        self.time_start_value.setValue(self.x_min)
        self.update_graph()
        
    
    
    @pyqtSlot()
    def show_all_action(self):
        self.x_min = 0
        self.x_max = 1
        if 'ts' in self.signal_data.columns:
            self.x_max = max(
                self.signal_data['ts'].max() -self.time_window_value.value(),
                self.x_max
                )
        if 'ts' in self.beat_list_data.columns:
            self.x_max = max(
                self.beat_list_data['ts'].max() - \
                    self.time_window_value.value(),
                self.x_max
                )
        if 'Timestamp_Inspiration' in self.breath_list_data.columns:
            self.x_max = max(
                self.breath_list_data['Timestamp_Inspiration'].max() - \
                    self.time_window_value.value(),
                self.x_max
                )
        if self.autores_timesetamp_df.shape[0] > 0:
            self.x_max = max(
                self.autores_timestamp_df.max().max() - \
                    self.time_window_value.value(),
                self.x_max
                )
        
        self.time_start_value.setValue(self.x_min)
        self.time_window_value.setValue(self.x_max-self.x_min)
        self.update_graph()

    

    @pyqtSlot()
    def window_reset_action(self):
        # !!! setting default value in a settings file
        self.time_window_value.setValue(15)
        self.update_graph()



    @pyqtSlot()
    def zoom_in_action(self):
        self.time_window_value.setValue(self.time_window_value.value() * 0.5)
        self.x_min += self.time_window_value.value() * 0.5
        self.time_start_value.setValue(self.x_min)
        self.update_graph()
    


    @pyqtSlot()
    def zoom_out_action(self):
        self.time_window_value.setValue(self.time_window_value.value() * 2)
        self.x_min -= self.time_window_value.value() * 0.25
        self.time_start_value.setValue(self.x_min)
        self.update_graph()
    


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
        
        #    constant measure
        self.constant_measure_label.hide()
        self.constant_value.hide()
    
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
            elif self.data_type.data == 'Constant':
                #    constant measure
                self.constant_measure_label.show()
                self.constant_value.show()
                
        
        
    @pyqtSlot()
    def jump_to_autores_trial_action(self):
        pass
    
    @pyqtSlot()
    def jump_to_autores_ts_action(self):
        pass
    
    @pyqtSlot()
    def update_derived_filter_selections(self):
        self.derived_filter_value.clear()
        filter_column = self.derived_filter_selector.currentText()
        filter_source = self.derived_filter_selector.itemData(
            self.derived_filter_selector.currentIndex()
            )
        #!!! this isn't working
        if filter_source == 'breathlist':
            filter_values = list(self.breath_list_data[filter_column].unique())
            for f in filter_values:
                self.derived_filter_value.addItem(f'{f}',userData=f)
                print(filter_column,filter_source,f)
        
        else:
            self.log_text('unable to generate filter values', 'red')
        
        
    
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
        graph['g_l_layout'] = graph_left_layout
        graph['layout'] = graph_right_layout
        graph_left_layout.addWidget(graph['graph_label'])
        graph['graph'] = pyqtgraph.PlotWidget()
        graph['legend'] = graph['graph'].addLegend()
        graph['legend'].setColumnCount(3)
        graph['legend'].setOffset([0.1,-0.1])
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
        graph['y_auto'] = QCheckBox('Autoscale Y axis')
        graph['y_auto'].setChecked(True)
        graph_right_layout.addWidget(graph['y_auto'])
        graph['y_max_label'] = QLabel('Y Max')
        graph['y_max'] = QDoubleSpinBox()
        graph['y_max'].setMinimum(-999999)
        graph['y_max'].setMaximum(999999)
        graph['y_max'].setValue(2)
        graph_right_layout.addWidget(graph['y_max'])
        graph['y_min_label'] = QLabel('Y Min')
        graph['y_min'] = QDoubleSpinBox()
        graph['y_min'].setMinimum(-999999)
        graph['y_min'].setMaximum(999999)
        graph['y_min'].setValue(-2)
        graph_right_layout.addWidget(graph['y_min'])
        self.graph[self.graph_counter] = graph
        self.graph_selector.addItem(f'Graph: {self.graph_counter}')
        def remove_graph(self,graph,graph_layout):
            # delete widgets generated with the graph
            for k in list(graph.keys()):
                graph[k].setParent(None)
            # delete widgets added to the graph
            for i in range(graph_right_layout.count())[::-1]:
                graph_right_layout.itemAt(i).widget().setParent(None)
            
            for i in range(graph_left_layout.count())[::-1]:
                graph_left_layout.itemAt(i).widget().setParent(None)
            # remove layouts
            graph_layout.removeItem(graph_left_layout)
            graph_layout.removeItem(graph_right_layout)
            self.graph_layout.removeItem(graph_layout)
            # purge entry in graph selector
            self.graph_selector.removeItem(
                self.graph_selector.findText(graph['graph_label'].text())
                )
            # purge entry in self.graph
            self.graph.pop(int(graph['graph_label'].text().split(' ')[1]))
            
            if self.graph_layout.count() == 0:
                self.add_graph()
        
        
        
    def update_graph(self):
        
        # redraw data
        self.x_min = self.time_start_value.value()
        self.x_max = self.x_min+self.time_window_value.value()

        for k,v in self.plotted.items():
            x_val,y_val,name = self.gather_graph_data(
                v['data_type'],
                v['selector'],
                v['selector_filter'],
                v['offset'],
                v['source']
                )
            v['line'].setData(
                x=list(x_val),
                y=list(y_val),
                name=v['name'],
                pen=v['pen'],
                **v['symbol']
                )

        for g in self.graph:
            # y axis scale
            if not self.graph[g]['y_auto'].isChecked():
                self.graph[g]['graph'].setYRange(
                    self.graph[g]['y_min'].value(),
                    self.graph[g]['y_max'].value(),
                    padding=0
                    )
            else:
                self.graph[g]['graph'].autoRange(padding=None)
            # x axis scale
            self.graph[g]['graph'].setXRange(self.x_min,self.x_max,padding=0)
        # dimensions on screen
        widths = []
        heights = []
        for g in self.graph:
            widths.append(self.graph[g]['graph'].width())
            heights.append(self.graph[g]['graph'].height())
        for g in self.graph:
            self.graph[g]['graph'].resize(min(widths),min(heights))
    
    
    
    def gather_graph_data(
            self,
            data_type,
            selector,
            selector_filter = None,
            offset=0,
            source = None
            ):
        
        name = selector
        
        if data_type == 'Signal':
            data_filter = (self.signal_data['ts']>=self.x_min) & \
                (self.signal_data['ts']<=self.x_max)
            x_val = self.signal_data['ts'][data_filter]
            y_val = self.signal_data[
                selector
                ][data_filter]
            graph_width = self.graph[list(self.graph.keys())[0]]['graph'].width()
            if len(x_val)>graph_width * 4:
                downsample_factor = int(len(x_val)/graph_width/4)
                x_val=x_val[::downsample_factor]
                y_val=y_val[::downsample_factor]
                self.log_text(
                    f'downsampling signal by factor of {downsample_factor}',
                    'orange'
                    )
            
            
        elif data_type == 'Breath/Beat':
            if selector == 'Breath-I':
                data_filter = (self.breath_list_data['Timestamp_Inspiration']>=self.x_min) & \
                    (self.breath_list_data['Timestamp_Inspiration']<=self.x_max)
                x_val = self.breath_list_data['Timestamp_Inspiration'][data_filter]
            elif selector == 'Breath-E':
                data_filter = (self.breath_list_data['Timestamp_Expiration']>=self.x_min) & \
                    (self.breath_list_data['Timestamp_Expiration']<=self.x_max)
                x_val = self.breath_list_data['Timestamp_Expiration'][data_filter]
            elif selector == 'Beat':
                data_filter = (self.beat_list_data['ts']>=self.x_min) & \
                    (self.beat_list_data['ts']<=self.x_max)
                x_val = self.beat_list_data['ts'][data_filter]
            else: # timestamp column from autores
                x_val = self.autores_results_data['Challenge'][
                    selector
                    ]
            y_val = [offset for i in list(x_val)]
            
        elif data_type == 'Derived Filter':
            data_filter = (self.breath_list_data['Timestamp_Inspiration']>=self.x_min) & \
                (self.breath_list_data['Timestamp_Inspiration']<=self.x_max) & \
                (
                    self.breath_list_data[selector] == \
                    selector_filter
                    )
            print(f'{selector_filter}')
            x_val = self.breath_list_data['Timestamp_Inspiration'][data_filter]
            y_val = [offset for i in list(x_val)]
            
        elif data_type == 'Derived Measure':
            if source == 'beatlist':
                data_filter = (self.beat_list_data['ts']>=self.x_min) & \
                    (self.beat_list_data['ts']<=self.x_max)
                x_val = self.beat_list_data['ts'][data_filter]
                y_val = self.beat_list_data[
                    selector
                    ][data_filter]
            elif source == 'breathlist':
                data_filter = (self.breath_list_data['Timestamp_Inspiration']>=self.x_min) & \
                    (self.breath_list_data['Timestamp_Inspiration']<=self.x_max)
                x_val = self.breath_list_data['Timestamp_Inspiration'][data_filter]
                y_val = self.breath_list_data[
                    selector
                    ][data_filter]
                
        elif data_type == 'Constant':
            x_val = [self.x_min,self.x_max]
            y_val = [offset,offset]
            name = f'constant {self.constant_value.value()}'
        
        else:
            self.log_text('unable to gather graph data','red')
        
        
        return x_val,y_val,name
    
    
    
    def update_jump_to_labels(self):
        current_index = self.jump_to_current_combo.currentIndex()
        
        # at end of list
        if current_index == self.jump_to_current_combo.count() - 1:
            self.jump_to_next_label.setText('[X]')
            self.jump_to_prev_label.setText(
                self.jump_to_current_combo.itemText(current_index-1)
                )
        # at start of list
        elif current_index == 0:
            self.jump_to_prev_label.setText('[X]')
            self.jump_to_next_label.setText(
                self.jump_to_current_combo.itemText(current_index+1)
                )
        #
        else:
            self.jump_to_prev_label.setText(
                self.jump_to_current_combo.itemText(current_index-1)
                )
            self.jump_to_next_label.setText(
                self.jump_to_current_combo.itemText(current_index+1)
                )
                
            
    
    def jump_to_current_action(self):
        current_index = self.jump_to_current_combo.currentIndex()
        current_text = self.jump_to_current_combo.currentText()
        current_ts = self.jump_to_current_combo.itemData(current_index)
        if current_index < 0:
            return
        self.x_min = max(current_ts - self.time_window_value.value()/2, 0)
        self.time_start_value.setValue(self.x_min)
        
        self.log_text(f'jumping to {current_text} @ {current_ts}','blue')
        self.update_jump_to_labels()
        self.update_graph()
        
        
    
    def jump_to_prev_action(self):
        current_index = self.jump_to_current_combo.currentIndex()
        
        # at start of list
        if current_index <= 0:
            self.log_text('Nowhere to jump to','red')
        #
        else:
            self.jump_to_current_combo.setCurrentIndex(current_index-1)
            self.jump_to_current_action()

    def jump_to_next_action(self):
        current_index = self.jump_to_current_combo.currentIndex()
        
        if current_index == self.jump_to_current_combo.count() - 1:
        # at end of list
            self.log_text('Nowhere to jump to','red')
        #
        else:
            self.jump_to_current_combo.setCurrentIndex(current_index+1)
            self.jump_to_current_action()
    
    def update_jump_to_source_combo(self):
        self.jump_to_source_combo.clear()
        for k in self.jump_to_dict:
            self.jump_to_source_combo.addItem(k)
    
    
    def update_jump_to_list(self):
        self.jump_to_current_combo.clear()
        print('updating')
        self.log_text('updating jump_to_list','blue')
        
        for i in range(
                self.jump_to_dict[self.jump_to_source_combo.currentText()].shape[0]
                ):
            self.jump_to_current_combo.addItem(
                self.jump_to_dict[self.jump_to_source_combo.currentText()].iloc[i][
                    'text'
                    ],
                userData = self.jump_to_dict[
                    self.jump_to_source_combo.currentText()
                    ].iloc[i]['ts']
                )
    
    
    
    def prep_breath_list_timestamps(self):
        
        for c in [
                'Exp_Condition',
                'Auto_Condition',
                'Man_Condition',
                'Auto_Block_Id',
                'Auto_Selection_Id',
                'Man_Selection_Id'
                ]:
            if f'Breathlist:{c}' in self.jump_to_dict.keys():
                self.jump_to_dict.pop(f'Breathlist:{c}')
                
            if len(self.breath_list_data[c].unique())>1:
                self.jump_to_dict[f'Breathlist:{c}'] = self.breath_list_data[
                    ['Timestamp_Inspiration',c]
                    ].groupby(c).min().reset_index().sort_values(
                        'Timestamp_Inspiration'
                        ).rename(
                            columns={c:'text','Timestamp_Inspiration':'ts'}
                            )
        self.update_jump_to_source_combo()
                        
            

    
    def prep_breath_list_filters(self):
        self.derived_filter_selector.clear()
        for c in [
                'Breath_Inclusion_Filter',
                'AUTO_Inclusion_Filter',
                'MAN_Inclusion_Filter',
                'Exp_Condition',
                'Auto_Condition',
                'Man_Condition',
                'Auto_Block_Id',
                'Auto_Selection_Id',
                'Man_Selection_Id'
                ]:
            if c in self.breath_list_data.columns:
                self.derived_filter_selector.addItem(c,userData='breathlist')
        self.update_derived_filter_selections()
    
    def prep_breath_list_derived(self):
        # current version is hard coded load...could try a dynamic load
        # or shift the usable columns into an external config file
        
        self.log_text('preparing breath list derived parameters','blue')
        
        # purge items that come from a breath_list
        for i in range(self.derived_measure_selector.count())[::-1]:
            if self.derived_measure_selector.itemData(i) == 'breathlist':
                self.derived_measure_selector.removeItem(i)
        
        # repopulate with items that come from the new breath_list
        derived_parameters = [
            'Inspiratory_Duration',
            'Expiratory_Duration',
            'Breath_Cycle_Duration',
            'IS_TT',
            'VF',
            'Tidal_Volume_uncorrected',
            'Tidal_Volume_exhale_uncorrected',
            'IS_iTV',
            'Peak_Inspiratory_Flow',
            'Peak_Expiratory_Flow',
            'DVTV',
            'apnea_local_threshold',
            'sigh_local_threshold',
            'per500',
            'Apnea',
            'Sigh',
            'O2_uncalibrated',
            'CO2_uncalibrated',
            'corrected_o2',
            'corrected_co2',
            'Chamber_Temp_uncalibrated',
            'Chamber_Temperature',
            'Body_Temperature_Linear',
            'mav',
            'O2_concentration',
            'CO2_concentration',
            'base_selection',
            'base_o2',
            'base_co2',
            'base_tv',
            'VT__Tidal_Volume_corrected',
            'Peak_Inspiratory_Flow_corrected',
            'Peak_Expiratory_Flow_corrected',
            'VO2',
            'VCO2',
            'VE__Ventilation',
            'VEVO2',
            'RER',
            'VTpg__Tidal_Volume_per_gram_corrected',
            'VEpg__Ventilation_per_gram',
            'VO2pg','VCO2pg',
            'TT_per_TV',
            'TT_per_TVpg',
            'O2_per_Air__VO2_x_TT_per_TV_'
            ]
        for c in derived_parameters:
            if c in self.breath_list_data.columns:
                self.derived_measure_selector.addItem(c,userData='breathlist')
                
    
    def prep_beat_list_derived(self):
        # current version is hard coded load...could try a dynamic load
        # or shift the usable columns into an external config file
        self.log_text('preparing beat list derived parameters','blue')
        # purge items that come from a breath_list
        for i in range(self.derived_measure_selector.count())[::-1]:
            if self.derived_measure_selector.itemData(i) == 'beatlist':
                self.derived_measure_selector.removeItem(i)
        
        # repopulate with items that come from the new breath_list
        derived_parameters = [
            'HR',
            'RR'
            ]
        for c in derived_parameters:
            if c in self.beat_list_data.columns:
                self.derived_measure_selector.addItem(c,userData='beatlist')
    
    
    def prep_autores_timestamps_and_filters(self):
        self.log_text('extracting autores timestamps', 'blue')
        non_timestamp_keywords = [
            '_volume',
            '_vf',
            '_ve',
            '_breath_duration',
            '_vt',
            '_hr',
            '_rr',
            'latency_',
            'discrep_',
            'duration_',
            'trial_number'
            ]
        time_stamp_columns = []
        ts_list = []
        text_list = []
        for c in self.autores_results_data['Challenge'].columns:
            
            if not any([i.lower() in c.lower() for i in non_timestamp_keywords]):
                time_stamp_columns.append(c)
                self.log_text(c,'green')
        
        # self.autores_timesetamp_df = self.autores_results_data['Challenge'][time_stamp_columns]
        
        trials = list(self.autores_results_data['Challenge']['trial_number'])
        
        for t in trials:
            # self.autores_trial_combo.addItem(f'{t}',userData = 'autores')
            
            for tsc in time_stamp_columns:
                if list(
                        pandas.to_numeric(
                            self.autores_results_data['Challenge'][
                                self.autores_results_data['Challenge']\
                                    ['trial_number']==t
                                ][tsc]).fillna(False))[0]:
                    ts_list.append(
                        float(
                            self.autores_results_data['Challenge'][
                            self.autores_results_data['Challenge']['trial_number']==t
                            ][tsc]
                            )
                        )
                    text_list.append(f'{t}:{tsc}')
        self.jump_to_dict['Autores-Challenge'] = pandas.DataFrame(
            {'ts':ts_list,'text':text_list}
            ).sort_values('ts')
        self.jump_to_dict['Autores-ExpCondition'] = self.autores_results_data[
            'Timestamps'
            ].sort_values('ts')
        
        self.update_jump_to_source_combo()
        
        for tsc in time_stamp_columns:
            # self.autores_ts_combo.addItem(f'{tsc}',userData = 'autores')
            self.breath_beat_selector.addItem(f'{tsc}', userData = 'autores')
        
        
    
    def add_to_graph_action(self):
        try:
            self.x_min = self.time_start_value.value()
            self.x_max = self.time_start_value.value() + \
                self.time_window_value.value()
            
            graph = self.graph[
                int(self.graph_selector.currentText().split(' ')[1])
                ]
            
            self.plotted_counter +=1
            
            # set default, override if applicable
            selector_filter = None
            offset = 0
            source = None
            # gather gata
            if self.data_type.data == 'Signal':
                selector = self.signal_selector.currentText()
                    
            elif self.data_type.data == 'Breath/Beat':
                selector = self.breath_beat_selector.currentText()
                offset = self.breath_beat_offset.value()

            elif self.data_type.data == 'Derived Filter':
                selector = self.derived_filter_selector.currentText()
                selector_filter = self.derived_filter_value.itemData(
                    self.derived_filter_value.currentIndex()
                    )
                offset = self.derived_filter_offset.value()
                print(f'{self.derived_filter_value.currentIndex()}')
                print(self.derived_filter_value.itemData(0))
                print(self.derived_filter_value.itemData(1))
                print(f'{selector}\n{selector_filter}\n{offset}')
                
            elif self.data_type.data == 'Derived Measure':
                selector = self.derived_measure_selector.currentText()
                source = self.derived_measure_selector.itemData(
                    self.derived_measure_selector.currentIndex()
                    )
            elif self.data_type.data == 'Constant':
                selector = 'Constant'
                offset = self.constant_value.value()
            
            x_val,y_val,name = self.gather_graph_data(
                self.data_type.data,
                selector,
                selector_filter=selector_filter,
                offset=offset,
                source=source
                )
            
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
                symbol = {'symbol':None}
                
            else:
                
                symbol = {
                    'symbol':self.marker_style_value.currentText().split('_')[0],
                    'symbolBrush':self.marker_color_value.currentText()[0],
                    'symbolPen':pyqtgraph.mkPen(
                        self.border_color_value.currentText()[0],
                        width=self.border_size_value.value()
                        ),
                    'symbolSize':self.marker_size_value.value()                    
                    }
            
            remove = QPushButton(
                f'Remove: {selector} : {self.plotted_counter}'
                )
            
            line = graph['graph'].plot(
                x=list(x_val),
                y=list(y_val),
                name=name,
                pen=pen,
                **symbol
                )
            
            self.plotted[self.plotted_counter]={
                'line': line,
                'graph':graph,
                'offset':offset,
                'pen':pen,
                'symbol':symbol,
                'data_type':self.data_type.data,
                'name':name,
                'selector':selector,
                'selector_filter':selector_filter,
                'source':source,
                'line_id':self.plotted_counter,
                f'remove{self.plotted_counter}':remove
                }
            graph['layout'].addWidget(
                self.plotted[self.plotted_counter][f'remove{self.plotted_counter}']
                )
            self.plotted[self.plotted_counter][
                f'remove{self.plotted_counter}'
                ].clicked.connect(
                    lambda: remove_line(
                        graph,
                        line,
                        remove
                        )
                    )
            self.update_graph()
            
        except Exception:
            self.log_text(
                f'unable to prepare graph element: {Exception}<br/>{traceback.format_exc()}',
                'red'
                )
    
    

    @pyqtSlot()
    def mode_radio_action(self):
        mode_radio = self.sender()
        if mode_radio.isChecked():
            self.data_mode = mode_radio.mode
            self.log_text(f'Data Mode : {self.data_mode}','blue')

    
    
    def log_text(self,text,color):
        self.text1.insertHtml(html_text_color(text,color))
        self.text1.repaint()
        self.text1.verticalScrollBar().setSliderPosition(
            self.text1.verticalScrollBar().maximum()
            )
        
        
    
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
                    f'unable to load file: {Exception}<br/>{traceback.format_exc()}',
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
                self.breath_beat_selector.addItem('Breath-I')
                self.breath_beat_selector.addItem('Breath-E')
                self.prep_breath_list_timestamps()
                self.prep_breath_list_filters()
                self.prep_breath_list_derived()
                
                # additional combo box population needed
                # !!!
            except Exception:
                self.log_text(
                    f'unable to load file: {Exception}<br/>{traceback.format_exc()}',
                    'red'
                    )
    
    def select_beat_list_file_action(self):
        self.beat_list_path = QFileDialog.getOpenFileName(
            caption = 'select Beat List',
            filter = ('csv (*.csv)')
            )[0]
        self.log_text(f'selecting Beat List: {os.path.basename(self.beat_list_path)}','blue'
            )
        self.beat_list_label.setText(f'Beat List: {os.path.basename(self.beat_list_path)}')
        
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
                self.prep_beat_list_derived()
            except Exception:
                self.log_text(
                    f'unable to load file: {Exception}<br/>{traceback.format_exc()}',
                    'red'
                    )
    
    
    
    def select_autores_results_action(self):
        self.autores_results_path = QFileDialog.getOpenFileName(
            caption = 'select Autores Results',
            filter = ('Excel (*.xlsx)')
            )[0]
        self.log_text(f'selecting Autores Results: {self.autores_results_path}','blue'
            )
        self.autores_results_label.setText(f'Autores Results: {os.path.basename(self.autores_results_path)}')
        
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
                    'Challenge':pandas.read_excel(self.autores_results_path,'Challenge'),
                    'Timestamps':pandas.read_excel(self.autores_results_path,'Timestamps'),
                    }
                self.prep_autores_timestamps_and_filters()
                self.log_text(
                    f'Autores data loaded: {self.autores_results_data["Challenge"].columns}',
                    'black'
                    )
            except Exception:
                self.log_text(
                    f'unable to load file: {Exception}<br/>{traceback.format_exc()}',
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

