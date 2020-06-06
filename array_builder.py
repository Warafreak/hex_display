# this file is used to create the initial array that will be used for displaying our effects
import fixedsizes as fixed
import numpy as np
import pandas as pd

#array containing the mapping of channel to position
hex_lp = np.array([[-1,1,7,-1],[3,0,4,5],[21,2,6,11],[20,22,10,8],[23,18,14,9],[17,16,12,15],[-1,19,13,-1]],dtype=int)

#map for a rotation of the hexagon by 60 degrees counterclockwise
shift_map = np.array([[0,7,11,3],[2,6,15,19],[1,10,14,23],[5,9,18,22],[4,13,17,26],[8,12,21,25],[24,16,20,27]],dtype=int)

#functions to apply rotation to a suiting array
def rotate_hex_by_one(array):
    if (array.shape!=(fixed.HEX_Y,fixed.HEX_X)):
        return array
    new_array = np.zeros((fixed.HEX_Y,fixed.HEX_X),dtype=int)
    for i in range(shift_map.size):
        np.put(new_array, i, array.flat[shift_map.flat[i]])
    array = new_array
    return array
    
def rotate_hex_by_n(array, n):
    for i in range(n):
        array = rotate_hex_by_one(array)
    return array
    
def initiate_array(raw_info):
    # ensure correct input
    if (raw_info.shape!=(5,)):
        return np.zeros((fixed.HEX_Y,fixed.HEX_X),dtype=int)
    # copy template array
    array = hex_lp.copy()
    # advance all contained channels along according to position in chain
    np.putmask(array, array>=0, array+raw_info[0]*fixed.TLC5947_CHANNELS)
    # rotate array to correct position
    array = rotate_hex_by_n(array, raw_info[2])
    array = conform_array_to_type(array, raw_info[1])
    return array

# cut arrays down to size according to type
def conform_array_to_type(array, type):
    if (array.shape!=(fixed.HEX_Y,fixed.HEX_X)) or (type==0):
        return array
    elif type==1:
        return array[4::1, :fixed.HEX_X]
    elif type==2:
        return array[0:4:1, :fixed.HEX_X]
    elif type==3:
        return array[:fixed.HEX_Y, 2::1]
    elif type==4:
        return array[:fixed.HEX_Y, 0:2:1]
    else:
        return array
    
# insert a smaller array into a larger one
def insert_at_position(dest_array, src_array, x, y):
    for i_y in range(np.size(src_array,0)):
        for i_x in range(np.size(src_array,1)):
            if (src_array[i_y, i_x]!=-1):
                dest_array[y+i_y, x+i_x] = src_array[i_y, i_x]
    return dest_array
    

def static_array_from_xlsx(file):
    # reading the controller placement info from .xlsx file
    # format: nr_of_controller type_of_hexagon rotation origin_x origin_y
    raw_excel = pd.read_excel(file, skiprows=0)
    controller_info = np.array(raw_excel)
    
    static_array = np.zeros((fixed.DISPLAY_Y,fixed.DISPLAY_X),dtype=int)
    
    for i in range(fixed.DRIVER_COUNT):
        hexagon = initiate_array(controller_info[i])
        static_array = insert_at_position(static_array, hexagon, controller_info[i, 3], controller_info[i, 4])

    #print(static_array)
    return static_array
