import struct
from capstone import CS_ARCH_X86, CS_MODE_32, Cs

path = r"D:\SteamLibrary\steamapps\common\SourceFilmmaker\game\bin\engine.dll"
data = open(path, "rb").read()
md = Cs(CS_ARCH_X86, CS_MODE_32)

str_off = data.find(b"Unknown command")
e = struct.unpack_from("<I", data, 0x3C)[0]
image_base = struct.unpack_from("<I", data, e + 4 + 20 + 28)[0]
n = struct.unpack_from("<H", data, e + 6)[0]
osize = struct.unpack_from("<H", data, e + 20)[0]
sec = e + 24 + osize
for i in range(n):
    s = sec + i * 40
    vs, va, rs, rp = struct.unpack_from("<IIII", data, s + 8)
    if rp <= str_off < rp + rs:
        str_rva = va + (str_off - rp)
        break
va = image_base + str_rva
print("Unknown command VA", hex(va))
pat = struct.pack("<I", va)
i = 0
while True:
    j = data.find(pat, i)
    if j < 0:
        break
    print(f"\nxref file {hex(j)}")
    for insn in md.disasm(data[j - 80 : j + 24], j - 80):
        if j - 40 <= insn.address <= j + 16:
            print(f"  {hex(insn.address)}: {insn.mnemonic} {insn.op_str}")
    i = j + 1
