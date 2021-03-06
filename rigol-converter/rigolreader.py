#!/usr/bin/env python
# coding: utf-8

"""This script is intended to convert .rof files generated by
rigol power supply to simple text csv files with ASCii data.

Simple usage:
Usage: python rigolreader.py inpytfile.rof > outpufile.csv


Author: Konstantin Shpakov, august 2019.


REFERENCE:
1) DP800 Series Programmable Linear DC Power Supply User's Guide
2) DP800 file format description

"""

import struct
import numpy as np


ENCODING = 'latin-1'

CSV_SEPARATOR = ";"

# each data value in file is 4-byte integer
DATA_BYTES = 4

# converts values to volts and amperes
VOLTS_AMPERES_COEFF = 0.0001

# numpy binary data format selector
fmt = {"MSB": ">",      # most significant byte first (big-endian)
       "LSB": "<",      # least significant byte first (little-endian)
       "uint": "u",       # unsigned integer
       "int": "i",       # signed integer
       "float": "f"}       # float

DATA_FORMAT = "{}{}{}".format(fmt["LSB"], fmt["int"], DATA_BYTES)

# number of channels for each model
ch_num = {"DP821A": 2}

# model label from hex code
model_dict = {b"\n": "DP821A"}


def read_rof(filename):
    """ Reads ROF binary file (generated by Rigol power supply)
    and returns it's data in numpy.ndarray format
    and file info (header) in dict format

    :param filename: ROF binary file name
    :return: data, head
    :rtype: numpy.ndarray, dict
    """
    with open(filename, "rb") as fid:
        data = list()

        # read header info
        head = dict()
        head["filetype"] = fid.read(3).decode(ENCODING)
        fid.read(1)  # unused last byte of file type value
        head["model"] = model_dict[fid.read(1)]

        fid.read(1)  # unused byte
        head["data_info_len"] = struct.unpack('1h', fid.read(2))[0]
        head["data_len"] = struct.unpack('1i', fid.read(4))[0]
        head["head_crc"] = fid.read(2)
        head["data_crc"] = fid.read(2)
        head["period"] = struct.unpack('1i', fid.read(4))[0]
        head["points"] = struct.unpack('1i', fid.read(4))[0]
        head["oldest_data_subscript"] = fid.read(4)

        # values number == points * number_of_cahnnels * 2
        data_values = head["points"] * ch_num[head["model"]] * 2  # 2 columns (voltage, current)
        data_bytes = data_values * DATA_BYTES
        raw_data = fid.read(data_bytes)

        data = np.ndarray(shape=(head["points"], ch_num[head["model"]] * 2), dtype=DATA_FORMAT, buffer=raw_data)

        # convert to float
        data = data.astype(np.float32)

        # convert to volts and amperes
        data = data * VOLTS_AMPERES_COEFF

        # get time column
        x_data = np.array([val * head["period"] for val in range(head["points"])], dtype=data.dtype, order="F")

        # add time column
        data = np.insert(data, 0, x_data, axis=1)

    # print("================================")
    # print("\n".join(str(line) for line in data))
    #
    # for idx, line in enumerate(data):
    #     if idx == 30:
    #         break
    #     print(CSV_SEPARATOR.join(str(val) for val in line))

    return data, head


def main():
    """Reads input ROF file and outputs (print) data table line by line
    Usage: python rigolreader.py inpytfile.rof > outpufile.csv
    :return: None
    """
    # TODO: RTF and RDF support
    # TODO: ROF RTF RDF output data table structure description

    import sys

    print_head = False

    # check
    assert len(sys.argv) > 1, "Please specify file path/name."
    assert len(sys.argv) < 3, "Too many input arguments!"

    if sys.argv[1] == "-h" or sys.argv[1] == "--help":
        print("Usage: python rigolreader.py inpytfile.rof > outpufile.csv\n"
              "\n")
        return

    # read
    data, head = read_rof(sys.argv[1])

    # output
    for idx, line in enumerate(data):
        print(CSV_SEPARATOR.join(str(val) for val in line))


if __name__ == "__main__":
    main()
    # read_rof("detector_1.ROF")
