#!/usr/bin/env python
"""
Event handler
"""

import logging
import os

import numpy as np
import pyqtgraph as pg
from qtpy.QtWidgets import QFileDialog

from ibeatles import DataType, interact_me_style, normal_style

# MVP widget
from ibeatles.app.presenters.time_spectra_presenter import TimeSpectraPresenter

# backend function from core
from ibeatles.core.io.data_loading import get_time_spectra_filename
from ibeatles.session import SessionSubKeys
from ibeatles.tools.tof_bin import BinAutoMode, BinMode
from ibeatles.tools.tof_bin.auto_event_handler import AutoEventHandler
from ibeatles.tools.tof_bin.manual_event_handler import ManualEventHandler
from ibeatles.tools.tof_bin.plot import Plot
from ibeatles.tools.tof_bin.utilities.get import Get
from ibeatles.tools.utilities import TimeSpectraKeys
from ibeatles.utilities.file_handler import FileHandler
from ibeatles.utilities.load_files import LoadFiles
from ibeatles.utilities.status_message_config import (
    StatusMessageStatus,
    show_status_message,
)
from ibeatles.utilities.table_handler import TableHandler


class EventHandler:
    def __init__(self, parent=None, top_parent=None):
        self.parent = parent
        self.top_parent = top_parent

        self.time_spectra_presenter = None

    def check_widgets(self):
        # enable widgets when a folder has been selected
        folder_selected = self.parent.ui.folder_selected.text()
        if os.path.exists(folder_selected):
            enabled_state = True
        else:
            enabled_state = False

        self.parent.ui.bin_tabWidget.setEnabled(enabled_state)
        self.parent.ui.x_axis_groupBox.setEnabled(enabled_state)
        self.parent.ui.stats_tabWidget.setEnabled(enabled_state)
        self.parent.ui.bin_bottom_tabWidget.setEnabled(enabled_state)
        self.parent.ui.export_pushButton.setEnabled(enabled_state)
        self.parent.ui.image_tabWidget.setEnabled(enabled_state)

        # enable export bin when there are bins selected
        o_get = Get(parent=self.parent)
        bin_mode = o_get.bin_mode()
        if bin_mode == BinMode.auto:
            state_auto_table_has_at_least_one_row_checked = self._auto_table_has_at_least_one_row_checked()
            self.parent.ui.export_pushButton.setEnabled(state_auto_table_has_at_least_one_row_checked)
        elif bin_mode == BinMode.manual:
            state_manual_table_has_at_least_one_real_bin = self._manual_table_has_at_least_one_real_bin()
            self.parent.ui.export_pushButton.setEnabled(state_manual_table_has_at_least_one_real_bin)

        # if data loaded, change stylesheet of buttons
        if self.parent.list_tif_files:
            self.parent.ui.select_folder_pushButton.setStyleSheet(normal_style)
            self.parent.ui.export_pushButton.setStyleSheet(interact_me_style)

    def _manual_table_has_at_least_one_real_bin(self):
        """return True if there is at least one bin defined"""

        if self.parent.manual_bins[TimeSpectraKeys.file_index_array]:
            if isinstance(self.parent.manual_bins[TimeSpectraKeys.file_index_array][0], list):
                return True
        return False

    def _auto_table_has_at_least_one_row_checked(self):
        """check that the auto table has at least one row enabled (first column widget is checked)"""
        o_table = TableHandler(table_ui=self.parent.ui.bin_auto_tableWidget)
        nbr_row = o_table.row_count()
        for _row in np.arange(nbr_row):
            widget = o_table.get_widget(row=_row, column=0)
            if widget:
                checkbox = widget.children()[1]
                if checkbox.isChecked():
                    return True
        return False

    def select_input_folder(self):
        default_path = self.top_parent.session_dict[DataType.sample][SessionSubKeys.current_folder]
        folder = QFileDialog.getExistingDirectory(
            parent=self.parent,
            caption="Select folder containing images to load",
            directory=default_path,
            options=QFileDialog.ShowDirsOnly,
        )

        if folder == "":
            logging.info("User Canceled the selection of folder!")
            show_status_message(
                parent=self.parent,
                message="User cancelled the file dialog window",
                duration_s=5,
                status=StatusMessageStatus.warning,
            )
            return

        list_tif_files = FileHandler.get_list_of_tif(folder=folder)
        if not list_tif_files:
            logging.info("-> folder does not contain any tif file!")
            show_status_message(
                parent=self.parent,
                message=f"Folder {os.path.basename(folder)} does not contain any TIFF files!",
                duration_s=5,
                status=StatusMessageStatus.error,
            )
            return

        self.parent.ui.folder_selected.setText(folder)
        logging.info(f"Users selected the folder: {folder}")
        self.parent.list_tif_files = list_tif_files

    def load_data(self):
        if not self.parent.list_tif_files:
            return

        dict = LoadFiles.load_interactive_data(parent=self.parent, list_tif_files=self.parent.list_tif_files)
        self.parent.image_size["height"] = dict["height"]
        self.parent.image_size["width"] = dict["width"]
        self.parent.images_array = dict["image_array"]
        self.parent.integrated_image = np.mean(dict["image_array"], axis=0)

    def load_time_spectra_file(self):
        """
        load the time spectra file
        """
        logging.info("Loading time spectra file ...")
        folder = self.parent.ui.folder_selected.text()

        time_spectra_file = get_time_spectra_filename(folder)
        logging.info(f"in load_time_spectra_file, time_spectra_file: {time_spectra_file}")
        if not time_spectra_file:
            logging.info("Time spectra file not found!")
            show_status_message(
                parent=self.parent,
                message="Time spectra file not found!",
                status=StatusMessageStatus.error,
                duration_s=5,
            )
            return

        if self.time_spectra_presenter is None:
            self.time_spectra_presenter = TimeSpectraPresenter(self.parent)

        distance_source_detector_m = float(self.top_parent.ui.distance_source_detector.text())
        detector_offset = float(self.top_parent.ui.detector_offset.text())

        logging.info(f"distance_source_detector_m: {distance_source_detector_m}")
        logging.info(f"detector_offset: {detector_offset}")

        # try:
        self.time_spectra_presenter.load_data(time_spectra_file, distance_source_detector_m, detector_offset)
        self.update_time_spectra_data()
        # except Exception as e:
        #     logging.error(f"Error loading time spectra: {str(e)}")
        #     show_status_message(
        #         parent=self.parent,
        #         message=f"Error loading time spectra: {str(e)}",
        #         status=StatusMessageStatus.error,
        #         duration_s=5,
        #     )

    def update_time_spectra_data(self):
        logging.info("Updating time spectra data ...")
        time_spectra_data = self.time_spectra_presenter.model.get_data()

        self.parent.time_spectra[TimeSpectraKeys.file_name] = time_spectra_data["filename"]
        self.parent.time_spectra[TimeSpectraKeys.tof_array] = time_spectra_data["tof_array"]
        self.parent.time_spectra[TimeSpectraKeys.lambda_array] = time_spectra_data["lambda_array"]
        self.parent.time_spectra[TimeSpectraKeys.file_index_array] = np.arange(len(time_spectra_data["tof_array"]))
        self.parent.time_spectra[TimeSpectraKeys.counts_array] = time_spectra_data["counts_array"]

        # update time spectra tab
        self.parent.ui.time_spectra_name_label.setText(os.path.basename(time_spectra_data["filename"]))
        self.parent.ui.time_spectra_preview_pushButton.setEnabled(True)
        logging.info("... done!")

    def display_integrated_image(self):
        logging.info("Displaying integrated image ...")
        self.parent.integrated_view.clear()

        if self.parent.integrated_image is None:
            return

        self.parent.integrated_view.setImage(self.parent.integrated_image)

        roi = self.parent.bin_roi
        x0 = roi["x0"]
        y0 = roi["y0"]
        width = roi["width"]
        height = roi["height"]
        roi_item = pg.ROI([x0, y0], [width, height])
        roi_item.addScaleHandle([1, 1], [0, 0])
        self.parent.integrated_view.addItem(roi_item)
        roi_item.sigRegionChanged.connect(self.parent.bin_roi_changed)
        self.parent.roi_item = roi_item
        logging.info("... done!")

    def display_profile(self):
        logging.info("Displaying profile ...")
        if self.parent.integrated_image is None:
            return

        integrated_image = self.parent.integrated_image
        image_view = self.parent.integrated_view
        roi_item = self.parent.roi_item

        region = roi_item.getArraySlice(integrated_image, image_view.imageItem)
        x0 = region[0][0].start
        x1 = region[0][0].stop - 1
        y0 = region[0][1].start
        y1 = region[0][1].stop - 1

        width = x1 - x0
        height = y1 - y0

        self.parent.bin_roi = {"x0": x0, "y0": y0, "width": width, "height": height}

        o_plot = Plot(parent=self.parent)
        o_plot.refresh_profile_plot_and_clear_bins()
        logging.info("... done!")

    def bin_xaxis_changed(self):
        o_get = Get(parent=self.parent)
        if o_get.bin_mode() == BinMode.auto:
            self.entering_tab_auto()
        elif o_get.bin_mode() == BinMode.manual:
            o_event = ManualEventHandler(parent=self.parent)
            # o_event.update_manual_snapping_indexes_bins()
            o_event.update_items_displayed()

    def bin_auto_manual_tab_changed(self, new_tab_index=-1):
        if new_tab_index == -1:
            new_tab_index = self.parent.ui.bin_tabWidget.currentIndex()

        if new_tab_index == 0:
            self.parent.session[SessionSubKeys.bin_mode] = BinMode.auto

        elif new_tab_index == 1:
            self.parent.session[SessionSubKeys.bin_mode] = BinMode.manual

        elif new_tab_index == 2:
            pass

        else:
            raise NotImplementedError("LinearBin mode not implemented!")

        self.entering_tab()

    def entering_tab(self):
        o_get = Get(parent=self.parent)
        if o_get.bin_mode() == BinMode.auto:
            self.entering_tab_auto()
        elif o_get.bin_mode() == BinMode.manual:
            self.entering_tab_manual()
        else:
            raise NotImplementedError("tab not implemented yet!")

    def entering_tab_manual(self):
        # if table has one entry, select first row
        o_table = TableHandler(table_ui=self.parent.ui.bin_manual_tableWidget)
        nbr_row = o_table.row_count()
        if nbr_row > 0:
            o_table.select_row(0)

        o_plot = Plot(parent=self.parent)
        o_plot.refresh_profile_plot_and_clear_bins()

        o_manual_event = ManualEventHandler(parent=self.parent)
        o_manual_event.display_all_items()

    def entering_tab_auto(self):
        o_get = Get(parent=self.parent)
        o_auto_event = AutoEventHandler(parent=self.parent)
        if o_get.bin_auto_mode() == BinAutoMode.linear:
            o_auto_event.auto_linear_radioButton_changed()
        elif o_get.bin_auto_mode() == BinAutoMode.log:
            o_auto_event.auto_log_radioButton_changed()
        o_auto_event.refresh_auto_tab()
