import struct

path = r"D:\SteamLibrary\steamapps\common\SourceFilmmaker\game\bin\engine.dll"
data = open(path, "rb").read()
err_push = 0x1E475F  # push "Engine hunk overflow!"

# Ищем cmp reg, imm32 (3D ?? ?? ?? ??) и cmp [mem], imm32 (81 ?? ?? ?? ?? ??)
limits = {
    0x04000000: "64MB",
    0x08000000: "128MB",
    0x10000000: "256MB",
    0x20000000: "512MB",
    0x40000000: "1GB",
    0x80000000: "2GB",
}

start = err_push - 0x800
end = err_push
chunk = data[start:end]

print("Scan 0x800 bytes before error push", hex(start), "-", hex(end))
for imm, name in limits.items():
    pat = struct.pack("<I", imm)
    # cmp eax, imm
    pat3d = b"\x3d" + pat
    idx = 0
    while True:
        i = chunk.find(pat3d, idx)
        if i < 0:
            break
        print(f"  cmp eax, {name} @ {hex(start + i)}")
        idx = i + 1
    # cmp r32, imm (81 /0)
    for modrm in range(0xF8, 0x100):
        p = bytes([0x81, modrm]) + pat
        idx = 0
        while True:
            i = chunk.find(p, idx)
            if i < 0:
                break
            print(f"  cmp r/m({modrm:02x}), {name} @ {hex(start + i)}")
            idx = i + 1

# jg/jl/jae near hunk - search 0f 8? after cmp
print("\nAll imm32 in window matching 256MB or 128MB:")
for off in range(len(chunk) - 4):
    v = struct.unpack_from("<I", chunk, off)[0]
    if v in limits:
        print(hex(start + off), limits[v], "bytes", chunk[off - 2 : off + 6].hex())
