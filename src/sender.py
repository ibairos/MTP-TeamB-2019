#!/usr/bin/python3
#
# Receiver part for the Short Range Mode competition of Team B
# This version uses STOP&WAIT with timeout if the ACK is not received
# It also uses CRC to ensure packet integrity
# Author: Ibai Ros
# Date: 05/01/2019
# Version: 1.1

import time
from src import util


class Sender(object):
    def __init__(self, config, sender, receiver):
        self.config = config
        self.sender = sender
        self.receiver = receiver

    def wait_for_ack(self, receiver):
        """ This is a blocking function that waits
        until the ACK is available in the receiver pipe
        or until the timeout expires. """

        start_time = time.time()
        while not receiver.available(self.config.RECEIVER_PIPE):
            if time.time() - start_time < self.config.ACK_TIMEOUT:
                time.sleep(0.001)
            else:
                return False
        return True

    def build_frame(self, payload, seq_num):
        """ Function that builds the frame in bytes """

        seq = seq_num.to_bytes(self.config.SEQ_NUM_SIZE, byteorder='big')
        crc = util.calculate_crc(self.config, seq + payload)

        return crc + seq + payload

    def transmit(self):
        """ This main function initializes the radios and sends
        all the data gathered from the file. """

        # Read file
        util.compress_file(self.config)
        payload_list = util.read_file(self.config, self.config.IN_FILEPATH_COMPRESSED)

        # Initialize loop variables and functions
        self.receiver.startListening()
        tx_success = False
        seq_num = 1

        # Send file
        while not tx_success:
            # Sending payload
            for payload in payload_list:
                retransmit = True
                attempt = 0
                while retransmit:
                    util.send_packet(self.sender, self.build_frame(payload, seq_num))
                    attempt = attempt + 1
                    rx_buffer = []
                    if self.wait_for_ack(self.receiver):
                        self.receiver.read(rx_buffer, self.receiver.getDynamicPayloadSize())
                        crc = rx_buffer[:self.config.CRC_SIZE]
                        seq = int.from_bytes(
                            rx_buffer[self.config.CRC_SIZE:self.config.CRC_SIZE + self.config.SEQ_NUM_SIZE],
                            byteorder='big')
                        ack = rx_buffer[self.config.CRC_SIZE + self.config.SEQ_NUM_SIZE:]
                        seq_ack = rx_buffer[self.config.CRC_SIZE:]
                        if util.check_crc(crc, seq_ack):
                            if seq == seq_num:
                                if bytes(ack) == b'ACK':
                                    retransmit = False
                                    print("Packet number " + str(seq_num) + " transmitted successfully")
                                    seq_num = seq_num + 1
                                elif bytes(ack) == b'ERROR':
                                    print("        Packet number " + str(seq_num) + " transmitted incorrectly")
                                else:
                                    print("        Unknown error when transmitting packet number " + str(seq_num))
                            else:
                                print("        Received Out of Order ACK. Received: " + str(seq) + " Expecting: " + str(seq_num))
                        else:
                            print("        Received incorrect ACK number " + str(seq_num))
                    else:
                        if not (seq_num == 1 and attempt != 1):
                            print("    Attempt " + str(attempt) + " to retransmit packet number " + str(seq_num))

                    if attempt > 1000 and seq_num > 1:
                        print("Transmission ended after trying to retransmit for more than 1000 times")
                        return False

            retransmit_final = True
            attempt_final = 0
            while retransmit_final:
                util.send_packet(self.sender, self.build_frame(b'ENDOFTRANSMISSION', seq_num))
                attempt_final = attempt_final + 1
                rx_buffer = []
                if self.wait_for_ack(self.receiver):
                    self.receiver.read(rx_buffer, self.receiver.getDynamicPayloadSize())
                    crc = rx_buffer[:self.config.CRC_SIZE]
                    seq = int.from_bytes(
                        rx_buffer[self.config.CRC_SIZE:self.config.CRC_SIZE + self.config.SEQ_NUM_SIZE],
                        byteorder='big')
                    ack = rx_buffer[self.config.CRC_SIZE + self.config.SEQ_NUM_SIZE:]
                    seq_ack = rx_buffer[self.config.CRC_SIZE:]
                    if util.check_crc(crc, seq_ack) and seq == seq_num:
                        if bytes(ack) == b'ACK':
                            retransmit_final = False
                            tx_success = True
                            print("TRANSMISSION SUCCESSFUL")
                else:
                    print("    Attempt " + str(attempt_final) + " to retransmit FINAL packet")
                    if attempt_final > 1000:
                        print("Program ended after failing to transmit the EOT message")
                        return False

        # Return true if success
        return True
