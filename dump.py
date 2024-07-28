import os
import sys
from binary import BinaryReader


with open(sys.argv[1], "rb") as f:
    reader = BinaryReader(f.read())

header = reader.read_bytes(0x80)

if not header.startswith(b"MIT"):
    raise ValueError("Invalid MIT header")

shift = 16

buffer = reader.read_bytes_into_reader(0x304)
count = reader.read_unsigned_int_32_le()
buffer.append(reader.read_bytes(0xc))

files = []

for i in range(count):
    files.append({
        "size": reader.read_unsigned_int_32_le(),
        "filename": reader.read_c_string_with_size(0x1c, "shift-jis").strip("\x00"),
    })
    shift += 32

now_pos = reader.pos

folder = sys.argv[1] + "_extracted"
os.makedirs(folder, exist_ok=True)

for index, file in enumerate(files):
    if index:
        distance_to_move = files[index - 1]["size"] + shift
        read_size = file["size"] - files[index - 1]["size"]
    else:
        distance_to_move = shift
        read_size = file["size"]
    
    reader.goto(900)
    reader.skip(distance_to_move)
    with open(os.path.join(folder, file["filename"]), "wb") as f:
        f.write(reader.read_bytes(file["size"]))
