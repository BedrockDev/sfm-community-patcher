# Quick RE: keyvalue string space in vstdlib.dll
import struct
import sys

try:
    import pefile
except ImportError:
    pefile = None

path = sys.argv[1] if len(sys.argv) > 1 else r"D:\SteamLibrary\steamapps\common\SourceFilmmaker\game\bin\vstdlib.dll"
d = open(path, "rb").read()
needle = b"Out of keyvalue string space"
fo = d.find(needle)
print("string file offset", hex(fo))

if pefile:
    pe = pefile.PE(path)
    rva = pe.get_rva_from_offset(fo)
    va = pe.OPTIONAL_HEADER.ImageBase + rva
    print("RVA", hex(rva), "VA", hex(va))
    for sec in pe.sections:
        if sec.Name.rstrip(b"\x00") != b".text":
            continue
        code = d[sec.PointerToRawData : sec.PointerToRawData + sec.SizeOfRawData]
        base = sec.VirtualAddress
        for i in range(len(code) - 5):
            if code[i] == 0x68 and struct.unpack_from("<I", code, i + 1)[0] == va:
                r = base + i
                print("PUSH ref RVA", hex(r), "file", hex(pe.get_offset_from_rva(r)))
            # lea reg, [imm32] modrm 0x05/0x15/0x0d/0x1d/0x35/0x3d with imm32
            if code[i] in (0x8D,) and i + 6 < len(code):
                mod = code[i + 1]
                if mod in (0x05, 0x0D, 0x15, 0x1D, 0x35, 0x3D):
                    imm = struct.unpack_from("<I", code, i + 2)[0]
                    if imm == va:
                        r = base + i
                        print("LEA ref RVA", hex(r), "file", hex(pe.get_offset_from_rva(r)))

# search common table size constants near GetSymbol
for pat, name in [
    (bytes.fromhex("00 00 20 00"), "512KB str"),
    (bytes.fromhex("00 00 10 00"), "1MB?"),
    (bytes.fromhex("00 08 00 00"), "2048 hash"),
    (bytes.fromhex("FF FF 7F 00"), "0x7FFFFF"),
    (bytes.fromhex("00 00 08 00"), "512*1024/128"),
]:
    c = d.count(pat)
    if c:
        print(f"{name}: {c} occurrences")

PY
