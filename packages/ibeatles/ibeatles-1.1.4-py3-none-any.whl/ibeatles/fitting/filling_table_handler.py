#!/usr/bin/env python
"""
Filling table handler
"""

import numpy as np
from qtpy import QtCore, QtGui
from qtpy.QtWidgets import QCheckBox, QTableWidgetItem

from ibeatles.fitting import FittingKeys
from ibeatles.fitting.kropff import SessionSubKeys as KropffsessionSubKeys
from ibeatles.utilities.table_handler import TableHandler


class FillingTableHandler:
    table_dictionary: dict = {}
    advanced_mode_flag = True

    def __init__(self, grand_parent=None, parent=None):
        self.grand_parent = grand_parent
        self.parent = parent

    def set_mode(self, advanced_mode=True):
        self.advanced_mode_flag = advanced_mode
        list_header_table_advanced_columns = [10, 11]
        list_parent_advanced_columns = [15, 16, 17, 18]

        self.parent.ui.header_table.horizontalHeader().blockSignals(True)
        self.parent.ui.value_table.horizontalHeader().blockSignals(True)

        # hide column a5 and a6
        for _col_index in list_header_table_advanced_columns:
            self.parent.ui.header_table.setColumnHidden(_col_index, not advanced_mode)
        for _col_index in list_parent_advanced_columns:
            self.parent.ui.value_table.setColumnHidden(_col_index, not advanced_mode)

        self.parent.ui.header_table.horizontalHeader().blockSignals(False)
        self.parent.ui.value_table.horizontalHeader().blockSignals(False)

        # repopulate table
        self.fill_table()

    def get_row_to_show_state(self):
        """
        return 'all', 'active' or 'lock'
        """
        if self.parent.ui.show_all_bins.isChecked():
            return "all"
        elif self.parent.ui.show_only_active_bins.isChecked():
            return "active"
        else:
            return "lock"

    def fill_table(self):
        self.fill_march_table()
        self.fill_kropff_table()

    def fill_kropff_table(self):
        self.fill_kropff_high_tof_table()
        self.fill_kropff_low_tof_table()
        self.fill_kropff_bragg_peak_table()

    def fill_kropff_high_tof_table(self):
        o_table = TableHandler(table_ui=self.parent.ui.high_lda_tableWidget)
        o_table.block_signals(True)

        o_table.remove_all_rows()
        table_dictionary = self.grand_parent.kropff_table_dictionary
        nbr_row = len(table_dictionary)

        for _index in np.arange(nbr_row):
            _str_index = str(_index)

            _entry = table_dictionary[_str_index]

            o_table.insert_empty_row(row=_index)

            o_table.insert_item(
                row=_index,
                column=0,
                value=_entry[FittingKeys.row_index] + 1,
                editable=False,
                align_center=True,
            )
            o_table.insert_item(
                row=_index,
                column=1,
                value=_entry[FittingKeys.column_index] + 1,
                editable=False,
                align_center=True,
            )

            # from column 2 to 5
            list_value = [
                _entry[KropffsessionSubKeys.a0]["val"],
                _entry[KropffsessionSubKeys.b0]["val"],
                _entry[KropffsessionSubKeys.a0]["err"],
                _entry[KropffsessionSubKeys.b0]["err"],
            ]

            for _local_index, _value in enumerate(list_value):
                o_table.insert_item(
                    row=_index,
                    column=_local_index + 2,
                    value=_value,
                    format_str="{:.4f}",
                    editable=False,
                    align_center=True,
                )

        # select first row
        o_table.block_signals(True)
        o_table.select_row(0)

        o_table.block_signals(False)

    def fill_kropff_low_tof_table(self):
        o_table = TableHandler(table_ui=self.parent.ui.low_lda_tableWidget)
        o_table.remove_all_rows()
        table_dictionary = self.grand_parent.kropff_table_dictionary
        nbr_row = len(table_dictionary)
        o_table.block_signals(True)

        for _index in np.arange(nbr_row):
            _str_index = str(_index)
            _entry = table_dictionary[_str_index]

            o_table.insert_empty_row(row=_index)

            o_table.insert_item(
                row=_index,
                column=0,
                value=_entry[FittingKeys.row_index] + 1,
                editable=False,
                align_center=True,
            )
            o_table.insert_item(
                row=_index,
                column=1,
                value=_entry[FittingKeys.column_index] + 1,
                editable=False,
                align_center=True,
            )

            # from column 2 to 5
            list_value = [
                _entry[KropffsessionSubKeys.ahkl]["val"],
                _entry[KropffsessionSubKeys.bhkl]["val"],
                _entry[KropffsessionSubKeys.ahkl]["err"],
                _entry[KropffsessionSubKeys.bhkl]["err"],
            ]
            for _local_index, _value in enumerate(list_value):
                o_table.insert_item(
                    row=_index,
                    column=_local_index + 2,
                    value=_value,
                    format_str="{:.4f}",
                    editable=False,
                    align_center=True,
                )

        # select first row
        o_table.select_row(0)

        o_table.block_signals(False)

    def fill_kropff_bragg_peak_table(self):
        o_table = TableHandler(table_ui=self.parent.ui.bragg_edge_tableWidget)
        o_table.remove_all_rows()
        table_dictionary = self.grand_parent.kropff_table_dictionary
        nbr_row = len(table_dictionary)
        o_table.block_signals(True)

        for _index in np.arange(nbr_row):
            _str_index = str(_index)
            _entry = table_dictionary[_str_index]

            o_table.insert_empty_row(row=_index)

            o_table.insert_item(
                row=_index,
                column=0,
                value=_entry[FittingKeys.row_index] + 1,
                editable=False,
                align_center=True,
            )
            o_table.insert_item(
                row=_index,
                column=1,
                value=_entry[FittingKeys.column_index] + 1,
                editable=False,
                align_center=True,
            )

            # from column 2 to 7
            list_value = [
                _entry[KropffsessionSubKeys.lambda_hkl]["val"],
                _entry[KropffsessionSubKeys.tau]["val"],
                _entry[KropffsessionSubKeys.sigma]["val"],
                _entry[KropffsessionSubKeys.lambda_hkl]["err"],
                _entry[KropffsessionSubKeys.tau]["err"],
                _entry[KropffsessionSubKeys.sigma]["err"],
            ]

            for _local_index, _value in enumerate(list_value):
                format_str = ""
                if _value:
                    number_of_digits = self.parent.ui.kropff_bragg_peak_number_of_digits_spinBox.value()
                    format_str = "{:." + str(number_of_digits) + "f}"
                o_table.insert_item(
                    row=_index,
                    column=_local_index + 2,
                    value=_value,
                    format_str=format_str,
                    editable=False,
                    align_center=True,
                )

        # select first row
        o_table.select_row(0)

        o_table.block_signals(False)

    def fill_march_table(self):
        self.clear_table_ui()
        table_dictionary = self.grand_parent.march_table_dictionary

        row_to_show_state = self.get_row_to_show_state()
        nbr_row = len(table_dictionary)

        self.parent.ui.value_table.blockSignals(True)

        for _index in np.arange(nbr_row):
            _str_index = str(_index)
            _entry = table_dictionary[_str_index]

            # add new row
            self.parent.ui.value_table.insertRow(_index)

            # row and column index (columns 0 and 1)
            self.set_item(
                table_ui=self.parent.ui.value_table,
                row=_index,
                col=0,
                value=_entry[FittingKeys.row_index] + 1,
            )  # +1 because table starts indexing at 1

            self.set_item(
                table_ui=self.parent.ui.value_table,
                row=_index,
                col=1,
                value=_entry[FittingKeys.column_index] + 1,
            )  # +1 because table starts indexing at 1

            # add lock button in first cell (column: 2)
            _lock_button = QCheckBox()
            _is_lock = _entry[FittingKeys.lock]

            _lock_button.setChecked(_is_lock)
            _lock_button.stateChanged.connect(
                lambda state=0, row=_index: self.parent.lock_button_state_changed(state, row)
            )

            self.parent.ui.value_table.setCellWidget(_index, 2, _lock_button)

            # add active button in second cell (column: 3)
            _active_button = QCheckBox()
            _is_active = _entry[FittingKeys.active]

            _active_button.setChecked(_is_active)
            _active_button.stateChanged.connect(
                lambda state=0, row=_index: self.parent.active_button_state_changed(state, row)
            )

            self.parent.ui.value_table.setCellWidget(_index, 3, _active_button)

            # bin # (column: 1)
            # _bin_number = QTableWidgetItem("{:02}".format(_index))
            # grand_parent_ui.setItem(_index, 1, _bin_number)

            # from column 2 -> nbr_column
            list_value = [
                _entry["fitting_confidence"],
                _entry["d_spacing"]["val"],
                _entry["d_spacing"]["err"],
                _entry["sigma"]["val"],
                _entry["sigma"]["err"],
                _entry["alpha"]["val"],
                _entry["alpha"]["err"],
                _entry["a1"]["val"],
                _entry["a1"]["err"],
                _entry["a2"]["val"],
                _entry["a2"]["err"],
                _entry["a5"]["val"],
                _entry["a5"]["err"],
                _entry["a6"]["val"],
                _entry["a6"]["err"],
            ]

            list_fixed_flag = [
                False,
                _entry["d_spacing"]["fixed"],
                _entry["d_spacing"]["fixed"],
                _entry["sigma"]["fixed"],
                _entry["sigma"]["fixed"],
                _entry["alpha"]["fixed"],
                _entry["alpha"]["fixed"],
                _entry["a1"]["fixed"],
                _entry["a1"]["fixed"],
                _entry["a2"]["fixed"],
                _entry["a2"]["fixed"],
                _entry["a5"]["fixed"],
                _entry["a5"]["fixed"],
                _entry["a6"]["fixed"],
                _entry["a6"]["fixed"],
            ]

            for _local_index, _value in enumerate(list_value):
                self.set_item(
                    table_ui=self.parent.ui.value_table,
                    row=_index,
                    col=_local_index + 4,
                    value=_value,
                    fixed_flag=list_fixed_flag[_local_index],
                )

            if row_to_show_state == "active":
                if not _is_active:
                    self.parent.ui.value_table.hideRow(_index)
            elif row_to_show_state == "lock":
                if not _is_lock:
                    self.parent.ui.value_table.hideRow(_index)

        self.parent.ui.value_table.blockSignals(False)

    def set_item(self, table_ui=None, row=0, col=0, value="", fixed_flag=False):
        item = QTableWidgetItem(str(value))
        if fixed_flag:
            item.setTextColor(QtGui.QColor(255, 0, 0, alpha=255))
        item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)

        table_ui.setItem(row, col, item)

    def clear_table_ui(self):
        self.parent.ui.blockSignals(True)
        nbr_row = self.parent.ui.value_table.rowCount()
        for _row in np.arange(nbr_row):
            self.parent.ui.value_table.removeRow(0)
        self.parent.ui.value_table.blockSignals(False)

    def clear_table(self):
        self.unselect_full_table()
        self.parent.ui.value_table.blockSignals(True)
        nbr_row = self.parent.ui.value_table.rowCount()
        for _row in np.arange(nbr_row):
            self.parent.ui.value_table.removeRow(0)
        self.parent.ui.value_table.blockSignals(False)

        self.parent.selection_in_grand_parent_changed()
