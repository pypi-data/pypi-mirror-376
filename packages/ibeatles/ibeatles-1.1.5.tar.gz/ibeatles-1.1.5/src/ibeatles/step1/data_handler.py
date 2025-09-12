#!/usr/bin/env python
"""
Data Handler (step 1)
"""

import glob
import os
from pathlib import PurePath

import numpy as np
from loguru import logger
from qtpy.QtWidgets import QFileDialog, QListWidgetItem

from ibeatles import DataType

# MVP-based widget import
from ibeatles.app.presenters.time_spectra_presenter import TimeSpectraPresenter

# Import backend function from new core module
from ibeatles.core.io.data_loading import get_time_spectra_filename
from ibeatles.utilities.file_handler import (
    FileHandler,
    get_list_of_most_dominant_extension_from_folder,
)
from ibeatles.utilities.gui_handler import GuiHandler
from ibeatles.utilities.load_files import LoadFiles
from ibeatles.utilities.status_message_config import (
    StatusMessageStatus,
    show_status_message,
)
from ibeatles.utilities.system import is_os_mac

TIME_SPECTRA_NAME_FORMAT = "*_Spectra.txt"


class DataHandler:
    user_canceled = False

    def __init__(self, parent=None, data_type=None):
        self.parent = parent

        self.time_spectra_presenter = None

        if data_type is None:
            o_gui = GuiHandler(parent=parent)
            data_type = o_gui.get_active_tab()

        self.data_type = data_type

        self.list_ui = {
            "sample": {
                "list": self.parent.ui.list_sample,
                "folder": self.parent.ui.sample_folder,
                "time_spectra": {
                    "filename": self.parent.ui.time_spectra,
                    "folder": self.parent.ui.time_spectra_folder,
                },
            },
            "ob": {
                "list": self.parent.ui.list_open_beam,
                "folder": self.parent.ui.open_beam_folder,
            },
            "normalized": {
                "list": self.parent.ui.list_normalized,
                "folder": self.parent.ui.normalized_folder,
                "time_spectra": {
                    "filename": self.parent.ui.time_spectra_2,
                    "folder": self.parent.ui.time_spectra_folder_2,
                },
            },
            "time_spectra": {
                "text": self.parent.ui.time_spectra,
                "text2": self.parent.ui.time_spectra_2,
                "folder": self.parent.ui.time_spectra_folder,
                "folder2": self.parent.ui.time_spectra_folder_2,
            },
        }

    def raises_error(self):
        raise ValueError

    def select_folder(self):
        if is_os_mac():
            _folder = str(
                QFileDialog.getExistingDirectory(
                    caption="Select {} folder".format(self.data_type),
                    directory=os.path.dirname(self.parent.default_path[self.data_type]),
                    options=QFileDialog.ShowDirsOnly,
                )
            )
        else:
            _folder = str(
                QFileDialog.getExistingDirectory(
                    caption="Select {} folder".format(self.data_type),
                    directory=os.path.dirname(self.parent.default_path[self.data_type]),
                    options=QFileDialog.DontUseNativeDialog,
                )
            )
        return _folder

    def import_files_from_folder(self, folder="", extension=None):
        logger.info(f"importing files from folder with extension: {extension =}")
        if folder == "":
            self.user_canceled = True
            return False

        if not extension:
            # load the most dominant files
            logger.info("loading the most dominant extension")
            list_of_files, ext = get_list_of_most_dominant_extension_from_folder(folder=folder)
            logger.info(f"\textension: {ext}")
            logger.info(f"\tnbr_files: {len(list_of_files)}")

        elif type(extension) is list:
            for _ext in extension:
                list_of_files = self.get_list_of_files(folder=folder, file_ext=_ext)
                if list_of_files:
                    break
        else:
            list_of_files = self.get_list_of_files(folder=folder, file_ext=extension)

        if not list_of_files:
            logger.info(f"Folder {folder} is empty or does not contain the right file format!")
            show_status_message(
                parent=self.parent,
                message="Folder selected is empty or contains the wrong file formats!",
                status=StatusMessageStatus.error,
                duration_s=5,
            )
            return False

        logger.info(f" len(list_of_files) = {len(list_of_files)}")
        if len(list_of_files) > 2:
            logger.info(f"  list_of_files[0] = {list_of_files[0]}")
            logger.info("    ...")
            logger.info(f"  list_of_files[-1] = {list_of_files[-1]}")
        else:
            logger.info(f"  list_of_files = {list_of_files}")
        self.load_files(list_of_files)
        return True

    def import_time_spectra(self):
        if self.parent.data_metadata[self.data_type]["data"] is not None:
            if (self.data_type == DataType.sample) or (self.data_type == DataType.normalized):
                self.load_time_spectra()

    def get_list_of_files(self, folder="", file_ext=".fits"):
        """list of files in that folder with that extension"""
        file_regular_expression = os.path.join(folder, "*" + file_ext)
        list_of_files = glob.glob(file_regular_expression)
        list_of_files.sort()
        return list_of_files

    def load_files(self, list_of_files):
        logger.info("Loading files")
        image_type = DataHandler.get_image_type(list_of_files)
        logger.info(f" image type: {image_type}")
        o_load_image = LoadFiles(parent=self.parent, image_ext=image_type, list_of_files=list_of_files)
        self.populate_list_widget(o_load_image)
        self.record_data(o_load_image)

    def record_data(self, o_load_image):
        self.parent.list_files[self.data_type] = o_load_image.list_of_files
        self.parent.data_metadata[self.data_type]["folder"] = o_load_image.folder
        self.parent.data_metadata[self.data_type]["data"] = np.array(o_load_image.image_array)

    def get_time_spectra_file(self):
        folder = self.parent.default_path["sample"]
        return get_time_spectra_filename(folder)

    def browse_file_name(self):
        [file_name, _] = QFileDialog.getOpenFileName(
            caption="Select the Time Spectra File",
            directory=self.parent.default_path[self.data_type],
            filter="Txt ({});;All (*.*)".format(TIME_SPECTRA_NAME_FORMAT),
        )
        if file_name:
            return file_name

    def load_time_spectra(self, time_spectra_file=None):
        logger.info("running load_time_spectra method")
        if time_spectra_file is None:
            time_spectra_file = self.get_time_spectra_file()
            if not time_spectra_file:
                time_spectra_file = self.browse_file_name()

        if time_spectra_file is None:
            logger.info("User cancel browsing for time_spectra!")
            show_status_message(
                parent=self.parent,
                message="User cancel browsing for time spectra file!",
                status=StatusMessageStatus.warning,
                duration_s=5,
            )
            return

        logger.info(f"time_spectra_file: {time_spectra_file}")
        self.parent.data_metadata[self.data_type]["time_spectra"]["filename"] = time_spectra_file

        if self.time_spectra_presenter is None:
            self.time_spectra_presenter = TimeSpectraPresenter(self.parent)

        distance_source_detector_m = float(self.parent.ui.distance_source_detector.text())
        detector_offset = float(self.parent.ui.detector_offset.text())

        try:
            self.time_spectra_presenter.load_data(time_spectra_file, distance_source_detector_m, detector_offset)
            self.save_tof_and_lambda_array()
            self.print_time_spectra_filename(time_spectra_file)
        except Exception as e:
            logger.error(f"Error loading time spectra: {str(e)}")
            show_status_message(
                parent=self.parent,
                message=f"Error loading time spectra: {str(e)}",
                status=StatusMessageStatus.error,
                duration_s=5,
            )

    def save_tof_and_lambda_array(self):
        time_spectra_data = self.time_spectra_presenter.model.get_data()
        tof_array = time_spectra_data["tof_array"]
        lambda_array = time_spectra_data["lambda_array"]

        if self.data_type == "sample":
            tof_key = "data"
            lambda_key = "lambda"
        elif self.data_type == "normalized":
            tof_key = "normalized_data"
            lambda_key = "normalized_lambda"

        self.parent.data_metadata["time_spectra"][tof_key] = tof_array
        self.parent.data_metadata["time_spectra"][lambda_key] = lambda_array

    def print_time_spectra_filename(self, time_spectra_filename):
        """display the folder and filename in the corresponding widgets"""
        time_spectra_filename = PurePath(time_spectra_filename)
        base_time_spectra = str(time_spectra_filename.name)
        folder_name = str(time_spectra_filename.parent)
        self.list_ui[self.data_type]["time_spectra"]["filename"].setText(base_time_spectra)
        self.list_ui[self.data_type]["time_spectra"]["folder"].setText(folder_name)
        self.parent.data_metadata[self.data_type]["time_spectra"]["folder"] = folder_name

    def retrieve_files(self, data_type="sample"):
        """
        type = ['sample', 'ob', 'normalized', 'time_spectra']
        """
        self.data_type = data_type

        mydialog = FileDialog()
        mydialog.setDirectory(self.parent.default_path[data_type])
        mydialog.exec_()

        selected_files = mydialog.filesSelected()

        if selected_files:
            if len(selected_files) == 1:
                if os.path.isdir(selected_files[0]):
                    self.load_directory(selected_files[0])
                else:
                    self.load_files(selected_files[0])
            else:
                self.load_files(selected_files)

            if (data_type == "sample") or (data_type == "normalized"):
                self.retrieve_time_spectra()
                self.load_time_spectra()

        else:
            self.user_canceled = True

        # calculate mean data array for normalization tab
        if data_type == "sample":
            _data = self.parent.data_metadata["sample"]["data"]
            normalization_mean_data = np.mean(_data, axis=0)
            self.parent.data_metadata["normalization"]["data"] = normalization_mean_data

    def retrieve_time_spectra(self):
        folder = self.parent.default_path[self.data_type]
        time_spectra_name_format = "*_Spectra.txt"
        [file_name, _] = QFileDialog.getOpenFileName(
            caption="Select the Time Spectra File",
            directory=folder,
            filter="Txt ({});;All (*.*)".format(time_spectra_name_format),
        )

        if file_name:
            folder_name = str(FileHandler.get_parent_path(file_name))
            base_file_name = str(FileHandler.get_base_filename(file_name))
            self.parent.time_spectra_folder = str(FileHandler.get_parent_folder(file_name))

            self.list_ui[self.data_type]["time_spectra"]["filename"].setText(base_file_name)
            self.list_ui[self.data_type]["time_spectra"]["folder"].setText(folder_name)
            self.parent.data_metadata[self.data_type]["time_spectra"]["folder"] = folder_name
            self.parent.data_metadata[self.data_type]["time_spectra"]["filename"] = file_name

            self.load_time_spectra(time_spectra_file=file_name)
            return True

        return False

    def load_directory(self, folder):
        list_files = glob.glob(folder + "/*.*")
        if len(list_files) == 0:
            raise TypeError
        image_type = self.get_image_type(list_files)
        o_load_image = LoadFiles(parent=self.parent, image_ext=image_type, folder=folder)
        self.populate_list_widget(o_load_image)
        self.parent.data_files[self.data_type] = o_load_image.list_of_files
        self.parent.data_metadata[self.data_type]["folder"] = o_load_image.folder
        # self.parent.sample_folder = os.path.dirname(o_load_image.folder)
        self.parent.sample_folder = o_load_image.folder
        self.parent.data_metadata[self.data_type]["data"] = o_load_image.image_array

    def populate_list_widget(self, o_loader):
        list_of_files = o_loader.list_of_files

        _list_ui = self.list_ui[self.data_type]["list"]
        _list_ui.clear()
        for _row, _file in enumerate(list_of_files):
            _item = QListWidgetItem(_file)
            _list_ui.insertItem(_row, _item)

        _folder = o_loader.folder
        self.folder = _folder
        self.parent.default_path[self.data_type] = _folder
        self.list_ui[self.data_type]["folder"].setText(os.path.basename(os.path.abspath(_folder)))

    @staticmethod
    def get_image_type(list_of_files):
        image_type = FileHandler.get_file_extension(list_of_files[0])
        return image_type


class FileDialog(QFileDialog):
    selected_files: list = []

    def __init__(self, *args):
        QFileDialog.__init__(self, *args)
        self.setOption(self.DontUseNativeDialog, False)
        self.setFileMode(self.ExistingFiles)

    def openClicked(self):
        indexes = self.tree.selectionModel().selectedIndexes()
        files = []
        for i in indexes:
            if i.column() == 0:
                files.append(os.path.join(str(self.directory().absolutePath()), str(i.data())))
        self.selected_files = files
        self.close()

    def filesSelected(self):
        return self.selected_files
