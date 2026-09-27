"""验证 active manifest、当前语料与双索引是否完全一致。"""

import json

from rag_one.state import verify_project_state


def main() -> None:
    print(json.dumps(verify_project_state(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

