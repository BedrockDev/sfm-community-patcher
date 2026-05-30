import struct
from capstone import CS_ARCH_X86, CS_MODE_32, Cs

path = r"D:\SteamLibrary\steamapps\common\SourceFilmmaker\game\bin\engine.dll"
data = open(path, "rb").read()
md = Cs(CS_ARCH_X86, CS_MODE_32)

str_off = data.find(b"sv_cheats")
print("sv_cheats string", hex(str_off), repr(data[str_off : str_off + 32]))

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
i = 0
while True:
    j = data.find(pat, i)
    if j < 0:
        break
    print(f"\nxref {hex(j)}")
    for insn in md.disasm(data[j - 32 : j + 24], j - 32):
        if j - 16 <= insn.address <= j + 12:
            print(f"  {hex(insn.address)}: {insn.mnemonic} {insn.op_str}")
    i = j + 1

# search push offset sv_cheats in .text
rva_pat = struct.pack("<I", str_rva)
print("RVA push count", data.count(rva_pat))
