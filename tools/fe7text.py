"""Decode FE7U/FE8U Huffman text."""
import struct

class TextDecoder:
    def __init__(self, data, root_pp, table_pp, text_table):
        self.d = data
        self.root = struct.unpack_from('<I', data, struct.unpack_from('<I', data, root_pp)[0] - 0x08000000)[0] - 0x08000000
        self.table = struct.unpack_from('<I', data, table_pp)[0] - 0x08000000
        self.text_table = text_table

    def decode(self, tid):
        p = struct.unpack_from('<I', self.d, self.text_table + 4 * tid)[0]
        if p & 0x80000000:
            p &= 0x7FFFFFFF
            o = p - 0x08000000; out = bytearray()
            while self.d[o]:
                out.append(self.d[o]); o += 1
            return out.decode('latin1')
        o = p - 0x08000000
        out = bytearray()
        node = self.root
        bits = 0; cnt = 0
        while True:
            if cnt == 0:
                bits = self.d[o]; o += 1; cnt = 8
            b = bits & 1; bits >>= 1; cnt -= 1
            idx = struct.unpack_from('<H', self.d, node + (2 if b else 0))[0]
            node = self.table + idx * 4
            v = struct.unpack_from('<i', self.d, node)[0]
            if v >= 0:
                continue
            v &= 0xFFFF
            if v & 0xFF00:
                out += bytes([v & 0xFF, v >> 8])
            else:
                if (v & 0xFF) == 0:
                    break
                out.append(v & 0xFF)
            node = self.root
            if len(out) > 4000:
                break
        return out.decode('latin1')

def fe7(data):
    return TextDecoder(data, 0x6B8, 0x6BC, 0xB808AC)
