import struct
import sys

path = sys.argv[1] if len(sys.argv) > 1 else r"D:\SteamLibrary\steamapps\common\SourceFilmmaker\game\bin\engine.dll"
data = open(path, "rb").read()
str_off = data.find(b"Engine hunk overflow!")
print("file offset", hex(str_off))

e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
opt = e_lfanew + 4 + 20
image_base = struct.unpack_from("<I", data, opt + 28)[0]
num_sections = struct.unpack_from("<H", data, e_lfanew + 6)[0]
opt_size = struct.unpack_from("<H", data, e_lfanew + 20)[0]
sec = e_lfanew + 24 + opt_size
str_rva = None
for i in range(num_sections):
    s = sec + i * 40
    name = data[s : s + 8].rstrip(b"\x00")
    vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", data, s + 8)
    if rawptr <= str_off < rawptr + rawsize:
        str_rva = vaddr + (str_off - rawptr)
        print("section", name.decode(), "RVA", hex(str_rva), "VA", hex(image_base + str_rva))
        break

if str_rva:
    imm = struct.pack("<I", str_rva)
    hits = []
    i = 0
    while True:
        j = data.find(imm, i)
        if j < 0:
            break
        if j > 0 and data[j - 1] == 0x68:
            hits.append(j - 1)
        i = j + 1
    print("push imm32 hits", len(hits), [hex(h) for h in hits])

for name, val in [
    ("64MB", 0x4000000),
    ("128MB", 0x8000000),
    ("256MB", 0x10000000),
    ("512MB", 0x20000000),
    ("1GB", 0x40000000),
    ("2GB", 0x80000000),
]:
    print(name, "count", data.count(struct.pack("<I", val)))

# also search 128, 256 as dword near hunk string refs
for val in [0x80, 0x100, 128, 256]:
    print(f"const {val}", data.count(struct.pack("<I", val)))

va = image_base + str_rva
off = data.find(struct.pack("<I", va))
print("VA ref file offset", hex(off) if off >= 0 else "none")
if off >= 0:
    chunk = data[off - 48 : off + 48]
    print("context hex:", chunk.hex())
    # scan backward for function start / cmp instructions with size constants
    window = data[off - 256 : off]
    for name, val in [
        ("64MB", 0x4000000),
        ("128MB", 0x8000000),
        ("256MB", 0x10000000),
        ("512MB", 0x20000000),
        ("1GB", 0x40000000),
    ]:
        p = struct.pack("<I", val)
        pos = window.rfind(p)
        if pos >= 0:
            print(f"  nearest {name} at", hex(off - 256 + pos))
