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
        payload_tx_success = False
        rcv_seq_num = 0

        # Send file
        while not tx_success:
            first_packet_transmitted = False
            while not first_packet_transmitted:
                util.send_packet(self.sender, self.build_frame(payload_list[0], 1))
                rx_buffer = []
                if self.wait_for_ack(self.receiver):
                    self.receiver.read(rx_buffer, self.receiver.getDynamicPayloadSize())
                    crc = rx_buffer[:self.config.CRC_SIZE]
                    ack_seq_num = int.from_bytes(
                        rx_buffer[self.config.CRC_SIZE:self.config.CRC_SIZE + self.config.SEQ_NUM_SIZE],
                        byteorder='big')
                    ack = rx_buffer[self.config.CRC_SIZE + self.config.SEQ_NUM_SIZE:]
                    seq_ack = rx_buffer[self.config.CRC_SIZE:]
                    if util.check_crc(crc, seq_ack):
                        if bytes(ack) == b'ACK' and ack_seq_num == 1:
                            print("Packet 1 transmitted successfully")
                            rcv_seq_num = 1
                            first_packet_transmitted = True
                        else:
                            print("        Unknown error when transmitting packet number 1")
                    else:
                        print("        Received corrupt ACK")

            while not payload_tx_success:
                chunks_left = len(payload_list) - rcv_seq_num
                if chunks_left >= self.config.BURST_SIZE:
                    burst_size = self.config.BURST_SIZE
                else:
                    burst_size = chunks_left
                for sent_seq in range((rcv_seq_num + 1), (rcv_seq_num + 1) + burst_size):
                    util.send_packet(self.sender, self.build_frame(payload_list[sent_seq - 1], sent_seq))
                rx_buffer = []
                if self.wait_for_ack(self.receiver):
                    self.receiver.read(rx_buffer, self.receiver.getDynamicPayloadSize())
                    crc = rx_buffer[:self.config.CRC_SIZE]
                    ack_seq_num = int.from_bytes(
                        rx_buffer[self.config.CRC_SIZE:self.config.CRC_SIZE + self.config.SEQ_NUM_SIZE],
                        byteorder='big')
                    ack = rx_buffer[self.config.CRC_SIZE + self.config.SEQ_NUM_SIZE:]
                    seq_ack = rx_buffer[self.config.CRC_SIZE:]
                    if util.check_crc(crc, seq_ack):
                        if bytes(ack) == b'ACK':
                            print("Packets " + str(rcv_seq_num + 1) + "-" + str(ack_seq_num)
                                  + " transmitted successfully (" + str(ack_seq_num - rcv_seq_num) + " OK)")
                            rcv_seq_num = ack_seq_num
                            if rcv_seq_num == len(payload_list):
                                payload_tx_success = True
                        else:
                            print("        Unknown error when transmitting packet number " + str(ack_seq_num))
                    else:
                        print("        Received corrupt ACK")
                else:
                    print("    Attempt to retransmit from packet number " + str(rcv_seq_num + 1))

            retransmit_final = True
            attempt_final = 0
            final_seq_num = rcv_seq_num + 1
            while retransmit_final:
                util.send_packet(self.sender, self.build_frame(b'ENDOFTRANSMISSION', final_seq_num))
                attempt_final = attempt_final + 1
                rx_buffer = []
                if self.wait_for_ack(self.receiver):
                    self.receiver.read(rx_buffer, self.receiver.getDynamicPayloadSize())
                    crc = rx_buffer[:self.config.CRC_SIZE]
                    ack_seq_num = int.from_bytes(
                        rx_buffer[self.config.CRC_SIZE:self.config.CRC_SIZE + self.config.SEQ_NUM_SIZE],
                        byteorder='big')
                    ack = rx_buffer[self.config.CRC_SIZE + self.config.SEQ_NUM_SIZE:]
                    seq_ack = rx_buffer[self.config.CRC_SIZE:]
                    if util.check_crc(crc, seq_ack) and ack_seq_num == final_seq_num:
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
