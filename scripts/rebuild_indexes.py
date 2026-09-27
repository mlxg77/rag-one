"""一次构建并原子发布同版本的向量与 BM25 索引。"""

import argparse

from rag_one.indexing.indexer import build_and_publish_indexes
from rag_one.ingestion.splitter import CHUNK_OVERLAP, CHUNK_SIZE


def main() -> None:
    parser = argparse.ArgumentParser(description="构建并发布同版本向量/BM25 索引")
    parser.add_argument("--chunk-size", type=int, default=CHUNK_SIZE)
    parser.add_argument("--chunk-overlap", type=int, default=CHUNK_OVERLAP)
    args = parser.parse_args()
    stats = build_and_publish_indexes(
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )
    print(
        f"已发布 {stats['index_version']}：{stats['docs']} 篇 / {stats['chunks']} chunks / "
        f"{stats['bm25_terms']} BM25 词项 / {stats['publish_duration_ms']} ms"
    )


if __name__ == "__main__":
    main()
