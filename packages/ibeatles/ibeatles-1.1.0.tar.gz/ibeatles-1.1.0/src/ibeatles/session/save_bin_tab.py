#!/usr/bin/env python
"""
SaveBinTab class
"""

from loguru import logger

from ibeatles import BINNING_LINE_COLOR, DEFAULT_ROI, DataType
from ibeatles.session import SessionKeys, SessionSubKeys
from ibeatles.session.save_tab import SaveTab
from ibeatles.utilities.pyqrgraph import Pyqtgrah as PyqtgraphUtilities


class SaveBinTab(SaveTab):
    def bin(self):
        """record the ROI selected"""

        if not self.parent.data_metadata[DataType.bin]["ui_accessed"]:
            return

        def format_numpy_array_into_list(numpy_array=None):
            if numpy_array is not None:
                formatted_array = []
                for _entry in numpy_array:
                    _new_entry = [int(value) for value in _entry]
                    formatted_array.append(_new_entry)
                return list(formatted_array)
            else:
                return None

        if self.parent.binning_roi is None:
            self.parent.binning_roi = DEFAULT_ROI

        [name, x0, y0, width, height, bin_size] = self.parent.session_dict[DataType.bin][SessionSubKeys.roi]

        binning_line_view_pos = self.parent.binning_line_view["pos"]
        formatted_binning_line_view_pos = format_numpy_array_into_list(binning_line_view_pos)

        binning_line_view_adj = self.parent.binning_line_view["adj"]
        formatted_binning_line_view_adj = format_numpy_array_into_list(binning_line_view_adj)

        binning_line_view_line_color = BINNING_LINE_COLOR

        if self.parent.binning_line_view["image_view"]:
            o_pyqt = PyqtgraphUtilities(
                parent=self.parent,
                image_view=self.parent.binning_line_view["image_view"],
                data_type=DataType.bin,
            )
            state = o_pyqt.get_state()
            o_pyqt.save_histogram_level(data_type_of_data=DataType.normalized)
            histogram = self.parent.image_view_settings[DataType.bin]["histogram"]
        else:
            state = None
            histogram = None

        logger.info("Recording parameters of bin tab")
        logger.info(f" x0:{x0}, y0:{y0}, width:{width}, height:{height}, bin_size:{bin_size}")
        if binning_line_view_pos is not None:
            logger.info(f" len(binning_line_view_pos): {len(binning_line_view_pos)}")
        else:
            logger.info(" binning_line_view_pos: None")

        if formatted_binning_line_view_adj is not None:
            logger.info(f" len(binning_line_view_adj): {len(binning_line_view_adj)}")
        else:
            logger.info(" binning_line_view_adj: None")

        logger.info(f" binning_line_view_line_color: {binning_line_view_line_color}")
        logger.info(f" state: {state}")
        logger.info(f" histogram: {histogram}")

        self.session_dict[SessionKeys.bin][SessionSubKeys.roi] = [
            name,
            x0,
            y0,
            width,
            height,
            bin_size,
        ]
        self.session_dict[SessionKeys.bin][SessionSubKeys.binning_line_view]["pos"] = formatted_binning_line_view_pos
        self.session_dict[SessionKeys.bin][SessionSubKeys.binning_line_view]["adj"] = formatted_binning_line_view_adj
        self.session_dict[SessionKeys.bin][SessionSubKeys.binning_line_view]["line color"] = (
            binning_line_view_line_color
        )
        self.session_dict[DataType.bin][SessionSubKeys.image_view_state] = state
        self.session_dict[DataType.bin][SessionSubKeys.image_view_histogram] = histogram
        self.session_dict[DataType.bin][SessionSubKeys.ui_accessed] = self.parent.data_metadata[DataType.bin][
            "ui_accessed"
        ]
