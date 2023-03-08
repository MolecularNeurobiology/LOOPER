# -*- coding: utf-8 -*-
"""
Created on Tue Mar  7 22:55:19 2023

@author: wardc
"""

__version__ = '1.0.0'

#%% import libraries

from ccac_form import Ui_MainWindow
from ccac import copy_to_multiple, compare_checksums, finalize_ccac

from PyQt5.QtWidgets import QFileDialog, QMessageBox, QAbstractItemView
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import QModelIndex

import logging
import sys

#%% define classes

class gui_logger():
    def __init__(self, status_window):
        self.status_window = status_window
        
    def info(self,message):
        gui_color = 'blue'
        gui_style = None
        self.status_window.insertHtml(
            (
                f'<span style="color:{gui_color}"><{gui_style}>'
                +f'{message}'
                +f'</{gui_style}></span><br>'
                )
            )
        
    def debug(self,message):
        gui_color = 'black'
        gui_style = None
        self.status_window.insertHtml(
            (
                f'<span style="color:{gui_color}"><{gui_style}>'
                +f'{message}'
                +f'</{gui_style}></span><br>'
                )
            )
        
    def warning(self,message):
        gui_color = 'red'
        gui_style = None
        self.status_window.insertHtml(
            (
                f'<span style="color:{gui_color}"><{gui_style}>'
                +f'{message}'
                +f'</{gui_style}></span><br>'
                )
            )
        
    def error(self,message):
        gui_color = 'red'
        gui_style = 'strong'
        self.status_window.insertHtml(
            (
                f'<span style="color:{gui_color}"><{gui_style}>'
                +f'{message}'
                +f'</{gui_style}></span><br>'
                )
            )



