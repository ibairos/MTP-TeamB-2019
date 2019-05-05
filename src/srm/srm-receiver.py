#!/usr/bin/python3
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
channels = [30, 40]

# Define constants
SENDER_CSN = 25
SENDER_CE = 0
SENDER_CHANNEL = channels[1]  # Channel 20
SENDER_PIPE = pipes[1]

RECEIVER_CSN = 24
RECEIVER_CE = 1
RECEIVER_CHANNEL = channels[0]  # Channel 10
RECEIVER_PIPE = pipes[0]

DATA_SIZE = 28  # Size of the data chunks (28 bytes)
SEQ_NUM_SIZE = 2  # Size of the seq number (2 bytes)
CRC_SIZE = 2  # Size of the CRC in bytes (2 bytes)

DATA_TIMEOUT = 0.03  # Timeout for receiving the data
HELLO_TIMEOUT = 0.01  # Timeout for receiving the HELLO message (10 ms)

OUT_FILEPATH = sys.argv[1]  # Filepath of the output file


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
    """ Function that stores the file in memory """

    with open(file_path, "wb") as f:
        for chunk in payload_list:
            f.write(chunk)


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


def calculate_crc(payload):
    """ This is a function for calculating the crc
    and making sure it has the right length. """

    crc = crc16.crc16xmodem(payload)
    crc_bytes = crc.to_bytes(CRC_SIZE, byteorder='big')

    return crc_bytes


def check_crc(crc, seq_payload):
    """ Function that checks the CRC and returns the result """

    crc_int = int.from_bytes(bytes(crc), 'big')

    crc_payload = crc16.crc16xmodem(bytes(seq_payload))

    if crc_int == crc_payload:
        return True
    else:
        return False


def build_frame(payload, seq_num):
    """ Function that builds the frame in bytes """

    seq = seq_num.to_bytes(SEQ_NUM_SIZE, byteorder='big')
    crc = calculate_crc(seq + payload)

    return crc + seq + payload


def send_packet(sender, payload):
    """ Send the packet through the sender radio. """

    sender.write(payload)


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

    # HELLO function, commented for now
    # hello(sender, receiver)

    # Initialize loop variables and functions
    rx_success = False
    seq_num = 1
    payload_list = list()
    receiver.startListening()

    # Receive file
    while not rx_success:
        rx_buffer = []
        received_something = False
        while not received_something:
            if wait_for_data(receiver):
                receiver.read(rx_buffer, receiver.getDynamicPayloadSize())
                received_something = True

        payload = rx_buffer[CRC_SIZE + SEQ_NUM_SIZE:]
        if bytes(payload) != b'ENDOFTRANSMISSION':
            crc = rx_buffer[:CRC_SIZE]
            seq = int.from_bytes(rx_buffer[CRC_SIZE:CRC_SIZE + SEQ_NUM_SIZE], byteorder='big')
            seq_payload = rx_buffer[CRC_SIZE:]
            if check_crc(crc, seq_payload):
                if seq == seq_num:
                    send_packet(sender, build_frame(b'ACK', seq_num))
                    payload_list.append(bytes(payload))
                    print("Packet number " + str(seq_num) + " received successfully")
                    seq_num = seq_num + 1
                elif seq == seq_num - 1:
                    seq_num = seq_num - 1
                    send_packet(sender, build_frame(b'ACK', seq_num))
                    print("        ACK number " + str(seq_num - 1) + " was lost. Resending...")
                else:
                    print("        Receiver out of order packet. Received: " + str(seq) + " Expecting: " + str(seq_num))
            else:
                send_packet(sender, build_frame(b'ERROR', seq_num))
                print("    Packet number " + str(seq_num) + " received incorrectly")
        else:
            send_packet(sender, build_frame(b'ACK', seq_num))
            rx_success = True
            print("RECEPTION SUCCESSFUL")

    write_file(OUT_FILEPATH, payload_list)


if __name__ == '__main__':
    main()
