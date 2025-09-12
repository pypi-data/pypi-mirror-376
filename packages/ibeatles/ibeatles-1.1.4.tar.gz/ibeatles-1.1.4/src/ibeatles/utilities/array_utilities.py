import numpy as np
from scipy.ndimage import convolve


def find_nearest_index(array, value):
    idx = (np.abs(np.array(array) - value)).argmin()
    return idx


def get_min_max_xy(pos_array):
    min_x = 10000
    max_x = -1
    min_y = 10000
    max_y = -1

    for xy in pos_array:
        [_x, _y] = xy
        if _x < min_x:
            min_x = _x
        if _x > max_x:
            max_x = _x
        if _y < min_y:
            min_y = _y
        if _y > max_y:
            max_y = _y

    return {"x": {"min": min_x, "max": max_x}, "y": {"min": min_y, "max": max_y}}


def gamma_filtering(data_array, threshold=0.1):
    """
    this algorithm will perform the gamma filtering. That means that
    every pixel counts that are above threshold of the total average counts
    will be replaced by the average value of the 9 pixels around it.
    """

    final_data_array = []
    for _data in data_array:
        _data_filtered = single_gamma_filtering(_data)
        final_data_array.append(_data_filtered)

    return final_data_array


def single_gamma_filtering(data, threshold=0.1):
    raw_data = np.copy(data)

    # find mean counts
    mean_counts = np.mean(raw_data)

    thresolded_raw_data = raw_data * threshold

    # get pixels where value is above threshold
    position = []
    [height, width] = np.shape(raw_data)
    for _x in np.arange(width):
        for _y in np.arange(height):
            if thresolded_raw_data[_y, _x] > mean_counts:
                position.append([_y, _x])

    # convolve entire image using 3x3 kerne
    mean_kernel = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]]) / 8.0
    convolved_data = convolve(raw_data, mean_kernel, mode="constant")

    # replace only pixel above threshold by convolved data
    for _coordinates in position:
        [_y, _x] = _coordinates
        raw_data[_y, _x] = convolved_data[_y, _x]

    return raw_data


def exclude_y_value_when_error_is_nan(axis, error_axis):
    axis_cleaned = []
    error_axis_cleaned = []

    for _x, _error in zip(axis, error_axis):
        if (_x == "None") or (_error == "None") or (_x is None) or (_error is None):
            axis_cleaned.append(np.nan)
            error_axis_cleaned.append(np.nan)
        else:
            axis_cleaned.append(float(_x))
            error_axis_cleaned.append(float(_error))

    return axis_cleaned, error_axis_cleaned


def calculate_median(array_of_value=None):
    if array_of_value is None:
        return None

    try:
        array_of_value = np.where(np.isinf(array_of_value), np.nan, array_of_value)
        array_of_value = np.where(np.isneginf(array_of_value), np.nan, array_of_value)
    except TypeError:
        return None

    return np.nanmedian(array_of_value)


def from_nparray_to_list(nparray=None, json_friendly=False) -> list:
    if nparray is None:
        return None

    if json_friendly:
        nparray = [str(_value) for _value in nparray]

    return list(nparray)
