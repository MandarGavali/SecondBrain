import math

from secondbrain.config import settings
from secondbrain.core.logger import get_logger
from secondbrain.lomcp import cache
from secondbrain.lomcp.specs import embedding_text, schema_tokens, spec_hash, tool_schema

logger = get_logger("lomcp.predictor")


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def select_names(
    scores: dict[str, float],
    top_k: int,
    margin: float,
    min_sim: float,
    always_include: list[str],
) -> list[str]:
    """Pick tools close to the best score, always keep core tools, never return an empty set."""
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    best = ranked[0][1] if ranked else 0.0
    chosen = [n for n, s in ranked if s >= min_sim and s >= best - margin][:top_k]
    for name in always_include:
        if name in scores and name not in chosen:
            chosen.append(name)
    if not chosen:  # fail safe: expose everything
        chosen = [n for n, _ in ranked]
    return chosen


class ToolIndex:
    def __init__(self, tools, embedder=None):
        self.tools = list(tools)
        self._embedder = embedder
        self.entries: dict[str, dict] | None = None

    @property
    def embedder(self):
        if self._embedder is None:
            from secondbrain.rag.embeddings.gemini_embeddings import get_embedding_model

            self._embedder = get_embedding_model()
        return self._embedder

    def build(self) -> None:
        entries: dict[str, dict] = {}
        missing: list[str] = []
        for tool in self.tools:
            schema = tool_schema(tool)
            digest = spec_hash(tool.name, tool.description, schema)
            cache.set_json(f"lomcp:schema:{tool.name}:{digest}", schema)
            vec = cache.get_json(f"lomcp:vec:{tool.name}:{digest}")
            entries[tool.name] = {
                "schema": schema,
                "hash": digest,
                "vec": vec,
                "tokens": schema_tokens(schema),
                "text": embedding_text(tool),
            }
            if vec is None:
                missing.append(tool.name)
        if missing:
            vectors = self.embedder.embed_documents([entries[n]["text"] for n in missing])
            for name, vec in zip(missing, vectors):
                entries[name]["vec"] = vec
                cache.set_json(f"lomcp:vec:{name}:{entries[name]['hash']}", vec)
        self.entries = entries

    def predict(self, query: str) -> dict:
        if self.entries is None:
            self.build()
        qvec = self.embedder.embed_query(query)
        scores = {n: cosine(qvec, e["vec"]) for n, e in self.entries.items()}
        always = [n.strip() for n in settings.lomcp_always_include.split(",") if n.strip()]
        names = select_names(
            scores, settings.lomcp_top_k, settings.lomcp_margin, settings.lomcp_min_sim, always
        )
        return {
            "names": names,
            "scores": {n: round(s, 4) for n, s in scores.items()},
            "tokens_full": sum(e["tokens"] for e in self.entries.values()),
            "tokens_selected": sum(self.entries[n]["tokens"] for n in names),
        }


_index: ToolIndex | None = None


def get_index() -> ToolIndex:
    global _index
    if _index is None:
        from secondbrain.agent.tools import get_tools

        _index = ToolIndex(get_tools())
    return _index


def predict_tools(query: str) -> dict:
    return get_index().predict(query)
