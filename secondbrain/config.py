"""Feature flags and thresholds.

Values are read from the environment on EVERY access, so tests and the evaluation
harness can switch configurations at runtime (os.environ[...] = ...).
"""
import os

# attribute -> (ENV_NAME, type, default)
_DEFS = {
    # orchestration
    "graph_mode": ("GRAPH_MODE", str, "agent"),
    "force_route": ("FORCE_ROUTE", str, ""),
    "enable_router": ("ENABLE_ROUTER", bool, True),
    "router_mode": ("ROUTER_MODE", str, "hybrid"),
    "simple_k": ("SIMPLE_K", int, 4),
    "retry_k": ("RETRY_K", int, 6),
    "max_agent_steps": ("MAX_AGENT_STEPS", int, 4),
    # LO-MCP
    "enable_lomcp": ("ENABLE_LOMCP", bool, True),
    "lomcp_top_k": ("LOMCP_TOP_K", int, 3),
    "lomcp_margin": ("LOMCP_MARGIN", float, 0.08),
    "lomcp_min_sim": ("LOMCP_MIN_SIM", float, 0.30),
    "lomcp_always_include": ("LOMCP_ALWAYS_INCLUDE", str, "search_documents"),
    # verification
    "enable_verify": ("ENABLE_VERIFY", bool, True),
    "verify_simple_llm": ("VERIFY_SIMPLE_LLM", bool, False),
    "w_retrieval": ("CONF_W_RETRIEVAL", float, 0.30),
    "w_relevance": ("CONF_W_RELEVANCE", float, 0.20),
    "w_grounded": ("CONF_W_GROUNDED", float, 0.50),
    "score_rel_min": ("CONF_SCORE_REL_MIN", float, 0.50),
    "conf_high": ("CONF_HIGH", float, 0.70),
    "conf_medium": ("CONF_MEDIUM", float, 0.45),
    "conf_abstain": ("CONF_ABSTAIN", float, 0.30),
    "max_retries": ("MAX_RETRIES", int, 1),
    # ingestion quality
    "quality_enabled": ("QUALITY_ENABLED", bool, True),
    "quality_min_chars": ("QUALITY_MIN_CHARS", int, 60),
    "quality_min_alpha": ("QUALITY_MIN_ALPHA", float, 0.55),
    # AAM
    "enable_aam": ("ENABLE_AAM", bool, True),
    "aam_mode": ("AAM_MODE", str, "background"),
    "aam_sim_threshold": ("AAM_SIM_THRESHOLD", float, 0.60),
    "aam_max_facts": ("AAM_MAX_FACTS", int, 8),
}


class _Settings:
    def __getattr__(self, name):
        try:
            env, typ, default = _DEFS[name]
        except KeyError:
            raise AttributeError(name) from None
        raw = os.getenv(env)
        if raw is None or raw.strip() == "":
            return default
        raw = raw.strip()
        if typ is bool:
            return raw.lower() in {"1", "true", "yes", "on"}
        try:
            return typ(raw)
        except ValueError:
            return default


settings = _Settings()
