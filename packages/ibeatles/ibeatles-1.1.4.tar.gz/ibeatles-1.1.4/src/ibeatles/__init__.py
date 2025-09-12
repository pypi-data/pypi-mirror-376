import os

from qtpy.uic import loadUi

from ibeatles import ui

try:
    from ._version import __version__  # noqa: F401
except ImportError:
    __version__ = "unknown"

root = os.path.dirname(os.path.realpath(__file__))
refresh_image = os.path.join(root, "icons/refresh.png")
up_image = os.path.join(root, "icons/up_arrow.png")
down_image = os.path.join(root, "icons/down_arrow.png")
settings_image = os.path.join(root, "icons/plotSettings.png")
vertical_splitter_file = os.path.join(root, "icons/vertical_splitter_handle.png")
horizontal_splitter_file = os.path.join(root, "icons/horizontal_splitter_handle.png")
infos_file = os.path.join(root, "icons/info.png")
preview_file = os.path.join(root, "icons/preview.png")
error_icon_file = os.path.join(root, "icons/error_icon.png")

# tools
fitting_image = os.path.join(root, "icons/fitting_logo.png")
pixel_binning_image = os.path.join(root, "icons/pixel_binning_logo.png")
rotate_image = os.path.join(root, "icons/rotate_logo.png")
strain_mapping_image = os.path.join(root, "icons/strain_mapping_logo.png")
tof_binning_image = os.path.join(root, "icons/tof_binning_logo.png")
tof_combine_image = os.path.join(root, "icons/combine_tof_logo.png")
right_blue_arrow = os.path.join(root, "icons/right_blue_arrow.png")

# tof bin
bin_image = os.path.join(root, "icons/bin.png")
auto_image = os.path.join(root, "icons/auto.png")
manual_image = os.path.join(root, "icons/manual.png")
more_infos_image = os.path.join(root, "icons/more_infos.png")
stats_table_image = os.path.join(root, "icons/stats_table.png")
stats_plot_image = os.path.join(root, "icons/stats_plot.png")

# steps
step1_icon = os.path.join(root, "static/step1.png")
step2_icon = os.path.join(root, "static/step2.png")
step3_icon = os.path.join(root, "static/step3.png")
step4_icon = os.path.join(root, "static/step4.png")

DEFAULT_ROI = ["default", "0", "0", "20", "20", "0"]
DEFAULT_NORMALIZATION_ROI = [True, "0", "0", "20", "20", "background"]
DEFAULT_BIN = [0, 0, 20, 20, 10]
BINNING_LINE_COLOR = (255, 0, 0, 255, 1.0)

interact_me_style = "background-color: lime"
error_style = "background-color: red"
normal_style = ""

ANGSTROMS = "\u212b"
LAMBDA = "\u03bb"
MICRO = "\u00b5"
SUB_0 = "\u2080"
DELTA = "\u0394"

MATERIAL_BRAGG_PEAK_TO_DISPLAY_AT_THE_SAME_TIME = 4


class XAxisMode:
    tof_mode = "tof"
    lambda_mode = "lambda"
    file_index_mode = "file_index"


class DataType:
    sample = "sample"
    ob = "ob"
    df = "df"
    normalized = "normalized"
    normalization = "normalization"
    bin = "bin"
    fitting = "fitting"
    time_spectra = "time_spectra"
    time_spectra_normalized = "time_spectra_normalized"
    none = "none"


class ScrollBarParameters:
    maximum = "maximumx value"
    value = "current value"


class RegionType:
    sample = "sample"
    background = "background"


def load_ui(ui_filename, baseinstance):
    ui_filename = os.path.split(ui_filename)[-1]
    ui_path = os.path.dirname(ui.__file__)

    # get the location of the ui directory
    # this function assumes that all ui files are there
    filename = os.path.join(ui_path, ui_filename)
    print(f"loading {filename}")
    return loadUi(filename, baseinstance=baseinstance)


class Material:
    """
    keys to use when retrieving or saving the h, k, l, lambda and d0 value, as well as the
    lattice, crystal structure and if the user defined or not that entry.
    """

    element_name = "name of the element"
    lattice = "lattice"
    crystal_structure = "structure of the crystal"
    hkl_d0 = "list of h,k and l and respective d0 value"
    user_defined = "is this user defined?"
    via_lattice_and_crystal_structure = "using method 1 of add_element"
    via_d0 = "using method 2"
    method_used = "either via_lattice or via_d0"
    user_defined_bragg_edge_list = "list of hkl, d0 of the user defined material"
    full_list_of_element_names = "list of names of element displayed in the 2 comboBoxes"
    local_bragg_edge_list = "local Bragg edge list of material defined byt he user"


class FileType:
    ascii = "txt"
    json = "json"
    hdf5 = "h5"
