# Copyright (C) 2024  Mahsa Khazaei, Heba Mahdi, Azim Ahmadzadeh

# This file is part of H-Alpha Anomalyzer.
#
# H-Alpha Anomalyzer is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# H-Alpha Anomalyzer is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with H-Alpha Anomalyzer. If not, see <https://www.gnu.org/licenses/>.


import numpy as np
import pandas as pd
from tqdm import tqdm

def _calculate_cell_wise_ranges(images_data, grid_size=8, lower_range_end=20,
                                upper_range_start=80, step_size=2):
    """
    Calculate candidate upper and lower percentage values for each grid cell 
    of the training images data for the One-way ANOVA F-test.

    Parameters
    ----------
    images_data : pd.DataFrame
        The DataFrame containing the training images data.
    grid_size : int, optional
        The number of rows and columns to divide each image into, by default 8.
    lower_range_end : int, optional
        The end of candidate lower ranges, by default 20.
    upper_range_start : int, optional
        The start of candidate upper ranges, by default 80.
    step_size : int, optional
        The step size for candidate ranges, by default 2.

    Returns
    -------
    df_all_ranges : pd.DataFrame
        A DataFrame with candidate ranges for each grid cell of the training 
        images data.
    """
    all_ranges = []

    for image_name in tqdm(images_data['image_name'].unique(),
                           desc="Computing Candidate Ranges"):
        image_data = images_data[images_data['image_name'] == image_name]

        for row in range(grid_size):
            for column in range(grid_size):
                data_cells = images_data[
                    (images_data['row'] == row) &
                    (images_data['column'] == column)
                    ]

                lower_range_arr = np.linspace(0, 20, 11)
                upper_range_arr = np.linspace(80, 100, 11)

                lower_range_val = np.percentile(data_cells['cell_pixel_avg'], lower_range_arr)
                upper_range_val = np.percentile(data_cells['cell_pixel_avg'], upper_range_arr)

                data_cell = image_data[
                    (image_data['row'] == row) &
                    (image_data['column'] == column)
                    ]

                for i, lower_range in enumerate(lower_range_arr):
                    for j, upper_range in enumerate(upper_range_arr):
                        if not data_cell.empty:
                            all_ranges.append([
                                image_name, row, column,
                                lower_range, upper_range,
                                lower_range_val[i], upper_range_val[j],
                                data_cell['cell_pixel_avg'].values[0],
                                data_cell['label'].values[0]
                            ])

    columns = [
        'image_name', 'row', 'column', 'lower_range', 'upper_range',
        'lower_range_val', 'upper_range_val', 'cell_pixel_avg', 'label'
    ]
    df_all_ranges = pd.DataFrame(all_ranges, columns=columns)

    return df_all_ranges
