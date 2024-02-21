#!/usr/bin/python
# -*- coding: utf-8 -*-
import struct
import sys
import matplotlib.pyplot as plt
from decimal import Decimal

def tlvHeaderDecode(data):
    (tlvType, tlvLength) = struct.unpack('2I', data)
    return (tlvType, tlvLength)

def parseDetectedObjects(data, tlvLength, numObj):
    # Extract xyzQFormat from the correct position
    xyzQFormat, = struct.unpack('H', data[2:4])
    print(f"xyzQFormat: {xyzQFormat}")
    
    object_coordinates = []
    for i in range(numObj):  # Use numObj to terminate the loop correctly
        slice_data = data[4+12*i:4+12*i+12]
        if len(slice_data) != 12:
            continue
        rangeIdx, dopplerIdx, peakVal, x, y, z = struct.unpack('3H3h', slice_data)
        print(f"Raw values - x: {x}, y: {y}, z: {z}")
        x_val = float(Decimal(x) / Decimal(1 << xyzQFormat))
        y_val = float(Decimal(y) / Decimal(1 << xyzQFormat))
        z_val = float(Decimal(z) / Decimal(1 << xyzQFormat))
        object_coordinates.append((x_val, y_val, z_val))
        print(f"Object {i+1}/{numObj}: X={x_val}, Y={y_val}, Z={z_val}")
    return object_coordinates

def is_magic(bytevec, byteVecIdx):
    # Check if there are at least 8 bytes available starting from byteVecIdx
    if len(bytevec) >= byteVecIdx + 8:
        # Define the expected magic pattern as a list of bytes
        expected_magic = [2, 1, 4, 3, 6, 5, 8, 7]
        # Check if each byte in the pattern matches the corresponding byte in bytevec
        for i in range(8):
            if bytevec[byteVecIdx + i] != expected_magic[i]:
                return False  # If any byte doesn't match, return False
        return True  # All bytes in the pattern match
    return False  # Not enough bytes available, return False

def parseFrame(data):
    if not is_magic(data, 0):
        print("Data corrupted")
        return
    
    headerLength = 36
    (
        magic,
        version,
        length,
        platform,
        frameNum,
        cpuCycles,
        numObj,
        numTLVs,
    ) = struct.unpack('Q7I', data[:headerLength])

    print('Packet ID:\t%d ' % frameNum)
    print('Version:\t%x ' % version)
    print('TLV:\t\t%d ' % numTLVs)
    print('Detect Obj:\t%d ' % numObj)
    print('Platform:\t%X ' % platform)

    if version > 0x01000005:
        subFrameNum = struct.unpack('I', data[36:40])[0]
        headerLength = 40
        print('Subframe:\t%d ' % subFrameNum)

    pendingBytes = length - headerLength
    data = data[headerLength:]
    detected_objects_coordinates = []

    for tlvidx in range(numTLVs):
        tlvType, tlvLength = tlvHeaderDecode(data[:8])
        data = data[8:]
        if tlvType == 1:
            #index for bytes of detected objects is 48 onward
            detected_objects_coordinates.extend(parseDetectedObjects(data[48:], tlvLength, numObj))
        elif tlvType == 2:
            # MMWDEMO_OUTPUT_MSG_RANGE_PROFILE
            # Process range profile data
            pass
        elif tlvType == 3:
            # MMWDEMO_OUTPUT_MSG_NOISE_PROFILE
            # Process noise profile data
            pass
        elif tlvType == 4:
            # MMWDEMO_OUTPUT_MSG_AZIMUT_STATIC_HEAT_MAP
            # Process azimuth static heat map data
            pass
        elif tlvType == 5:
            # MMWDEMO_OUTPUT_MSG_RANGE_DOPPLER_HEAT_MAP
            # Process range-doppler heat map data
            pass
        elif tlvType == 6:
            # MMWDEMO_OUTPUT_MSG_STATS
            # Process statistics data
            pass
        elif tlvType == 7:
            # MMWDEMO_OUTPUT_MSG_DETECTED_POINTS_SIDE_INFO
            # Process detected points side info data
            pass
        elif tlvType == 8:
            # MMWDEMO_OUTPUT_MSG_AZIMUT_ELEVATION_STATIC_HEAT_MAP
            # Process azimuth-elevation static heat map data
            pass
        elif tlvType == 9:
            # MMWDEMO_OUTPUT_MSG_TEMPERATURE_STATS
            # Process temperature statistics data
            pass

    return detected_objects_coordinates, data, frameNum

TLV_type = {
    "MMWDEMO_OUTPUT_MSG_DETECTED_POINTS": 1,
    "MMWDEMO_OUTPUT_MSG_RANGE_PROFILE": 2,
    "MMWDEMO_OUTPUT_MSG_NOISE_PROFILE": 3,
    "MMWDEMO_OUTPUT_MSG_AZIMUT_STATIC_HEAT_MAP": 4,
    "MMWDEMO_OUTPUT_MSG_RANGE_DOPPLER_HEAT_MAP": 5,
    "MMWDEMO_OUTPUT_MSG_STATS": 6,
    "MMWDEMO_OUTPUT_MSG_DETECTED_POINTS_SIDE_INFO": 7,
    # /*All messages from this point forward are present only on SDK >= 3.0*/
    "MMWDEMO_OUTPUT_MSG_AZIMUT_ELEVATION_STATIC_HEAT_MAP": 8,
    "MMWDEMO_OUTPUT_MSG_TEMPERATURE_STATS": 9,
    "MMWDEMO_OUTPUT_MSG_MAX": 10}

if __name__ == '__main__':
    fileName = "slope-diff-data/1/xwr16xx_processed_stream_2023_09_14T16_41_23_134.dat"
    with open(fileName, "rb") as rawDataFile:
        rawData = rawDataFile.read()
    magic = b'\x02\x01\x04\x03\x06\x05\x08\x07'
    offset = rawData.find(magic)
    rawData = rawData[offset:]
    
    while rawData:
        detected_objects_coordinates, rawData, frameNum = parseFrame(rawData)
        if frameNum != 862:
            continue
        else:
            # Extract x, y, and z coordinates
            x_coords = [coord[0] for coord in detected_objects_coordinates]
            y_coords = [coord[1] for coord in detected_objects_coordinates]
            z_coords = [coord[2] for coord in detected_objects_coordinates]
            # Plotting
            fig = plt.figure()
            ax = fig.add_subplot(111, projection='3d')
            ax.scatter(x_coords, y_coords, z_coords, c='r', marker='o')
            ax.set_xlabel('X Coordinate')
            ax.set_ylabel('Y Coordinate')
            ax.set_zlabel('Z Coordinate')
            plt.show()
