from coterie_agents.validators import validate_crew, validate_store


def test_validate_crew_basic_migration():
    c = validate_crew({"name": "Jet", "role": "runner", "status": "busy", "task": "Wipe rig"})
    assert c["tasks"] == ["Wipe rig"]
    assert c["status"] == "busy"


def test_validate_store_list_and_map():
    s = validate_store(
        [
            {"name": "Mixie", "role": "chemist", "tasks": "Mix"},
            {"role": "tech"},  # missing name becomes "unknown"
        ]
    )
    assert "Mixie" in s and "unknown" in s
