import os
import sys
from binary import BinaryReader


def is_dbcs_lead_byte(byte: int) -> bool:
    return 0x81 <= byte <= 0x9f or 0xe0 <= byte <= 0xfc

with open(sys.argv[1], "rb") as f:
    reader = BinaryReader(f.read())

count = reader.read_unsigned_int_32_le()

headers = []

split_headers = []

for _ in range(count):
    headers.append(reader.read_bytes_into_reader(72))

v13 = reader.read_unsigned_int_16_le()
unk = reader.read_unsigned_int_16_le()

folder = sys.argv[1] + "_extracted"
os.makedirs(folder, exist_ok=True)

content = reader.read_bytes_into_reader(v13)

for header in headers:
    title = header.read_c_string_with_size(72 - 8, "shift-jis").strip("\x00")
    header.skip(4)
    offset = header.read_unsigned_int_32_le()
    
    split_headers.append((title, offset))


for index, (title, offset) in enumerate(split_headers):
    reader.goto(offset)
    if len(split_headers) == 0:
        data = content
    else:
        if index + 1 < len(split_headers):
            data = content.read_bytes_into_reader(split_headers[index + 1][1] - offset)
        else:
            data = content.read_to_eof_into_reader()
    
    texts = []
    
    while not data.eof:
        command = data.read_byte()
        match command:
            case 0:
                now_pos = data.pos
                for _ in range(32):
                    string = data.read_c_string_bytes()
                    if len(string):
                        if is_dbcs_lead_byte(string[0]):
                            texts.append(string.decode("shift-jis").strip("\x00"))
                            now_pos = data.pos
                        else:
                            data.goto(now_pos)
                    else:
                        data.goto(now_pos)
            case 1:
                pass
            case 2:
                now_pos = data.pos
                for _ in range(32):
                    string = data.read_c_string_bytes()
                    if len(string):
                        if is_dbcs_lead_byte(string[0]) or string[0] == 65:
                            texts.append(string.decode("shift-jis").strip("\x00"))
                            now_pos = data.pos
                        else:
                            data.goto(now_pos)
                    else:
                        data.goto(now_pos)
            case 3:
                data.skip(4)
            case 5:
                # cg load
                index_ = data.read_unsigned_int_16_le()
            case 7:
                data.skip(2)
            case 10:
                # load wav
                index_ = data.read_unsigned_int_16_le()
                wav_name = data.read_c_string("shift-jis")
            case 11:
                data.skip(2)
            case 13:
                # load bmp
                index_ = data.read_unsigned_int_16_le()
                bmp_name = data.read_c_string("shift-jis")
            case 14:
                # load png
                index_ = data.read_unsigned_int_16_le()
                png_name = data.read_c_string("shift-jis")
            case 15:
                data.skip(2)
            case 16:
                data.skip(2)
            case 17:
                data.skip(28)
            case 21:
                data.skip(12)
            case 24:
                data.skip(2)
            case 26:
                data.skip(2)
            case 27:
                data.skip(6)
            case 28:
                pass
            case 29:
                data.skip(10)
            case 30:
                # load ogg
                index_ = data.read_unsigned_int_16_le()
            case 32:
                data.skip(4)
            case 48:
                pass
            case 51:
                data.skip(2)
            case 61:
                pass
            case _:
                raise ValueError(f"Unknown command: {command}")
    
    file = os.path.join(folder, str(index) + "_" + title.strip() + ".txt").replace("\x00", "")
    print(file)
    with open(file, "w") as f:
        for line in texts:
            f.write(line + "\n")
