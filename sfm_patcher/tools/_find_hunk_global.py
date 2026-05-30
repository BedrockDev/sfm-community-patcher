import struct

path = r"D:\SteamLibrary\steamapps\common\SourceFilmmaker\game\bin\engine.dll"
data = open(path, "rb").read()

# глобал лимита из cmp ebx, [0x106702ec]
GLOBAL = 0x106702EC
pat = struct.pack("<I", GLOBAL)

idx = 0
print("refs to", hex(GLOBAL))
while True:
    i = data.find(pat, idx)
    if i < 0:
        break
    ctx = data[max(0, i - 8) : i + 12]
    print(hex(i), ctx.hex())
    idx = i + 1

# поиск mov [global], reg / mov [global], imm
for off in range(len(data) - 8):
    # C7 05 EC 02 67 10 imm32  mov dword ptr [global], imm
    if data[off : off + 2] == b"\xc7\x05" and data[off + 2 : off + 6] == pat:
        imm = struct.unpack_from("<I", data, off + 6)[0]
        print("mov [global], imm @", hex(off), "=", hex(imm), f"({imm // (1024*1024)} MB)")
