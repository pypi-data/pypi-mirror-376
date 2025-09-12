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

import numpy as np


def elevation(skymap, constant_elevation, n_points, remove_edge_cases):
    # First check that elevation is valid
    if constant_elevation < 0 or constant_elevation > 90:
        raise ValueError(f"Elevation of {constant_elevation} is outside of valid range (0,90).")

    # Pull azimuth and elevation arrays from skymap
    azimuth = skymap.full_azimuth
    elevation = skymap.full_elevation

    # In the case that the user requests 90 degrees, return the single closest pixel
    if constant_elevation == 90:
        diffs = np.abs(elevation - constant_elevation)
        y, x = np.where(diffs == np.nanmin(diffs))
        return (np.array([x[0]]), np.array([y[0]]))

    # Take a guess at a good number of points if None is supplied
    if n_points is None:
        if constant_elevation < 30:
            step = 1 * (257 / float(elevation.shape[0]))
        elif constant_elevation >= 30 and constant_elevation < 60:
            step = 3 * (257 / float(elevation.shape[0]))
        elif constant_elevation >= 60 and constant_elevation < 85:
            step = 10 * (257 / float(elevation.shape[0]))
        else:
            step = 30
    else:
        step = 360 / n_points

    # Iterate through azimuth array in steps
    x_list = []
    y_list = []
    for az_min in np.arange(0, 360, step):

        # Get indices of this azimuth slice
        az_max = az_min + step
        az_slice_idx = np.logical_and(azimuth >= az_min, azimuth < az_max)

        # Get index of pixel nearest to target elevation
        masked_elevation = np.where(az_slice_idx, elevation, np.nan)
        diffs = np.abs(masked_elevation - constant_elevation)
        y, x = np.where(diffs == np.nanmin(diffs))

        if x.shape == (0, ) or y.shape == (0, ):  # pragma: nocover
            continue

        # Add to master lists
        x_list.append(x[0])
        y_list.append(y[0])

    # Close contour
    x_list.append(x_list[0])
    y_list.append(y_list[0])

    if (remove_edge_cases is True):
        # Remove any points lying on the edge of CCD bounds and return
        x_list = np.array(x_list)
        y_list = np.array(y_list)
        edge_case_idx = np.where(np.logical_and.reduce([x_list > 0, x_list < elevation.shape[1] - 0, y_list > 1, y_list < elevation.shape[0] - 1]))
        x_list = x_list[edge_case_idx]
        y_list = y_list[edge_case_idx]
        return (x_list, y_list)
    else:
        # Convert to arrays, return
        return (np.array(x_list), np.array(y_list))
