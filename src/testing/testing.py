import hashlib

import RPi.GPIO as GPIO

import spidev
import sys
import os
import time
import crc16
import chardet
from subprocess import *


DATA_SIZE = 30  # Size of the data chunks (27 bytes)
CRC_SIZE = 2

MODE = "testing"
ENCODING = "UTF-8"

CURRENT_DIRECTORY = os.getcwd()
PROJECT_ROOT = CURRENT_DIRECTORY.split("/src/")[0]

IN_FILENAME_RAW = "utf-8.txt"
IN_FILENAME_COMPRESSED = "utf-8.7z"
IN_FILEPATH_RAW = PROJECT_ROOT + "/files/input/" + MODE + "/raw/" + IN_FILENAME_RAW
IN_FILEPATH_COMPRESSED = PROJECT_ROOT + "/files/input/" + MODE + "/compressed/" + IN_FILENAME_COMPRESSED

OUT_FILENAME_RAW = IN_FILENAME_RAW
OUT_FILENAME_COMPRESSED = "utf-8.7z"
OUT_FILEPATH_RAW = PROJECT_ROOT + "/files/output/" + MODE + "/raw/" + OUT_FILENAME_RAW
OUT_FILEPATH_COMPRESSED = PROJECT_ROOT + "/files/output/" + MODE + "/compressed/" + OUT_FILENAME_COMPRESSED

COMPRESSION_LEVEL = 6


def wait_for_hello(receiver):
    """ This is a blocking function that waits
    until we receive a HELLOACK message back or
    the timeout expires. """

    # Commented, since we do not use it
    #  start_time = time.time()
    #  while not receiver.available(RECEIVER_PIPE):
    #      if time.time() - start_time < HELLO_TIMEOUT:
    #          time.sleep(0.001)
    #      else:
    #          return False
    #  return True


def read_file(file_path):
    """ Gets the provided file and reads its content as bytes,
    after that, it stores everything in the variable payload_list,
    which it returns. """

    payload_list = list()

    if os.path.isfile(file_path):
        print("Loading File in: " + file_path)
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(DATA_SIZE)
                if chunk:
                    payload_list.append(chunk)
                else:
                    break
    else:
        print("ERROR: file does not exist in PATH: " + file_path)

    print("Length of the file in chunks: " + str(len(payload_list)))

    return payload_list


def list_dir(rel_path):
    dirs = os.listdir(rel_path)
    return dirs


def compress_file(in_file_path, out_file_path):
    command = '7z a -mx=' + str(COMPRESSION_LEVEL) + " " + out_file_path + " " + in_file_path
    result = check_output(command, stderr=STDOUT, shell=True)
    ok_string = b'Everything is Ok'
    if ok_string in result:
        return True
    else:
        return False


def read_file_and_encoding(file_path):

    payload_list = list()

    if os.path.isfile(file_path):
        print("Loading File in: " + file_path)
        raw_data = open(file_path, 'rb').read()
        global ENCODING
        ENCODING = chardet.detect(raw_data)['encoding']
        encoding = ENCODING
        pos = 0
        while True:
            chunk = raw_data[pos:pos+DATA_SIZE]
            payload_list.append(chunk)
            if len(chunk) != DATA_SIZE:
                break
            pos = pos + DATA_SIZE
    else:
        print("ERROR: file does not exist in PATH: " + file_path)

    print("Length of the file in chunks: " + str(len(payload_list)))

    return payload_list


def calculate_crc(payload):
    """ This is a function for calculating the crc
    and making sure it has the right length. """

    crc = crc16.crc16xmodem(payload)
    crc_bytes = crc.to_bytes(2, byteorder='big')

    return crc_bytes


def build_frame(payload):
    """ Function that builds the frame in bytes """

    crc = calculate_crc(payload)
    frame = crc + payload
    return frame


def detect_encoding(file):
    """ Function that detects encoding and return it """
    raw_data = open(file, 'rb').read()
    result = chardet.detect(raw_data)
    enc = result['encoding']
    return enc


def check_crc(crc, payload):
    """ Function that checks the CRC and returns the result """

    crc_int = int.from_bytes(crc, 'big')

    crc_payload = crc16.crc16xmodem(payload)

    if crc_int == crc_payload:
        return True
    else:
        return False


def receive_frame(frame):
    crc = frame[:CRC_SIZE]
    payload = frame[CRC_SIZE:]
    crc_check = check_crc(crc, payload)
    if crc_check:
        return payload
    else:
        return None


def calculate_hash(payload_list, encoding):
    hash_str = hashlib.md5(repr(payload_list).encode(encoding)).hexdigest()
    hash_bytes = bytes(hash_str.encode(encoding))
    return hash_bytes


def hash_raw_file(file_path):
    command = "md5sum " + file_path
    md5 = check_output(command, stderr=STDOUT, shell=True)
    result = md5.decode("utf-8").split(" ")[0]
    return result


def hello(sender, receiver):
    """ Function that sends HELLO messages
    until we get a response """

    hello_rcv = False
    while not hello_rcv:
        send_packet(sender, b'HELLO')
        receiver.startListening()
        if wait_for_hello(receiver):
            hello_ack = []
            receiver.read(hello_ack, receiver.getDynamicPayloadSize())
            receiver.stopListening()
            if bytes(hello_ack) == b'HELLOACK':
                hello_rcv = True
                print("Received HELLO ACK. Starting file transmission...")


def hello_rx(sender, receiver):
    """ Function that waits for the HELLO message
    until we get one """

    hello_rcv = False
    while not hello_rcv:
        receiver.startListening()
        if wait_for_hello(receiver):
            hello_syn = []
            receiver.read(hello_syn, receiver.getDynamicPayloadSize())
            receiver.stopListening()
            if bytes(hello_syn) == b'HELLO':
                send_packet(sender, b'HELLOACK')
                hello_rcv = True
                print("Received HELLO. Starting file reception...")


def main():

    hash_raw_file(IN_FILEPATH_RAW)

    compress_file(IN_FILEPATH_RAW, IN_FILEPATH_COMPRESSED)

    payload_list_raw = read_file_and_encoding(IN_FILEPATH_RAW)
    payload_list_compressed = read_file_and_encoding(IN_FILEPATH_COMPRESSED)

    print("CP")

    payload_list = payload_list_raw

    received_frames = list()

    for payload in payload_list:
        data = receive_frame(build_frame(payload))
        if data is not None:
            received_frames.append(data)
        else:
            print("FAILED")

    if received_frames == payload_list:
        print("SUCCESS")
        print(calculate_hash(payload_list, ENCODING))
        print(calculate_hash(received_frames, ENCODING))
    else:
        print("FAILURE")


if __name__ == '__main__':
    main()
