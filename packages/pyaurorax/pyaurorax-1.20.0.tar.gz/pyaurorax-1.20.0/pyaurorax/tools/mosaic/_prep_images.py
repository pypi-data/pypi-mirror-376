# Copyright 2024 University of Calgary
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import numpy as np
from typing import List
from ..classes.mosaic import MosaicData
from ..._util import show_warning


def __determine_cadence(timestamp_arr: List[datetime.datetime]):
    """
    Determines the cadence using a list of timestamps

    It does this calculation by iterating through some of the timestamps
    and looks for the most frequent delta in seconds.
    """
    # go through timestamps and extracting the diffs between each
    diff_seconds_list = []
    curr_ts = None
    checked_timestamps = 0
    for i in range(0, len(timestamp_arr)):
        if (checked_timestamps > 10):
            # bail out of we've checked 10 timestamps, that'll be enough
            break
        if (curr_ts is None):
            # first iteration, initialize curr_ts variable
            curr_ts = timestamp_arr[i].replace(microsecond=0)
        else:
            # calculate difference in seconds
            diff_dt = timestamp_arr[i].replace(microsecond=0) - curr_ts
            diff_seconds_list.append(int(diff_dt.seconds))
            curr_ts = timestamp_arr[i].replace(microsecond=0)
        checked_timestamps += 1

    # identify the most common diff second
    most_frequent_diff_second = max(diff_seconds_list, key=diff_seconds_list.count)

    # the above search only works to determine the cadence in seconds as an integer,
    # if burst data is passed in, this will result in a cadence of zero. In this case
    # we must get an estimate of the cadence in microseconds. We will essentially
    # repeat the above process without rounding microseconds to zero.
    if most_frequent_diff_second == 0:

        # go through timestamps and extracting the diffs between each
        diff_milliseconds_list = []
        curr_ts = None
        checked_timestamps = 0
        for i in range(0, len(timestamp_arr)):
            if (checked_timestamps > 10):
                # bail out of we've checked 10 timestamps, that'll be enough
                break
            if (curr_ts is None):
                # first iteration, initialize curr_ts variable
                curr_ts = timestamp_arr[i]
            else:
                # calculate difference in milliseconds
                diff_dt = timestamp_arr[i] - curr_ts
                diff_milliseconds_list.append(round(diff_dt.microseconds * 10**(-4)))
                curr_ts = timestamp_arr[i]
            checked_timestamps += 1

        # identify the most common diff second
        most_frequent_diff_microsecond = max(diff_milliseconds_list, key=diff_milliseconds_list.count)

        # obtain seconds in decimal form
        most_frequent_diff_second = most_frequent_diff_microsecond * 10**(-2)

    # return
    return most_frequent_diff_second


