import sys

from capstone import CS_ARCH_X86, CS_MODE_32, Cs

path = r"D:\SteamLibrary\steamapps\common\SourceFilmmaker\game\bin\engine.dll"
data = open(path, "rb").read()
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True

regions = [
    (0x2F7310, 0x40),
    (0x2EF530, 0x30),
]

for start, size in regions:
    print(f"\n===== {hex(start)} =====")
    code = data[start : start + size]
    for insn in md.disasm(code, start):
        print(f"file+{hex(insn.address - start)} ({hex(insn.address)}): {insn.mnemonic}\t{insn.op_str}")
