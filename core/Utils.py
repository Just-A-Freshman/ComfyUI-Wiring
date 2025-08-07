from typing import Sequence, Generator, List, Tuple, Dict, Union, Any
from collections import defaultdict
from pathlib import Path
import json

from .header import WorkflowData


CONFIG = Path(__file__).parent / "config"
TEMPLATE = CONFIG / "template.json"
NODE_OPTIONS = CONFIG / "node_options.json"
GROUP_OPTIONS = CONFIG / "group_options.json"
COLLAPSE_WIDTH = 150
COLLAPSE_HEIGHT = 30





class Tool(object):
    @staticmethod
    def flatten_generator(seq: Sequence)-> Generator[Any, Any, None]:
        for item in seq:
            if isinstance(item, list):
                yield from Tool.flatten_generator(item)
            else:
                yield item

    @staticmethod
    def topological_sort(workflow_data: WorkflowData) -> List[List[int]]:
        in_degree = {node.id: 0 for node in workflow_data.nodes}
        out_edges = defaultdict(list)
        for link in workflow_data.links:
            if link.input_node_id in in_degree and link.output_node_id in in_degree:
                out_edges[link.input_node_id].append(link.output_node_id)
                in_degree[link.output_node_id] += 1
        columns = []
        current_degree = in_degree.copy()
        while current_degree:
            zero_degree_nodes = [node for node, deg in current_degree.items() if deg == 0]
            if not zero_degree_nodes:
                raise ValueError("Cycle detected in dependency graph")
            columns.append(zero_degree_nodes)
            for node in zero_degree_nodes:
                del current_degree[node]
                for neighbor in out_edges[node]:
                    if neighbor in current_degree:
                        current_degree[neighbor] -= 1
        return columns
 
    @staticmethod
    def exclude_outliers(data: List, top_n: int = 2, threshold: float = 2) -> None:
        if len(data) <= top_n:
            return
        
        sorted_data = sorted(data, reverse=True)
        top_values = sorted_data[:top_n]
        rest_values = sorted_data[top_n:]
        rest_mean = sum(rest_values) / len(rest_values)
        
        for value in top_values:
            if value / rest_mean > threshold:
                data.remove(value)

    @staticmethod
    def merge_dict_by_key(similar_key_dict: dict[int, list], threshold: int = 1) -> defaultdict[int, list]:
        if not similar_key_dict:
            return defaultdict(list)

        sorted_keys = sorted(similar_key_dict.keys())
        groups = []
        current_group = [sorted_keys[0]]
        
        for key in sorted_keys[1:]:
            if key - current_group[-1] <= threshold:
                current_group.append(key)
            else:
                groups.append(current_group)
                current_group = [key]
        groups.append(current_group)

        result = defaultdict(list)
        for group in groups:
            max_key = max(group)
            merged_values = []
            for key in group:
                merged_values.extend(similar_key_dict[key])
            result[max_key] = merged_values
        return result
    
    @staticmethod
    def rectangle_intersection_area(rect1: Tuple[int, int, int, int], rect2: Tuple[int, int, int, int]) -> float:
        left1, top1, right1, bottom1 = rect1
        left2, top2, right2, bottom2 = rect2
        intersect_left = max(left1, left2)
        intersect_right = min(right1, right2)
        intersect_top = max(top1, top2)
        intersect_bottom = min(bottom1, bottom2)
        intersect_width = max(0, intersect_right - intersect_left)
        intersect_height = max(0, intersect_bottom - intersect_top)
        return intersect_width * intersect_height

    

class NodeOptions(object):
    gap_x: int = 100
    gap_y: int = 100
    max_span: int = 6
    size_align: bool = True
    set_node: bool = True
    force_unfold: bool = True

    @classmethod
    def load_setting(cls) -> None:
        with open(GROUP_OPTIONS, "r", encoding="utf-8") as f:
            options: dict = json.load(f)
            cls.update_setting(options)

    @classmethod
    def update_setting(cls, options: Dict[str, Union[int, bool]]) -> None:
        cls.gap_x = options.get("gap_x", 100)
        cls.gap_y = options.get("gap_y", 100)
        cls.max_span = options.get("max_span", 6)
        cls.size_align = bool(options.get("size_align", True))
        cls.set_node = bool(options.get("set_node", True))
        cls.force_unfold = bool(options.get("force_unfold", True))



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


