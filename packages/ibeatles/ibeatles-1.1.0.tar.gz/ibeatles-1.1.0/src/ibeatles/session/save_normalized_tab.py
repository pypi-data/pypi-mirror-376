#!/usr/bin/env python
"""
SaveNormalizedTab class
"""

from loguru import logger

from ibeatles import DataType
from ibeatles.session import SessionKeys, SessionSubKeys
from ibeatles.utilities.pyqrgraph import Pyqtgrah as PyqtgraphUtilities

from .save_tab import SaveTab


class SaveNormalizedTab(SaveTab):
    def normalized(self):
        """record the ROI selected"""

        data_type = DataType.normalized

        list_files = self.parent.list_files[data_type]
        current_folder = self.parent.data_metadata[data_type]["folder"]
        time_spectra_filename = self.parent.data_metadata[data_type]["time_spectra"]["filename"]
        list_files_selected = [int(index) for index in self.parent.list_file_selected[data_type]]
        list_roi = self.parent.list_roi[data_type]

        o_pyqt = PyqtgraphUtilities(
            parent=self.parent,
            image_view=self.parent.ui.normalized_image_view,
            data_type=data_type,
        )
        state = o_pyqt.get_state()
        o_pyqt.save_histogram_level()
        histogram = self.parent.image_view_settings[data_type]["histogram"]

        logger.info("Recording parameters of normalized tab")
        logger.info(f" len(list files) = {len(list_files)}")
        logger.info(f" current folder: {current_folder}")
        logger.info(f" time spectra filename: {time_spectra_filename}")
        logger.info(f" list files selected: {list_files_selected}")
        logger.info(f" len(list rois): {len(list_roi)}")
        logger.info(f" state: {state}")
        logger.info(f" histogram: {histogram}")

        self.session_dict[data_type][SessionSubKeys.list_files] = list_files
        self.session_dict[data_type][SessionSubKeys.current_folder] = current_folder
        self.session_dict[data_type][SessionSubKeys.time_spectra_filename] = time_spectra_filename
        self.session_dict[data_type][SessionSubKeys.list_files_selected] = list_files_selected
        self.session_dict[data_type][SessionSubKeys.list_rois] = list_roi
        self.session_dict[data_type][SessionSubKeys.image_view_state] = state
        self.session_dict[data_type][SessionSubKeys.image_view_histogram] = histogram
        self.session_dict[SessionKeys.reduction] = self.parent.session_dict[SessionKeys.reduction]
