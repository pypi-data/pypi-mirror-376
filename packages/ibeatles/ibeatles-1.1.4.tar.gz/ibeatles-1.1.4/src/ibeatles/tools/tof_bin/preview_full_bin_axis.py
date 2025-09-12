#!/usr/bin/env python
"""
Preview full bin axis
"""

from qtpy.QtWidgets import QDialog

from ibeatles import load_ui
from ibeatles.tools import ANGSTROMS, MICRO
from ibeatles.tools.tof_bin import TO_ANGSTROMS_UNITS, TO_MICROS_UNITS
from ibeatles.tools.tof_bin.utilities.get import Get
from ibeatles.tools.utilities import TimeSpectraKeys
from ibeatles.utilities.table_handler import TableHandler


class PreviewFullBinAxis(QDialog):
    def __init__(self, parent=None):
        self.parent = parent

        QDialog.__init__(self, parent=parent)
        self.ui = load_ui("ui_preview_full_bin_axis.ui", baseinstance=self)
        self.setWindowTitle("Full Bin Axis Requested")

        self.update_widgets()

    def update_widgets(self):
        o_get = Get(parent=self.parent)

        # top labels
        bin_type = o_get.bin_auto_mode()
        self.ui.bin_type_label.setText(bin_type)

        bin_axis = o_get.current_bin_tab_working_axis()
        self.ui.axis_label.setText(bin_axis)

        if bin_axis == TimeSpectraKeys.file_index_array:
            units = "N/A"
            str_format = "{}"
            coeff = 1
        elif bin_axis == TimeSpectraKeys.tof_array:
            units = f"{MICRO}s"
            str_format = "{:.2f}"
            coeff = TO_MICROS_UNITS
        else:
            units = f"{ANGSTROMS}"
            str_format = "{:.3f}"
            coeff = TO_ANGSTROMS_UNITS

        self.ui.units_label.setText(units)

        # table
        full_bin_axis_requested = self.parent.full_bin_axis_requested
        o_table = TableHandler(table_ui=self.ui.tableWidget)
        for _row, _left_bin_value in enumerate(full_bin_axis_requested[:-1]):
            o_table.insert_empty_row(row=_row)
            o_table.insert_item(
                row=_row,
                column=0,
                value=_left_bin_value * coeff,
                format_str=str_format,
                editable=False,
            )
            o_table.insert_item(
                row=_row,
                column=1,
                value=full_bin_axis_requested[_row + 1] * coeff,
                format_str=str_format,
                editable=False,
            )
