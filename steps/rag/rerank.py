from zenml import step
from publish_assist.application.networks.embeddings import CrossEncoderModelSingleton

@step
def rerank_chunks(topic: str, retrieval: dict, top_n: int = 5) -> dict:
    chunks = retrieval["chunks"]
    if not chunks:
        return retrieval

    reranker = CrossEncoderModelSingleton()
    pairs = [(topic, c["text"]) for c in chunks]
    scores = reranker.score(pairs)

    scored = list(zip(chunks, scores))
    scored.sort(key=lambda x: x[1], reverse=True)

    reranked = []
    for c, s in scored[:top_n]:
        c["rerank_score"] = s
        reranked.append(c)

    return {
        "kind": retrieval["kind"],
        "chunks": reranked,
        "reranker": "cross_encoder",
    }
