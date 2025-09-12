import glob
import json
import os
import shutil
from collections import Counter
from datetime import datetime
from pathlib import Path

import numpy as np
from astropy.io import fits
from PIL import Image
from qtpy.QtWidgets import QFileDialog

TIME_SPECTRA_NAME_FORMAT = "*_Spectra.txt"


class FileHandler:
    @classmethod
    def get_list_of_folders(cls, top_folder):
        full_list = glob.glob(top_folder + "/*")
        full_list.sort()
        list_folders = []
        for _entry in full_list:
            if os.path.isdir(_entry):
                list_folders.append(_entry)
        return list_folders

    @classmethod
    def get_list_of_all_subfolders(cls, top_folder):
        tuple_folders = os.walk(top_folder)
        return [x[0] for x in tuple_folders]

    @classmethod
    def get_list_of_tif(cls, folder):
        full_list = glob.glob(folder + "/*.tif*")
        full_list.sort()
        return full_list

    @classmethod
    def get_parent_folder(cls, full_folder):
        folder_parts = Path(full_folder).parts
        return folder_parts[-2]

    @classmethod
    def get_parent_path(cls, full_path):
        full_path = Path(full_path)
        return full_path.parent

    @classmethod
    def get_base_filename(cls, full_file_name):
        return Path(full_file_name).name

    @staticmethod
    def get_file_extension(file_name):
        ext = Path(file_name).suffix
        return ext

    @classmethod
    def retrieve_ascii_contain(cls, full_file_name):
        file_contain = []
        with open(full_file_name) as f:
            file_contain = f.read()
        return file_contain

    @classmethod
    def cleanup_list_of_files(cls, list_of_files=[], base_number=5):
        """Will only keep the files that have the same number of character as
        the first n files"""
        if len(list_of_files) == 0:
            return []

        len_base_files = []
        for _file in list_of_files[0:base_number]:
            len_base_files.append(len(_file))

        # make sure all the length of the base number files match
        set_len_base_files = set(len_base_files)
        if len(set_len_base_files) > 1:
            raise ValueError("Format Input File Do Not Match!")

        len_file = len_base_files[0]
        final_list = []
        for _file in list_of_files:
            if len(_file) == len_file:
                final_list.append(_file)

        return final_list

    @classmethod
    def make_fits(cls, data=[], filename=""):
        fits.writeto(filename, data, overwrite=True)

    @classmethod
    def make_tiff(cls, data=[], filename=""):
        new_image = Image.fromarray(data)
        new_image.save(filename)

    @classmethod
    def make_ascii_file(cls, metadata=[], data=[], output_file_name="", sep=","):
        f = open(output_file_name, "w")
        for _meta in metadata:
            _line = _meta + "\n"
            f.write(_line)

        if len(np.shape(data)) > 1:
            for _data in data:
                _str_data = [str(_value) for _value in _data]
                _line = sep.join(_str_data) + "\n"
                f.write(_line)
        else:
            _str_data = [str(_value) + "\n" for _value in data]
            for _data in _str_data:
                f.write(_data)

        f.close()

    def make_json_file(data_dict: dict = None, output_file_name: str = None):
        with open(output_file_name, "w") as json_file:
            json.dump(data_dict, json_file)

    @staticmethod
    def make_or_reset_folder(folder_name):
        if os.path.exists(folder_name):
            shutil.rmtree(folder_name)
        os.makedirs(folder_name)

    @staticmethod
    def make_folder(folder_name):
        os.makedirs(folder_name)

    @staticmethod
    def make_or_append_date_time_to_folder(folder_name):
        if os.path.exists(folder_name):
            _current_date_time = FileHandler.get_current_timestamp()
            folder_name += f"_{_current_date_time}"
        os.makedirs(folder_name)
        return folder_name

    @staticmethod
    def get_current_timestamp():
        """Convert the unix time stamp into a human-readable time format

        Format return will look like  "y2018_m01_d29_h10_mn30"
        """
        now = datetime.now()
        return now.strftime("y%Y_m%m_d%d_h%H_mn%M")


def retrieve_timestamp_file_name(folder):
    time_spectra = glob.glob(folder + "/" + TIME_SPECTRA_NAME_FORMAT)
    if time_spectra and os.path.exists(time_spectra[0]):
        return f"{time_spectra[0]}"

    else:
        return ""


def read_ascii(filename=""):
    """return contain of an ascii file"""
    with open(filename, "r") as f:
        text = f.read()
    return text


def write_ascii(text="", filename=""):
    with open(filename, "w") as f:
        f.write(text)


def get_current_timestamp():
    """Convert the unix time stamp into a human-readable time format

    Format return will look like  "y2018_m01_d29_h10_mn30"
    """
    now = datetime.now()
    return now.strftime("y%Y_m%m_d%d_h%H_mn%M")


def create_full_export_file_name(base_name, ext):
    """
    Create the name of the file to export all tabs
    """
    file_name = f"{base_name}_{get_current_timestamp()}.{ext}"
    if os.path.exists(file_name):
        file_name = f"{base_name}_{get_current_timestamp()}_{get_current_timestamp()}.{ext}"

    return file_name


def select_folder(start_folder="./"):
    return str(
        QFileDialog.getExistingDirectory(
            caption="Select output folder",
            directory=start_folder,
            options=QFileDialog.ShowDirsOnly,
        )
    )


def get_list_of_most_dominant_extension_from_folder(folder="", files=None):
    """
    This will return the list of files from the most dominant file extension found in the folder
    as well as the most dominant extension used
    """

    if folder:
        list_of_input_files = glob.glob(os.path.join(folder, "*"))
    else:
        list_of_input_files = files

    list_of_input_files.sort()
    list_of_base_name = [os.path.basename(_file) for _file in list_of_input_files]

    # work with the largest common file extension from the folder selected

    counter_extension = Counter()
    for _file in list_of_base_name:
        [_base, _ext] = os.path.splitext(_file)
        counter_extension[_ext] += 1

    dominand_extension = ""
    dominand_number = 0
    for _key in counter_extension.keys():
        if counter_extension[_key] > dominand_number:
            dominand_extension = _key
            dominand_number = counter_extension[_key]

    list_of_input_files = glob.glob(os.path.join(folder, "*" + dominand_extension))
    list_of_input_files.sort()

    list_of_input_files = [os.path.abspath(_file) for _file in list_of_input_files]

    return [list_of_input_files, dominand_extension]
