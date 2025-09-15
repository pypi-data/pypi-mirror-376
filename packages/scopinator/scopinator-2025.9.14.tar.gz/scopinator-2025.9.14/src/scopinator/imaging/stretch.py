#
# Adapted from GraXpert.
#

import multiprocessing
import logging
import numpy as np

from enum import Enum
from multiprocessing import shared_memory
from dataclasses import dataclass

multiprocessing.freeze_support()


@dataclass
class MTFStretchParameters:
    midtone: float
    shadow_clipping: float
    highlight_clipping: float = 1.0


StretchParameter = Enum(
    "StretchParameter",
    [
        "No Stretch",
        "10% Bg, 3 sigma",
        "15% Bg, 3 sigma",
        "20% Bg, 3 sigma",
        "30% Bg, 2 sigma",
    ],
)


class StretchParameters:
    stretch_option: StretchParameter
    bg: float
    sigma: float
    do_stretch: bool = True
    channels_linked: bool = False
    images_linked: bool = False

    def __init__(
        self,
        stretch_option: StretchParameter,
        channels_linked: bool = False,
        images_linked: bool = False,
    ):
        self.stretch_option = stretch_option
        self.channels_linked = channels_linked
        self.images_linked = images_linked

        # Convert enum to string for comparison
        stretch_name = stretch_option.name if hasattr(stretch_option, 'name') else str(stretch_option)
        
        if stretch_name == "No Stretch":
            self.do_stretch = False
            self.bg = 0.15  # Default values even when not stretching
            self.sigma = 3.0

        elif stretch_name == "10% Bg, 3 sigma":
            self.bg = 0.1
            self.sigma = 3.0

        elif stretch_name == "15% Bg, 3 sigma":
            self.bg = 0.15
            self.sigma = 3.0

        elif stretch_name == "20% Bg, 3 sigma":
            self.bg = 0.2
            self.sigma = 3.0

        elif stretch_name == "30% Bg, 2 sigma":
            self.bg = 0.3
            self.sigma = 2.0
            
        else:
            # Default fallback
            self.bg = 0.15
            self.sigma = 3.0


def stretch(data, stretch_params: StretchParameters):
    if not stretch_params.do_stretch:
        return data

    mtf_stretch_param = calculate_mtf_stretch_parameters_for_image(stretch_params, data)
    return stretch_all([data], [mtf_stretch_param])[0]


def stretch_all(datas, mtf_stretch_params: list[MTFStretchParameters]):
    shms = []
    copies = []
    result = []

    for data, mtf_stretch_param in zip(datas, mtf_stretch_params):
        shm = shared_memory.SharedMemory(create=True, size=data.nbytes)
        copy = np.ndarray(data.shape, dtype=data.dtype, buffer=shm.buf)
        np.copyto(copy, data)
        shms.append(shm)
        copies.append(copy)

        for c in range(copy.shape[-1]):
            stretch_channel(shm.name, c, mtf_stretch_param[c], copy.shape, copy.dtype)

    for copy in copies:
        copy = np.copy(copy)
        result.append(copy)

    for shm in shms:
        shm.close()
        shm.unlink()

    return result


def calculate_mtf_stretch_parameters_for_image(stretch_params, image):
    if stretch_params.channels_linked:
        mtf_stretch_param = calculate_mtf_stretch_parameters_for_channel(
            stretch_params, image
        )
        return [mtf_stretch_param] * image.shape[-1]

    else:
        return [
            calculate_mtf_stretch_parameters_for_channel(stretch_params, image[:, :, i])
            for i in range(image.shape[-1])
        ]


def calculate_mtf_stretch_parameters_for_channel(stretch_params, channel):
    channel = channel.flatten()[::4]

    indx_clip = np.logical_and(channel < 1.0, channel > 0.0)
    median = np.median(channel[indx_clip])
    mad = np.median(np.abs(channel[indx_clip] - median))

    shadow_clipping = np.clip(median - stretch_params.sigma * mad, 0, 1.0)
    highlight_clipping = 1.0
    midtone = MTF(
        (median - shadow_clipping) / (highlight_clipping - shadow_clipping),
        stretch_params.bg,
    )

    return MTFStretchParameters(midtone, shadow_clipping)


def stretch_channel(shm_name, c, mtf_stretch_params, shape, dtype):
    # logging.info("stretch.stretch_channel started")
    existing_shm = shared_memory.SharedMemory(name=shm_name)
    channels = np.ndarray(shape, dtype, buffer=existing_shm.buf)  # [:,:,channel_idx]
    channel = channels[:, :, c]

    try:
        channel[channel <= mtf_stretch_params.shadow_clipping] = 0.0
        channel[channel >= mtf_stretch_params.highlight_clipping] = 1.0

        indx_inside = np.logical_and(
            channel > mtf_stretch_params.shadow_clipping,
            channel < mtf_stretch_params.highlight_clipping,
        )

        channel[indx_inside] = (
            channel[indx_inside] - mtf_stretch_params.shadow_clipping
        ) / (mtf_stretch_params.highlight_clipping - mtf_stretch_params.shadow_clipping)

        channel = MTF(channel, mtf_stretch_params.midtone)
    except:
        logging.exception("An error occured while stretching a color channel")
    finally:
        existing_shm.close()

    # logging.info("stretch.stretch_channel finished")


def MTF(data, midtone):
    if type(data) is np.ndarray:
        data[:] = (midtone - 1) * data[:] / ((2 * midtone - 1) * data[:] - midtone)
    else:
        data = (midtone - 1) * data / ((2 * midtone - 1) * data - midtone)

    return data
