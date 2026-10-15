"""Schreibt einen OLE-Container (Compound File Binary, „CFB").

Word bettet ein ChemDraw-Objekt nicht als Bild ein, sondern als OLE-Objekt:
eine kleine Dateisystem-artige Containerdatei (`word/embeddings/oleObjectN.bin`)
mit der ChemDraw-Zeichnung im Stream `CONTENTS` und einer EMF-Fassung zum
Anzeigen. Nur so bleibt die Struktur im Word-Dokument per Doppelklick in
ChemDraw bearbeitbar — genau wie in der Vorlage.

Das Format ist [MS-CFB]. Hier wird nur der Teil geschrieben, der dafür nötig
ist: 512-Byte-Sektoren, 64-Byte-Mini-Sektoren, keine DIFAT-Sektoren (die
bräuchte es erst jenseits von ~27 MB). Gelesen wird nichts — die Struktur der
Vorlage wurde einmal analysiert und wird hier nachgebaut.

Aufbau der erzeugten Datei:

    [FAT-Sektoren][Verzeichnis][MiniFAT][Mini-Stream][Stream-Daten…]

Ströme unter 4096 Bytes liegen im Mini-Stream (der selbst ein normaler Strom
ist und dem „Root Entry" gehört), größere in eigenen Sektoren.
"""
import struct

SECTOR = 512
MINI_SECTOR = 64
MINI_CUTOFF = 4096
DIR_ENTRY = 128

FREESECT = 0xFFFFFFFF
ENDOFCHAIN = 0xFFFFFFFE
FATSECT = 0xFFFFFFFD
NOSTREAM = 0xFFFFFFFF

MAX_FAT_IN_HEADER = 109  # ohne DIFAT-Sektoren

# ChemDraw-Zeichnung als OLE-Objekt: Klassen-ID und die festen kleinen Ströme
# wurden aus der Vorlage übernommen (procedure_FluIBioxHOTf.docx).
CHEMDRAW_CLSID = bytes.fromhex("216dba412ea0ce118fd90020afd1f20c")
CHEMDRAW_PROGID = "ChemDraw_x64.Document.6.0"
_OLE_STREAM = bytes.fromhex("0100000200000000000000000000000000000000")
_OBJINFO_STREAM = bytes.fromhex("000003000d00")
_COMPOBJ_STREAM = bytes.fromhex(
    "0100feff030a0000ffffffff216dba412ea0ce118fd90020afd1f20c"
    "1b0000004353204368656d447261772036342d62697420447261776"
    "96e67001c0000004368656d4472617720496e74657263686"
    "16e676520466f726d6174001a0000004368656d447261775f78363"
    "42e446f63756d656e742e362e3000f439b271000000000000000000000000"
)


class OleWriteError(Exception):
    pass


def _pad(data: bytes, size: int) -> bytes:
    rest = len(data) % size
    return data + b"\0" * (size - rest) if rest else data


def _sort_key(name: str) -> tuple[int, str]:
    """Reihenfolge der Verzeichniseinträge nach [MS-CFB]: erst Namenslänge,
    dann der großgeschriebene Name."""
    return (len(name), name.upper())


def _balanced_tree(ids: list[int]) -> tuple[int, dict[int, tuple[int, int]]]:
    """Baut aus den (sortierten) Eintrags-IDs einen ausgeglichenen Baum.

    Gibt die Wurzel und je Eintrag (linkes, rechtes Kind) zurück. Alle Knoten
    bleiben schwarz — ein ausgeglichener Baum erfüllt die Rot-Schwarz-Regeln
    dann von selbst, und Leser prüfen die Färbung ohnehin nicht.
    """
    links: dict[int, tuple[int, int]] = {}

    def build(lo: int, hi: int) -> int:
        if lo > hi:
            return NOSTREAM
        mid = (lo + hi) // 2
        links[ids[mid]] = (build(lo, mid - 1), build(mid + 1, hi))
        return ids[mid]

    root = build(0, len(ids) - 1)
    return root, links


def _dir_entry(name: str, obj_type: int, left: int, right: int, child: int,
               clsid: bytes, start: int, size: int) -> bytes:
    raw = name.encode("utf-16-le") + b"\0\0"
    if len(raw) > 64:
        raise OleWriteError(f"Stream-Name zu lang: {name!r}")
    e = bytearray(DIR_ENTRY)
    e[0:len(raw)] = raw
    struct.pack_into("<H", e, 64, len(raw))
    e[66] = obj_type
    e[67] = 1  # schwarz
    struct.pack_into("<III", e, 68, left, right, child)
    e[80:96] = clsid
    struct.pack_into("<I", e, 116, start)
    struct.pack_into("<Q", e, 120, size)
    return bytes(e)


