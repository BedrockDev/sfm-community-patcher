import struct

path = r"D:\SteamLibrary\steamapps\common\SourceFilmmaker\game\bin\engine.dll"
data = open(path, "rb").read()
err_push = 0x1E475F

limits = [0x02000000, 0x04000000, 0x08000000, 0x10000000, 0x20000000, 0x40000000]

for window_size in [0x2000, 0x8000, 0x20000]:
    start = err_push - window_size
    chunk = data[start:err_push]
    print(f"\n=== window {hex(window_size)} before error ===")
    found = False
    for off in range(len(chunk) - 4):
        v = struct.unpack_from("<I", chunk, off)[0]
        if v not in limits:
            continue
        pre = chunk[max(0, off - 6) : off]
        post = chunk[off : off + 8]
        # interesting if preceded by cmp/cmp-like or mov
        if pre and pre[-1] in (0x3D, 0x3B, 0x81) or (len(pre) >= 2 and pre[-2] == 0x81):
            print(hex(start + off), hex(v), "pre", pre.hex(), "post", post.hex())
            found = True
        elif pre and pre[-1] == 0xB8:  # mov eax, imm
            print(hex(start + off), "mov imm", hex(v), chunk[off - 1 : off + 5].hex())
            found = True
    if not found:
        print("(no cmp/mov patterns)")

# all push VA to error string
va = 0x10366568
pat = struct.pack("<I", va)
idx = 0
print("\nAll VA xrefs:")
while True:
    i = data.find(pat, idx)
    if i < 0:
        break
    print(hex(i), "op before", hex(data[i - 1]) if i else "?")
    idx = i + 1
