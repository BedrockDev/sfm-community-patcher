path = r"D:\SteamLibrary\steamapps\common\SourceFilmmaker\game\bin\engine.dll"
d = open(path, "rb").read()
sigs = [
    ("cmp 512M", bytes.fromhex("3D 00 00 00 20")),
    ("cmp 128M", bytes.fromhex("3D 00 00 00 08")),
    ("mov 48M", bytes.fromhex("BE 00 00 30 03")),
    ("cmp 40M", bytes.fromhex("81 FE 00 00 28 02")),
    ("push 32M", bytes.fromhex("68 00 00 00 02")),
]
for n, p in sigs:
    loc = []
    i = 0
    while True:
        j = d.find(p, i)
        if j < 0:
            break
        loc.append(hex(j))
        i = j + 1
    print(n, len(loc), loc[:10])

print("RBTree str", hex(d.find(b"CUtlRBTree overflow!")))
