import RPi.GPIO as GPIO
from conf import pins

class GPIOManager:
    def __init__(self):
        # Initialization
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        # Setup inputs
        GPIO.setup(pins.SW_ROLE, GPIO.IN)
        GPIO.setup(pins.SW_MODE, GPIO.IN)
        GPIO.setup(pins.BTN_GO, GPIO.IN)
        # Setup outputs
        GPIO.setup(pins.LED_WAIT, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(pins.LED_PROCESS, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(pins.LED_SUCCESS, GPIO.OUT, initial=GPIO.LOW)

    def network_starting(self):
        self.leds_off()
        GPIO.output(pins.LED_WAIT, 1)

    def network_tx(self):
        self.leds_off()
        GPIO.output(pins.LED_PROCESS, 1)

    def network_rx(self):
        self.leds_off()
        GPIO.output(pins.LED_PROCESS, 1)
        GPIO.output(pins.LED_WAIT, 1)

    def network_error(self):
        self.leds_off()

    def network_succes(self):
        self.leds_off()
        GPIO.output(pins.LED_SUCCESS, 1)

    def leds_off(self):
        GPIO.output(pins.LED_WAIT, 0)
        GPIO.output(pins.LED_PROCESS, 0)
        GPIO.output(pins.LED_SUCCESS, 0)




