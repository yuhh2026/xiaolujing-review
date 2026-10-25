"""对照英文进行原位校译：复用译文原有字体、字号及每个文字绘制位置。"""
from pathlib import Path
from io import BytesIO
import json
import sys
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ContentStream, ByteStringObject, ArrayObject, FloatObject, NameObject, DictionaryObject, DecodedStreamObject

if not __debug__:
    raise SystemExit("请勿用python -O运行：原位编辑需要启用全部检查")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import argparse, hashlib
parser = argparse.ArgumentParser(description="复用原字体的Unicode字槽原位替换；不支持的排版明确拒绝")
parser.add_argument("--pdf", required=True)
parser.add_argument("--manifest", required=True)
parser.add_argument("--output", required=True)
parser.add_argument("--work", required=True)
parser.add_argument("--fallback-font")
config = parser.parse_args()
SOURCE = Path(config.pdf).resolve()
OUTPUT = Path(config.output).resolve()
ROOT = Path(config.work).resolve()
ROOT.mkdir(parents=True, exist_ok=True)
assert SOURCE != OUTPUT, "本工具只写独立校译版，验证后另行备份写回"
assert not OUTPUT.exists(), "输出已存在；先验证或选择新的临时输出，避免误覆盖"
doc = json.loads(Path(config.manifest).read_text(encoding="utf-8"))
assert doc.get("source_sha256") == hashlib.sha256(SOURCE.read_bytes()).hexdigest(), "源PDF哈希不符"
entries = doc["changes"]
assert entries, "清单为空"
RULES = []
for c in entries:
    assert isinstance(c.get("page"), int) and c["page"] > 0
    assert c.get("basis") and c.get("old") and c["old"] != c["new"]
    assert len(c["old"]) == len(c["new"]), "快捷路径只处理等字符槽修改；不得为凑字数改变原意"
    RULES.append((c["page"], c["old"], c["new"], c["basis"]))

def raw_bytes(value):
    return value.original_bytes if hasattr(value, "original_bytes") else bytes(value)


def width(font, code):
    """读取原PDF字宽，单位为千分之一字号。"""
    if font["/Subtype"] == "/Type0":
        d = font["/DescendantFonts"][0].get_object()
        arr = d.get("/W", [])
        j = 0
        while j < len(arr):
            first, nxt = int(arr[j]), arr[j + 1]
            if isinstance(nxt, ArrayObject):
                if first <= code < first + len(nxt):
                    return float(nxt[code - first])
                j += 2
            else:
                if first <= code <= int(nxt):
                    return float(arr[j + 2])
                j += 3
        return float(d.get("/DW", 1000))
    # 标准西文字体的等长字母替换在本轮不改变内容，因此不需要虚构字宽。
    arr = font.get("/Widths")
    if arr:
        return float(arr[code - int(font.get("/FirstChar", 0))])
    return None


reader = PdfReader(SOURCE)
writer = PdfWriter()
writer.clone_document_from_reader(reader)
log = []
changed_pages = []
glyph_requests = {}
proof_fonts = {}
glyph_check_fonts = {}


def proof_font(font, resources):
    """为替换字建立同字体副本，避免字体补字影响原文任何未改字符。"""
    desc = font["/DescendantFonts"][0].get_object()
    old_file = desc["/FontDescriptor"]["/FontFile2"]
    key = old_file.indirect_reference.idnum
    if key not in proof_fonts:
        new_file = DecodedStreamObject()
        new_file.set_data(old_file.get_data())
        file_ref = writer._add_object(new_file)
        fd = DictionaryObject(desc["/FontDescriptor"])
        fd[NameObject("/FontFile2")] = file_ref
        new_desc = DictionaryObject(desc)
        new_desc[NameObject("/FontDescriptor")] = writer._add_object(fd)
        new_top = DictionaryObject(font)
        new_top[NameObject("/DescendantFonts")] = ArrayObject([writer._add_object(new_desc)])
        font_ref = writer._add_object(new_top)
        resource_name = NameObject("/FProof" + str(key))
        proof_fonts[key] = (resource_name, font_ref, new_file)
        glyph_requests[file_ref.idnum] = [new_file, str(font["/BaseFont"]), set()]
    resource_name, font_ref, new_file = proof_fonts[key]
    resources[resource_name] = font_ref
    return resource_name, new_file.indirect_reference.idnum


