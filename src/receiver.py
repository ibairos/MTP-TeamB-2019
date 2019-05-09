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


class Receiver(object):
    def __init__(self, config, sender, receiver):
        self.config = config
        self.sender = sender
        self.receiver = receiver

    def wait_for_data(self, receiver):
        """ This is a blocking function that waits
        until the ACK is available in the receiver pipe
        or until the timeout expires. """

        start_time = time.time()
        while not receiver.available(self.config.RECEIVER_PIPE):
            if time.time() - start_time < self.config.DATA_TIMEOUT:
                time.sleep(0.001)
            else:
                return False
        return True

    def build_frame(self, payload, seq_num):
        """ Function that builds the frame in bytes """

        seq = seq_num.to_bytes(self.config.SEQ_NUM_SIZE, byteorder='big')
        crc = util.calculate_crc(self.config, seq + payload)

        return crc + seq + payload

    def receive(self):
        """ This main function initializes the radios,
        receives the file and stores it in memory. """

        # Initialize loop variables and functions
        rx_success = False
        seq_num = 1
        payload_list = list()
        self.receiver.startListening()

        # Receive file
        while not rx_success:
            rx_buffer = []
            received_something = False
            while not received_something:
                if self.wait_for_data(self.receiver):
                    self.receiver.read(rx_buffer, self.receiver.getDynamicPayloadSize())
                    received_something = True

            payload = rx_buffer[self.config.CRC_SIZE + self.config.SEQ_NUM_SIZE:]
            if bytes(payload) != b'ENDOFTRANSMISSION':
                crc = rx_buffer[:self.config.CRC_SIZE]
                seq = int.from_bytes(
                    rx_buffer[self.config.CRC_SIZE:self.config.CRC_SIZE + self.config.SEQ_NUM_SIZE],
                    byteorder='big')
                seq_payload = rx_buffer[self.config.CRC_SIZE:]
                if util.check_crc(crc, seq_payload):
                    if seq == seq_num:
                        util.send_packet(self.sender, self.build_frame(b'ACK', seq_num))
                        if seq_num == 1 and len(payload_list) == 0:
                            payload_list.append(bytes(payload))
                            print("Packet number " + str(seq_num) + " received successfully")
                    elif seq == seq_num + 1:
                        seq_num = seq_num + 1
                        payload_list.append(bytes(payload))
                        util.send_packet(self.sender, self.build_frame(b'ACK', seq_num))
                        print("Packet number " + str(seq_num) + " received successfully")
                    else:
                        print("        Receiver out of order packet. Rcv: " + str(seq) + " Exp: " + str(seq_num + 1))
                else:
                    util.send_packet(self.sender, self.build_frame(b'ERROR', seq_num))
                    print("    Packet number " + str(seq_num) + " received incorrectly")
            else:
                seq_num = seq_num + 1
                util.send_packet(self.sender, self.build_frame(b'ACK', seq_num))
                rx_success = True
                print("RECEPTION SUCCESSFUL")

        # Save and uncompress file
        try:
            util.write_file(self.config.OUT_FILEPATH_COMPRESSED, payload_list)
            util.uncompress_file(self.config)
        except IOError:
            print("ERROR when saving the file")
            return False

        # Return true if successful
        return True
