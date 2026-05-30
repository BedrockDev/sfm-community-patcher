import struct
from capstone import CS_ARCH_X86, CS_MODE_32, Cs

path = r"D:\SteamLibrary\steamapps\common\SourceFilmmaker\game\bin\engine.dll"
data = open(path, "rb").read()
md = Cs(CS_ARCH_X86, CS_MODE_32)

str_off = data.find(b"CUtlRBTree overflow!")
print("string", hex(str_off))

# RVA
e = struct.unpack_from("<I", data, 0x3C)[0]
image_base = struct.unpack_from("<I", data, e + 4 + 20 + 28)[0]
n = struct.unpack_from("<H", data, e + 6)[0]
osize = struct.unpack_from("<H", data, e + 20)[0]
sec = e + 24 + osize
str_rva = None
for i in range(n):
    s = sec + i * 40
    vs, va, rs, rp = struct.unpack_from("<IIII", data, s + 8)
    if rp <= str_off < rp + rs:
        str_rva = va + (str_off - rp)
        break
va = image_base + str_rva
print("VA", hex(va))
pat = struct.pack("<I", va)
idx = 0
while True:
    i = data.find(pat, idx)
    if i < 0:
        break
    print("xref file", hex(i))
    chunk = data[i - 64 : i + 32]
    for insn in md.disasm(chunk, i - 64):
        if i - 32 <= insn.address <= i + 16:
            print(f"  {hex(insn.address)}: {insn.mnemonic} {insn.op_str}")
    idx = i + 1

# search cmp with 0xFFFF nearby common patterns
for pat_hex, name in [
    ("81 F9 FF FF 00 00", "cmp ecx, 0xFFFF"),
    ("3D FF FF 00 00", "cmp eax, 0xFFFF"),
    ("81 FF FF FF 00 00", "cmp edi, 0xFFFF"),
]:
    p = bytes.fromhex(pat_hex.replace(" ", ""))
    loc = []
    j = 0
    while len(loc) < 5:
        k = data.find(p, j)
        if k < 0:
            break
        loc.append(hex(k))
        j = k + 1
    print(name, "count", len(loc), loc)