for page_no, page in enumerate(writer.pages, 1):
    if not any(rule[0] == page_no for rule in RULES):
        continue
    stream = ContentStream(page.get_contents(), writer)
    fonts = page["/Resources"]["/Font"]
    current_font = None
    current_size = 0
    current_rise = 0
    slots = []
    text_values = {}
    font_for_op = {}
    state_for_op = {}
    for op_i, (args, op) in enumerate(stream.operations):
        if op == b"Tf":
            current_font = str(args[0])
            current_size = float(args[1])
        elif op == b"Ts":
            current_rise = float(args[0])
        elif op == b"Tj":
            font = fonts[current_font].get_object()
            data = raw_bytes(args[0])
            txt = data.decode("utf-16-be") if font["/Subtype"] == "/Type0" else str(args[0])
            text_values[op_i] = txt
            font_for_op[op_i] = current_font
            state_for_op[op_i] = (current_size, current_rise)
            for j, char in enumerate(txt):
                slots.append((op_i, j, char))
    joined = "".join(x[2] for x in slots)
    pending = {}
    replacement_font = {}
    for selected_page, old, new, reason in RULES:
        if selected_page is not None and selected_page != page_no:
            continue
        start = 0
        while (pos := joined.find(old, start)) >= 0:
            # 完整政策名优先于通用词替换，避免在旧文字索引上重复替换同一位置。
            if any((slots[pos + k][0], slots[pos + k][1]) in pending for k in range(len(old))):
                start = pos + len(old)
                continue
            for offset, char in enumerate(new):
                op_i, j, previous = slots[pos + offset]
                if previous != char:
                    assert (op_i, j) not in pending, (page_no, old, "规则重叠")
                    font = fonts[font_for_op[op_i]].get_object()
                    assert font["/Subtype"] == "/Type0", (page_no, previous, char, font_for_op[op_i])
                    # 使用原字体的CID映射；缺字时终止，不替换字体、不输出方框。
                    d = font["/DescendantFonts"][0].get_object()
                    cmap = d["/CIDToGIDMap"].get_data()
                    assert ord(char) < 65536
                    assert int.from_bytes(cmap[ord(char) * 2:ord(char) * 2 + 2], "big") != 0, char
                    # 只有CID真对应Unicode且字槽宽度一致时才用快捷路径。
                    font_key = d["/FontDescriptor"]["/FontFile2"].indirect_reference.idnum
                    if font_key not in glyph_check_fonts:
                        glyph_check_fonts[font_key] = TTFont(BytesIO(d["/FontDescriptor"]["/FontFile2"].get_data()), lazy=True)
                    check_font = glyph_check_fonts[font_key]
                    name = check_font.getBestCmap().get(ord(previous))
                    assert name and check_font.getGlyphID(name) == int.from_bytes(cmap[ord(previous)*2:ord(previous)*2+2], "big"), "CID不是Unicode，需专门适配"
                    assert width(font, ord(previous)) == width(font, ord(char)), "新字宽不适合原字槽，不自动压缩字体"
                    resource_name, key = proof_font(font, fonts)
                    glyph_requests[key][2].add(char)
                    replacement_font[op_i] = resource_name
                    pending[(op_i, j)] = char
            log.append({"page": page_no, "old": old, "new": new, "basis": reason})
            start = pos + len(old)
    if not pending:
        continue
    changed_pages.append(page_no)
    wrapped = {}
    for op_i in sorted({i for i, _ in pending}):
        original = text_values[op_i]
        revised = "".join(pending.get((op_i, j), c) for j, c in enumerate(original))
        font = fonts[font_for_op[op_i]].get_object()
        old_w = sum(width(font, ord(c)) for c in original)
        new_w = sum(width(font, ord(c)) for c in revised)
        content = ByteStringObject(revised.encode("utf-16-be"))
        if abs(new_w - old_w) < 0.001:
            stream.operations[op_i] = ([content], b"Tj")
        else:
            # 保持原字槽推进量不变，后续文字、行尾、分页不会移动。
            stream.operations[op_i] = ([ArrayObject([content, FloatObject(new_w - old_w)])], b"TJ")
        size, _ = state_for_op[op_i]
        wrapped[op_i] = [
            ([replacement_font[op_i], FloatObject(size)], b"Tf"),
            stream.operations[op_i],
            ([NameObject(font_for_op[op_i]), FloatObject(size)], b"Tf"),
        ]
    stream.operations = [entry for i, original in enumerate(stream.operations) for entry in wrapped.get(i, [original])]
    page.replace_contents(stream)