def prep_images(image_list, data_attribute, spect_emission, spect_band, spect_band_bg):
    # set image dimensions and number of sites
    if (data_attribute == "data"):
        # check that the timestamp and data match in size
        for i in range(0, len(image_list)):
            if (image_list[i].data.shape[-1] != len(image_list[i].timestamp)):
                raise ValueError(("Number of frames does not match number of timestamp records. There are %d timestamp " +
                                  "records, and %d images for list index %d") % (
                                      len(image_list[i].timestamp),
                                      image_list[i].data.shape[-1],
                                      i,
                                  ))
    elif (data_attribute == "calibrated_data"):
        # check that the timestamp and calibrated data match in size
        for i in range(0, len(image_list)):
            if (image_list[i].calibrated_data.shape[-1] != len(image_list[i].timestamp)):
                raise ValueError(("Number of frames does not match number of timestamp records. There are %d timestamp " +
                                  "records, and %d images for list index %d") % (
                                      len(image_list[i].timestamp),
                                      image_list[i].calibrated_data.shape[-1],
                                      i,
                                  ))
    else:
        raise ValueError("Invalid 'data_attribute' parameter. Must be either 'data' or 'calibrated_data'.")

    # Determine integration bounds for spectrograph data
    wavelength_range = {
        "green": [557.0 - 1.5, 557.0 + 1.5],
        "red": [630.0 - 1.5, 630.0 + 1.5],
        "blue": [427.8 - 3.0, 427.8 + 0.5],
        "hbeta": [486.1 - 1.5, 486.1 + 1.5]
    }[spect_emission]

    wavelength_bg_range = {
        "green": [552.0 - 1.5, 552.0 + 1.5],
        "red": [625.0 - 1.5, 625.0 + 1.5],
        "blue": [430.0 - 1.0, 430.0 + 1.0],
        "hbeta": [480.0 - 1.0, 480.0 + 1.0]
    }[spect_emission]

    # Check if manual integration bands were supplied
    if spect_band is not None:
        wavelength_range = spect_band
        if spect_band_bg is None:
            show_warning(
                "Wavelength band supplied without background band. No background subtraction will be performed.",
                stacklevel=1,
            )
            wavelength_bg_range = None
        else:
            wavelength_bg_range = spect_band_bg

    # determine the number of expected frames
    #
    # NOTE: this is done to ensure that the eventual image arrays are all the
    # same size, and we adequately account for dropped frames.
    #
    # Steps:
    #   1) finding the over-arching start and end times of data across all sites
    #   2) determine the cadence using the timestamps
    #   3) determine the number of expected frames using the cadence, start and end
    #
    start_dt = image_list[0].timestamp[0]
    end_dt = image_list[0].timestamp[-1]
    for site_data in image_list:
        this_start_dt = site_data.timestamp[0]
        this_end_dt = site_data.timestamp[-1]
        if (this_start_dt < start_dt):
            start_dt = this_start_dt
        if (this_end_dt > end_dt):
            end_dt = this_end_dt
    cadence = __determine_cadence(image_list[0].timestamp)

    # cadence will be a float if and only if __determine_cadence() decides that burst
    # data has been passed in. If that's the case, we need to be careful with
    # milliseconds
    if isinstance(cadence, float):

        is_burst = True
        # round to 2 decimal places (microseconds)
        curr_dt = start_dt.replace(microsecond=(round(start_dt.microsecond * 10**(-4)) * 10**4))
        expected_num_frames = 0
        expected_timestamps = []
        while (curr_dt <= end_dt):
            expected_timestamps.append(curr_dt)
            expected_num_frames += 1
            curr_dt += datetime.timedelta(seconds=cadence)

    # Otherwise, we just handle the timestamps/cadence in terms of integer seconds
    else:
        is_burst = False
        curr_dt = start_dt.replace(microsecond=0)
        expected_num_frames = 0
        expected_timestamps = []
        while (curr_dt <= end_dt):
            expected_timestamps.append(curr_dt)
            expected_num_frames += 1
            curr_dt += datetime.timedelta(seconds=cadence)

    # for each site
    data_type_list = []
    site_uid_list = []
    images_dict = {}
    for site_image_data in image_list:

        if (data_attribute == "data"):
            site_data = site_image_data.data
        else:
            # data attribute can only be "calibrated_data"
            site_data = site_image_data.calibrated_data  # pragma: nocover

        if site_image_data.dataset is None:  # pragma: nocover
            show_warning("Skipping data objects with missing datasets.", stacklevel=1)
            continue

        # set image dimensions
        if "SPECT" in site_image_data.dataset.name:
            height = site_data.shape[1]
            width = 1
        else:
            height = site_data.shape[0]
            width = site_data.shape[1]

        # Determine number of channels of image data
        if len(site_data.shape) == 4:
            n_channels = site_data.shape[2]
        else:
            n_channels = 1

        int_w = None
        int_bg_w = None
        wavelength = None
        if "spect" in site_image_data.dataset.name.lower():
            n_channels = 1
            current_data_type = "spect"
            data_type_list.append(current_data_type)

            # Extract wavelength from metadata, and get integration indices
            wavelength = site_image_data.metadata[0]["wavelength"]
            int_w = np.where((wavelength >= wavelength_range[0]) & (wavelength <= wavelength_range[1]))
            if wavelength_bg_range is not None:
                int_bg_w = np.where((wavelength >= wavelength_bg_range[0]) & (wavelength <= wavelength_bg_range[1]))
        else:
            current_data_type = "asi"
            data_type_list.append(current_data_type)

        # add to site uid list - must use try as metadata differs between networks
        try:
            site_uid = site_image_data.metadata[0]["site_unique_id"]
        except KeyError:
            try:
                site_uid = site_image_data.metadata[0]["Site unique ID"]
            except KeyError:
                try:
                    site_uid = site_image_data.metadata[0]["site_uid"].decode('utf-8')
                except KeyError as e:  # pragma: nocover
                    raise KeyError("Unable to find site UID in Metadata") from e

        # We don't attempt to handle the same site being passed in for multiple networks
        if site_uid in images_dict.keys():

            d_keys = np.array(list(images_dict.keys()))
            if data_type_list[np.where(d_keys == site_uid)[0][0]] != current_data_type:
                site_uid = site_uid + '_' + current_data_type

            else:
                show_warning("Same site between differing networks detected. Omitting additional '%s' data" % (site_uid), stacklevel=1)
                continue
        site_uid_list.append(site_uid)

        # initialize this site's data destination variables
        images_dict[site_uid] = np.squeeze(np.full((height, width, n_channels, expected_num_frames), np.nan))

        # find the index in the data corresponding to each expected timestamp
        for i in range(0, len(expected_timestamps)):

            # If we are working with burst data, we simply grab the *closest* frame
            # from each image for each timestamp, as cadence is not consistent enough
            # to restrict to exact matches
            if is_burst:
                searching_dt = expected_timestamps[i]
                found_idx = min(range(len(site_image_data.timestamp)), key=lambda j: abs(site_image_data.timestamp[j] - searching_dt))

            # If we are not working with burst data, use a binary search (we assume it is already sorted)
            # to find the location in image_data that exactly matches each expected timestamp
            else:
                searching_dt = expected_timestamps[i]
                found_idx = None
                low = 0
                high = len(site_image_data.timestamp) - 1
                while (low <= high):
                    mid = low + (high - low) // 2
                    this_ts = site_image_data.timestamp[mid].replace(microsecond=0)

                    if (this_ts == searching_dt):
                        found_idx = mid
                        break
                    elif (this_ts > searching_dt):
                        high = mid - 1
                    else:
                        low = mid + 1

            if (found_idx is None):
                # didn't find the timestamp, just move on because there will be no data
                # for this timestamp
                continue
            else:
                # found data for this timestamp
                if current_data_type == "spect":

                    # Integrate over wavelengths to get Rayleighs
                    spectra = site_data[:, :, found_idx]

                    if (int_w is None) or (wavelength is None) or (int_bg_w is None):
                        wavelength = site_image_data.metadata[0]["wavelength"]
                        int_w = np.where((wavelength >= wavelength_range[0]) & (wavelength <= wavelength_range[1]))
                        if wavelength_bg_range is not None:  # pragma: nocover
                            int_bg_w = np.where((wavelength >= wavelength_bg_range[0]) & (wavelength <= wavelength_bg_range[1]))

                    rayleighs = np.trapezoid(spectra[int_w[0], :], x=wavelength[int_w[0]], axis=0)

                    if wavelength_bg_range is not None:
                        if int_bg_w is not None:
                            rayleighs -= np.trapezoid(spectra[int_bg_w[0], :], x=wavelength[int_bg_w[0]], axis=0)  # type: ignore

                    rayleighs = np.nan_to_num(rayleighs, nan=0.0)
                    rayleighs[np.where(rayleighs < 0.0)] = 0.0  # type: ignore

                    images_dict[site_uid][:, i] = rayleighs

                else:
                    if n_channels != 1:
                        images_dict[site_uid][:, :, :, i] = site_data[:, :, :, found_idx]
                    else:
                        images_dict[site_uid][:, :, i] = site_data[:, :, found_idx]

    dimensions_dict = {}
    for site_uid, image in images_dict.items():
        dimensions_dict[site_uid] = (image.shape[0], image.shape[1])

    # cast into object
    prepped_data = MosaicData(site_uid_list=site_uid_list,
                              timestamps=expected_timestamps,
                              images=images_dict,
                              images_dimensions=dimensions_dict,
                              data_types=data_type_list)

    # return
    return prepped_data
