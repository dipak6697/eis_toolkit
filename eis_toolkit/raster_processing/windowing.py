from typing import Tuple

import numpy as np
import rasterio
from rasterio import transform
from rasterio.windows import Window

from eis_toolkit.exceptions import CoordinatesOutOfBoundsException, InvalidWindowSizeException, NonMatchingCrsException


def _extract_window(  # type: ignore[no-any-unimported]
    raster: rasterio.io.DatasetReader,
    center_coords: Tuple[float, float],
    height: int,
    width: int,
) -> Tuple[np.ndarray, dict]:

    center_x = center_coords[0]
    center_y = center_coords[1]

    center_row, center_col = transform.rowcol(raster.transform, center_x, center_y)

    height_px = int(height / 2)
    width_px = int(width / 2)
    top_left_row = center_row - height_px
    top_left_col = center_col - width_px

    if height % 2 == 0 or width % 2 == 0:
        px_x, px_y = transform.xy(raster.transform, center_row, center_col)
        if height % 2 == 0:
            if center_y < px_y:
                top_left_row += 1
        if width % 2 == 0:
            if center_x > px_x:
                top_left_col += 1

    window = Window(
        col_off=top_left_col,
        row_off=top_left_row,
        width=width,
        height=height,
    )

    out_image = raster.read(
        boundless=True,
        window=window,
        fill_value=-9999,
    )

    top_left_coordinates = transform.xy(
        transform=raster.transform,
        rows=top_left_row,
        cols=top_left_col,
        offset="ul",
    )

    out_transform = rasterio.Affine(
        raster.transform[0],
        raster.transform[1],
        top_left_coordinates[0],
        raster.transform[3],
        raster.transform[4],
        top_left_coordinates[1],
    )

    out_meta = raster.meta.copy()
    out_meta.update(
        {
            "height": out_image.shape[1],
            "width": out_image.shape[2],
            "transform": out_transform,
        }
    )

    return out_image, out_meta


def extract_window(  # type: ignore[no-any-unimported]
    raster: rasterio.io.DatasetReader,
    center_coords: Tuple[float, float],
    center_coord_crs: int,
    height: int,
    width: int,
) -> Tuple[np.ndarray, dict]:
    """Extract window from raster.

       Center coordinate must be inside the raster but window can extent outside the raster in which case padding with
       -9999 is used.
    Args:
        raster (rasterio.io.DatasetReader): Source raster.
        center_coords (Tuple[int, int]): center coordinates for window int the form (x, y).
        center_coord_crs (int): EPSG code that defines the coordinate reference system.
        height (int): window height in pixels.
        width (int): window width in pixels.

    Returns:
        out_image (numpy.ndarray): Extracted raster window.
        out_meta (dict): The updated metadata.

    Raises:
        CoordinatesOutOfBoundException: Window center coordinates are out of raster bounds.
        InvalidWindowSizeException: Window size is too small.
        NonMatchingCrsException: Raster and center coordinates are not in same crs.
    """

    if height < 1 or width < 1:
        raise InvalidWindowSizeException

    if center_coord_crs != int(raster.crs.to_string()[5:]):
        raise NonMatchingCrsException

    center_x = center_coords[0]
    center_y = center_coords[1]

    if (
        center_x < raster.bounds.left
        or center_x > raster.bounds.right
        or center_y < raster.bounds.bottom
        or center_y > raster.bounds.top
    ):
        raise CoordinatesOutOfBoundsException

    out_image, out_meta = _extract_window(raster, center_coords, height, width)

    return out_image, out_meta
