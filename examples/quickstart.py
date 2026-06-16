"""Minimal end-to-end example for the Tessera Python SDK.

    TESSERA_API_KEY=tsk_live_... python examples/quickstart.py
"""

from __future__ import annotations

from tessera_memory import Tessera


def main() -> None:
    client = Tessera()

    client.memories.add(
        content="Ada prefers dark roast coffee.",
        user_id="ada",
        role="user",
    )

    hits = client.search(query="what coffee does Ada like?", top_k=5)
    print("search hits:", hits)

    answer = client.query(query="what coffee does Ada like?", mode="chat")
    print("query answer:", answer)


if __name__ == "__main__":
    main()
