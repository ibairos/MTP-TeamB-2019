#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Receiver part for the Quick Mode competition of Team B
# This version uses STOP&WAIT with timeout if the ACK is not received
# It also uses CRC to ensure packet integrity
# Date: 10/04/2019
# Version: 1.0

import RPi.GPIO as GPIO

from lib_nrf24 import NRF24
import spidev
import sys
import os
import time
import hashlib

# Initialize GPIOs
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

pipes = [[0xe7, 0xe7, 0xe7, 0xe7, 0xe7], [0xc2, 0xc2, 0xc2, 0xc2, 0xc2]]


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


def send_packet(sender, payload):
    """ Send the packet through the sender radio. """
    sender.write(payload)
    print("Send: " + str(payload))


def read_file(file_path):
    """ Gets the provided file and reads its content as bytes,
    after that, it stores everything in the variable payload_list,
    which it returns. """

    payload_list = list()

    if os.path.isfile(file_path):
        print("Loading File in: " + file_path)

        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(32)
                if chunk:
                    payload_list.append(chunk)
                else:
                    break
    else:
        print("ERROR: file does not exist in PATH: " + file_path)

    print("Length of the file in chunks: " + str(len(payload_list)))

    return payload_list


def main():
    """ This main function initializes the radios and sends
    all the data gathered from the file. """

    sender = initialize_radios(0, 25, 0x60)

    sender.openWritingPipe(pipes[1])

    print("Radio Information")
    sender.printDetails()
    # Read file
    payload_list = read_file(sys.argv[1])

    i = 0
    while i < 10:
        # Sending the file
        x = 0
        for payload in payload_list:
            send_packet(sender, payload)
            x = x + 1

        # Sending the final packet
        print("Sent final packet")
        send_packet(sender, b"ENDOFTRANSMISSION")
        time.sleep(2)
        print("Sent HASH: " + str(bytes(hashlib.md5(repr(payload_list).encode('utf-8')).hexdigest().encode('utf-8'))))
        print("Hash without testing: " + str(hashlib.md5(repr(payload_list).encode('utf-8')).hexdigest()))
        send_packet(sender, bytes(hashlib.md5(repr(payload_list).encode('utf-8')).hexdigest().encode('utf-8')))
        print("End of transmission " + str(i))
        i = i + 1
        time.sleep(0.5)


if __name__ == '__main__':
    main()