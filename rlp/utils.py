import struct


ALL_BYTES = {
    i: struct.pack('B', i)
    for i in range(256)
}
