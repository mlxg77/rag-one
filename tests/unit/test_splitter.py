"""切分逻辑单元测试：块大小 / 断点 / 重叠 / id 与 metadata 规则。全程离线。

运行：python -X utf8 -m pytest tests/unit/test_splitter.py -v
"""

from rag_one.ingestion.splitter import split_records, split_text


def test_short_text_single_chunk():
    assert split_text("很短的一段话。") == ["很短的一段话。"]


def test_empty_and_blank_text_return_empty():
    assert split_text("") == []
    assert split_text("   \n\n  ") == []


def test_long_text_chunks_respect_size():
    text = "这是一句测试文本。" * 300  # 2700 字符
    chunks = split_text(text, chunk_size=200, chunk_overlap=50)
    assert len(chunks) > 1
    assert all(len(c) <= 200 for c in chunks)


def test_overlap_ge_chunk_size_still_terminates():
    # overlap >= chunk_size：start 每次至少前进 1，必须能终止（防死循环护栏）
    chunks = split_text("x" * 100, chunk_size=10, chunk_overlap=10)
    assert len(chunks) > 1


def test_boundary_prefers_sentence_end():
    # 断点必须落在句子边界：除最后一块外每块都以句号收尾
    text = "句子内容测试。" * 100
    chunks = split_text(text, chunk_size=100, chunk_overlap=20)
    assert len(chunks) > 1
    assert all(c.endswith("。") for c in chunks)


def test_adjacent_chunks_overlap():
    text = "段落内容ABCDEF。" * 50
    chunks = split_text(text, chunk_size=100, chunk_overlap=30)
    assert len(chunks) >= 2
    # 前一块的尾部片段应出现在后一块里（重叠生效）
    tail = chunks[0][-20:]
    assert tail in chunks[1]


def test_split_records_id_without_page():
    records = [{"text": "短内容", "metadata": {"source": "a.md"}}]
    chunks = split_records(records)
    assert len(chunks) == 1
    assert chunks[0]["id"] == "a.md:chunk-0"
    assert chunks[0]["metadata"] == {
        "source": "a.md",
        "chunk_index": 0,
        "start_char": 0,
        "end_char": 3,
    }
    assert "page" not in chunks[0]["metadata"]  # txt/md 不带 page 键


def test_split_records_id_with_page():
    records = [{"text": "PDF 内容", "metadata": {"source": "10-faq.pdf", "page": 3}}]
    chunks = split_records(records)
    assert chunks[0]["id"] == "10-faq.pdf:page-3:chunk-0"
    assert chunks[0]["metadata"] == {
        "source": "10-faq.pdf",
        "chunk_index": 0,
        "start_char": 0,
        "end_char": 6,
        "page": 3,
    }


def test_split_records_long_text_index_increases():
    records = [{"text": "内容。" * 500, "metadata": {"source": "a.md"}}]
    chunks = split_records(records)
    assert len(chunks) > 1
    assert [c["metadata"]["chunk_index"] for c in chunks] == list(range(len(chunks)))
    assert [c["id"] for c in chunks] == [f"a.md:chunk-{i}" for i in range(len(chunks))]
