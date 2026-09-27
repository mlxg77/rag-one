"""加载器单元测试：md/txt 读取、目录过滤排序、PDF 逐页。全程离线。

运行：python -X utf8 -m pytest tests/test_loaders.py -v
"""

from src.loaders import PROJECT_ROOT, load_directory, load_file, load_md, load_pdf, load_txt


def test_load_txt_returns_single_record(tmp_path):
    p = tmp_path / "note.txt"
    p.write_text("第一条内容。", encoding="utf-8")
    assert load_txt(p) == [{"text": "第一条内容。", "metadata": {"source": "note.txt"}}]


def test_load_md_keeps_markup(tmp_path):
    p = tmp_path / "doc.md"
    p.write_text("# 标题\n\n正文内容", encoding="utf-8")
    records = load_md(p)
    assert len(records) == 1
    assert records[0]["metadata"]["source"] == "doc.md"
    assert records[0]["text"].startswith("# 标题")  # 保留 # 标记，切分阶段要用


def test_load_txt_empty_skipped(tmp_path):
    p = tmp_path / "empty.txt"
    p.write_text("   \n\n", encoding="utf-8")
    assert load_txt(p) == []


def test_load_txt_missing_file_returns_empty(tmp_path):
    assert load_txt(tmp_path / "nope.txt") == []


def test_load_file_unknown_suffix_skipped(tmp_path, capsys):
    assert load_file(tmp_path / "table.docx") == []
    assert "跳过" in capsys.readouterr().out


def test_load_directory_sorted_and_filtered(tmp_path):
    (tmp_path / "b.md").write_text("B 内容", encoding="utf-8")
    (tmp_path / "a.txt").write_text("A 内容", encoding="utf-8")
    (tmp_path / "c.rst").write_text("C 内容", encoding="utf-8")  # 不支持：跳过
    (tmp_path / "sub").mkdir()  # 子目录：跳过
    records = load_directory(tmp_path)
    # 文件名排序 + 只保留支持的类型
    assert [r["metadata"]["source"] for r in records] == ["a.txt", "b.md"]


def test_load_pdf_real_file_pages_increasing():
    # 用仓库自带 PDF 做轻断言：能提取、页码递增、文本非空
    pdf = PROJECT_ROOT / "data" / "raw" / "10-faq.pdf"
    records = load_pdf(pdf)
    assert records, "10-faq.pdf 应能提取出文本"
    pages = [r["metadata"]["page"] for r in records]
    assert len(set(pages)) == len(pages)          # 无重复页
    assert pages == sorted(pages) and pages[0] >= 1
    assert all(r["metadata"]["source"] == "10-faq.pdf" for r in records)
    assert all(r["text"].strip() for r in records)
