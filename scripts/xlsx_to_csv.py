"""Convert the take-home .xlsx exports into the CSVs the router reads.

Standard library only. Usage:
    python3 scripts/xlsx_to_csv.py "Copy of accounts.xlsx" data/accounts.csv
"""

import csv
import sys
import zipfile
import xml.etree.ElementTree as ET

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def _cell_index(ref):
    letters = "".join(c for c in ref if c.isalpha())
    row = int("".join(c for c in ref if c.isdigit()))
    col = 0
    for c in letters:
        col = col * 26 + (ord(c) - 64)
    return row - 1, col - 1


def read_first_sheet(path):
    z = zipfile.ZipFile(path)
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        root = ET.fromstring(z.read("xl/sharedStrings.xml"))
        for si in root.findall("m:si", NS):
            shared.append("".join(t.text or "" for t in si.findall(".//m:t", NS)))

    workbook = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    targets = {r.attrib["Id"]: r.attrib["Target"] for r in rels}
    sheet = workbook.find("m:sheets/m:sheet", NS)
    target = targets[sheet.attrib["{%s}id" % REL_NS]]
    if not target.startswith("xl/"):
        target = "xl/" + target.lstrip("/")

    cells = {}
    for c in ET.fromstring(z.read(target)).findall(".//m:c", NS):
        row, col = _cell_index(c.attrib["r"])
        v = c.find("m:v", NS)
        value = ""
        if c.attrib.get("t") == "s" and v is not None:
            value = shared[int(v.text)]
        elif c.attrib.get("t") == "inlineStr":
            value = "".join(t.text or "" for t in c.findall(".//m:t", NS))
        elif v is not None and v.text is not None:
            value = v.text
        cells.setdefault(row, {})[col] = value

    max_row = max(cells)
    max_col = max(max(r) for r in cells.values())
    table = [[cells.get(r, {}).get(c, "") for c in range(max_col + 1)] for r in range(max_row + 1)]
    return [row for row in table if any(row)]


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    rows = read_first_sheet(sys.argv[1])
    with open(sys.argv[2], "w", newline="") as f:
        csv.writer(f).writerows(rows)
    print("wrote %d rows to %s" % (len(rows) - 1, sys.argv[2]))


if __name__ == "__main__":
    main()
