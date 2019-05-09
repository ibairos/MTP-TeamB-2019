#!/usr/bin/python3
#
# Main part of the MTP Team B code
# This version combines all of the other functions developed for the individual parts
# Author: Ibai Ros
# Date: 08/05/2019
# Version: 1.0


import time
import RPi.GPIO as GPIO
from threading import Thread

from src import util

from src.sender import Sender
from src.receiver import Receiver

from conf import conf_qm_receiver, conf_qm_sender
from conf import conf_srm_receiver, conf_srm_sender
from conf import conf_mrm_receiver, conf_mrm_sender
from conf import conf_burst_receiver, conf_burst_sender
from conf import conf_general

from const import mode, role

# Sleeping for 10 secs until system wakes up
time.sleep(10)

# Initialization
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Global variables
SENDER = None
RECEIVER = None

MODE = mode.NONE
ROLE = role.NONE

GO = False


def init_radios(config):
    global SENDER, RECEIVER
    
    # Initialize the sender radio and print details
    SENDER = util.initialize_radios(config.SENDER_CE, config.SENDER_CSN, config.SENDER_CHANNEL, config)
    SENDER.openWritingPipe(config.SENDER_PIPE)
    print("Sender Information")
    SENDER.printDetails()

    # Initialize the receiver radio and print details
    RECEIVER = util.initialize_radios(config.RECEIVER_CE, config.RECEIVER_CSN, config.RECEIVER_CHANNEL, config)
    RECEIVER.openReadingPipe(0, config.RECEIVER_PIPE)
    print("Receiver Information")
    RECEIVER.printDetails()


def check_role():
    global ROLE
    sw_role = GPIO.input(conf_general.SW_ROLE)
    if sw_role == 0:
        ROLE = role.RX
        return True
    elif sw_role == 1:
        ROLE = role.TX
        return True
    else:
        return False


def check_mode():
    global MODE
    MODE = mode.SRM
    return True


def setup_gpio():
    # Setup inputs
    GPIO.setup(conf_general.SW_ROLE, GPIO.IN)
    GPIO.setup(conf_general.SW_GO, GPIO.IN)
    # Setup outputs
    GPIO.setup(conf_general.LED_RX_ROLE, GPIO.OUT)
    GPIO.setup(conf_general.LED_TX_ROLE, GPIO.OUT)
    GPIO.setup(conf_general.LED_TX_RX_PROCESS, GPIO.OUT)


def select_conf():
    if ROLE == role.TX:
        if MODE == mode.QM:
            print("Entering QM-TX Mode...")
            return conf_qm_sender
        elif MODE == mode.SRM:
            print("Entering SRM-TX Mode...")
            return conf_srm_sender
        elif MODE == mode.MRM:
            print("Entering MRM-TX Mode...")
            return conf_mrm_sender
        elif MODE == mode.BURST:
            print("Entering BURST-TX Mode...")
            return conf_burst_sender
        elif MODE == mode.NONE:
            print("No mode selected. Exiting...")
            exit(0)
    elif ROLE == role.RX:
        if MODE == mode.QM:
            print("Entering QM-RX Mode...")
            return conf_qm_receiver
        elif MODE == mode.SRM:
            print("Entering SRM-RX Mode...")
            return conf_srm_receiver
        elif MODE == mode.MRM:
            print("Entering MRM-RX Mode...")
            return conf_mrm_receiver
        elif MODE == mode.BURST:
            print("Entering BURST-RX Mode...")
            return conf_burst_receiver
        elif MODE == mode.NONE:
            print("No mode selected. Exiting...")
            exit(0)
    else:
        print("No role selected. Exiting...")
        exit(0)


def start_tx_rx_blink():
    blink_thread = Thread(target=blink, args=(conf_general.TX_RX_BLINK_PERIOD,))
    blink_thread.start()


def start_wait_blink():
    blink_thread = Thread(target=blink, args=(conf_general.WAIT_BLINK_PERIOD,))
    blink_thread.start()


def blink(blink_period):
    while GO:
        GPIO.output(conf_general.LED_TX_RX_PROCESS, 1)
        time.sleep(blink_period)
        GPIO.output(conf_general.LED_TX_RX_PROCESS, 0)
        time.sleep(blink_period)


def set_success_led():
    GPIO.output(conf_general.LED_TX_RX_PROCESS, 1)
    GPIO.output(conf_general.LED_TX_ROLE, 1)


def main():
    global GO

    setup_gpio()

    check_role()
    check_mode()

    config_file = select_conf()

    init_radios(config_file)

    device = None

    if ROLE == role.TX:
        device = Sender(config_file, SENDER, RECEIVER)
    elif ROLE == role.RX:
        device = Receiver(config_file, SENDER, RECEIVER)
    else:
        exit(0)

    while not GO:
        go_sw = GPIO.input(conf_general.SW_GO)
        if go_sw == 1:
            GO = True
            print("Go pushed, starting transmission...")
        else:
            time.sleep(0.1)

    util.clear_outputs(config_file)

    success = False
    if ROLE == role.TX:
        start_tx_rx_blink()
        success = device.transmit()
    elif ROLE == role.RX:
        start_tx_rx_blink()
        success = device.receive()
    else:
        exit(0)

    if success:
        GO = False
        set_success_led()


if __name__ == '__main__':
    main()
