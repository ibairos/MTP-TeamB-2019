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

from conf import conf_nm
from conf import conf_srm_receiver, conf_srm_sender
from conf import conf_burst_receiver, conf_burst_sender
from conf import pins

from const import mode, role, const

from NM import network_mode
from conf.conf_nm import team_configuration
from GPIO_Manager_NM import GPIOManager


# Initialization
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Global variables
SENDER = None
RECEIVER = None

MODE = mode.NONE
ROLE = role.NONE

GO = False
TX_SUCCESS = False


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
    sw_role = GPIO.input(pins.SW_ROLE)
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
    mode_sw = GPIO.input(pins.SW_MODE)

    if mode_sw == 0:
        MODE = mode.SRM
    elif mode_sw == 1:
        MODE = mode.NM
    else:
        MODE = mode.NONE
        return False

    return True


def setup_gpio():
    # Setup inputs
    GPIO.setup(pins.SW_ROLE, GPIO.IN)
    GPIO.setup(pins.SW_MODE, GPIO.IN)
    GPIO.setup(pins.BTN_GO, GPIO.IN)
    # Setup outputs
    GPIO.setup(pins.LED_WAIT, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(pins.LED_PROCESS, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(pins.LED_SUCCESS, GPIO.OUT, initial=GPIO.LOW)


def select_conf():
    if ROLE == role.TX:
        if MODE == mode.SRM:
            print("Entering SRM-TX Mode...")
            return conf_srm_sender
        elif MODE == mode.NM:
            print("Entering NM...")
            return conf_nm
        elif MODE == mode.BURST:
            print("Entering BURST-TX Mode...")
            return conf_burst_sender
        elif MODE == mode.NONE:
            print("No mode selected. Exiting...")
            exit(0)
    elif ROLE == role.RX:
        if MODE == mode.SRM:
            print("Entering SRM-RX Mode...")
            return conf_srm_receiver
        elif MODE == mode.NM:
            print("Entering NM Mode...")
            return conf_nm
        elif MODE == mode.BURST:
            print("Entering BURST-RX Mode...")
            return conf_burst_receiver
        elif MODE == mode.NONE:
            print("No mode selected. Exiting...")
            exit(0)
    else:
        print("No role selected. Exiting...")
        exit(0)


def start_process_blink():
    blink_thread = Thread(target=blink_process, args=(const.PROCESS_BLINK_PERIOD,))
    blink_thread.start()


def start_wait_blink():
    blink_thread = Thread(target=blink_wait, args=(const.WAIT_BLINK_PERIOD,))
    blink_thread.start()


def blink_process(blink_period):
    while GO:
        GPIO.output(pins.LED_PROCESS, 1)
        time.sleep(blink_period)
        GPIO.output(pins.LED_PROCESS, 0)
        time.sleep(blink_period)


def blink_wait(blink_period):
    while not TX_SUCCESS and not GO:
        GPIO.output(pins.LED_WAIT, 1)
        time.sleep(blink_period)
        GPIO.output(pins.LED_WAIT, 0)
        time.sleep(blink_period)


def set_success_led(code):
    GPIO.output(pins.LED_SUCCESS, code)


def main():
    global GO, TX_SUCCESS

    setup_gpio()

    while not (check_mode() and check_role()):
        print("Mode and role checked unsuccessfully. Retrying...")
        time.sleep(0.5)

    if MODE is mode.NM:
        print("Entered NM code")
        led_manager = GPIOManager()
        network_mode.start(ROLE, led_manager, team_configuration)

    ####################################################
    # This code will not be executed if the mode is NM #
    ####################################################

    # Basic init
    program_ended = False
    execution_number = 0

    while not program_ended and MODE is not mode.NM:
        # Increment and print execution number
        execution_number = execution_number + 1
        print("Execution number " + str(execution_number) + " started")
        execution_ended = False

        while not execution_ended:
            # If there is any errors, we restart the cycle and read the parameters again
            if not check_role():
                break
            if not check_mode():
                break

            # Read proper configuration file
            config_file = select_conf()

            # Initialize radios and tx/rx devices
            init_radios(config_file)
            if ROLE == role.TX:
                device = Sender(config_file, SENDER, RECEIVER)
            elif ROLE == role.RX:
                device = Receiver(config_file, SENDER, RECEIVER)
            else:
                break

            # Show program is waiting for the GO
            start_wait_blink()
            print("Waiting for the GO...")

            # Wait until GO is pushed
            while not GO:
                go_sw = GPIO.input(pins.BTN_GO)
                if go_sw == 0:
                    GO = True
                    print("GO pushed, starting transmission/reception...")
                else:
                    time.sleep(0.05)

            # Clear output folders
            print("Clearing outputs...")
            util.clear_outputs(config_file)

            # Start tx/rx
            if ROLE == role.TX:
                start_process_blink()
                success = device.transmit()
            elif ROLE == role.RX:
                start_process_blink()
                success = device.receive()
            else:
                break

            # Set success LED according to the result
            GO = False
            if success:
                TX_SUCCESS = True
                set_success_led(const.CODE_SUCCESS)
            else:
                set_success_led(const.CODE_ERROR)

            # Wait for the user to see that the program has ended successfully
            # If ANOTHER EXECUTION is desired, GO must be pushed
            # If END OF PROGRAM is desired, NOTHING should be done
            while not execution_ended:
                go_sw = GPIO.input(pins.BTN_GO)
                if go_sw == 0:
                    execution_ended = True
                    print("GO pushed, ending execution ...")
                else:
                    time.sleep(0.05)

        # Print the success of the execution
        if TX_SUCCESS:
            print("Execution " + str(execution_number) + " ended SUCCESSFULLY")
        else:
            print("Execution " + str(execution_number) + " ended WITH ERRORS")


if __name__ == '__main__':
    main()
