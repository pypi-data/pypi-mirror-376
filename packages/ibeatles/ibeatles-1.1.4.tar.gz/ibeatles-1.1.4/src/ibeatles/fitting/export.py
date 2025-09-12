#!/usr/bin/env python
"""
Export configuration
"""

import os

from loguru import logger
from qtpy.QtWidgets import QFileDialog

from ibeatles import DataType, FileType
from ibeatles.fitting import FittingTabSelected
from ibeatles.fitting.get import Get
from ibeatles.session import SessionKeys, SessionSubKeys
from ibeatles.utilities.file_handler import (
    create_full_export_file_name,
)
from ibeatles.utilities.get import Get as MainGet
from ibeatles.utilities.json_handler import save_json
from ibeatles.utilities.status_message_config import (
    StatusMessageStatus,
    show_status_message,
)
from ibeatles.utilities.time import get_current_time_in_special_file_name_format


class Export:
    def __init__(self, parent=None, grand_parent=None):
        self.parent = parent
        self.grand_parent = grand_parent

    def config_for_cli(self, output_folder: str = None):
        o_get = Get(parent=self.parent)
        main_tab_selected = o_get.main_tab_selected()
        if main_tab_selected == FittingTabSelected.march_dollase:
            logger.info("Export in Marche Dollase mode not supported yet!")
            show_status_message(
                parent=self.parent,
                message="Export in Marche Dollase mode not supported yet!",
                status=StatusMessageStatus.error,
                duration_s=10,
            )
            return

        _current_time = get_current_time_in_special_file_name_format()

        output_folder = os.path.abspath(output_folder)
        output_file_name = create_full_export_file_name(
            os.path.join(output_folder, f"config_{_current_time}"), FileType.json
        )

        logger.info(f"Exporting configuration to be used by the command line version (CLI) -> {output_file_name}")

        # o_get = Get(parent=self.parent)
        # strain_mapping_dict = o_get.strain_mapping_dictionary()

        session_dict = self.grand_parent.session_dict

        raw_data_dir = session_dict[DataType.sample][SessionSubKeys.current_folder]
        if session_dict[DataType.sample][SessionSubKeys.list_files]:
            _, raw_data_extension = os.path.splitext(session_dict[DataType.sample][SessionSubKeys.list_files][0])
        else:
            raw_data_extension = None

        open_beam_data_dir = session_dict[DataType.ob][SessionSubKeys.current_folder]
        if session_dict[DataType.ob][SessionSubKeys.list_files]:
            _, open_beam_data_extension = os.path.splitext(session_dict[DataType.ob][SessionSubKeys.list_files][0])
        else:
            open_beam_data_extension = None

        list_normalization_roi = session_dict[DataType.normalization][SessionSubKeys.roi]
        normalization_sample_background = []
        for _roi in list_normalization_roi:
            _state, x0, y0, width, height, _type = _roi
            if (_type == "background") and _state:
                normalization_sample_background.append({"x0": x0, "y0": y0, "width": width, "height": height})

        moving_average_active = session_dict[SessionKeys.reduction][SessionSubKeys.activate]
        moving_average_dimension = session_dict[SessionKeys.reduction][SessionSubKeys.dimension]
        moving_average_size = {
            "y": session_dict[SessionKeys.reduction][SessionSubKeys.size]["y"],
            "x": session_dict[SessionKeys.reduction][SessionSubKeys.size]["x"],
        }
        if moving_average_dimension == "3D":
            moving_average_size["z"] = session_dict[SessionKeys.reduction][SessionSubKeys.size["z"]]

        moving_average_type = session_dict[SessionKeys.reduction][SessionSubKeys.type]

        if session_dict[SessionKeys.reduction][SessionSubKeys.process_order] == "option1":
            processing_order = "Moving average, Normalization"
        else:
            processing_order = "Normalization, Moving average"

        o_get = MainGet(parent=self.grand_parent)
        analysis_material_element = o_get.get_material()

        pixel_binning = {
            "x0": session_dict[SessionKeys.bin][SessionSubKeys.roi][1],
            "y0": session_dict[SessionKeys.bin][SessionSubKeys.roi][2],
            "width": session_dict[SessionKeys.bin][SessionSubKeys.roi][3],
            "height": session_dict[SessionKeys.bin][SessionSubKeys.roi][4],
            "bins_size": session_dict[SessionKeys.bin][SessionSubKeys.roi][5],
        }

        fitting_lambda_range = session_dict[SessionKeys.fitting][SessionSubKeys.lambda_range_index]

        # table_dictionary = self.grand_parent.kropff_table_dictionary
        # logger.info(f"{session_dict[SessionKeys.fitting].keys() =}")
        # print(f"{session_dict[SessionKeys.fitting]['xaxis'] = }")

        session_dict[SessionKeys.fitting][SessionSubKeys.xaxis] = [
            float(x) for x in self.grand_parent.normalized_lambda_bragg_edge_x_axis
        ]
        x_axis = session_dict[SessionKeys.fitting][SessionSubKeys.xaxis]

        lambda_min = x_axis[fitting_lambda_range[0]] * 1e-10
        lambda_max = x_axis[fitting_lambda_range[1]] * 1e-10

        lambda_0 = float(self.parent.ui.bragg_edge_calculated.text())
        strain_mapping_d0 = float(f"{lambda_0 / 2.0:04.4f}")

        quality_threshold = 0.8

        distance_source_detector_in_m = session_dict[SessionKeys.instrument][SessionSubKeys.distance_source_detector]
        detector_offset_in_us = session_dict[SessionKeys.instrument][SessionSubKeys.detector_value]

        normalized_data_dir = os.path.join(output_folder, f"normalized_{_current_time}")
        analysis_results_dir = os.path.join(output_folder, f"analysis_{_current_time}")
        strain_results_dir = os.path.join(output_folder, f"strain_{_current_time}")

        config = {
            "raw_data": {
                "raw_data_dir": raw_data_dir,
                "extension": raw_data_extension,
            },
            "open_beam": {
                "open_beam_data_dir": open_beam_data_dir,
                "extension": open_beam_data_extension,
            },
            "normalization": {
                "sample_background": normalization_sample_background,
                "moving_average": {
                    "active": moving_average_active,
                    "dimension": moving_average_dimension,
                    "size": moving_average_size,
                    "type": moving_average_type,
                },
                "processing_order": processing_order,
            },
            "analysis": {
                "material": {
                    "element": analysis_material_element,
                },
                "pixel_binning": pixel_binning,
                "fitting": {
                    "lambda_min": lambda_min,
                    "lambda_max": lambda_max,
                },
                "strain_mapping": {
                    "d0": strain_mapping_d0,
                    "quality_threshold": quality_threshold,
                    "visualization": {
                        "interpolation_method": "nearest",
                        "colormap": "viridis",
                        "alpha": 0.5,
                        "display_fit_quality": True,
                    },
                    "output_file_config": {
                        "strain_map_format": "png",
                        "fitting_grid_format": "pdf",
                        "figure_dpi": 300,
                        "csv_format": {
                            "delimiter": ",",
                            "include_metadata_header": True,
                            "metadata_comment_char": "#",
                            "na_rep": "null",
                        },
                    },
                    "save_intermediate_results": False,
                },
                "distance_source_detector_in_m": distance_source_detector_in_m,
                "detector_offset_in_us": detector_offset_in_us,
            },
            "output": {
                "normalized_data_dir": normalized_data_dir,
                "analysis_results_dir": analysis_results_dir,
                "strain_results_dir": strain_results_dir,
            },
        }

        save_json(json_file_name=output_file_name, json_dictionary=config)

    def select_output_folder(self):
        working_dir = os.path.dirname(
            os.path.dirname(self.grand_parent.session_dict[DataType.normalized][SessionSubKeys.current_folder])
        )
        output_folder = str(
            QFileDialog.getExistingDirectory(self.parent, "Select where to export the config file ...", working_dir)
        )
        return output_folder
