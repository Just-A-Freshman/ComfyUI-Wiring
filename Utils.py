from typing import Dict, Set, Sequence, Generator, Any, List
from collections import defaultdict
from pathlib import Path
import json

from header import WorkflowData


NODE_LINK_TABLE = Path("config/node_link_table.json")



class UtilsTool(object):
    @staticmethod
    def flatten_generator(seq: Sequence)-> Generator[Any, Any, None]:
        for item in seq:
            if isinstance(item, list):
                yield from UtilsTool.flatten_generator(item)
            else:
                yield item

    @staticmethod
    def filter_pure_link(links: Sequence[Sequence[int]]) -> set:
        # eg: links = [[1, 3], [4, 5]]，表示1号输出到3号...
        input_map: Dict[int, Set] = {}
        output_map: Dict[int, Set] = {}
        
        for left_node, right_node in links:
            if left_node not in output_map:
                output_map[left_node] = set()
            output_map[left_node].add(right_node)
            
            if right_node not in input_map:
                input_map[right_node] = set()
            input_map[right_node].add(left_node)
        
        pure_link = set()
        for left_node, right_node in links:
            if left_node in output_map and len(output_map[left_node]) != 1:
                continue
            if right_node in input_map and len(input_map[right_node]) != 1:
                continue
            pure_link.add((left_node, right_node))
        
        return pure_link
    
    @staticmethod
    def exclude_outliers(data: List, top_n: int = 2, threshold: float = 2) -> None:
        if len(data) <= top_n:
            return []
        
        sorted_data = sorted(data, reverse=True)
        top_values = sorted_data[:top_n]
        rest_values = sorted_data[top_n:]
        rest_mean = sum(rest_values) / len(rest_values)
        
        for value in top_values:
            if value / rest_mean > threshold:
                data.remove(value)

    @staticmethod
    def update_node_link_table(workflow_data: WorkflowData) -> None:
        node_link_map = defaultdict(dict)
        node_id_map = {node.id: node for node in workflow_data.nodes}
        for link in workflow_data.links:
            input_node = node_id_map[link.input_node_id]
            if link.link_type != "*":
                node_link_map[input_node.type][link.input_port] = link.link_type
        with open(NODE_LINK_TABLE, "r", encoding="utf-8") as f:
            node_link_table: Dict = json.load(f)
        node_link_table.update(node_link_map)
        with open(NODE_LINK_TABLE, "w", encoding="utf-8") as f:
            json.dump(node_link_table, f, ensure_ascii=False, indent=4)

