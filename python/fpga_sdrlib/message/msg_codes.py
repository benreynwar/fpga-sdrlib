from fpga_sdrlib import config

errorcode_shift = 1
errorcode_mod = pow(2, config.msg_errorcode_width)
modulecode_shift = errorcode_shift * errorcode_mod
modulecode_mod = pow(2, config.msg_modulecode_width)
formatcode_shift = modulecode_shift * modulecode_mod
formatcode_mod = pow(2, config.msg_formatcode_width)
length_shift = formatcode_shift * formatcode_mod
length_mod = pow(2, config.msg_length_width)
header_shift = length_shift * length_mod

def parse_packet(packet):
    header = packet[0]
    is_header = header//header_shift
    length = (header//length_shift) % length_mod
    formatcode = (header//formatcode_shift) % formatcode_mod
    modulecode = (header//modulecode_shift) % modulecode_mod
    errorcode = (header//errorcode_shift) % errorcode_mod
    length = (header//length_shift) % length_mod
    if not is_header:
        raise StandardError("Header of packet thinks it's not a header.")
    if len(packet) != length+1:
        raise StandardError("Packet is of length {0} but thinks it is of length {1}.".format(len(packet), length+1))
    if modulecode not in packet_codes:
        raise StandardError("The module code {0} is unknown.".format(module_code))
    if errorcode not in packet_codes[modulecode]:
        raise StandardError("The error code {0} is unknown for module {1}".format(errorcode, modulecode))
    return packet_codes[modulecode][errorcode](packet)
    
def nothing_test_packet(packet):
    if len(packet) != 2:
        raise StandardError("Packet of type 0, 0 should have length 2")
    return "nothing: received {0}".format(packet[1])

packet_codes = {
    0: {
        0: nothing_test_packet,
        }
    }
