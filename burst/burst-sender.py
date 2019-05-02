#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Receiver part for the Short Range Mode competition of Team B
# This version uses STOP&WAIT with timeout if the ACK is not received
# It also uses CRC to ensure packet integrity
# Author: Ibai Ros
# Date: 05/01/2019
# Version: 1.1

import RPi.GPIO as GPIO

from lib_nrf24 import NRF24
import spidev
import sys
import os
import time
import crc16
import chardet
import hashlib

# Initialization
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
pipes = [[0xe7, 0xe7, 0xe7, 0xe7, 0xe7], [0xc2, 0xc2, 0xc2, 0xc2, 0xc2]]
channels = [0xA0, 0x14]  # Channels 10 and 20

# Define constants
SENDER_CSN = 25
SENDER_CE = 0
SENDER_CHANNEL = channels[0]  # Channel 10
SENDER_PIPE = pipes[0]

RECEIVER_CSN = 22
RECEIVER_CE = 1
RECEIVER_CHANNEL = channels[1]  # Channel 20
RECEIVER_PIPE = pipes[1]

DATA_SIZE = 30  # Size of the data chunks (27 bytes)
CRC_SIZE = 2  # Size of the CRC in bytes (2 bytes)

ACK_TIMEOUT = 0.03  # Timeout for receiving the ACK (30 ms)
HELLO_TIMEOUT = 0.01  # Timeout for receiving the HELLOACK message (10 ms)

IN_FILEPATH = sys.argv[1]  # Filepath of the input file

ENCODING = "UTF-8"


def initialize_radios(csn, ce, channel):
    """ This function initializes the radios, each
    radio being the NRF24 transceivers.

    It gets 3 arguments, csn = Chip Select, ce = Chip Enable
    and the channel that will be used to transmit or receive the data."""

    radio = NRF24(GPIO, spidev.SpiDev())
    radio.begin(csn, ce)
    time.sleep(2)
    radio.setRetries(15, 15)
    radio.setPayloadSize(32)
    radio.setChannel(channel)

    radio.setDataRate(NRF24.BR_250KBPS)
    radio.setPALevel(NRF24.PA_MIN)
    radio.setAutoAck(False)
    radio.enableDynamicPayloads()
    radio.enableAckPayload()

    return radio


def read_file_and_encoding(file_path):
    """ Gets the provided file and reads its content as bytes,
        after that, it stores everything in the variable payload_list,
        which it returns. It also detects the encoding. """

    global ENCODING
    payload_list = list()

    if os.path.isfile(file_path):
        print("Loading File in: " + file_path)
        raw_data = open(file_path, 'rb').read()
        ENCODING = chardet.detect(raw_data)['encoding']
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


def wait_for_ack(receiver):
    """ This is a blocking function that waits
    until the ACK is available in the receiver pipe
    or until the timeout expires. """

    start_time = time.time()
    while not receiver.available(RECEIVER_PIPE):
        if time.time() - start_time < ACK_TIMEOUT:
            time.sleep(0.001)
        else:
            return False
    return True


def wait_for_hello(receiver):
    """ This is a blocking function that waits
    until we receive a HELLOACK message back or
    the timeout expires. """

    start_time = time.time()
    while not receiver.available(RECEIVER_PIPE):
        if time.time() - start_time < HELLO_TIMEOUT:
            time.sleep(0.001)
        else:
            return False
    return True


def send_packet(sender, payload):
    """ Send the packet through the sender radio. """

    sender.write(payload)


def calculate_crc(payload):
    """ This is a function for calculating the crc
    and making sure it has the right length. """

    crc = crc16.crc16xmodem(payload)
    crc_bytes = crc.to_bytes(CRC_SIZE, byteorder='big')

    return crc_bytes


def build_frame(payload):
    """ Function that builds the frame in bytes """

    crc = calculate_crc(payload)
    return crc + payload


def error_available(receiver):
    """ This function checks if there is any error messages """

    if receiver.available(RECEIVER_PIPE):
        return True
    else:
        return False


def calculate_hash(payload_list, encoding):
    """ This function is used for calculating the hash of the payload_list """

    hash_str = hashlib.md5(repr(payload_list).encode(encoding)).hexdigest()
    hash_bytes = bytes(hash_str.encode(encoding))
    return hash_bytes


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


def main():
    """ This main function initializes the radios and sends
    all the data gathered from the file. """

    # Initialize the sender radio and print details
    sender = initialize_radios(SENDER_CE, SENDER_CSN, SENDER_CHANNEL)
    sender.openWritingPipe(SENDER_PIPE)
    print("Sender Information")
    sender.printDetails()

    # Initialize the receiver radio and print details
    receiver = initialize_radios(RECEIVER_CE, RECEIVER_CSN, RECEIVER_CHANNEL)
    receiver.openReadingPipe(0, RECEIVER_PIPE)
    print("Receiver Information")
    receiver.printDetails()

    # HELLO function, commented for now
    # hello(sender, receiver)

    # Read file
    payload_list = read_file_and_encoding(IN_FILEPATH)

    # Initialize loop variables and functions
    receiver.startListening()

    # Sending payload
    retransmit = True

    while retransmit:
        receiver.flush_rx()
        ack = []
        for payload in payload_list:
            send_packet(sender, build_frame(payload))
            if error_available(receiver):
                receiver.read(ack, receiver.getDynamicPayloadSize())
                if bytes(ack) == b'ERROR':
                    break
        if not error_available(receiver):
            eot_payload = "TeamB_EOT-" + ENCODING
            send_packet(sender, bytes(eot_payload.encode("utf-8")))
            send_packet(sender, calculate_hash(payload_list, ENCODING))
            if wait_for_ack(receiver):
                receiver.read(ack, receiver.getDynamicPayloadSize())
                if bytes(ack) == b'ACK':
                    retransmit = False

    print("FILE TRANSMITTED SUCCESSFULLY")


if __name__ == '__main__':
    main()
