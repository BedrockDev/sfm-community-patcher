import struct
from capstone import CS_ARCH_X86, CS_MODE_32, Cs

path = r"D:\SteamLibrary\steamapps\common\SourceFilmmaker\game\bin\engine.dll"
data = open(path, "rb").read()
md = Cs(CS_ARCH_X86, CS_MODE_32)

for name, addr in [("hunk_end", 0x106702EC), ("hunk_base", 0x106702E8), ("hunk_size_cfg", 0x1064549C)]:
    pat = struct.pack("<I", addr)
    idx = 0
    print(f"\n=== {name} {hex(addr)} ===")
    n = 0
    while n < 25:
        i = data.find(pat, idx)
        if i < 0:
            break
        start = max(0, i - 12)
        code = data[start : i + 16]
        for insn in md.disasm(code, start):
            if insn.address <= i < insn.address + insn.size:
                print(f"  {hex(insn.address)}: {insn.mnemonic} {insn.op_str}")
                break
        idx = i + 1
        n += 1
