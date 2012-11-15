from fpga_sdrlib.config import msg_length_width, msg_width

def stream_to_packets(stream, bits_for_length=msg_length_width, width=msg_width, allow_samples=True):
    header_shift = pow(2, width-1)
    length_shift1 = pow(2, width-1-bits_for_length)
    length_shift2 = pow(2, bits_for_length)
    in_packet = False
    packet_length = None
    packet_pos = None
    packet = None
    packets = []
    for block in stream:
        if block is None:
            continue
        header = block // header_shift
        if header:
            packet_length = block // length_shift1 - header*length_shift2
            if in_packet:
                raise ValueError("Got a header when we weren't expecting it. Pos is {0}. New length is {1}".format(packet_pos, packet_length))
            if packet_length > 0:
                packet_pos = 0
                in_packet = True
                packet = [block]
            else:
                packets.append([block])
        if (not header) and (not in_packet):
            # Treat a sample as a packet of length 1.
            if not allow_samples:
                raise ValueError("No header found when expecting one.")
            packets.append([block])
        if (not header) and in_packet:
            packet.append(block)
            packet_pos += 1
            if packet_pos == packet_length:
                packets.append(packet)
                packet = None
                in_packet = False
                packet_pos = None
    return packets

def stream_to_samples_and_packets(stream, bits_for_length=msg_length_width, width=msg_width):
    header_shift = pow(2, width-1)
    mixed = stream_to_packets(stream, bits_for_length, width, True)
    packets = []
    samples = []
    for p in mixed:
        if len(p) > 1:
            packets.append(p)
        else:
            header = p[0] // header_shift
            if header:
                packets.append(p)
            else:
                samples.append(p[0])
    return samples, packets
            

def make_packet_dict(packets):
    packet_dict = {}
    for p in packets:
        if p[0] in packet_dict:
            raise StandardError("Unlikely clash between packets.  Redo with another random seed.")
        packet_dict[p[0]] = p
    return packet_dict

