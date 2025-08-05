from typing import Sequence, Generator, Any, List
from collections import defaultdict

from .header import WorkflowData






class UtilsTool(object):
    @staticmethod
    def flatten_generator(seq: Sequence)-> Generator[Any, Any, None]:
        for item in seq:
            if isinstance(item, list):
                yield from UtilsTool.flatten_generator(item)
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
    def merge_dict_by_key(similar_key_dict: defaultdict[int, list], threshold: int = 1) -> defaultdict[int, list]:
        if not similar_key_dict:
            return defaultdict()
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
        
        result: defaultdict[int, list] = defaultdict(list)
        for group in groups:
            max_key = max(group)
            merged_values = []
            for key in group:
                merged_values.extend(similar_key_dict[key])
            result[max_key] = merged_values
        
        return result

    

