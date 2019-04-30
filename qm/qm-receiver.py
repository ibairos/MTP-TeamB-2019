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
import time
import spidev
import sys
import os
import hashlib

# Initialize GPIOs
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Define the pipes that will be used to send the data from one transceiver to the other
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


def write_file(file_path, payload_list):

    with open(file_path, "wb") as f:
        for chunk in payload_list:
            f.write(chunk)


def wait_for_data(receiver):
    while not receiver.available(pipes[1]):
        time.sleep(0.01)


def main():
    receiver = initialize_radios(0, 25, 0x60)
    receiver.openReadingPipe(0, pipes[1])

    print("Receiver Information")
    receiver.printDetails()

    payload_list = list()

    # Receiving the file
    receiver.startListening()
    transmission_end = False
    retransmit = True
    x = 0
    while not transmission_end or retransmit:
        data = []
        while not data:
            wait_for_data(receiver)
            receiver.read(data, receiver.getDynamicPayloadSize())
            print("Received " + str(x) + " -> " + str(bytes(data)))
            if bytes(data) == b"ENDOFTRANSMISSION":
                print("Received final packet. Waiting for the hash...")
                hash_rcv = []
                wait_for_data(receiver)
                receiver.read(hash_rcv, receiver.getDynamicPayloadSize())
                print("Hash 1: " + str(bytes(hash_rcv).decode('utf-8')))
                print("Hash 2: " + str(hashlib.md5(repr(payload_list).encode('utf-8')).hexdigest()))

                if bytes(hash_rcv) == hashlib.md5(repr(payload_list).encode('utf-8')).hexdigest().encode('utf-8'):
                    print("HASH correct, end of transmission...")
                    transmission_end = True
                    retransmit = False
                    break
                else:
                    print("Hash incorrect, starting again...")
                    payload_list = list()
                    break
            else:
                payload_list.append(bytes(data))
                x = x + 1

    write_file(sys.argv[1], payload_list)


if __name__ == '__main__':
    main()
