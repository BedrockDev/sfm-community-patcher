from capstone import CS_ARCH_X86, CS_MODE_32, Cs

path = r"D:\SteamLibrary\steamapps\common\SourceFilmmaker\game\bin\engine.dll"
data = open(path, "rb").read()
md = Cs(CS_ARCH_X86, CS_MODE_32)
pat = bytes.fromhex("A9 00 40 00 00")
i = 0
while True:
    j = data.find(pat, i)
    if i < 0 and j < 0:
        break
    if j < 0:
        break
    print(f"\n=== {hex(j)} ===")
    for insn in md.disasm(data[j - 8 : j + 24], j - 8):
        if j - 8 <= insn.address <= j + 20:
            print(f"{hex(insn.address)}: {insn.mnemonic} {insn.op_str}")
    i = j + 1
