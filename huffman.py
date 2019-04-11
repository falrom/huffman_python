"""
usage: python huffman.py command [-h] -i INPUT -o OUTPUT

positional arguments:
  command                       "compress" or "uncompress"

optional arguments:
  -h, --help                    show this help message and exit
  -i INPUT, --input INPUT       Input file path.
  -o OUTPUT, --output OUTPUT    Output file path.
"""


class HufNode():
    def __init__(self, byte=None):
        self.byte = byte
        self.code = None
        self.frequency = 0
        self.parent = None
        self.left_child = None
        self.right_child = None


class HuffmanCodec():
    def __init__(self):
        self.byte_kinds = 0
        self.num_nodes = 0
        self.source_file_len = 0
        self.byte_frequency = None
        self.tree = None
        self.codebook = None

    def reset(self):
        self.__init__()

    def count(self, file_path):
        print('Log: Preproccessing - %s' % file_path)
        byte_dict = {}
        with open(file_path, 'rb') as file:
            byte = file.read(1)
            while len(byte) > 0:
                byte = byte[0]
                if byte in byte_dict:
                    byte_dict[byte] += 1
                else:
                    byte_dict[byte] = 1
                byte = file.read(1)
        self.byte_kinds = len(byte_dict)
        self.num_nodes = 2 * self.byte_kinds - 1
        self.source_file_len = sum(byte_dict.values())
        self.tree = [HufNode() for i in range(self.num_nodes)]
        self.byte_frequency = list(byte_dict.items())

    def build_tree(self):
        print('Log: Building Huffman tree...')
        assert self.tree is not None
        assert self.byte_frequency is not None

        if self.byte_kinds == 1:
            return

        for i, item in enumerate(self.byte_frequency):
            self.tree[i].byte = item[0]
            self.tree[i].frequency = item[1]
        for i in range(self.byte_kinds, self.num_nodes):
            # min_1 <= min_2
            min_1 = self.source_file_len
            min_2 = self.source_file_len
            node_1 = None
            node_2 = None
            for j in range(i):
                if self.tree[j].parent is None:
                    if self.tree[j].frequency >= min_2:
                        continue
                    if self.tree[j].frequency < min_1:
                        min_2 = min_1
                        node_2 = node_1
                        min_1 = self.tree[j].frequency
                        node_1 = j
                    else:
                        min_2 = self.tree[j].frequency
                        node_2 = j
            self.tree[node_1].parent = i
            self.tree[node_2].parent = i
            self.tree[node_1].code = '0'
            self.tree[node_2].code = '1'
            self.tree[i].left_child = node_1
            self.tree[i].right_child = node_2
            self.tree[i].frequency = min_1 + min_2

    def generate_coodbook(self):
        print('Log: Generating coodbook...')
        assert self.tree is not None

        if self.byte_kinds == 1:
            return

        self.codebook = {}
        for i in range(self.byte_kinds):
            byte = self.tree[i].byte
            node = i
            code = ''
            while self.tree[node].parent is not None:
                code = self.tree[node].code + code
                node = self.tree[node].parent
            self.codebook[byte] = code

    def encode(self, file_path_in, file_path_out):
        print('Log: Input  file - %s' % file_path_in)
        print('Log: Output file - %s' % file_path_out)
        print('Log: Encoding...')
        with open(file_path_in, 'rb') as file_in:
            with open(file_path_out, 'wb') as file_out:
                if self.source_file_len == 0:
                    return

                # 1 byte for num_bytes
                if self.byte_kinds >= 256:
                    file_out.write(bytes([0]))
                else:
                    file_out.write(bytes([self.byte_kinds]))

                # 5*num_bytes byte for count_bytes
                for byte, count in self.byte_frequency:
                    file_out.write(bytes([byte]))
                    file_out.write(int(count).to_bytes(4, 'big'))

                # content
                if self.byte_kinds == 1:
                    return
                code_stream = ''
                byte = file_in.read(1)
                while len(byte) > 0:
                    byte = byte[0]
                    code_stream += self.codebook[byte]
                    while len(code_stream) >= 8:
                        code = 0
                        for i in range(8):
                            code <<= 1
                            if code_stream[i] == '1':
                                code |= 1
                        file_out.write(bytes([code]))
                        code_stream = code_stream[8:]
                    byte = file_in.read(1)

                # the left bits:
                if len(code_stream) > 0:
                    code = 0
                    for c in code_stream:
                        code <<= 1
                        if c == '1':
                            code |= 1
                    code <<= 8 - len(code_stream)
                    file_out.write(bytes([code]))

    def decode(self, file_path_in, file_path_out):
        print('Log: Input  file - %s' % file_path_in)
        print('Log: Output file - %s' % file_path_out)
        with open(file_path_in, 'rb') as file_in:
            with open(file_path_out, 'wb') as file_out:
                byte_kinds = file_in.read(1)
                if len(byte_kinds) == 0:
                    return
                self.byte_kinds = byte_kinds[0]
                if self.byte_kinds == 0:
                    self.byte_kinds = 256

                self.byte_frequency = []
                self.source_file_len = 0
                for i in range(self.byte_kinds):
                    byte = file_in.read(1)[0]
                    count = int().from_bytes(file_in.read(4), 'big')
                    self.byte_frequency.append((byte, count))
                    self.source_file_len += count

                if self.byte_kinds == 1:
                    for i in range(self.byte_frequency[0][1]):
                        file_out.write(bytes([self.byte_frequency[0][0]]))
                    return

                self.num_nodes = 2 * self.byte_kinds - 1
                self.tree = [HufNode() for i in range(self.num_nodes)]
                self.build_tree()

                print('Log: Decoding...')
                writen_len = 0
                node = self.num_nodes - 1
                byte = file_in.read(1)
                while len(byte) > 0:
                    byte = byte[0]
                    for i in range(8):
                        if byte & 128:
                            node = self.tree[node].right_child
                        else:
                            node = self.tree[node].left_child
                        if node < self.byte_kinds:
                            file_out.write(bytes([self.tree[node].byte]))
                            writen_len += 1
                            if writen_len >= self.source_file_len:
                                return
                            node = self.num_nodes - 1
                        byte <<= 1
                    byte = file_in.read(1)

    def compress(self, file_path_in, file_path_out=None):
        self.reset()
        print('****************compress****************')
        if file_path_out is None:
            file_path_out = file_path_in + '.hfm'

        self.count(file_path_in)
        self.build_tree()
        self.generate_coodbook()
        self.encode(file_path_in, file_path_out)
        print('****************************************')

    def uncompress(self, file_path_in, file_path_out):
        self.reset()
        print('***************uncompress***************')
        self.decode(file_path_in, file_path_out)
        print('****************************************')


