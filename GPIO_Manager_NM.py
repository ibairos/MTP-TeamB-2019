import RPi.GPIO as GPIO
from conf import conf_general

class GPIOManager:
    def __init__(self):
        # Initialization
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        # Setup inputs
        GPIO.setup(conf_general.SW_ROLE, GPIO.IN)
        GPIO.setup(SW_GO, GPIO.IN)
        # Setup outputs
        GPIO.setup(conf_general.LED_RX_ROLE, GPIO.OUT)
        GPIO.setup(conf_general.LED_TX_ROLE, GPIO.OUT)
        GPIO.setup(conf_general.LED_TX_RX_PROCESS, GPIO.OUT)
        # Setting up LEDs to off
        GPIO.output(conf_general.LED_TX_RX_PROCESS, 0)
        GPIO.output(conf_general.LED_TX_ROLE, 0)
        GPIO.output(conf_general.LED_RX_ROLE, 0)

    def network_starting(self):
        self.leds_off(self)
        GPIO.output(conf_general.LED_TX_RX_PROCESS, 1)

    def network_tx(self):
        self.leds_off(self)
        GPIO.output(conf_general.LED_TX_ROLE, 1)

    def network_rx(self):
        self.leds_off(self)
        GPIO.output(conf_general.LED_RX_ROLE, 1)

    def network_error(self):
        self.leds_off(self)
        GPIO.output(conf_general.LED_RX_ROLE, 1)
        GPIO.output(conf_general.LED_TX_ROLE, 1)
        GPIO.output(conf_general.LED_TX_RX_PROCESS, 1)

    def network_succes(self):
        self.leds_off(self)
        GPIO.output(conf_general.LED_RX_ROLE, 1)
        GPIO.output(conf_general.LED_TX_ROLE, 1)
        GPIO.output(conf_general.LED_TX_RX_PROCESS, 1)


    def leds_off(self):
        GPIO.output(conf_general.LED_TX_RX_PROCESS, 0)
        GPIO.output(conf_general.LED_TX_ROLE, 0)
        GPIO.output(conf_general.LED_RX_ROLE, 0)




