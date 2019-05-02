#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Receiver part for the Short Range Mode competition of Team B
# This version uses STOP&WAIT with timeout if the ACK is not received
# It also uses CRC to ensure packet integrity
# Author: Ibai Ros
# Date: 05/01/2019
# Version: 1.1

from lib_nrf24 import NRF24
import RPi.GPIO as GPIO
import spidev
import sys
import time
import crc16

# Initialization
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
pipes = [[0xe7, 0xe7, 0xe7, 0xe7, 0xe7], [0xc2, 0xc2, 0xc2, 0xc2, 0xc2]]
channels = [0xA0, 0x14]

# Define constants
SENDER_CSN = 25
SENDER_CE = 0
SENDER_CHANNEL = channels[1]  # Channel 20
SENDER_PIPE = pipes[1]

RECEIVER_CSN = 22
RECEIVER_CE = 1
RECEIVER_CHANNEL = channels[0]  # Channel 10
RECEIVER_PIPE = pipes[0]

DATA_SIZE = 27  # Size of the data chunks (27 bytes)
DATA_TIMEOUT = 0.01  # Timeout for receiving the DATA after the ACK is sent (10 ms)
HELLO_TIMEOUT = 0.01  # Timeout for receiving the HELLO message (10 ms)


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


def wait_for_data(receiver):
    """ This is a blocking function that waits
    until the ACK is available in the receiver pipe
    or until the timeout expires. """

    start_time = time.time()
    while not receiver.available(RECEIVER_PIPE):
        if time.time() - start_time < DATA_TIMEOUT:
            time.sleep(0.001)
        else:
            return False
    return True


def wait_for_hello(receiver):
    """ This is a blocking function that waits
    until we receive a HELLO message or the
    timeout expires. """

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


def check_crc(crc, payload):
    """ Function that checks the CRC and returns the result """

    crc_str = str(bytes(crc))
    if len(crc_str) < 5:
        padding_length = 5 - len(crc_str)
        if padding_length != 0:
            for i in range(0, padding_length):
                crc_str = '0' + crc_str
    crc_payload = str(bytes(crc16.crc16xmodem(bytes(payload)).encode('utf-8')))
    if crc_payload == crc_str:
        return True
    else:
        return False


def write_file(file_path, payload_list):
    """ Function that stores the file in memory """

    with open(file_path, "wb") as f:
        for chunk in payload_list:
            f.write(chunk)


def hello(sender, receiver):
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
    """ This main function initializes the radios,
    receives the file and stores it in memory. """

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

    # Initialize loop variables and functions
    rx_success = False
    seq_num = 1
    payload_list = list()
    receiver.startListening()

    # HELLO function, commented for now
    # hello(sender, receiver)

    # Receive file
    while not rx_success:
        rx_buffer = []
        received_something = False
        while not received_something:
            if wait_for_data(receiver):
                receiver.read(rx_buffer, receiver.getDynamicPayloadSize())
                received_something = True
            elif len(payload_list) != 0:
                send_packet(sender, b'ACK')

        receiver.stopListening()
        if bytes(rx_buffer) != b"ENDOFTRANSMISSION":
            crc = rx_buffer[:-5]
            payload = rx_buffer[-5:]
            if check_crc(crc, payload):
                send_packet(sender, b'ACK')
                payload_list.append(bytes(payload))
                seq_num = seq_num + 1
                print("Packet number " + seq_num + " received successfully")
            else:
                send_packet(sender, b'ERROR')
                print("    Packet number " + seq_num + " received incorrectly")
        else:
            send_packet(sender, b'ACK')
            rx_success = True
            print("RECEPTION SUCCESSFUL")
        receiver.startListening()

    write_file(sys.argv[1], payload_list)


if __name__ == '__main__':
    main()