# 原PDF为保留CID的子集字体，cmap非零仍可能对应空轮廓。
# 仅补齐替换字的空轮廓，其余原字形、字宽、坐标与字体资源保持不变。
# Noto CJK Serif与思源宋体为同源字形项目；使用官方SC字库的400/700字重。
full_font_path = Path(config.fallback_font).resolve() if config.fallback_font else None
full_fonts = {}
filled = []
for key, (font_file, base_name, chars) in glyph_requests.items():
    subset = TTFont(BytesIO(font_file.get_data()))
    cmap = subset.getBestCmap()
    missing = [c for c in chars if subset["glyf"][cmap[ord(c)]].numberOfContours == 0 and not c.isspace()]
    if not missing:
        continue
    weight = 700 if "Bold" in base_name else 400
    if weight not in full_fonts:
        assert full_font_path and full_font_path.exists(), "替换字缺少轮廓；需匹配原字体的完整字库，不自动换宋体"
        cache = Path.home() / ".cache" / "xiaolujing-review" / "static-fonts"
        cache.mkdir(parents=True, exist_ok=True)
        cached = cache / (hashlib.sha256(full_font_path.read_bytes()).hexdigest() + "-" + str(weight) + ".ttf")
        if cached.exists():
            full = TTFont(cached)
        else:
            full = TTFont(full_font_path)
            if "fvar" in full:
                full = instantiateVariableFont(full, {"wght": weight}, inplace=True)
            full.save(cached)
        full_fonts[weight] = full
    full = full_fonts[weight]
    full_cmap = full.getBestCmap()
    glyph_set = full.getGlyphSet()
    assert subset["head"].unitsPerEm == full["head"].unitsPerEm
    for char in missing:
        pen = DecomposingRecordingPen(glyph_set)
        glyph_set[full_cmap[ord(char)]].draw(pen)
        outline = TTGlyphPen(None)
        pen.replay(outline)
        target = cmap[ord(char)]
        subset["glyf"][target] = outline.glyph()
        filled.append({"font": base_name, "char": char, "weight": weight})
    buf = BytesIO()
    subset.save(buf)
    font_file.set_data(buf.getvalue())
    font_file[NameObject("/Length1")] = __import__("pypdf").generic.NumberObject(len(buf.getvalue()))

# 所有规则必须按预期匹配；任何未应用项会阻止输出，不能悄悄漏改。
for entry in entries:
    found = sum(x["page"] == entry["page"] and x["old"] == entry["old"] for x in log)
    assert found == entry.get("expected_count", 1), ("匹配数不符", entry["page"], entry["old"], found)
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == doc["source_sha256"]
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
staging = OUTPUT.with_name(OUTPUT.name + ".part")
assert not staging.exists()
writer.write(staging)
staging.replace(OUTPUT)
(ROOT / "translation_changes.json").write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
(ROOT / "glyph_fills.json").write_text(json.dumps(filled, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"output": str(OUTPUT), "pages": len(writer.pages), "changed_pages": changed_pages, "replacements": len(log)}, ensure_ascii=False))
