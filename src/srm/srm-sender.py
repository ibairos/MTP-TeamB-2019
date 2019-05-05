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
import os
import time
import crc16
import chardet

# Initialization
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
pipes = [[0xe7, 0xe7, 0xe7, 0xe7, 0xe7], [0xc2, 0xc2, 0xc2, 0xc2, 0xc2]]
channels = [30, 40]  # Channels 30 and 40

# Define constants
SENDER_CSN = 25
SENDER_CE = 0
SENDER_CHANNEL = channels[0]  # Channel 10
SENDER_PIPE = pipes[0]

RECEIVER_CSN = 24
RECEIVER_CE = 1
RECEIVER_CHANNEL = channels[1]  # Channel 20
RECEIVER_PIPE = pipes[1]

SEQ_NUM_SIZE = 2  # Size of the seq number (2 bytes)
DATA_SIZE = 28  # Size of the data chunks (28 bytes)
CRC_SIZE = 2  # Size of the CRC in bytes (2 bytes)

ACK_TIMEOUT = 0.01  # Timeout for receiving the ACK (30 ms)
HELLO_TIMEOUT = 0.01  # Timeout for receiving the HELLOACK message (10 ms)

IN_FILEPATH = sys.argv[1]  # Filepath of the input file


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
    payload_list = read_file(IN_FILEPATH)

    # Initialize loop variables and functions
    receiver.startListening()
    tx_success = False
    seq_num = 1

    # Send file
    while not tx_success:
        # Sending payload
        for payload in payload_list:
            retransmit = True
            attempt = 0
            while retransmit:
                send_packet(sender, build_frame(payload, seq_num))
                attempt = attempt + 1
                rx_buffer = []
                if wait_for_ack(receiver):
                    receiver.read(rx_buffer, receiver.getDynamicPayloadSize())
                    crc = rx_buffer[:CRC_SIZE]
                    seq = int.from_bytes(rx_buffer[CRC_SIZE:CRC_SIZE + SEQ_NUM_SIZE], byteorder='big')
                    ack = rx_buffer[CRC_SIZE + SEQ_NUM_SIZE:]
                    seq_ack = rx_buffer[CRC_SIZE:]
                    if check_crc(crc, seq_ack):
                        if seq != seq_num:
                            print("Received Out of Order ACK. Received: " + str(seq) + " Expecting: " + str(seq_num))
                        elif bytes(ack) == b'ACK':
                            retransmit = False
                            print("Packet number " + str(seq_num) + " transmitted successfully")
                            seq_num = seq_num + 1
                        elif bytes(ack) == b'ERROR':
                            print("        Packet number " + str(seq_num) + " transmitted incorrectly")
                        else:
                            print("        Unknown error when transmitting packet number " + str(seq_num))
                    else:
                        print("        Received incorrect ACK number " + str(seq_num))
                else:
                    print("    Attempt " + str(attempt) + " to retransmit packet number " + str(seq_num))
                    if attempt > 1000:
                        exit("Program ended after trying to retransmit for more than 1000 times")

        retransmit_final = True
        attempt_final = 0
        while retransmit_final:
            send_packet(sender, build_frame(b'ENDOFTRANSMISSION', seq_num))
            attempt_final = attempt_final + 1
            rx_buffer = []
            if wait_for_ack(receiver):
                receiver.read(rx_buffer, receiver.getDynamicPayloadSize())
                crc = rx_buffer[:CRC_SIZE]
                seq = int.from_bytes(rx_buffer[CRC_SIZE:CRC_SIZE + SEQ_NUM_SIZE], byteorder='big')
                ack = rx_buffer[CRC_SIZE + SEQ_NUM_SIZE:]
                seq_ack = rx_buffer[CRC_SIZE:]
                if check_crc(crc, seq_ack) and seq == seq_num:
                    if bytes(ack) == b'ACK':
                        retransmit_final = False
                        tx_success = True
                        print("TRANSMISSION SUCCESSFUL")
            else:
                print("    Attempt " + str(attempt_final) + " to retransmit FINAL packet")
                if attempt_final > 1000:
                    exit("Program ended after failing to transmit the EOT message")


if __name__ == '__main__':
    main()
