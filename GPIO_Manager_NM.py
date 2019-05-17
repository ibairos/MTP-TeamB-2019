import RPi.GPIO as GPIO
from conf import pins


class GPIOManager:
    def __init__(self):
        print("Initialized GPIO manager")

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

    def network_success(self):
        self.leds_off()
        GPIO.output(pins.LED_WAIT, 1)
        GPIO.output(pins.LED_PROCESS, 1)
        GPIO.output(pins.LED_SUCCESS, 1)

    def leds_off(self):
        GPIO.output(pins.LED_WAIT, 0)
        GPIO.output(pins.LED_PROCESS, 0)
        GPIO.output(pins.LED_SUCCESS, 0)




