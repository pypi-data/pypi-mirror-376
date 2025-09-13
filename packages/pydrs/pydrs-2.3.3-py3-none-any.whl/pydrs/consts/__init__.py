ETH_RESET_CMD = b""
ETH_ANSWER_ERR = 0x22
ETH_ANSWER_NOQUEUE = 0x23
DP_MODULE_MAX_COEFF = 16
NUM_MAX_COEFFS_DSP = 12
NUM_DSP_CLASSES = 7

ETH_CMD_REQUEST = b"\x11"
ETH_CMD_WRITE = b"\x03"


COM_FUNCTION = "\x50"
COM_WRITE_VAR = "\x20"
COM_CREATE_BSMP_GROUP = "\x30"
COM_GET_BSMP_GROUP_LIST = "\x04"
COM_GET_BSMP_GROUP_VARS = "\x06"
COM_READ_BSMP_GROUP_VALUES = "\x12"

WRITE_FLOAT_SIZE_PAYLOAD = "\x00\x05"
WRITE_DOUBLE_SIZE_PAYLOAD = "\x00\x03"
COM_READ_VAR = "\x10\x00\x01"
COM_REQUEST_CURVE = "\x40"
COM_SEND_WFM_REF = "\x41"

UDC_FIRMWARE_VERSION = "0.45.00    05/23"

ufm_offset = {
    "serial": 0,
    "calibdate": 4,
    "variant": 9,
    "rburden": 10,
    "calibtemp": 12,
    "vin_gain": 14,
    "vin_offset": 16,
    "iin_gain": 18,
    "iin_offset": 20,
    "vref_p": 22,
    "vref_n": 24,
    "gnd": 26,
}

type_format = {
    "uint8_t": "BBHBB",
    "uint16_t": "BBHHB",
    "uint32_t": "BBHIB",
    "float": "BBHfB",
}

bytes_format = {"Uint16": "H", "Uint32": "L", "Uint64": "Q", "float": "f"}

type_size = {"uint8_t": 6, "uint16_t": 7, "uint32_t": 9, "float": 9}

num_blocks_curves_fax = [16, 16, 16]
size_curve_block = [1024, 1024, 1024]

hradc_variant = [
    "HRADC-FBP",
    "HRADC-FAX-A",
    "HRADC-FAX-B",
    "HRADC-FAX-C",
    "HRADC-FAX-D",
]

hradc_input_types = [
    "GND",
    "Vref_bipolar_p",
    "Vref_bipolar_n",
    "Temp",
    "Vin_bipolar_p",
    "Vin_bipolar_n",
    "Iin_bipolar_p",
    "Iin_bipolar_n",
]

num_dsp_modules = [4, 4, 4, 6, 8, 4, 2, 2]
num_coeffs_dsp_modules = [0, 1, 1, 4, 8, 16, 2]
dsp_classes_names = [
    "DSP_Error",
    "DSP_SRLim",
    "DSP_LPF",
    "DSP_PI",
    "DSP_IIR_2P2Z",
    "DSP_IIR_3P3Z",
    "DSP_VdcLink_FeedForward",
    "DSP_Vect_Product",
]

num_blocks_curves_fbp = [4, 4, 4]
