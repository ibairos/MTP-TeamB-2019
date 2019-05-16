from bunch import Bunch
import logging
from RF24 import *


team_configuration = Bunch({
        "File_Path_Input": "/home/pi/MTP-TeamB-2019/files/input/nm/file.txt",
        "File_Path_Output": "/home/pi/MTP-TeamB-2019/files/input/nm/file.txt",
        "Log_Path": "/home/pi/MTP-TeamB-2019/logs/logger.log",
        "Log_Level": logging.DEBUG,
        "Tx_CS": RPI_V2_GPIO_P1_22,
        "Tx_CSN": BCM2835_SPI_CS0,
        "Rx_CS": RPI_V2_GPIO_P1_15,
        "Rx_CSN": BCM2835_SPI_CS1,
        "address": 3})
