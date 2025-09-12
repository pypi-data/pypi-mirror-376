from ibeatles import RegionType

roi_label_color = {
    RegionType.sample: "#0000ff",  # blue
    RegionType.background: "#ff0000",
}  # red


class KernelType:
    box = "Box"
    gaussian = "Gaussian"
