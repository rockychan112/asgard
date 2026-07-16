"""Bake the demo page: design/demo.html (template with __POOL_JSON__ placeholder)
+ design/demo_data.json  ->  docs/index.html (self-contained, works from file:// too).

    python design/inject_demo.py
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
template = (ROOT / "design" / "demo.html").read_text(encoding="utf-8")
data = (ROOT / "design" / "demo_data.json").read_text(encoding="utf-8").strip()
data = data.replace("</", "<\\/")  # keep the inline <script> block unbreakable
out = template.replace("__POOL_JSON__", data)
(ROOT / "docs" / "index.html").write_text(out, encoding="utf-8")
print(f"baked docs/index.html ({len(out)//1024} KB, pool inlined)")
