#!/usr/bin/env python3
"""单文件 HTML 页面校验脚本（仅依赖 Python 标准库）

检查项：
  1. 标签结构是否配平（正确处理 HTML5 可选结束标签与 void 元素）
  2. id 属性是否唯一
  3. 页内锚点 (#xxx) 是否都能找到对应元素
  4. 相对路径的本地资源引用是否真实存在
  5. 必要的元信息（DOCTYPE / charset / viewport / title / html lang）
  6. 自包含性统计（有多少外部引用）

用法：
    python3 scripts/check_html.py index.html

退出码：
    0 = 全部通过（可能有警告）；1 = 存在错误
"""

from __future__ import annotations

import sys
from html.parser import HTMLParser
from pathlib import Path

VOID_ELEMENTS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}

P_CLOSERS = {
    "address", "article", "aside", "blockquote", "details", "div", "dl",
    "fieldset", "figcaption", "figure", "footer", "form", "h1", "h2", "h3",
    "h4", "h5", "h6", "header", "hgroup", "hr", "main", "nav", "ol", "p",
    "pre", "section", "table", "ul",
}

# 这些元素在 HTML5 里允许省略结束标签，遇到同类或父级结束时会自动闭合
IMPLICIT_CLOSE = {
    "li": {"li"},
    "dt": {"dt", "dd"},
    "dd": {"dd", "dt"},
    "p": P_CLOSERS,
    "option": {"option", "optgroup"},
    "optgroup": {"optgroup"},
    "rt": {"rt", "rp"},
    "rp": {"rt", "rp"},
    "caption": {"caption", "colgroup", "thead", "tbody", "tfoot", "tr"},
    "colgroup": {"caption", "thead", "tbody", "tfoot", "tr"},
    "thead": {"tbody", "tfoot"},
    "tbody": {"tbody", "tfoot"},
    "tfoot": {"tbody"},
    "tr": {"tr", "thead", "tbody", "tfoot"},
    "td": {"td", "th", "tr", "thead", "tbody", "tfoot"},
    "th": {"td", "th", "tr", "thead", "tbody", "tfoot"},
}

EXTERNAL_PREFIXES = (
    "http://", "https://", "//", "mailto:", "tel:", "data:",
    "javascript:", "ftp://",
)


class PageChecker(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, int]] = []
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.id_map: dict[str, list[int]] = {}
        self.anchor_refs: list[tuple[str, int]] = []
        self.local_refs: list[tuple[str, str, int]] = []
        self.external_refs: list[tuple[str, int]] = []
        self.has_doctype = False
        self.has_title = False
        self.has_charset = False
        self.has_viewport = False
        self.html_lang: str | None = None
        self.max_depth = 0
        self.total_tags = 0
        self.tag_kinds: set[str] = set()

    def _line(self) -> int:
        return self.getpos()[0]

    def _stack_names(self) -> str:
        return " > ".join(t for t, _ in self.stack) if self.stack else "（空）"

    def _classify_ref(self, value: str, attr: str, line: int) -> None:
        v = value.strip()
        if not v:
            return
        low = v.lower()
        if low.startswith("#"):
            target = v[1:]
            if target:
                self.anchor_refs.append((target, line))
        elif low.startswith(EXTERNAL_PREFIXES):
            self.external_refs.append((v, line))
        else:
            self.local_refs.append((v, attr, line))

    def _open(self, tag: str, attrs: list, line: int, self_closing: bool) -> None:
        tag = tag.lower()
        self.total_tags += 1
        self.tag_kinds.add(tag)

        a: dict[str, str] = {}
        for k, v in attrs:
            a[k.lower()] = v if v is not None else ""

        if a.get("id"):
            self.id_map.setdefault(a["id"], []).append(line)
        if tag == "html" and a.get("lang"):
            self.html_lang = a["lang"]
        if tag == "title":
            self.has_title = True
        if tag == "meta":
            if "charset" in a:
                self.has_charset = True
            if a.get("name", "").lower() == "viewport":
                self.has_viewport = True

        for attr in ("href", "src", "action", "poster"):
            if a.get(attr):
                self._classify_ref(a[attr], attr, line)

        if tag in VOID_ELEMENTS or self_closing:
            return

        while self.stack and tag in IMPLICIT_CLOSE.get(self.stack[-1][0], set()):
            self.stack.pop()
        self.stack.append((tag, line))
        self.max_depth = max(self.max_depth, len(self.stack))

    def handle_decl(self, decl: str) -> None:
        if decl.lower().startswith("doctype"):
            self.has_doctype = True

    def handle_starttag(self, tag: str, attrs: list) -> None:
        self._open(tag, attrs, self._line(), False)

    def handle_startendtag(self, tag: str, attrs: list) -> None:
        self._open(tag, attrs, self._line(), True)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        line = self._line()

        if tag in VOID_ELEMENTS:
            self.warnings.append(f"第 {line} 行：</{tag}> 是 void 元素，不应有结束标签")
            return
        if not any(t == tag for t, _ in self.stack):
            self.errors.append(
                f"第 {line} 行：</{tag}> 找不到对应的开始标签"
                f"（当前未闭合：{self._stack_names()}）"
            )
            return

        while self.stack and self.stack[-1][0] != tag:
            name, open_line = self.stack.pop()
            if name in IMPLICIT_CLOSE:
                self.warnings.append(
                    f"第 {open_line} 行：<{name}> 被 </{tag}> 隐式闭合"
                    "（HTML5 允许，但建议显式写结束标签）"
                )
            else:
                self.errors.append(
                    f"第 {open_line} 行：<{name}> 尚未闭合，就被第 {line} 行的 </{tag}> 打断了"
                )
        if self.stack:
            self.stack.pop()

    def finish(self) -> None:
        for name, line in self.stack:
            if name in IMPLICIT_CLOSE:
                self.warnings.append(f"第 {line} 行：<{name}> 到文件结尾仍未闭合（HTML5 允许）")
            else:
                self.errors.append(f"第 {line} 行：<{name}> 到文件结尾仍未闭合")


