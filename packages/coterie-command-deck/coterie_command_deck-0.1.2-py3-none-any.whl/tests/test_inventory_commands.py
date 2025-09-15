import json
from pathlib import Path
from typing import Any

from coterie_agents.commands import inventory as inv


def setup_tmp_inventory(tmp_path: Path) -> Path:
    p = tmp_path / "inventory.json"
    p.write_text(json.dumps({}), encoding="utf-8")
    return p


def test_add_list_value(tmp_path: Any, monkeypatch: Any, capsys: Any):
    inv_path = setup_tmp_inventory(tmp_path)
    monkeypatch.setattr(inv, "INVENTORY_FILE", inv_path)

    # add product
    inv.run(["inv_add", "soap01", "Blue Soap", "10", "gal", "3", "12.50"], {})
    # list
    inv.run(["inv_list"], {})
    out = capsys.readouterr().out
    assert "Blue Soap" in out

    # value
    inv.run(["inv_value"], {})
    out = capsys.readouterr().out
    assert "TOTAL INVENTORY VALUE" in out


def test_remove_then_check(tmp_path: Any, monkeypatch: Any, capsys: Any):
    inv_path = setup_tmp_inventory(tmp_path)
    monkeypatch.setattr(inv, "INVENTORY_FILE", inv_path)

    inv.run(["inv_add", "soap01", "Blue Soap", "10", "gal", "3", "12.50"], {})
    inv.run(["inv_remove", "soap01"], {})
    inv.run(["inv_check"], {})
    out = capsys.readouterr().out
    assert "Inventory is empty" in out or "All products above reorder level" in out
