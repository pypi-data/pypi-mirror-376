#!/usr/bin/env python
"""
Log launcher
"""

import os

from loguru import logger
from qtpy import QtGui
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QDialog, QMainWindow

from ibeatles import load_ui, refresh_image, settings_image
from ibeatles.session import SessionSubKeys
from ibeatles.utilities.file_handler import read_ascii, write_ascii
from ibeatles.utilities.get import Get


class LogLauncher:
    def __init__(self, parent=None):
        self.parent = parent

        if self.parent.log_id is None:
            log_id = Log(parent=self.parent)
            log_id.show()
            self.parent.log_id = log_id
        else:
            self.parent.log_id.activateWindow()
            self.parent.log_id.setFocus()


class Log(QMainWindow):
    def __init__(self, parent=None):
        self.parent = parent
        QMainWindow.__init__(self, parent=parent)
        ui_full_path = os.path.join(os.path.dirname(__file__), os.path.join("ui", "log.ui"))
        self.ui = load_ui(ui_full_path, baseinstance=self)
        self.setWindowTitle("Log")
        self.ui.log_text.setReadOnly(True)

        refresh_icon = QIcon(refresh_image)
        self.ui.refresh_pushButton.setIcon(refresh_icon)

        settings_icon = QIcon(settings_image)
        self.ui.settings_pushButton.setIcon(settings_icon)

        o_get = Get(parent=self.parent)
        self.log_file_name = o_get.get_log_file_name()

        self.check_log_size()
        self.loading_logging_file()

        # jump to end of file
        self.ui.log_text.moveCursor(QtGui.QTextCursor.End)

    def closeEvent(self, c):
        self.parent.log_id = None

    def loading_logging_file(self):
        try:
            log_text = read_ascii(self.log_file_name)
            self.ui.log_text.setPlainText(log_text)
            self.ui.log_text.moveCursor(QtGui.QTextCursor.End)
        except FileNotFoundError:
            self.ui.log_text.setPlainText("")

    def clear_clicked(self):
        if os.path.exists(self.log_file_name):
            write_ascii(text="", filename=self.log_file_name)
            logger.info("log file has been cleared by user")
        self.loading_logging_file()

    def check_log_size(self):
        o_handler = LogHandler(parent=self.parent, log_file_name=self.log_file_name)
        o_handler.cut_log_size_if_bigger_than_buffer()

    def launch_settings(self):
        log_id = LogSettings(parent=self, grand_parent=self.parent)
        log_id.show()


class LogSettings(QDialog):
    def __init__(self, parent=None, grand_parent=None):
        self.parent = parent
        self.grand_parent = grand_parent
        QDialog.__init__(self, parent=self.parent)
        ui_full_path = os.path.join(os.path.dirname(__file__), os.path.join("ui", "log_settings.ui"))
        self.ui = load_ui(ui_full_path, baseinstance=self)
        self.setWindowTitle("Log")
        self.init_widgets()

    def init_widgets(self):
        log_buffer_size = self.grand_parent.session_dict[SessionSubKeys.log_buffer_size]
        self.ui.buffer_size_spinBox.setValue(log_buffer_size)

    def accept(self):
        self.grand_parent.session_dict[SessionSubKeys.log_buffer_size] = self.ui.buffer_size_spinBox.value()
        self.parent.check_log_size()
        self.parent.loading_logging_file()
        self.close()


class LogHandler:
    def __init__(self, parent=None, log_file_name=""):
        self.parent = parent
        self.log_file_name = log_file_name

    def cut_log_size_if_bigger_than_buffer(self):
        log_buffer_size = self.parent.session_dict[SessionSubKeys.log_buffer_size]
        # check current size of log file
        log_text = read_ascii(self.log_file_name)
        log_text_split_by_cr = log_text.split("\n")
        log_file_size = len(log_text_split_by_cr)
        if log_file_size <= log_buffer_size:
            return
        else:
            new_log_text = log_text_split_by_cr[-log_buffer_size:]
            new_log_text = "\n".join(new_log_text)
            write_ascii(text=new_log_text, filename=self.log_file_name)
            logger.info("log file has been truncated to fit buffer size limit")