def build(streams: list[tuple[str, bytes]], clsid: bytes = b"\0" * 16) -> bytes:
    """Baut den Container aus `streams` (Name → Inhalt); `clsid` ist die
    Klassen-ID des Root-Eintrags (bei ChemDraw CHEMDRAW_CLSID)."""
    if not streams:
        raise OleWriteError("Keine Ströme angegeben")

    # 1. Aufteilen: kleine Ströme in den Mini-Stream, große in eigene Sektoren
    mini_stream = bytearray()
    mini_start: dict[str, int] = {}
    big: list[tuple[str, bytes]] = []
    for name, data in streams:
        if len(data) < MINI_CUTOFF:
            mini_start[name] = len(mini_stream) // MINI_SECTOR
            mini_stream += _pad(data, MINI_SECTOR)
        else:
            big.append((name, data))

    # 2. MiniFAT: je Mini-Sektor ein Eintrag, Ketten wie im großen FAT
    n_mini = len(mini_stream) // MINI_SECTOR
    minifat = [FREESECT] * n_mini
    for name, data in streams:
        if name not in mini_start:
            continue
        first = mini_start[name]
        count = max(1, -(-len(data) // MINI_SECTOR))
        for i in range(count - 1):
            minifat[first + i] = first + i + 1
        minifat[first + count - 1] = ENDOFCHAIN
    minifat_bytes = _pad(b"".join(struct.pack("<I", v) for v in minifat), SECTOR)

    # 3. Sektorbedarf zählen. Reihenfolge in der Datei:
    #    FAT | Verzeichnis | MiniFAT | Mini-Stream | große Ströme
    payloads: list[bytes] = [bytes(_pad(mini_stream, SECTOR))] if n_mini else []
    payloads += [_pad(data, SECTOR) for _, data in big]

    n_entries = 1 + len(streams)  # Root Entry + Ströme
    n_dir = -(-n_entries * DIR_ENTRY // SECTOR)
    n_minifat = len(minifat_bytes) // SECTOR
    n_payload = sum(len(p) // SECTOR for p in payloads)

    n_fixed = n_dir + n_minifat + n_payload
    n_fat = 1
    while True:  # FAT beschreibt sich selbst mit — bis es stabil ist
        need = -(-(n_fixed + n_fat) * 4 // SECTOR)
        if need <= n_fat:
            break
        n_fat = need
    if n_fat > MAX_FAT_IN_HEADER:
        raise OleWriteError("Datei zu groß für einen Container ohne DIFAT-Sektoren")

    # 4. Sektornummern vergeben und FAT-Ketten eintragen
    fat = [FREESECT] * (n_fat * SECTOR // 4)
    cursor = 0

    def take(count: int) -> int:
        """Belegt `count` aufeinanderfolgende Sektoren als eine Kette."""
        nonlocal cursor
        first = cursor
        for i in range(count - 1):
            fat[first + i] = first + i + 1
        fat[first + count - 1] = ENDOFCHAIN
        cursor += count
        return first

    for i in range(n_fat):  # die FAT-Sektoren selbst
        fat[cursor + i] = FATSECT
    fat_first = cursor
    cursor += n_fat

    dir_first = take(n_dir)
    minifat_first = take(n_minifat) if n_minifat else ENDOFCHAIN
    payload_first = [take(len(p) // SECTOR) for p in payloads]

    # 5. Verzeichnis: Root Entry + Ströme, verkettet als ausgeglichener Baum
    order = sorted(range(len(streams)), key=lambda i: _sort_key(streams[i][0]))
    ids = [i + 1 for i in order]  # Eintrag 0 ist der Root Entry
    tree_root, links = _balanced_tree(ids)

    big_start = dict(zip((n for n, _ in big), payload_first[1:] if n_mini else payload_first))
    entries = [_dir_entry(
        "Root Entry", 5, NOSTREAM, NOSTREAM, tree_root, clsid,
        payload_first[0] if n_mini else ENDOFCHAIN, len(mini_stream),
    )]
    for i, (name, data) in enumerate(streams):
        left, right = links.get(i + 1, (NOSTREAM, NOSTREAM))
        start = mini_start[name] if name in mini_start else big_start[name]
        entries.append(_dir_entry(name, 2, left, right, NOSTREAM, b"\0" * 16,
                                  start, len(data)))
    directory = _pad(b"".join(entries), SECTOR)

    # 6. Kopf schreiben
    head = bytearray(SECTOR)
    head[0:8] = bytes.fromhex("d0cf11e0a1b11ae1")
    struct.pack_into("<HHH", head, 24, 0x003E, 0x0003, 0xFFFE)
    struct.pack_into("<HH", head, 30, 9, 6)  # 512- bzw. 64-Byte-Sektoren
    struct.pack_into("<I", head, 44, n_fat)
    struct.pack_into("<I", head, 48, dir_first)
    struct.pack_into("<I", head, 56, MINI_CUTOFF)
    struct.pack_into("<I", head, 60, minifat_first)
    struct.pack_into("<I", head, 64, n_minifat)
    struct.pack_into("<I", head, 68, ENDOFCHAIN)  # erster DIFAT-Sektor: keiner
    for i in range(MAX_FAT_IN_HEADER):
        struct.pack_into("<I", head, 76 + 4 * i,
                         fat_first + i if i < n_fat else FREESECT)

    fat_bytes = b"".join(struct.pack("<I", v) for v in fat)
    return bytes(head) + fat_bytes + directory + minifat_bytes + b"".join(payloads)


def chemdraw_object(cdx: bytes, emf: bytes | None = None) -> bytes:
    """OLE-Container für eine ChemDraw-Zeichnung, wie ihn Word beim Einfügen
    aus ChemDraw anlegt. `emf` ist die Druckfassung (Stream `\\x03EPRINT`);
    ohne sie erzeugt ChemDraw sie beim Öffnen neu."""
    streams = [
        ("\x01Ole", _OLE_STREAM),
        ("\x01CompObj", _COMPOBJ_STREAM),
        ("\x03ObjInfo", _OBJINFO_STREAM),
        ("CONTENTS", cdx),
    ]
    if emf:
        streams.insert(2, ("\x03EPRINT", emf))
    return build(streams, CHEMDRAW_CLSID)
