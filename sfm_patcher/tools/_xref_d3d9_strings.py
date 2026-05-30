import struct
from capstone import CS_ARCH_X86, CS_MODE_32, Cs

path = r"D:\SteamLibrary\steamapps\common\SourceFilmmaker\game\bin\shaderapidx9.dll"
data = open(path, "rb").read()
md = Cs(CS_ARCH_X86, CS_MODE_32)

e = struct.unpack_from("<I", data, 0x3C)[0]
ib = struct.unpack_from("<I", data, e + 4 + 20 + 28)[0]
n = struct.unpack_from("<H", data, e + 6)[0]
osize = struct.unpack_from("<H", data, e + 20)[0]
sec = e + 24 + osize

for label, off in [("d3d9_vlk", 0x1463E4), ("d3d9.dll", 0x16B2C6)]:
    str_rva = None
    for i in range(n):
        s = sec + i * 40
        vs, va, rs, rp = struct.unpack_from("<IIII", data, s + 8)
        if rp <= off < rp + rs:
            str_rva = va + (off - rp)
            break
    va = ib + str_rva
    print(f"\n=== {label} VA {hex(va)} ===")
    pat = struct.pack("<I", va)
    i = 0
    while True:
        j = data.find(pat, i)
        if j < 0:
            break
        for insn in md.disasm(data[max(0, j - 16) : j + 24], max(0, j - 16)):
            if j - 4 <= insn.address <= j + 8:
                print(f"  {hex(insn.address)}: {insn.mnemonic} {insn.op_str}")
        i = j + 1
