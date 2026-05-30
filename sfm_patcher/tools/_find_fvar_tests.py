path = r"D:\SteamLibrary\steamapps\common\SourceFilmmaker\game\bin\engine.dll"
data = open(path, "rb").read()

hits = []
for i in range(len(data) - 7):
    if data[i + 3 : i + 7] != bytes.fromhex("00 40 00 00"):
        continue
    if data[i + 2] != 0x0C:
        continue
    if data[i] != 0xF7:
        continue
    modrm = data[i + 1]
    if modrm < 0x40 or modrm > 0x47:
        continue
    hits.append(i)

print("test [reg+0xc], 0x4000 count", len(hits))
for h in hits:
    print(hex(h), data[h : h + 9].hex())
