from libraries.lib_nrf24 import NRF24

# Packet size parameters
DATA_SIZE = 28
SEQ_NUM_SIZE = 2
CRC_SIZE = 2

# Burst size
BURST_SIZE = 20

# Timeouts
DATA_TIMEOUT = 0.01
ACK_TIMEOUT = 0.01

# Compression
COMPRESSION_LEVEL = 6

# Input Filepath (Only used by sender)
IN_PATH_RAW = "/home/pi/MTP-TeamB-2019/files/input/burst/raw/"
IN_PATH_COMPRESSED = "/home/pi/MTP-TeamB-2019/files/input/burst/compressed/"
DEFAULT_FILENAME_RAW = "file.txt"
DEFAULT_FILENAME_COMPRESSED = "file.7z"
IN_FILEPATH_RAW = IN_PATH_RAW + DEFAULT_FILENAME_RAW
IN_FILEPATH_COMPRESSED = IN_PATH_COMPRESSED + DEFAULT_FILENAME_COMPRESSED

# Output Filepath (Just for compatibility)
OUT_PATH_RAW = "/home/pi/MTP-TeamB-2019/files/output/burst/raw/"
OUT_PATH_COMPRESSED = "/home/pi/MTP-TeamB-2019/files/output/burst/compressed/"
OUT_FILEPATH_RAW = OUT_PATH_RAW + DEFAULT_FILENAME_RAW
OUT_FILEPATH_COMPRESSED = OUT_PATH_COMPRESSED + DEFAULT_FILENAME_COMPRESSED

# Channels / pipes
channels = [30, 40]
pipes = [[0xe7, 0xe7, 0xe7, 0xe7, 0xe7], [0xc2, 0xc2, 0xc2, 0xc2, 0xc2]]

SENDER_CHANNEL = channels[0]
SENDER_PIPE = pipes[0]

RECEIVER_CHANNEL = channels[1]
RECEIVER_PIPE = pipes[1]

# Radio parameters
SENDER_CSN = 25
SENDER_CE = 0
RECEIVER_CSN = 22
RECEIVER_CE = 1

# Power and bitrate
POWER = NRF24.PA_HIGH
BITRATE = NRF24.BR_2MBPS
