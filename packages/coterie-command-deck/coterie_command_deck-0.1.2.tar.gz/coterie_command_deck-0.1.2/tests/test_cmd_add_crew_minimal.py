import importlib


def test_add_crew_smoke(capsys):
    mod = importlib.import_module("coterie_agents.commands.add_crew")
    ctx = {"store": {}}
    mod.run(ctx["store"], "Jet", "runner")
    assert "Jet" in ctx["store"]
    assert ctx["store"]["Jet"]["role"] == "runner"