def main() -> int:
    target = Path(sys.argv[1] if len(sys.argv) > 1 else "index.html")
    if not target.is_file():
        print(f"[错误] 找不到文件：{target}")
        return 1

    raw = target.read_bytes()
    text = raw.decode("utf-8", errors="replace")

    checker = PageChecker()
    checker.feed(text)
    checker.close()
    checker.finish()

    base_dir = target.parent
    problems = list(checker.errors)
    notes = list(checker.warnings)

    # 检查 2：id 唯一性
    dup_ids = {k: v for k, v in checker.id_map.items() if len(v) > 1}
    for key, lines in dup_ids.items():
        where = "、".join(f"第 {n} 行" for n in lines)
        problems.append(f"id=\"{key}\" 重复出现：{where}")

    # 检查 3：页内锚点
    missing_anchors = [
        (a, line) for a, line in checker.anchor_refs if a not in checker.id_map
    ]
    for anchor, line in missing_anchors:
        problems.append(f"第 {line} 行：锚点 #{anchor} 在页面里找不到对应的 id")

    # 检查 4：本地资源
    missing_files = []
    for ref, attr, line in checker.local_refs:
        clean = ref.split("?")[0].split("#")[0]
        if not clean:
            continue
        if not (base_dir / clean).exists():
            missing_files.append((ref, attr, line))
    for ref, attr, line in missing_files:
        problems.append(f"第 {line} 行：{attr}=\"{ref}\" 指向的本地文件不存在")

    # 检查 5：必要元信息
    if not checker.has_doctype:
        problems.append("缺少 <!DOCTYPE html> 声明")
    if not checker.has_charset:
        problems.append("缺少 <meta charset=\"...\"> 声明")
    if not checker.has_viewport:
        problems.append("缺少 viewport meta（移动端会按桌面宽度渲染）")
    if not checker.has_title:
        problems.append("缺少 <title>，浏览器标签页会显示文件名")
    if not checker.html_lang:
        problems.append("<html> 缺少 lang 属性，影响屏幕阅读器与搜索引擎")

    # 输出报告
    print("=" * 62)
    print(f"页面校验：{target}")
    print("=" * 62)
    print(f"  字节数         {len(raw):,}")
    print(f"  字符数         {len(text):,}")
    print(f"  标签总数       {checker.total_tags:,}")
    print(f"  标签种类       {len(checker.tag_kinds)}")
    print(f"  最大嵌套深度   {checker.max_depth}")
    print(f"  页面内 id 数   {len(checker.id_map):,}")
    print(f"  锚点链接数     {len(checker.anchor_refs):,}")
    print(f"  外部引用数     {len(checker.external_refs):,}")
    if checker.external_refs:
        for ref, line in checker.external_refs[:10]:
            print(f"      · 第 {line} 行  {ref[:70]}")
    print()

    labels = [
        ("标签结构配平", not checker.errors),
        ("id 唯一性", not dup_ids),
        ("页内锚点完整", not missing_anchors),
        ("本地资源存在", not missing_files),
        (
            "必要元信息",
            checker.has_doctype and checker.has_charset and checker.has_viewport
            and checker.has_title and bool(checker.html_lang),
        ),
    ]
    for name, ok in labels:
        print(f"  [{'通过' if ok else '失败'}] {name}")

    if notes:
        print()
        print(f"警告 {len(notes)} 条：")
        for n in notes[:20]:
            print(f"  - {n}")
        if len(notes) > 20:
            print(f"  ...（还有 {len(notes) - 20} 条）")

    print()
    if problems:
        print(f"发现 {len(problems)} 个问题：")
        for p in problems[:40]:
            print(f"  [x] {p}")
        if len(problems) > 40:
            print(f"  ...（还有 {len(problems) - 40} 个）")
        print()
        print("校验未通过。")
        return 1

    print("校验全部通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
