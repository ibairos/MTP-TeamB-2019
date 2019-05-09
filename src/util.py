from libraries.lib_nrf24 import NRF24
import RPi.GPIO as GPIO
import spidev
import time
import os
import crc16
from subprocess import check_output, STDOUT, CalledProcessError


##########################
#    RADIO MANAGEMENT    #
##########################

def initialize_radios(csn, ce, channel, config):
    """ This function initializes the radios, each
    radio being the NRF24 transceivers.

    It gets 3 arguments, csn = Chip Select, ce = Chip Enable
    and the channel that will be used to transmit or receive the data."""

    radio = NRF24(GPIO, spidev.SpiDev())
    radio.begin(csn, ce)
    time.sleep(1)
    radio.setRetries(15, 15)
    radio.setPayloadSize(32)
    radio.setChannel(channel)

    radio.setDataRate(config.BITRATE)
    radio.setPALevel(config.POWER)
    radio.setAutoAck(False)
    radio.enableDynamicPayloads()
    radio.enableAckPayload()

    return radio


def send_packet(sender, payload):
    """ Send the packet through the sender radio. """

    sender.write(payload)


#######################
#    CRC UTILITIES    #
#######################

def calculate_crc(config, payload):
    """ This is a function for calculating the crc
    and making sure it has the right length. """

    crc = crc16.crc16xmodem(payload)
    crc_bytes = crc.to_bytes(config.CRC_SIZE, byteorder='big')

    return crc_bytes


def check_crc(crc, seq_payload):
    """ Function that checks the CRC and returns the result """

    crc_int = int.from_bytes(bytes(crc), 'big')

    crc_payload = crc16.crc16xmodem(bytes(seq_payload))

    if crc_int == crc_payload:
        return True
    else:
        return False


########################
#    FILE I/O UTILS    #
########################

def read_file(config, file_path):
    """ Gets the provided file and reads its content as bytes,
    after that, it stores everything in the variable payload_list,
    which it returns. """

    payload_list = list()

    if os.path.isfile(file_path):
        print("Loading File in: " + file_path)
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(config.DATA_SIZE)
                if chunk:
                    payload_list.append(chunk)
                else:
                    break
    else:
        print("ERROR: file does not exist in PATH: " + file_path)

    print("Length of the file in chunks: " + str(len(payload_list)))

    return payload_list


def write_file(file_path, payload_list):
    """ Function that stores the file in memory """

    with open(file_path, "wb") as f:
        for chunk in payload_list:
            f.write(chunk)


def compress_file(config):
    command = "7z a -mx=" + str(config.COMPRESSION_LEVEL) + " " + \
              config.IN_FILEPATH_COMPRESSED + " " + config.IN_FILEPATH_RAW
    result = check_output(command, stderr=STDOUT, shell=True)
    ok_string = b'Everything is Ok'
    if ok_string in result:
        return True
    else:
        return False


def uncompress_file(config):
    command = "7z x -o" + config.OUT_PATH_RAW + " " + config.OUT_FILEPATH_COMPRESSED
    try:
        result = check_output(command, stderr=STDOUT, shell=True)
    except CalledProcessError:
        return False
    ok_string = b'Everything is Ok'
    if ok_string in result:
        return True
    else:
        return False


def get_raw_filepath(config):
    path = config.IN_PATH_RAW
    for file in os.listdir(path):
        if file.endswith("txt"):
            return config.IN_PATH_RAW + file
    return None


def get_compressed_filepath(config):
    path = config.IN_PATH_COMPRESSED
    for file in os.listdir(path):
        if file.endswith("7z"):
            return config.IN_PATH_COMPRESSED + file
    return None


def clear_outputs(config):
    try:
        os.remove(config.OUT_FILEPATH_COMPRESSED)
    except IOError:
        print()
    try:
        os.remove(config.OUT_FILEPATH_RAW)
    except IOError:
        print()
    try:
        os.remove(config.IN_FILEPATH_COMPRESSED)
    except IOError:
        print()
    return True