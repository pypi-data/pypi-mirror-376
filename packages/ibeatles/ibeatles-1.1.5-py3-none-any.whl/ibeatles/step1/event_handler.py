#!/usr/bin/env python
"""
Event Handler (step 1)
"""

import os

from loguru import logger

from ibeatles import DataType, Material
from ibeatles.all_steps.event_handler import EventHandler as TopEventHandler
from ibeatles.step1.data_handler import DataHandler
from ibeatles.step1.gui_handler import Step1GuiHandler
from ibeatles.step1.plot import Step1Plot
from ibeatles.step2.initialization import Initialization as Step2Initialization
from ibeatles.utilities.bragg_edge_element_handler import BraggEdgeElementHandler
from ibeatles.utilities.retrieve_data_infos import RetrieveGeneralDataInfos


class EventHandler(TopEventHandler):
    def import_button_clicked(self):
        logger.info(f"{self.data_type} import button clicked")

        self.parent.loading_flag = True
        o_load = DataHandler(parent=self.parent, data_type=self.data_type)
        _folder = o_load.select_folder()
        state = o_load.import_files_from_folder(
            folder=_folder,
            extension=None,
        )

        if state:
            self.import_button_clicked_step2(folder=_folder)
        else:
            logger.info("Import button clicked ... operation canceled!")

    def import_button_clicked_step2(self, folder):
        o_load = DataHandler(parent=self.parent, data_type=self.data_type)
        o_load.import_time_spectra()
        self.parent.select_load_data_row(data_type=self.data_type, row=0)
        self.parent.retrieve_general_infos(data_type=self.data_type)
        self.parent.retrieve_general_data_infos(data_type=self.data_type)
        BraggEdgeElementHandler(parent=self.parent)
        o_plot = Step1Plot(parent=self.parent, data_type=self.data_type)
        o_plot.initialize_default_roi()
        o_plot.display_bragg_edge(mouse_selection=False)
        o_gui = Step1GuiHandler(parent=self.parent, data_type=self.data_type)
        o_gui.check_time_spectra_widgets()
        o_gui.check_step1_widgets()
        # self.parent.check_files_error()
        o_step2_gui = Step2Initialization(parent=self.parent)
        o_step2_gui.roi()
        self.update_default_path(folder=folder)
        # activate or not infos button
        self.parent.infos_window_update(data_type=self.data_type)

        if self.data_type == DataType.sample:
            self.parent.data_metadata["normalization"]["data"] = []

        self.parent.ui.sample_ob_splitter.setSizes([20, 450])

    def sample_list_selection_changed(self):
        if not self.parent.loading_flag:
            o_retrieve_data_infos = RetrieveGeneralDataInfos(parent=self.parent, data_type=DataType.sample)
            o_retrieve_data_infos.update()
            self.parent.roi_image_view_changed(mouse_selection=False)
        else:
            self.parent.loading_flag = False

    def update_default_path(self, folder="./"):
        parent_folder = os.path.abspath(folder)
        if self.data_type == DataType.sample:
            self.parent.default_path[DataType.ob] = parent_folder
            self.parent.default_path[DataType.normalization] = parent_folder
        elif self.data_type == DataType.ob:
            self.parent.default_path[DataType.normalization] = parent_folder
        elif self.data_type == DataType.normalization:
            self.parent.default_path[DataType.normalized] = parent_folder

    def check_status_of_material_widgets(self):
        """
        this check if the lattice and crystal structure widgets can be displayed in the load data and normalized
        tab and changed the visibility of those widgets accordingly

        True if the selected element is from the default list, or if user used method1 when adding a new material
        False otherwise
        """
        element = self.parent.ui.list_of_elements.currentText()
        if element in self.parent.user_defined_bragg_edge_list.keys():
            if (
                self.parent.user_defined_bragg_edge_list[element][Material.method_used]
                == Material.via_lattice_and_crystal_structure
            ):
                self.parent.ui.crystal_structure_groupBox.setVisible(True)
                self.parent.ui.lattice_groupBox.setVisible(True)
            else:
                self.parent.ui.crystal_structure_groupBox.setVisible(False)
                self.parent.ui.lattice_groupBox.setVisible(False)
        else:
            self.parent.ui.crystal_structure_groupBox.setVisible(True)
            self.parent.ui.lattice_groupBox.setVisible(True)
