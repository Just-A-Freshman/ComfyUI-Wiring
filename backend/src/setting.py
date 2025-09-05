from typing import List, Dict, Union, Any
from pathlib import Path
import json



CONFIG = Path(__file__).parent / "config"
TEMPLATE = CONFIG / "template.json"
NODE_OPTIONS = CONFIG / "node_options.json"
GROUP_OPTIONS = CONFIG / "group_options.json"
COLLAPSE_WIDTH = 150
COLLAPSE_HEIGHT = 30


class NodeOptions(object):
    gap_x: int = 100
    gap_y: int = 50
    max_span: int = 6
    size_align: bool = True
    set_node: bool = False
    fixed_fold_nodes: List[str] = []
    fixed_unfold_nodes: List[str] = []

    @classmethod
    def load_setting(cls) -> None:
        with open(NODE_OPTIONS, "r", encoding="utf-8") as f:
            options: dict = json.load(f)
            cls.update_setting(options)

    @classmethod
    def update_setting(cls, options: Dict[str, Any]) -> None:
        cls.gap_x = options.get("gap_x", 100)
        cls.gap_y = options.get("gap_y", 80)
        cls.max_span = options.get("max_span", 6)
        cls.size_align = bool(options.get("size_align", True))
        cls.set_node = bool(options.get("set_node", False))
        cls.fixed_fold_nodes = options.get("fixed_fold_nodes", [])
        cls.fixed_unfold_nodes = options.get("fixed_unfold_nodes", [])



class GroupOptions(object):
    group_contain_propertion: float = 0.8
    same_group_node_propertion: float = 0.9
    padding: int = 20
    heading_size_multiplier: int = 2
    undistrubuted_x: int = -1000
    undistrubuted_width: int = 500
    undistrubuted_height: int = 200
    undistrubuted_y_step: int = 300

    @classmethod
    def load_setting(cls) -> None:
        with open(GROUP_OPTIONS, "r", encoding="utf-8") as f:
            options: dict = json.load(f)
            cls.update_setting(options)

    @classmethod
    def update_setting(cls, options: Dict[str, Union[int, bool]]) -> None:
        cls.group_contain_propertion = options.get("group_contain_propertion", 0.8)
        cls.same_group_node_propertion = options.get("same_group_node_propertion", 0.9)
        cls.padding = options.get("padding", 20)
        cls.heading_size_multiplier = options.get("heading_size_multiplier", 2)
        cls.undistrubuted_x = options.get("undistrubuted_x", -1000)
        cls.undistrubuted_width = options.get("undistrubuted_width", 500)
        cls.undistrubuted_height = options.get("undistrubuted_height", 200)
        cls.undistrubuted_y_step = options.get("undistrubuted_y_step", 300)