def test():
    hc = HuffmanCodec()

    file_path_source = './test_cases/test.jpg'
    file_path_compressed = './test_cases/test.jpg.hfm'
    file_path_uncompressed = './test_cases/test.jpg.hfm.jpg'
    hc.reset()
    hc.compress(file_path_source, file_path_compressed)
    hc.uncompress(file_path_compressed, file_path_uncompressed)

    file_path_source = './test_cases/empty.file'
    file_path_compressed = './test_cases/empty.file.hfm'
    file_path_uncompressed = './test_cases/empty.file.hfm.file'
    hc.reset()
    hc.compress(file_path_source, file_path_compressed)
    hc.uncompress(file_path_compressed, file_path_uncompressed)

    file_path_source = './test_cases/one.file'
    file_path_compressed = './test_cases/one.file.hfm'
    file_path_uncompressed = './test_cases/one.file.hfm.file'
    hc.reset()
    hc.compress(file_path_source, file_path_compressed)
    hc.uncompress(file_path_compressed, file_path_uncompressed)


if __name__ == '__main__':
    # # Code test:
    # test()
    # exit()

    # Run:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('command', help='"compress" or "uncompress"')
    parser.add_argument('-i', '--input', required=True, help='Input file path.')
    parser.add_argument('-o', '--output', required=True, help='Output file path.')

    args = parser.parse_args()
    hc = HuffmanCodec()
    if args.command == 'compress':
        hc.compress(args.input, args.output)
    elif args.command == 'uncompress':
        hc.uncompress(args.input, args.output)
    else:
        print('Error: Unknown command')
