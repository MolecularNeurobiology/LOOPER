# -*- coding: utf-8 -*-
"""
Created on Tue Mar  7 22:55:19 2023

@author: wardc
"""

__version__ = "1.2.1"

# %% import libraries

from ccac_form import Ui_MainWindow
from ccac import copy_to_multiple, compare_checksums, finalize_ccac
from ccac import crawl_and_compare, export_crawl_and_compare_results

from PyQt5.QtWidgets import QFileDialog, QMessageBox, QAbstractItemView
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QFont
from PyQt5.QtCore import (
    QThreadPool,
    QRunnable,
    QTimer,
)

import os
import queue
import time


# %% define classes


class gui_logger:
    def __init__(self, status_window):
        self.status_window = status_window
        self.queue = queue.Queue()
        self.status_window.setFont(QFont("Courier"))

    def info(self, message):
        gui_color = "blue"
        gui_style = None

        self.queue.put_nowait(
            {"color": gui_color, "style": gui_style, "message": message}
        )

    def debug(self, message):
        gui_color = "black"
        gui_style = None

        self.queue.put_nowait(
            {"color": gui_color, "style": gui_style, "message": message}
        )

    def warning(self, message):
        gui_color = "red"
        gui_style = None

        self.queue.put_nowait(
            {"color": gui_color, "style": gui_style, "message": message}
        )

    def error(self, message):
        gui_color = "red"
        gui_style = "strong"

        self.queue.put_nowait(
            {"color": gui_color, "style": gui_style, "message": message}
        )

    def exception(self, message):
        gui_color = "red"
        gui_style = "strong"

        self.queue.put_nowait(
            {"color": gui_color, "style": gui_style, "message": message}
        )

    def process_queue(self):
        if not self.queue.empty():
            new_message = self.queue.get_nowait()
            gui_color = new_message["color"]
            gui_style = new_message["style"]
            message = new_message["message"]

            self.status_window.insertHtml(
                (
                    f'<span style="color:{gui_color}"><{gui_style}>'
                    + f"{message}"
                    + f"</{gui_style}></span><br>"
                )
            )
            self.status_window.ensureCursorVisible()


class Worker(QRunnable):
    def __init__(self, method):
        super(Worker, self).__init__()

        self.method = method

    def run(self):
        self.method()


