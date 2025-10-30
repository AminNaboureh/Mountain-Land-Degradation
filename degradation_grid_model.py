# -*- coding: utf-8 -*-
"""
Created on Thu Sep 19 15:37:25 2024

@author: Dell
"""

import numpy as np
from osgeo import gdal
import time
from multiprocessing import Pool

mountain_raster_path = "F:/Data/Data processing/mountain_land_area/mountain_zuixin.tif"
mountain_raster_dataset = gdal.Open(mountain_raster_path)
mountain_raster_band = mountain_raster_dataset.GetRasterBand(1)
x_size=mountain_raster_band.XSize
y_size=mountain_raster_band.YSize


# x_size_new = x_size + 403
# y_size_new = y_size + 337

mountain_nodata=mountain_raster_band.GetNoDataValue()


# landcover_raster_path = "E:/Data/Data processing/mountain_land_area/green_nogreen.tif"
landcover_raster_path = "F:/Data/Data processing/mountain_land_area/degradation_2022.tif"
landcover_raster_dataset = gdal.Open(landcover_raster_path)
landcover_raster_band = landcover_raster_dataset.GetRasterBand(1)
landcover_nodata=landcover_raster_band.GetNoDataValue()
xsize_land=landcover_raster_band.XSize
ysize_land=landcover_raster_band.YSize



surface_area_raster_path = "F:/Data/Data processing/mountain_land_area/surface_area_100_cj.tif"
surface_area_raster_dataset = gdal.Open(surface_area_raster_path)
surface_area_raster_band = surface_area_raster_dataset.GetRasterBand(1)
surface_nodata = surface_area_raster_band.GetNoDataValue()
x_size_surface = surface_area_raster_band.XSize
y_size_surface = surface_area_raster_band.YSize

transform = mountain_raster_dataset.GetGeoTransform()


scale_factor = int(transform[1] / 100)#scale_factor = 16
    
block_size = 1000

args_list = []

for x in range(0, x_size, block_size):
    cols = min(block_size, x_size - x)  # 避免超出数据范围
    
    # print(x,cols)  
    for y in range( 0, y_size, block_size):
        rows = min(block_size, y_size - y)  # 避免超出数据范围
        # print(rows)
        # mountain_block = mountain_raster_band.ReadAsArray(x,y,cols,rows)
        
        cols_new = cols * scale_factor
        rows_new = rows * scale_factor
        
        if cols_new < 5000:
            cols_new = xsize_land - block_size * scale_factor * 9
            
        if rows_new < 5000:
            rows_new = ysize_land - block_size * scale_factor * 8
            
      
        landcover_block = landcover_raster_band.ReadAsArray(x*scale_factor,y*scale_factor,cols_new,rows_new)
      
        surface_block = surface_area_raster_band.ReadAsArray(x*scale_factor,y*scale_factor,cols_new,rows_new)

        # # 将参数添加到参数列表中
        args_list.append((cols, rows, scale_factor, landcover_block, surface_block))
        
def calculate_green_ratio(args):
    cols, rows, scale_factor, landcover_block, surface_block = args
    count=0
    
    green_ratio_array=np.zeros((rows,cols), dtype=int)
    

    for  i  in range(0, rows):
        
        for j in range(0, cols):
           
            green_area_sum = 0
            total_area_sum = 0
            count+=1
            for k in range(scale_factor):
                for l in range(scale_factor):
                    # count+=1
                    
                    row_index = i * scale_factor + k
                    col_index = j * scale_factor + l
                    if row_index < landcover_block.shape[0] and col_index < landcover_block.shape[1]:
                        landcover_value = landcover_block[row_index, col_index]
                        surface_area = surface_block[row_index, col_index]
                        
                        landcover_value = landcover_block[row_index, col_index]
                        surface_area = surface_block[row_index, col_index]
                        
                      
                        total_area_sum += surface_area
                       
                       
                        if landcover_value == -1:                        
                            green_area_sum += surface_area

            if total_area_sum != 0:
                
                green_ratio = (green_area_sum / total_area_sum ) * 100
                
            else:
                
                green_ratio = 0        
            
            if np.isnan(green_ratio):
                
                green_ratio = -1
                
            green_ratio = int(round(green_ratio))
            
            green_ratio_array[i,j] = green_ratio
           
    return(green_ratio_array)  


result_blocks = []


for idx, args in enumerate(args_list):
    
    result_block = calculate_green_ratio(args)
    
    # print(idx)
    
    # print(result_block)
    
    result_blocks.append(result_block)
    
# print(result_blocks)


#final_result_array = np.vstack(result_blocks[i:i+3]) for i in range(0, len(result_blocks), 3)

final_result_array = np.hstack([np.vstack(result_blocks[i:i+9]) for i in range(0, len(result_blocks), 9)])

# print(final_result_array.shape[1],final_result_array.shape[0])
# print(final_result_array.shape)

target_resolution = 500  
x_resolution = transform[1]
y_resolution = transform[5]
scale_factor = int(round(target_resolution / abs(x_resolution)))
# print(transform[0])

new_cols = int(final_result_array.shape[1] * 500 / 500)
new_rows = int(final_result_array.shape[0] * 500 / 500)

# 导出为tif
# output_path = "E:/Data/Data processing/mountain_land_area/mgci_2018.tif"
# driver = gdal.GetDriverByName("GTiff")
# output_raster = driver.Create(output_path, final_result_array.shape[1], final_result_array.shape[0], 1, gdal.GDT_Int32)
# output_raster.GetRasterBand(1).WriteArray(final_result_array)
# output_raster.SetGeoTransform(transform)
# output_raster.SetProjection(mountain_raster_dataset.GetProjection())
# output_raster.FlushCache()
# output_raster = None   



new_transform = (transform[0], target_resolution, transform[2], transform[3], transform[4], -target_resolution)


output_path = "F:/Data/tuihuabili/PDML/Degradation_2022.tif"
driver = gdal.GetDriverByName("GTiff")
output_raster = driver.Create(output_path, new_cols, new_rows, 1, gdal.GDT_Int32)
output_raster.GetRasterBand(1).WriteArray(final_result_array)

output_raster.SetGeoTransform(new_transform)
output_raster.SetProjection(mountain_raster_dataset.GetProjection()) 
output_raster.FlushCache()

output_raster = None  
