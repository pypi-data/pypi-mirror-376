class SessionKeys:
    material = "material"
    instrument = "instrument"
    bin = "bin"
    fitting = "fitting"
    settings = "settings"
    reduction = "reduction"


class MaterialMode:
    pre_defined = "pre_defined"
    custom_method1 = "custom method 1"
    custom_method2 = "custom method 2"


class ReductionDimension:
    twod = "2D"
    threed = "3D"


class ReductionType:
    box = "Box"
    gaussian = "Gaussian"


class SessionSubKeys:
    # instrument
    distance_source_detector = "distance source detector"
    detector_value = "detector value"
    beam_index = "beam index"

    # general
    list_files = "list files"
    current_folder = "current folder"
    list_files_selected = "list files selected"
    list_rois = "list rois"
    extension = "extension"

    # sample
    time_spectra_filename = "time spectra filename"

    # ob
    image_view_state = "image view state"
    image_view_histogram = "image view histogram"

    # material
    pre_defined_selected_element = "selected element in the pre-defined mode"
    pre_defined_selected_element_index = "index of pre-defined element"
    material_mode = "material mode"
    pre_defined = "pre_defined"
    custom_method1 = "custom method 1"
    custom_method2 = "custom method 2"
    custom_material_name = "name of the custom material"

    lattice = "lattice"
    crystal_structure = "crystal structure"
    crystal_structure_index = "index of crystal structure (0 for BCC, 1 for FCC)"
    index = "index"
    name = "name"
    user_defined = "user_defined"
    user_defined_fill_fields_with_element_index = "index of element used to fill the fields of method1"
    material_hkl_table = "hkl, d0 or lambda0 table"
    column_names = "names of the columns"

    # bin
    state = "state"
    roi = "roi"
    binning_line_view = "binning line view"
    nbr_row = "nbr row"
    nbr_column = "nbr column"
    bin_size = "bin size"

    # fitting
    ui_accessed = "ui_accessed"
    x_axis = "x_axis"
    xaxis = "xaxis"
    transparency = "transparency"
    ui = "ui"
    lambda_range_index = "lambda range index"
    bin_coordinates = "bin_coordinates"
    bragg_peak_threshold = "bragg peak threshold"

    # settings
    log_buffer_size = "log buffer size"
    config_version = "config version"

    # reduction
    activate = "activate"
    dimension = "dimension"
    size = "size"
    type = "type"
    process_order = "process order"

    # bin in TOF
    top_folder = "top_folder"
    list_working_folders = "list_working_folders"
    list_working_folders_status = "list_working_folders_status"
    version = "version"
    detector_offset = "detector_offset"
    combine_algorithm = "combine_algorithm"
    combine_roi = "combine_roi"
    sample_position = "sample_position"
    bin_mode = "bin_mode"
    bin_algorithm = "bin_algorithm"
