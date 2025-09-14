from ctypes import *
import ctypes
import numpy as np
import os

try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    current_file = os.path.join(current_dir, "Pcl_wapper.dll")
    pclwapper = CDLL(current_file)
except Exception as e:
    raise OSError(f"Failed to load Pcl_wapper.dll: {e}")

def free_memory(ptr):
    pclwapper.PCL_FreeMemory.argtypes = [ctypes.POINTER(ctypes.c_float)]
    pclwapper.PCL_FreeMemory.restype = None
    pclwapper.PCL_FreeMemory(ptr)
def getrangeimageformpointscloud(points: np.ndarray) -> np.ndarray:
    pclwapper.PCL_CreateRangeImageFormPointsCloud.argtypes = [
        ctypes.POINTER(ctypes.c_float),  # float* srcpoints
        ctypes.POINTER(ctypes.c_int),    # int* pointsnum
        ctypes.POINTER(ctypes.c_int),    # int* width
        ctypes.POINTER(ctypes.c_int),    # int* height
        ctypes.POINTER(ctypes.POINTER(ctypes.c_float))  # float** rangeimage
    ]
    pclwapper.PCL_CreateRangeImageFormPointsCloud.restype = ctypes.c_int  # 返回int
    points_ptr = points.ctypes.data_as(ctypes.POINTER(ctypes.c_float))

    # 点的数量
    num_points = points.shape[0]
    num_points_ptr = ctypes.byref(ctypes.c_int(num_points))

    # 图像的宽度和高度
    imgw = ctypes.c_int()
    imgh = ctypes.c_int()
    width_ptr = ctypes.byref(imgw)
    height_ptr = ctypes.byref(imgh)

    # 为输出参数分配内存
    range_image_ptr = ctypes.POINTER(ctypes.c_float)()

    result = pclwapper.PCL_CreateRangeImageFormPointsCloud(points_ptr, num_points_ptr, width_ptr, height_ptr, ctypes.byref(range_image_ptr))
    if result != 0:
        raise RuntimeError("PCL_GetRangeImageFromPointsCloud failed")

    # 将结果转换为NumPy数组并返回
    array = np.ctypeslib.as_array(range_image_ptr, shape=(imgh.value, imgw.value,3)).astype(np.float32)[:,:,2]  # 只取深度通道
    free_memory(range_image_ptr)  # 释放C++分配的内存
    return array # 返回深度图像
def getgirdimageformpointscloud(points: np.ndarray,step=0.1) -> np.ndarray:
    pclwapper.gridPointCloud.argtypes = [
        ctypes.POINTER(ctypes.c_float),  # float* srcpoints
        ctypes.POINTER(ctypes.c_int),    # int* pointsnum
        ctypes.POINTER(ctypes.c_float),    # int* gridstep
        ctypes.POINTER(ctypes.c_int),    # int* width
        ctypes.POINTER(ctypes.c_int),    # int* height
        ctypes.POINTER(ctypes.POINTER(ctypes.c_float))  # float** rangeimage
    ]
    pclwapper.gridPointCloud.restype = ctypes.c_int  # 返回int
    points_ptr = points.ctypes.data_as(ctypes.POINTER(ctypes.c_float))

    # 点的数量
    num_points = points.shape[0]
    num_points_ptr = ctypes.byref(ctypes.c_int(num_points))

    # 图像的宽度和高度
    imgw = ctypes.c_int()
    imgh = ctypes.c_int()
    step_ptr = ctypes.byref(ctypes.c_float(step))
    width_ptr = ctypes.byref(imgw)
    height_ptr = ctypes.byref(imgh)

    # 为输出参数分配内存
    range_image_ptr = ctypes.POINTER(ctypes.c_float)()

    result = pclwapper.gridPointCloud(points_ptr, num_points_ptr,step_ptr ,width_ptr, height_ptr, ctypes.byref(range_image_ptr))
    if result != 0:
        raise RuntimeError("PCL_GetRangeImageFromPointsCloud failed")

    # 将结果转换为NumPy数组并返回
    array = np.ctypeslib.as_array(range_image_ptr, shape=(imgh.value, imgw.value,3)).astype(np.float32)[:,:,2]  # 只取深度通道
    free_memory(range_image_ptr)  # 释放C++分配的内存
    return array # 返回深度图像
def getminmax3d(points: np.ndarray) -> tuple:
    pclwapper.PCL_GetMinMax3D.argtypes = [
    ctypes.POINTER(ctypes.c_float),  # float* srcpoints
    ctypes.POINTER(ctypes.c_int),    # int* pointsnum
    ctypes.POINTER(ctypes.c_float),  # float* minx
    ctypes.POINTER(ctypes.c_float),  # float* miny
    ctypes.POINTER(ctypes.c_float),  # float* minz
    ctypes.POINTER(ctypes.c_float),  # float* maxx
    ctypes.POINTER(ctypes.c_float),  # float* maxy
    ctypes.POINTER(ctypes.c_float)   # float* maxz
    ]
    pclwapper.PCL_GetMinMax3D.restype = ctypes.c_int  # 返回int
    points_ptr = points.ctypes.data_as(ctypes.POINTER(ctypes.c_float))

    # 点的数量
    num_points = points.shape[0]
    num_points_ptr = ctypes.byref(ctypes.c_int(num_points))

    # 为输出参数分配内存
    min_x = ctypes.c_float()
    min_y = ctypes.c_float()
    min_z = ctypes.c_float()
    max_x = ctypes.c_float()
    max_y = ctypes.c_float()
    max_z = ctypes.c_float()
    result = pclwapper.PCL_GetMinMax3D(points_ptr, num_points_ptr, 
                                ctypes.byref(min_x), ctypes.byref(min_y), ctypes.byref(min_z),
                                ctypes.byref(max_x), ctypes.byref(max_y), ctypes.byref(max_z))
    if result != 0:
        raise RuntimeError("PCL_GetMinMax3D failed")
    return min_x.value, min_y.value, min_z.value, max_x.value, max_y.value, max_z.value