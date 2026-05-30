import struct
import sys

path = r"D:\SteamLibrary\steamapps\common\SourceFilmmaker\game\bin\engine.dll"
data = open(path, "rb").read()


def rva_to_offset(rva: int) -> int | None:
    e = struct.unpack_from("<I", data, 0x3C)[0]
    n = struct.unpack_from("<H", data, e + 6)[0]
    osize = struct.unpack_from("<H", data, e + 20)[0]
    sec = e + 24 + osize
    for i in range(n):
        s = sec + i * 40
        vs, va, rs, rp = struct.unpack_from("<IIII", data, s + 8)
        if va <= rva < va + max(vs, rs):
            return rp + (rva - va)
    return None


for label, rva in [
    ("hunk_end", 0x6702EC),
    ("hunk_base", 0x6702E8),
    ("hunk_align_mask", 0x670300),
    ("hunk_size_cfg", 0x64549C),
]:
    off = rva_to_offset(rva)
    if off is None:
        print(label, "no offset")
        continue
    val = struct.unpack_from("<I", data, off)[0]
    print(f"{label} RVA {hex(rva)} file {hex(off)} = {hex(val)} ({val // (1024*1024)} MB)")
