"""Tests the conversation-history logic in rag_chain.py with a fake LLM client."""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from rag_chain import RagPipeline, MAX_HISTORY_TURNS


class FakeLLM:
    def __init__(self):
        self.last_messages = None
        outer = self
        class _Comp:
            def create(self, **kw):
                outer.last_messages = kw["messages"]
                class R:  # mimic OpenAI response shape
                    choices = [type("C", (), {"message": type("M", (), {"content": "ok"})()})()]
                return R()
        self.chat = type("Chat", (), {"completions": _Comp()})()


def chunk(t="x"):
    return {"text": t, "topic": "normalization", "source_file": "n.txt", "distance": 0.1}


def test_short_followup_borrows_previous_question_for_retrieval():
    hist = [{"role": "user", "content": "What is 3NF?"}, {"role": "assistant", "content": "..."}]
    q = RagPipeline._retrieval_query("give an example", hist)
    assert q == "What is 3NF? give an example"


def test_long_question_is_not_modified():
    hist = [{"role": "user", "content": "What is 3NF?"}, {"role": "assistant", "content": "..."}]
    long_q = "How does BCNF differ from third normal form in practice?"
    assert RagPipeline._retrieval_query(long_q, hist) == long_q


def test_no_history_leaves_question_alone():
    assert RagPipeline._retrieval_query("why?", []) == "why?"


def test_generate_sends_history_then_context_only_on_last_turn():
    p = RagPipeline(); p._llm_client = FakeLLM()
    hist = [{"role": "user", "content": "What is 3NF?"}, {"role": "assistant", "content": "A form."}]
    p.generate("give an example", [chunk("CONTEXT-TEXT")], hist)
    msgs = p._llm_client.last_messages
    assert [m["role"] for m in msgs] == ["system", "user", "assistant", "user"]
    assert "CONTEXT-TEXT" in msgs[-1]["content"]
    assert "CONTEXT-TEXT" not in msgs[1]["content"]


def test_history_is_capped():
    p = RagPipeline(); p._llm_client = FakeLLM()
    hist = []
    for i in range(10):
        hist += [{"role": "user", "content": f"q{i}"}, {"role": "assistant", "content": f"a{i}"}]
    p.generate("next", [chunk()], hist)
    msgs = p._llm_client.last_messages
    assert len(msgs) == 1 + MAX_HISTORY_TURNS * 2 + 1   # system + capped history + current
    assert msgs[1]["content"] == f"q{10 - MAX_HISTORY_TURNS}"
