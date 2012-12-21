import random

from fpga_sdrlib.config import msg_length_width, msg_width, msg_errorcode_width

def generate_header(length, bits_for_length, width, target=None):
    if target is None:
        info_max = int(pow(2, width-1-bits_for_length)-1)
        info = random.randint(0, info_max)
    else:
        info = target * pow(2, msg_errorcode_width)
    header = (1 << int(width-1)) + (length << int(width-1-bits_for_length)) + info
    return header

def generate_random_packet(length, bits_for_length, width):
    packet = []
    packet.append(generate_header(length, bits_for_length, width))
    block_max = int(pow(2, width-1)-1)
    for j in range(length):
        d = random.randint(0, block_max)
        packet.append(d)
    return packet

def packet_from_content(content, bits_for_length=msg_length_width,
                        width=msg_width, target=0):
    l = len(content)
    packet = []
    packet.append(generate_header(l, bits_for_length, width, target))
    packet.extend(content)
    return packet

def generate_random_packets(max_length, n_packets, bits_for_length, width, prob_start=1, myrand=random.Random(), none_sample=True):
    """
    Generate a data stream containing a bunch of random packets.
    The lengths are distributed uniformly up to max_length-1.

    """
    data = []
    packets = []
    sample_max = int(pow(2, width-2))
    assert(pow(2, bits_for_length) >= max_length)
    for i in range(n_packets):
        while (myrand.random() > prob_start):
            if none_sample:
                data.append(None)
            else:
                data.append(myrand.randint(0, sample_max))
        l = myrand.randint(0, max_length)
        packet = generate_random_packet(l, bits_for_length, width)
        data.extend(packet)
        packets.append(packet)
    return data, packets

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
    if packet is not None:
        print(packet)
        raise ValueError("Incomplete packets")
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

