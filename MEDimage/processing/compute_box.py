#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Tuple

import numpy as np

from ..utils.imref import imref3d, intrinsicToWorld
from .compute_bounding_box import compute_bounding_box


def compute_box(vol: np.ndarray,
                roi: np.ndarray,
                spatial_ref: imref3d,
                box_string: str) -> Tuple[np.ndarray,
                                          np.ndarray,
                                          imref3d]:
    """Computes a new box around the ROI (Region of interest) from the original box
    and updates the volume and the ``spatial_ref``.

    Args:
        vol (ndarray): ROI mask with values of 0 and 1.
        roi (ndarray): ROI mask with values of 0 and 1.
        spatial_ref (imref3d): imref3d object (same functionality of MATLAB imref3d class).
        box_string (str): Specifies the new box to be computed

            * 'full': full imaging data as output.
            * 'box': computes the smallest bounding box.
            * Ex: 'box10' means 10 voxels in all three dimensions are added to the smallest bounding box. The number \
                after 'box' defines the number of voxels to add.
            * Ex: '2box' computes the smallest box and outputs double its \
                size. The number before 'box' defines the multiplication in size.
    
    Returns: 
        3-element tuple containing

        - ndarray: 3D array of imaging data defining the smallest box containing the ROI.
        - ndarray: 3D array of 1's and 0's defining the ROI in ROIbox.
        - imref3d: The associated imref3d object imaging data.

    Todo:
        * I would not recommend parsing different settings into a string. \
            Provide two or more parameters instead, and use None if one or more \
            are not used.
        * There is no else statement, so "new_spatial_ref" might be unset
    """

    if "box" in box_string:
        comp = box_string == "box"
        box_bound = compute_bounding_box(mask=roi)
        if not comp:
            # Always returns the first appearance
            ind_box = box_string.find("box")
            # Addition of a certain number of voxels in all dimensions
            if ind_box == 0:
                n_v = float(box_string[(ind_box+3):])
                n_v = np.array([n_v, n_v, n_v]).astype(int)
            else:  # Multiplication of the size of the box
                factor = float(box_string[0:ind_box])
                size_box = np.diff(box_bound, axis=1) + 1
                new_box = size_box * factor
                n_v = np.round((new_box - size_box)/2.0).astype(int)

            o_k = False

            while not o_k:
                border = np.zeros([3, 2])
                border[0, 0] = box_bound[0, 0] - n_v[0]
                border[0, 1] = box_bound[0, 1] + n_v[0]
                border[1, 0] = box_bound[1, 0] - n_v[1]
                border[1, 1] = box_bound[1, 1] + n_v[1]
                border[2, 0] = box_bound[2, 0] - n_v[2]
                border[2, 1] = box_bound[2, 1] + n_v[2]
                border = border + 1
                check1 = np.sum(border[:, 0] > 0)
                check2 = border[0, 1] <= vol.shape[0]
                check3 = border[1, 1] <= vol.shape[1]
                check4 = border[2, 1] <= vol.shape[2]

                check = check1 + check2 + check3 + check4

                if check == 6:
                    o_k = True
                else:
                    n_v = np.floor(n_v / 2.0)
                    if np.sum(n_v) == 0.0:
                        o_k = True
                        n_v = [0.0, 0.0, 0.0]
        else:
            # Will compute the smallest bounding box possible
            n_v = [0.0, 0.0, 0.0]

        box_bound[0, 0] -= n_v[0]
        box_bound[0, 1] += n_v[0]
        box_bound[1, 0] -= n_v[1]
        box_bound[1, 1] += n_v[1]
        box_bound[2, 0] -= n_v[2]
        box_bound[2, 1] += n_v[2]

        box_bound = box_bound.astype(int)

        vol = vol[box_bound[0, 0]:box_bound[0, 1] + 1,
                  box_bound[1, 0]:box_bound[1, 1] + 1,
                  box_bound[2, 0]:box_bound[2, 1] + 1]
        roi = roi[box_bound[0, 0]:box_bound[0, 1] + 1,
                  box_bound[1, 0]:box_bound[1, 1] + 1,
                  box_bound[2, 0]:box_bound[2, 1] + 1]

        # Resolution in mm, nothing has changed here in terms of resolution;
        # XYZ format here.
        res = np.array([spatial_ref.PixelExtentInWorldX,
                        spatial_ref.PixelExtentInWorldY,
                        spatial_ref.PixelExtentInWorldZ])

        # IJK, as required by imref3d
        size_box = (np.diff(box_bound, axis=1) + 1).tolist()
        size_box[0] = size_box[0][0]
        size_box[1] = size_box[1][0]
        size_box[2] = size_box[2][0]
        x_limit, y_limit, z_limit = intrinsicToWorld(spatial_ref, 
                                                box_bound[0, 0],
                                                box_bound[1, 0],
                                                box_bound[2, 0])
        new_spatial_ref = imref3d(size_box, res[0], res[1], res[2])

        # The limit is defined as the border of the first pixel
        new_spatial_ref.XWorldLimits = new_spatial_ref.XWorldLimits - (
            new_spatial_ref.XWorldLimits[0] - (x_limit - res[0]/2))
        new_spatial_ref.YWorldLimits = new_spatial_ref.YWorldLimits - (
            new_spatial_ref.YWorldLimits[0] - (y_limit - res[1]/2))
        new_spatial_ref.ZWorldLimits = new_spatial_ref.ZWorldLimits - (
            new_spatial_ref.ZWorldLimits[0] - (z_limit - res[2]/2))

    elif "full" in box_string:
        new_spatial_ref = spatial_ref

    return vol, roi, new_spatial_ref
