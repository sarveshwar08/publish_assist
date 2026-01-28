from zenml import step

def build_compressed_context(
    chunks: list[str],
    max_chars: int,
) -> str:
    context = []
    current_len = 0

    for chunk in chunks:
        if current_len + len(chunk) > max_chars:
            remaining = max_chars - current_len
            if remaining > 0:
                context.append(chunk[:remaining])
            break

        context.append(chunk)
        current_len += len(chunk)

    return "\n\n".join(context)

@step
def build_context(style: dict, content: dict) -> dict:
    style_ctx = [c["text"] for c in style["chunks"]]
    content_ctx = [c["text"] for c in content["chunks"]]
    
    style_context = build_compressed_context(
        style_ctx,
        max_chars=1200,
    )

    content_context = build_compressed_context(
        content_ctx,
        max_chars=2000,
    )

    sources = [
        {
            "doc_id": c["doc_id"],
            "chunk_id": c["chunk_id"],
            "score": c.get("rerank_score", c["score"]),
        }
        for c in content["chunks"]
    ]

    return {
        "style_context": style_context,
        "content_context": content_context,
        "sources": sources,
    }