class ccac_main_window(Ui_MainWindow):
    def __init__(self, MainWindow, model):
        self.setupUi(MainWindow)
        self.model = model
        self.model.reset_model(self.model)

        self.threadpool = QThreadPool()
        self.threadpool.setMaxThreadCount(1)

        self.safety_timer = QTimer()
        self.safety_timer.timeout.connect(self.enable_run_buttons_if_ready)
        self.safety_timer.setInterval(100)
        self.safety_timer.start()

        self.logging_timer = QTimer()
        self.logging_timer.timeout.connect(self.log_from_queue)
        self.logging_timer.setInterval(100)
        self.logging_timer.start()

        self.exit_status = []

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

        self.update_retry_limit()

        # connect buttons
        self.actionAbout.triggered.connect(self.action_about)

        self.actionSelect_Append_Files.triggered.connect(self.action_add_files)
        self.actionSelect_Append_Output_Folder_s.triggered.connect(
            self.action_add_directory
        )
        self.actionClear_Files.triggered.connect(self.action_remove_all_files)
        self.actionClear_Output_Folders.triggered.connect(
            self.action_remove_all_directories
        )
        self.actionReset_Form.triggered.connect(self.action_reset_form)

        self.actionCopy_and_Check.triggered.connect(
            self.action_copy_and_check_files_worker
        )

        self.actionCopy_Check_and_Clear.triggered.connect(
            self.action_copy_check_clear
        )
        
        self.actionCrawl_and_Compare_Tool.triggered.connect(
            self.action_crawl_and_compare
        )

        self.pushButton_add_files.clicked.connect(self.action_add_files)
        self.pushButton_remove_files.clicked.connect(self.action_remove_files)
        self.pushButton_add_folder.clicked.connect(self.action_add_directory)
        self.pushButton_remove_folders.clicked.connect(
            self.action_remove_directory
        )
        self.pushButton_copy_files.clicked.connect(
            self.action_copy_and_check_files_worker
        )
        self.pushButton_compare_files.clicked.connect(
            self.action_compare_files_worker
        )
        self.pushButton_clear_backed_up_files.clicked.connect(
            self.action_clear_files_worker
        )

        self.checkBox_clear_mode.stateChanged.connect(self.action_clear_mode)
        self.checkBox_delete_flag.stateChanged.connect(self.action_delete_flag)

    def log_from_queue(self):
        self.logger.process_queue()

    # disable/enable buttons
    def disable_run_buttons(self):
        self.pushButton_add_files.setEnabled(False)
        self.pushButton_add_folder.setEnabled(False)
        self.pushButton_clear_backed_up_files.setEnabled(False)
        self.pushButton_compare_files.setEnabled(False)
        self.pushButton_copy_files.setEnabled(False)
        self.pushButton_remove_files.setEnabled(False)
        self.pushButton_remove_folders.setEnabled(False)

        self.actionClear_Files.setEnabled(False)
        self.actionClear_Output_Folders.setEnabled(False)
        self.actionCopy_Check_and_Clear.setEnabled(False)
        self.actionCopy_and_Check.setEnabled(False)
        self.actionReset_Form.setEnabled(False)
        self.actionSelect_Append_Files.setEnabled(False)
        self.actionSelect_Append_Files.setEnabled(False)
        self.actionSelect_Append_Output_Folder_s.setEnabled(False)
        self.actionCrawl_and_Compare_Tool.setEnabled(False)

        # self.safety_timer.start()

    def enable_run_buttons_if_ready(self):
        if self.threadpool.activeThreadCount() > 0:
            pass
            # print(self.threadpool.activeThreadCount())

            # self.logger.debug(self.threadpool.activeThreadCount())

        else:
            # print(self.threadpool.activeThreadCount())

            # self.logger.debug(self.threadpool.activeThreadCount())

            self.pushButton_add_files.setEnabled(True)
            self.pushButton_add_folder.setEnabled(True)
            self.pushButton_clear_backed_up_files.setEnabled(True)
            self.pushButton_compare_files.setEnabled(True)
            self.pushButton_copy_files.setEnabled(True)
            self.pushButton_remove_files.setEnabled(True)
            self.pushButton_remove_folders.setEnabled(True)

            self.actionClear_Files.setEnabled(True)
            self.actionClear_Output_Folders.setEnabled(True)
            self.actionCopy_Check_and_Clear.setEnabled(True)
            self.actionCopy_and_Check.setEnabled(True)
            self.actionReset_Form.setEnabled(True)
            self.actionSelect_Append_Files.setEnabled(True)
            self.actionSelect_Append_Files.setEnabled(True)
            self.actionSelect_Append_Output_Folder_s.setEnabled(True)
            self.actionCrawl_and_Compare_Tool.setEnabled(True)

            self.spinBox_retry_limit.valueChanged.connect(
                self.update_retry_limit
            )

            # send user notification if applicable

            if self.exit_status:
                self.action_copy_check_clear_finished()
                self.exit_status = []
                self.model.good_copy_dict = {}
            elif self.model.good_copy_dict:
                self.action_copy_check_finished()
                self.model.good_copy_dict = {}

            # self.safety_timer.stop()
            # self.safety_timer.setInterval(100)

    def action_reset_form(self):
        self.model.reset_model(self.model)
        self.action_remove_all_files()
        self.action_remove_all_directories()
        self.spinBox_retry_limit.setValue(self.model.retry_limit)

    def update_retry_limit(self):
        self.model.retry_limit = self.spinBox_retry_limit.value()

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
        self.action_refresh_file_list()

    def action_add_directory(self):
        new_directory = QFileDialog.getExistingDirectory(
            None, "Select Directory to Place the Back Up File"
        )
        self.model.output_folder_list.append(new_directory)
        self.model.output_folder_list = list(
            set(self.model.output_folder_list)
        )
        self.model.output_folder_list.sort()
        self.action_refresh_folder_list()

    def action_remove_files(self):
        self.model.input_file_list = [
            f
            for i, f in enumerate(self.model.input_file_list)
            if i
            not in [
                item.row()
                for item in self.listView_files_to_copy.selectedIndexes()
            ]
        ]
        self.action_refresh_file_list()

    def action_remove_all_files(self):
        self.model.input_file_list = []
        self.action_refresh_file_list()

    def action_remove_directory(self):
        self.model.output_folder_list = [
            f
            for i, f in enumerate(self.model.output_folder_list)
            if i
            not in [
                item.row()
                for item in self.listView_backup_locations.selectedIndexes()
            ]
        ]
        self.action_refresh_folder_list()

    def action_remove_all_directories(self):
        self.model.output_folder_list = []
        self.action_refresh_folder_list()

    def action_copy_check_clear(self):
        self.checkBox_clear_mode.setChecked(True)
        self.checkBox_delete_flag.setChecked(True)
        self.model.delete_flag = True

        self.action_copy_and_check_files_worker()

    def action_refresh_file_list(self):
        self.model_files_to_copy.removeRows(
            0, self.model_files_to_copy.rowCount()
        )
        for f in self.model.input_file_list:
            self.model_files_to_copy.appendRow(QStandardItem(f))
        self.logger.debug(
            f'file list updated: {",".join(self.model.input_file_list)}'
        )
        self.model.good_copy_dict = {
            k: v for k, v in self.model.good_copy_dict.items()
            if k in self.model.input_file_list
        }

    def action_refresh_folder_list(self):
        self.model_backup_locations.removeRows(
            0, self.model_backup_locations.rowCount()
        )
        for f in self.model.output_folder_list:
            self.model_backup_locations.appendRow(QStandardItem(f))
        self.logger.debug(
            "output folders updated: "
            + f'{",".join(self.model.output_folder_list)}'
        )
        self.model.good_copy_dict = {}

    def action_about(self):
        QMessageBox.information(
            None,
            "About CCAC Tools",
            "\n".join(
                [f"{k} : {v}" for k, v in self.model.version_info.items()]
            ),
        )

    def action_copy_files(self, file, output_paths):

        copy_to_multiple(file, output_paths, self.logger)
        # time.sleep(10) # this line is useful to help confirm hash checking would detect bad copies - buys time to insert a difference in the file to detect
        self.action_compare_files([file], output_paths)

        r = 0
        while r < self.model.retry_limit:
            if all(self.model.good_copy_dict[file]):
                break
            elif len(self.model.good_copy_dict[file]) != len(output_paths):
                self.logger.warning(
                    f"missing copy detected, retrying {r}"
                    + f" of {self.model.retry_limit} possible times"
                )
                # copy file
                copy_to_multiple(file, output_paths, logger=self.logger)
                # compare checksums
                # time.sleep(10) # this line is useful to help confirm hash checking would detect bad copies - buys time to insert a difference in the file to detect
                self.model.good_copy_dict[file] = compare_checksums(
                    file, output_paths, logger=self.logger
                )

            else:
                self.logger.warning(
                    f"bad copy detected, retrying {r}"
                    + f" of {self.model.retry_limit} possible times"
                )
                for i, retry_path in enumerate(output_paths):
                    if not self.model.good_copy_dict[file][i]:
                        copy_to_multiple(
                            file, [retry_path], logger=self.logger
                        )
                        # time.sleep(10) # this line is useful to help confirm hash checking would detect bad copies - buys time to insert a difference in the file to detect
                        self.model.good_copy_dict[file][i] = compare_checksums(
                            file, [retry_path], logger=self.logger
                        )[0]

            r += 1
            

    def action_crawl_and_compare(self):
        self.logger.info('Launching the Crawl and Compare Tool')
        ref_directory = QFileDialog.getExistingDirectory(
            None, "Select Reference (i) Directory for file comparison"
        )
        self.logger.info(f'reference folder (i): {ref_directory}')
        test_directory = QFileDialog.getExistingDirectory(
            None, "Select Test (o) Directory for file comparison"
        )
        self.logger.info(f'test folder (o): {test_directory}')
        output_file = QFileDialog.getSaveFileName(
            None,
            "Select Filename for Comparison Report",
            "",
            "Excel File (*.xlsx)",
        )[0]
        self.logger.info(f'Comparison Report will be saved @: {output_file}')
        
        if not ref_directory:
            self.logger.error('No Reference directory set! exiting')
            return
        if not test_directory:
            self.logger.error('No Test directory set! exiting')
            return
        if not output_file:
            self.logger.error('No path for report file selected! exiting')
            return
        
        
        
        crawl_and_compare_worker = Worker(
            lambda input_dir=ref_directory, output_dir=test_directory, 
            output_path=output_file, logger = self.logger: 
                export_crawl_and_compare_results(
                    crawl_and_compare(
                        input_dir, output_dir=output_dir, logger=logger
                    ), output_path, logger=logger
                )
        )
            
        self.disable_run_buttons()
        self.threadpool.start(crawl_and_compare_worker)
            

    def action_copy_and_check_files_worker(self):
        if not self.model.output_folder_list or not self.model.input_file_list:
            self.logger.warning("unable to copy")
        else:

            self.disable_run_buttons()

            for i, f in enumerate(self.model.input_file_list):
                self.logger.info(
                    f"working on file {i+1} of "
                    + f"{len(self.model.input_file_list)}"
                )

                copy_worker = Worker(
                    lambda file=f, output_paths=self.model.output_folder_list:
                        self.action_copy_files(
                            file, output_paths
                        )
                )

                self.threadpool.start(copy_worker)

            if self.checkBox_clear_mode.isChecked():
                self.action_clear_files_worker()

    def action_compare_files_worker(self, files=None, output_paths=None):
        if not files:
            files = self.model.input_file_list
        if not output_paths:
            output_paths = self.model.output_folder_list
        self.disable_run_buttons()

        compare_worker = Worker(
            lambda f=files, o=output_paths: self.action_compare_files(f, o)
        )
        self.threadpool.start(compare_worker)

    def action_clear_files_worker(self):
        if not self.model.output_folder_list or not self.model.input_file_list:
            self.logger.warning("unable to copy")
        else:

            self.disable_run_buttons()
            compare_worker = Worker(
                lambda
                f=self.model.input_file_list,
                o=self.model.output_folder_list:
                    self.action_compare_files(
                        f, o
                    )
            )
            self.threadpool.start(compare_worker)
            clear_worker = Worker(self.action_clear_backed_up_files)
            self.threadpool.start(clear_worker)

    def action_copy_check_clear_finished(self):
        QMessageBox.information(
            None, "CCAC Report", "\n".join(self.exit_status)
        )

    def action_copy_check_finished(self):
        QMessageBox.information(
            None,
            "CCAC Report - copy and check only",
            "\n".join(
                [
                    f"{os.path.basename(k)} : good copy = {v} = {all(v)}"
                    for k, v in self.model.good_copy_dict.items()
                ]
            ),
        )

    def action_compare_specific_files(self, file, output_path, index):
        self.model.good_copy_dict[file][index] = compare_checksums(
            file, output_path, self.logger
        )

    def action_compare_files(self, files, output_paths):
        if not self.model.output_folder_list or not self.model.input_file_list:
            self.logger.warning("nothing to compare")
        else:

            self.disable_run_buttons()

            # self.model.good_copy_dict = {}
            for f in files:
                self.model.good_copy_dict[f] = compare_checksums(
                    f, output_paths, self.logger
                )

        # if not self.checkBox_clear_mode.isChecked():
        #     # self.action_copy_check_finished()
        #     pass

    def action_delete_flag(self):
        self.model.delete_flag = self.checkBox_delete_flag.isChecked()

    def action_clear_mode(self):
        self.model.delete_flag = self.checkBox_clear_mode.isChecked()
        self.checkBox_delete_flag.setChecked(
            self.checkBox_clear_mode.isChecked()
        )

    def action_clear_backed_up_files(self):
        self.exit_status = []
        if not self.model.output_folder_list or not self.model.input_file_list:
            self.logger.warning("unable to delete")
        else:

            self.disable_run_buttons()

            purge_list = []
            for f in self.model.input_file_list:
                exit_status = finalize_ccac(
                    self.model.good_copy_dict[f],
                    self.model.delete_flag,
                    f,
                    self.model.output_folder_list,
                )
                self.exit_status.append(
                    f"{os.path.basename(f)} : {exit_status}"
                )
                self.logger.info(f"{os.path.basename(f)} : {exit_status}")
                if exit_status == "file backed up, original deleted":
                    purge_list.append(f)
            self.model.input_file_list = [
                filename
                for filename in self.model.input_file_list
                if filename not in purge_list
            ]
            self.action_refresh_file_list()

        # self.action_copy_check_clear_finished()
