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
import matplotlib.pyplot as plt


def geo(aurorax_obj, images, skymap, altitude_km, lonlat_bounds, metric, n_channels, show_preview):
    # Select individual lats/lons from list
    lon_0 = lonlat_bounds[0]
    lon_1 = lonlat_bounds[1]
    lat_0 = lonlat_bounds[2]
    lat_1 = lonlat_bounds[3]

    # Determine if we are using single or 3 channel
    images = np.squeeze(images)
    if n_channels is not None:
        n_channels = n_channels
    else:
        n_channels = 1
        if (len(images.shape) == 3):
            # single channel
            n_channels = 1
        elif (len(images.shape) == 4):
            # three channel
            n_channels = 3

    # Ensure that coordinates are valid
    if lat_0 > 90 or lat_0 < -90:
        raise ValueError("Invalid latitude: " + str(lat_0))
    elif lat_1 > 90 or lat_1 < -90:
        raise ValueError("Invalid latitude: " + str(lat_1))
    elif lon_0 > 360 or lon_0 < -180:
        raise ValueError("Invalid longitude: " + str(lon_0))
    elif lon_1 > 360 or lon_1 < -180:
        raise ValueError("Invalid longitude: " + str(lon_1))

    # Convert (0,360) longitudes to (-180,180) if entered as such
    if lon_0 > 180:
        lon_0 -= 360.0
    if lon_1 > 180:
        lon_1 -= 360.0

    # Ensure that coordinates are properly ordered
    if lat_0 > lat_1:
        lat_0, lat_1 = lat_1, lat_0
    if lon_0 > lon_1:
        lon_0, lon_1 = lon_1, lon_0

    # Ensure that this is a valid polygon
    if (lat_0 == lat_1) or (lon_0 == lon_1):
        raise ValueError("Polygon defined with zero area.")

    # Obtain lat/lon arrays from skymap
    interp_alts = skymap.full_map_altitude / 1000.0
    if (altitude_km in interp_alts):
        altitude_idx = np.where(altitude_km == interp_alts)

        lats = np.squeeze(skymap.full_map_latitude[altitude_idx, :, :])
        lons = np.squeeze(skymap.full_map_longitude[altitude_idx, :, :])
        lons[np.where(lons > 180)] -= 360.0  # Fix skymap to be in (-180,180) format
    else:
        # Make sure altitude is in range that can be interpolated
        if (altitude_km < interp_alts[0]) or (altitude_km > interp_alts[2]):
            raise ValueError("Altitude " + str(altitude_km) + " outside valid range of " + str((interp_alts[0], interp_alts[2])))

        # Initialize empty lat/lon arrays
        lats = np.full(np.squeeze(skymap.full_map_latitude[0, :, :]).shape, np.nan, dtype=skymap.full_map_latitude[0, :, :].dtype)
        lons = np.full(np.squeeze(skymap.full_map_latitude[0, :, :]).shape, np.nan, dtype=skymap.full_map_latitude[0, :, :].dtype)

        # Interpolate lats and lons at desired altitude
        for i in range(skymap.full_map_latitude.shape[1]):
            for j in range(skymap.full_map_latitude.shape[2]):
                pixel_lats = skymap.full_map_latitude[:, i, j]
                pixel_lons = skymap.full_map_longitude[:, i, j]
                if np.isnan(pixel_lats).any() or np.isnan(pixel_lons).any():
                    continue
                lats[i, j] = np.interp(altitude_km, interp_alts, pixel_lats)
                lons[i, j] = np.interp(altitude_km, interp_alts, pixel_lons)

        lons[np.where(lons > 180)] -= 360.0  # Fix skymap to be in (-180,180) format

    # Check that lat/lon range is reasonable
    min_skymap_lat = np.nanmin(lats)
    max_skymap_lat = np.nanmax(lats)
    min_skymap_lon = np.nanmin(lons)
    max_skymap_lon = np.nanmax(lons)
    if (lat_0 <= min_skymap_lat) or (lat_1 >= max_skymap_lat):
        raise ValueError(f"Latitude range supplied is outside the valid range for this skymap {(min_skymap_lat,max_skymap_lat)}.")
    if (lon_0 <= min_skymap_lon) or (lon_1 >= max_skymap_lon):
        raise ValueError(f"Longitude range supplied is outside the valid range for this skymap {(min_skymap_lon,max_skymap_lon)}.")

    # Obtain indices into skymap within lat/lon range
    bound_idx = np.where(np.logical_and.reduce((lats >= float(lat_0), lats <= float(lat_1), lons >= float(lon_0), lons <= float(lon_1))))

    # If boundaries contain no data, raise error
    if len(bound_idx[0]) == 0 or len(bound_idx[1]) == 0:  # pragma: nocover
        raise ValueError("No data within desired bounds. Try a larger area.")

    # Convert from skymap coords to image coords
    bound_idx = tuple(i - 1 for i in bound_idx)
    bound_idx = tuple(np.maximum(idx, 0) for idx in bound_idx)

    # Slice out the bounded data
    if (n_channels == 1):
        bound_data = images[bound_idx[0], bound_idx[1], :]
        if (show_preview is True):
            preview_img = aurorax_obj.tools.scale_intensity(images[:, :, 0], top=230)
            preview_img[bound_idx[0], bound_idx[1]] = 255
            plt.figure()
            plt.imshow(preview_img, cmap="grey", origin="lower")
            plt.title("Bounded Area Preview")
            plt.axis("off")
            plt.show()
    elif (n_channels == 3):
        bound_data = images[bound_idx[0], bound_idx[1], :, :]
        if (show_preview is True):
            preview_img = aurorax_obj.tools.scale_intensity(images[:, :, :, 0], top=230)
            preview_img[bound_idx[0], bound_idx[1], 0] = 255
            preview_img[bound_idx[0], bound_idx[1], 1:] = 0
            plt.figure()
            plt.imshow(preview_img, origin="lower")
            plt.title("Bounded Area Preview")
            plt.axis("off")
            plt.show()
    else:  # pragma: nocover
        raise ValueError("Unrecognized image format with shape: " + str(images.shape))

    # Compute metric of interest
    if metric == "median":
        result = np.median(bound_data, axis=0)
    elif metric == "mean":
        result = np.mean(bound_data, axis=0)
    elif metric == "sum":
        result = np.sum(bound_data, axis=0)
    else:
        raise ValueError("Metric " + str(metric) + " is not recognized.")

    # return
    return result
