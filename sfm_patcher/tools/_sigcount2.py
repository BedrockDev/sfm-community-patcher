from capstone import CS_ARCH_X86, CS_MODE_32, Cs

path = r"D:\SteamLibrary\steamapps\common\SourceFilmmaker\game\bin\engine.dll"
d = open(path, "rb").read()
md = Cs(CS_ARCH_X86, CS_MODE_32)

pat = bytes.fromhex("3D 00 00 00 08")
i = 0
while True:
    j = d.find(pat, i)
    if j < 0:
        break
    code = d[j - 16 : j + 24]
    print(f"\n--- {hex(j)} ---")
    for insn in md.disasm(code, j - 16):
        if j - 16 <= insn.address < j + 20:
            print(f"{hex(insn.address)}: {insn.mnemonic} {insn.op_str}")
    i = j + 1
