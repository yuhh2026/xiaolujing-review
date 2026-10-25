"""小绿鲸PDF校译通用入口；不调用翻译API、不自动改写研究结论。"""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys
import pymupdf as fitz
from PIL import Image, ImageChops


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def inspect(args):
    source = Path(args.pdf).resolve()
    folder = Path(args.work).resolve() / sha(source)
    info = folder / "inspection.json"
    if info.exists():
        print(json.dumps({"cached": True, "index": str(info)}))
        return
    folder.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(source)
    result = {"source": str(source), "sha256": sha(source), "pages": []}
    for n, page in enumerate(doc, 1):
        # 每页单独缓存，助手可按需读取，避免重复导入全文。
        (folder / f"page_{n:03}.txt").write_text(page.get_text(sort=True), encoding="utf-8")
        result["pages"].append({"page": n, "size": list(page.rect), "fonts": [{"xref": x[0], "name": x[3], "resource": x[4]} for x in page.get_fonts()], "characters": len(page.get_text())})
    write_json(info, result)
    print(json.dumps({"pages": len(doc), "index": str(info), "sha256": result["sha256"]}))


def verify(args):
    before, after = fitz.open(args.before), fitz.open(args.after)
    edits = json.loads(Path(args.changes).read_text(encoding="utf-8"))
    changed_pages = {x["page"] for x in edits}
    assert len(before) == len(after), "页数变化"
    work = Path(args.work).resolve()
    work.mkdir(parents=True, exist_ok=True)
    rows = []
    for n, (a, b) in enumerate(zip(before, after), 1):
        assert a.rect == b.rect and a.rotation == b.rotation, (n, "页面尺寸或方向变化")
        assert str(a.get_drawings()) == str(b.get_drawings()), (n, "矢量图表变化")
        def images(doc, page):
            return [hashlib.sha256(doc.extract_image(x[0])["image"]).hexdigest() for x in page.get_images(full=True)]
        assert images(before, a) == images(after, b), (n, "图片变化")
        p, q = a.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False), b.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
        x = Image.frombytes("RGB", (p.width, p.height), p.samples)
        y = Image.frombytes("RGB", (q.width, q.height), q.samples)
        diff = ImageChops.difference(x, y)
        pixels = diff.convert("L").point(lambda v: 255 if v else 0).histogram()[255]
        if n not in changed_pages:
            assert pixels == 0, (n, "未改页面出现像素变化")
        else:
            y.save(work / f"corrected_{n:03}.png")
            box = diff.getbbox()
            if box:
                margin = 12
                box = (max(0, box[0]-margin), max(0, box[1]-margin), min(p.width, box[2]+margin), min(p.height, box[3]+margin))
                x.crop(box).save(work / f"before_detail_{n:03}.png")
                y.crop(box).save(work / f"after_detail_{n:03}.png")
        rows.append({"page": n, "changed_pixels": pixels})
    result = {"before_sha256": sha(args.before), "after_sha256": sha(args.after), "replacements": len(edits), "pages": rows, "visual_review_required": sorted(changed_pages)}
    write_json(work / "verification.json", result)
    print(json.dumps({"pages": len(rows), "replacements": len(edits), "structural_checks_passed": True, "visual_review_required": sorted(changed_pages)}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("inspect")
    p.add_argument("--pdf", required=True)
    p.add_argument("--work", required=True)
    p = commands.add_parser("apply")
    for name in ["pdf", "manifest", "output", "work"]:
        p.add_argument("--" + name, required=True)
    p.add_argument("--fallback-font")
    p = commands.add_parser("verify")
    for name in ["before", "after", "changes", "work"]:
        p.add_argument("--" + name, required=True)
    args = parser.parse_args()
    if args.command == "inspect":
        inspect(args)
    elif args.command == "verify":
        verify(args)
    else:
        # 确定性编辑器单独运行；无需将源码加载到模型上下文。
        raise SystemExit(subprocess.call([sys.executable, str(Path(__file__).with_name("content_patch.py")), *sys.argv[2:]]))


if __name__ == "__main__":
    main()
