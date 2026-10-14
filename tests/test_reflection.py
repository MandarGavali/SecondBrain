import json

from secondbrain.memory.reflection import reflect_session


class FakeMemory:
    def __init__(self):
        self.items = [{"id": "m1", "memory": "User works from home 2 days a week", "score": 0.9}]
        self.saved = []

    def search_memory(self, user_id, query, limit=5):
        return {"results": list(self.items)}

    def save_memory(self, user_id, messages, metadata=None, infer=True):
        self.saved.append(messages[0]["content"])
        return {"results": [{"id": "m2", "memory": messages[0]["content"]}]}


class FakeStore:
    def __init__(self):
        self.dead = {}

    def deprecated_ids(self, user_id):
        return set(self.dead)

    def deprecate(self, memory_id, user_id, old_text, superseded_by, new_text, reason):
        self.dead[memory_id] = (superseded_by, new_text)


def fake_llm(prompt: str) -> str:
    if "Existing memories" in prompt:
        return json.dumps({"1": "CONTRADICTS"})
    return json.dumps(["User now works from home 3 days a week"])


def test_contradiction_deprecates_old_and_adds_new():
    mem, store = FakeMemory(), FakeStore()
    stats = reflect_session("u1", [{"role": "user", "content": "I work from home 3 days now"}],
                            memory=mem, store=store, llm_call=fake_llm)
    assert stats == {"facts": 1, "added": 1, "skipped_same": 0, "deprecated": 1}
    assert "m1" in store.dead and store.dead["m1"][0] == "m2"
    assert mem.saved == ["User now works from home 3 days a week"]


def test_same_fact_is_not_duplicated():
    mem, store = FakeMemory(), FakeStore()

    def llm(prompt):
        return json.dumps({"1": "SAME"}) if "Existing memories" in prompt else json.dumps(["User works from home 2 days a week"])

    stats = reflect_session("u1", [{"role": "user", "content": "x"}], memory=mem, store=store, llm_call=llm)
    assert stats["skipped_same"] == 1 and stats["added"] == 0 and not store.dead


def test_bad_llm_output_is_safe():
    mem, store = FakeMemory(), FakeStore()
    stats = reflect_session("u1", [{"role": "user", "content": "x"}], memory=mem, store=store,
                            llm_call=lambda p: "not json")
    assert stats["facts"] == 0 and stats["added"] == 0
