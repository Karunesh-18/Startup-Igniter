"""Tests for ProjectMemoryManager's persist_callback integration point.

write_memory() previously had a "production path" comment claiming Supabase
persistence but never actually called anything -- every write to a
non-mock-store manager silently vanished. This is the integration point:
ai/ stays decoupled from backend/db (no SQLAlchemy import here), but a
caller that DOES have a DB session (backend/workers/tasks.py) can now pass
a callback and have writes actually land somewhere.
"""

from ai.memory.project_memory import MemoryEntry, ProjectMemoryManager


def test_write_memory_invokes_persist_callback_when_not_mock():
    persisted: list[MemoryEntry] = []
    manager = ProjectMemoryManager(use_mock_store=False, persist_callback=persisted.append)

    entry = manager.write_memory(
        project_id="proj-1", key="idea_analysis", value={"summary": "test"}, source_phase="idea"
    )

    assert len(persisted) == 1
    assert persisted[0] is entry
    assert persisted[0].key == "idea_analysis"


def test_write_memory_survives_persist_callback_raising():
    def failing_callback(entry: MemoryEntry) -> None:
        raise RuntimeError("db unavailable")

    manager = ProjectMemoryManager(use_mock_store=False, persist_callback=failing_callback)

    # Should not raise -- a persistence failure must not sink the caller's run.
    entry = manager.write_memory(
        project_id="proj-1", key="idea_analysis", value={"summary": "test"}, source_phase="idea"
    )
    assert entry.key == "idea_analysis"


def test_write_memory_without_callback_is_a_documented_noop():
    """No callback configured -- write still succeeds and returns a real
    MemoryEntry (with a real or mock embedding, per AI_USE_REAL_EMBEDDINGS),
    it just isn't persisted anywhere. This matches the pre-existing contract
    for callers that only care about mock_store=True."""
    manager = ProjectMemoryManager(use_mock_store=False)
    entry = manager.write_memory(
        project_id="proj-1", key="idea_analysis", value={"summary": "test"}, source_phase="idea"
    )
    assert entry.key == "idea_analysis"
    assert entry.embedding  # a real or mock embedding was still computed


def test_mock_store_ignores_persist_callback():
    """use_mock_store=True keeps using the in-memory dict, even if a callback
    is also supplied -- the callback is only for the non-mock production path."""
    persisted: list[MemoryEntry] = []
    manager = ProjectMemoryManager(use_mock_store=True, persist_callback=persisted.append)

    manager.write_memory(project_id="proj-1", key="k", value={"v": 1}, source_phase="idea")

    assert persisted == []
    assert manager.get_memory_by_key("proj-1", "k") is not None
