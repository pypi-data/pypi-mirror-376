#!/usr/bin/env python
"""
SaveFittingTab class
"""

from loguru import logger

from ibeatles import DataType
from ibeatles.fitting import FittingKeys, FittingTabSelected
from ibeatles.fitting.kropff import SessionSubKeys as KropffSessionSubKeys
from ibeatles.fitting.march_dollase import (
    SessionSubKeys as MarchDollaseSessionSubKeys,
)
from ibeatles.session import SessionKeys, SessionSubKeys
from ibeatles.session.save_tab import SaveTab
from ibeatles.utilities.pyqrgraph import Pyqtgrah as PyqtgraphUtilities


class SaveFittingTab(SaveTab):
    def fitting(self):
        if not self.parent.session_dict[DataType.fitting][SessionSubKeys.ui_accessed]:
            return

        self.general_infos()
        self.march_dollase()
        self.kropff()

    def general_infos(self):
        logger.info("Recording general fitting parameters")

        if self.parent.fitting_image_view:
            o_pyqt = PyqtgraphUtilities(
                parent=self.parent,
                image_view=self.parent.fitting_image_view,
                data_type=DataType.fitting,
            )
            state = o_pyqt.get_state()
            o_pyqt.save_histogram_level(data_type_of_data=DataType.normalized)
            histogram = self.parent.image_view_settings[DataType.fitting]["histogram"]
        else:
            state = None
            histogram = None

        fitting_bragg_edge_linear_selection = self.parent.fitting_bragg_edge_linear_selection
        if fitting_bragg_edge_linear_selection:
            min_lambda_index = int(fitting_bragg_edge_linear_selection[0])
            max_lambda_index = int(fitting_bragg_edge_linear_selection[1])
            self.session_dict[DataType.fitting]["lambda range index"] = [
                min_lambda_index,
                max_lambda_index,
            ]

        logger.info(f" state: {state}")
        logger.info(f" histogram: {histogram}")

        self.session_dict[DataType.fitting][FittingKeys.x_axis] = [
            float(x) for x in self.parent.normalized_lambda_bragg_edge_x_axis
        ]
        self.session_dict[DataType.fitting][FittingKeys.transparency] = self.parent.fitting_transparency_slider_value
        self.session_dict[DataType.fitting][FittingKeys.image_view_state] = state
        self.session_dict[DataType.fitting][FittingKeys.image_view_histogram] = histogram
        self.session_dict[DataType.fitting][FittingKeys.ui_accessed] = self.parent.session_dict[DataType.fitting][
            SessionSubKeys.ui_accessed
        ]
        self.session_dict[DataType.fitting][FittingKeys.ui] = self.parent.session_dict[DataType.fitting]["ui"]

    def march_dollase(self):
        logger.info("Recording March-Dollase fitting parameters")

        if self.parent.fitting_ui:
            self.parent.fitting_ui.save_all_parameters()

        table_dictionary = self.parent.march_table_dictionary

        formatted_table_dictionary = {}

        for _row in table_dictionary.keys():
            _entry = table_dictionary[_row]

            active_flag = _entry["active"]
            lock_flag = _entry["lock"]
            fitting_confidence = _entry["fitting_confidence"]
            d_spacing = _entry["d_spacing"]
            sigma = _entry["sigma"]
            alpha = _entry["alpha"]
            a1 = _entry["a1"]
            a2 = _entry["a2"]
            a5 = _entry["a5"]
            a6 = _entry["a6"]

            formatted_table_dictionary[_row] = {
                "active": active_flag,
                "lock": lock_flag,
                "fitting_confidence": fitting_confidence,
                "d_spacing": d_spacing,
                "sigma": sigma,
                "alpha": alpha,
                "a1": a1,
                "a2": a2,
                "a5": a5,
                "a6": a6,
            }
        self.session_dict[DataType.fitting][FittingTabSelected.march_dollase][
            MarchDollaseSessionSubKeys.table_dictionary
        ] = formatted_table_dictionary
        self.session_dict[DataType.fitting][FittingTabSelected.march_dollase][
            MarchDollaseSessionSubKeys.plot_active_row_flag
        ] = self.parent.display_active_row_flag

        x_axis = self.session_dict[DataType.fitting][SessionSubKeys.x_axis]
        if x_axis:
            logger.info(f" len(x_axis): {len(x_axis)}")
        else:
            logger.info(" x_axis is empty!")

        logger.info(f" lambda range index: {self.session_dict[SessionKeys.fitting][SessionSubKeys.lambda_range_index]}")

    def kropff(self):
        logger.info("Recording Kropff fitting parameters")
        table_dictionary = self.parent.kropff_table_dictionary

        formatted_table_dictionary = {}

        for _row in table_dictionary.keys():
            _entry = table_dictionary[_row]

            a0 = _entry["a0"]
            b0 = _entry["b0"]
            ahkl = _entry["ahkl"]
            bhkl = _entry["bhkl"]
            lambda_hkl = _entry["lambda_hkl"]
            tau = _entry["tau"]
            sigma = _entry["sigma"]
            bragg_peak_threshold = _entry["bragg peak threshold"]
            lock = _entry["lock"]
            rejected = _entry["rejected"]
            row_index = _entry[FittingKeys.row_index]
            column_index = _entry[FittingKeys.column_index]

            formatted_table_dictionary[_row] = {
                "a0": a0,
                "b0": b0,
                "ahkl": ahkl,
                "bhkl": bhkl,
                "lambda_hkl": lambda_hkl,
                "tau": tau,
                "sigma": sigma,
                "bragg_peak_threshold": bragg_peak_threshold,
                "lock": lock,
                "rejected": rejected,
                FittingKeys.row_index: row_index,
                FittingKeys.column_index: column_index,
            }

        self.import_from_parent_session_dict(
            key=KropffSessionSubKeys.table_dictionary, source=formatted_table_dictionary
        )
        self.import_from_parent_session_dict(key=KropffSessionSubKeys.automatic_bragg_peak_threshold_finder)
        self.import_from_parent_session_dict(key=KropffSessionSubKeys.automatic_bragg_peak_threshold_algorithm)
        self.import_from_parent_session_dict(key=KropffSessionSubKeys.high_tof)
        self.import_from_parent_session_dict(key=KropffSessionSubKeys.low_tof)
        self.import_from_parent_session_dict(key=KropffSessionSubKeys.bragg_peak)
        self.import_from_parent_session_dict(key=KropffSessionSubKeys.kropff_bragg_peak_good_fit_conditions)
        self.import_from_parent_session_dict(key=KropffSessionSubKeys.kropff_lambda_settings)
        self.import_from_parent_session_dict(key=KropffSessionSubKeys.bragg_peak_row_rejections_conditions)
        self.import_from_parent_session_dict(key=KropffSessionSubKeys.automatic_fitting_threshold_width)

    def import_from_parent_session_dict(self, key: SessionSubKeys = None, source: dict = None):
        """
        this method will move the key values specified from the self.parent.session_dict[fitting][kropff][key]
        if source is not specified, otherwise the source is used as input
        """
        if source is None:
            source = self.parent.session_dict[DataType.fitting][FittingTabSelected.kropff][key]

        self.session_dict[DataType.fitting][FittingTabSelected.kropff][key] = source