class ccac_main_window(Ui_MainWindow):
    def __init__(self, MainWindow, model):
        self.setupUi(MainWindow)
        self.model = model
        self.model.reset_model(self.model)
        
        self.logger = gui_logger(self.textEdit_status)
        
        # setup data models for mvc
        self.model_files_to_copy = QStandardItemModel()
        self.listView_files_to_copy.setModel(self.model_files_to_copy)
        self.listView_files_to_copy.setSelectionMode(
            QAbstractItemView.ExtendedSelection
        )
        
        self.model_backup_locations = QStandardItemModel()
        self.listView_backup_locations.setModel(self.model_backup_locations)
        self.listView_backup_locations.setSelectionMode(
            QAbstractItemView.ExtendedSelection
        )
        
        
        
        
        # connect buttons
        self.actionAbout.triggered.connect(self.action_about)
        
        self.actionSelect_Append_Files.triggered.connect(self.action_add_files)
        self.actionSelect_Append_Output_Folder_s.triggered.connect(self.action_add_directory)
        self.actionClear_Files.triggered.connect(self.action_remove_all_files)
        self.actionClear_Output_Folders.triggered.connect(self.action_remove_all_directories)
        self.actionReset_Form.triggered.connect(self.action_remove_all_files)
        self.actionReset_Form.triggered.connect(self.action_remove_all_directories)
        
        self.actionCopy_and_Check.triggered.connect(self.action_copy_files)
        self.actionCopy_Check_and_Clear.triggered.connect(self.action_copy_check_clear)
        
        self.pushButton_add_files.clicked.connect(self.action_add_files)
        self.pushButton_remove_files.clicked.connect(self.action_remove_files)
        self.pushButton_add_folder.clicked.connect(self.action_add_directory)
        self.pushButton_remove_folders.clicked.connect(
            self.action_remove_directory
        )
        self.pushButton_copy_files.clicked.connect(self.action_copy_files)
        self.pushButton_compare_files.clicked.connect(self.action_compare_files)
        self.pushButton_clear_backed_up_files.clicked.connect(self.action_clear_backed_up_files)
        
        self.checkBox_clear_mode.stateChanged.connect(self.action_clear_mode)
        self.checkBox_delete_flag.stateChanged.connect(self.action_delete_flag)
        
        
    def action_add_files(self):
        new_files = QFileDialog.getOpenFileNames(
                None,
                "Select Files to Back Up",
                "",
                "All Files (*)",
        )[0]
        self.model.input_file_list += new_files
        self.model.input_file_list = list(set(self.model.input_file_list))
        self.model.input_file_list.sort()
        print(self.model.input_file_list)
        self.action_refresh_file_list()
    
    def action_add_directory(self):
        new_directory = QFileDialog.getExistingDirectory(
            None,
            'Select Directory to Place the Back Up File'
        )
        self.model.output_folder_list.append(new_directory)
        self.model.output_folder_list = list(set(self.model.output_folder_list))
        self.model.output_folder_list.sort()
        print(self.model.output_folder_list)
        self.action_refresh_folder_list()
        
    def action_remove_files(self):
        print([item.row() for item in self.listView_files_to_copy.selectedIndexes()])
        self.model.input_file_list = [
            f for i,f in enumerate(self.model.input_file_list) if i not in 
            [
                item.row() for item in 
                self.listView_files_to_copy.selectedIndexes()
            ]
        ]
        self.action_refresh_file_list()
    
    
    def action_remove_all_files(self):
        self.model.input_file_list = []
        self.action_refresh_file_list()
        
    
    
    def action_remove_directory(self):
        print([item.row() for item in self.listView_backup_locations.selectedIndexes()])
        print([i for i,f in enumerate(self.model.output_folder_list)])
        print([i for i,f in enumerate(self.model.output_folder_list) if i not in [item.row() for item in self.listView_backup_locations.selectedIndexes()]])
        
        self.model.output_folder_list = [
            f for i,f in enumerate(self.model.output_folder_list) if i not in 
            [
                item.row() for item in 
                self.listView_backup_locations.selectedIndexes()
            ]
        ]
        print(self.model.output_folder_list)
        self.action_refresh_folder_list()
    
    
    def action_remove_all_directories(self):
        self.model.output_folder_list = []
        self.action_refresh_folder_list()
    
    
    
    def action_copy_check_clear(self):
        self.checkBox_clear_mode.setChecked(True)
        self.checkBox_delete_flag.setChecked(True)
        self.model.delete_flag = True
        self.action_copy_files()
    
    
    def action_refresh_file_list(self):
        self.model_files_to_copy.removeRows(0, self.model_files_to_copy.rowCount())
        for f in self.model.input_file_list:
            print(f)
            self.model_files_to_copy.appendRow(QStandardItem(f))
        print('refreshed file list')
        print(self.listView_files_to_copy.model)
        
    def action_refresh_folder_list(self):
        self.model_backup_locations.removeRows(0, self.model_backup_locations.rowCount())
        for f in self.model.output_folder_list:
            print(f)
            self.model_backup_locations.appendRow(QStandardItem(f))
        print('refreshed folders')
        
    def action_about(self):
        QMessageBox.information(
            None,
            'About CCAC Tools', 
            '\n'.join(
                [f'{k} : {v}' for k,v in self.model.version_info.items()]
                )
            )

    def action_copy_files(self):
        if not self.model.output_folder_list or not self.model.input_file_list:
            self.logger.warning('unable to copy')
        else:
            for f in self.model.input_file_list:
                copy_to_multiple(f,self.model.output_folder_list,self.logger)
            
            self.action_compare_files()
            
            if self.checkBox_clear_mode.isChecked():
                
                self.action_clear_backed_up_files()
                
    def action_compare_files(self):
        if not self.model.output_folder_list or not self.model.input_file_list:
            self.logger.warning('nothing to compare')
        else:
            self.good_copy_dict = {}
            for f in self.model.input_file_list:
                self.model.good_copy_dict[f] = compare_checksums(
                    f, self.model.output_folder_list, self.logger
                )
    
    def action_delete_flag(self):
        self.model.delete_flag = self.checkBox_delete_flag.isChecked()
        
    def action_clear_mode(self):
        self.model.delete_flag = self.checkBox_clear_mode.isChecked()
        self.checkBox_delete_flag.setChecked(self.checkBox_clear_mode.isChecked())
    
    def action_clear_backed_up_files(self):
        if not self.model.output_folder_list or not self.model.input_file_list:
            self.logger.warning('unable to delete')
        else:
            purge_list = []
            for f in self.model.input_file_list:
                exit_status = finalize_ccac(
                    self.model.good_copy_dict[f],
                    self.model.delete_flag, 
                    f,
                    self.model.output_folder_list
                )
                self.logger.info(exit_status)
                if exit_status == 'file backed up, original deleted':
                    purge_list.append(f)
            self.model.input_file_list = [
                filename for filename in self.model.input_file_list
                if filename not in purge_list
            ]
            self.action_refresh_file_list()
                