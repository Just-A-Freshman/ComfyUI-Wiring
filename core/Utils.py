from typing import Iterable, Generator, List, Tuple, Dict, Any
from collections import defaultdict



class AlgorithmTool(object):
    @staticmethod
    def topological_sort(graph: Dict[int, List[int]]) -> List[List[int]]:
        all_nodes = set(graph.keys())
        for neighbors in graph.values():
            all_nodes.update(neighbors)
        all_nodes = list(all_nodes)
        in_degree = {node: 0 for node in all_nodes}
        for output_nodes in graph.values():
            for output_node in output_nodes:
                in_degree[output_node] += 1
        columns = []
        current_degree = in_degree.copy()
        while current_degree:
            zero_degree_nodes = [node for node, deg in current_degree.items() if deg == 0]
            if not zero_degree_nodes:
                raise ValueError("Cycle detected in dependency graph")
            columns.append(zero_degree_nodes)
            for node in zero_degree_nodes:
                del current_degree[node]
                for neighbor in graph[node]:
                    if neighbor in current_degree:
                        current_degree[neighbor] -= 1
        return columns
    
    @staticmethod
    def gravity_sort(left_col: List[int], right_col: List[int], relations: List[Tuple[int, int]]) -> List:
        right_col_idx_map = {node: idx for idx, node in enumerate(right_col)}
        connections = {node: [] for node in left_col}

        for left_node, right_node in relations:
            if left_node in connections:
                connections[left_node].append(right_col_idx_map[right_node])

        avg_right_col = sum(right_col_idx_map.values()) / len(right_col) if right_col else 0
        barycenter = {}
        
        for node in left_col:
            if connections[node]:
                barycenter[node] = sum(connections[node]) / len(connections[node])
            else:
                barycenter[node] = avg_right_col
        sorted_left_col = sorted(left_col, key=lambda x: barycenter[x])
        return sorted_left_col

    @staticmethod
    def group_connected_nodes(graph: Dict[int, List[int]]) -> list[list[int]]:
        def find(u):
            if parent[u] != u:
                parent[u] = find(parent[u])  # 路径压缩，加速后续查询
            return parent[u]

        def union(u, v):
            u_root = find(u)
            v_root = find(v)
            if u_root == v_root:
                return
            if rank[u_root] < rank[v_root]:
                parent[u_root] = v_root
            else:
                parent[v_root] = u_root
                if rank[u_root] == rank[v_root]:
                    rank[u_root] += 1

        all_nodes = set()
        for node, output_nodes in graph.items():
            all_nodes.add(node)
            for neighbor in output_nodes:
                all_nodes.add(neighbor)
        
        parent = {node: node for node in all_nodes}
        rank = {node: 0 for node in all_nodes}
        
        for node in graph:
            for neighbor in graph[node]:
                union(node, neighbor)
        
        groups = defaultdict(list)
        for node in all_nodes:
            root = find(node)
            groups[root].append(node)
        
        return list(groups.values())

    @staticmethod
    def branched_sort(nodes: List[int], connections: List[Tuple[int, int, int, int]]) -> List[int]:
        node_set = set(nodes)
        filtered_conn = filter(lambda x: x[0] in node_set and x[2] in node_set, connections)
        graph_inputs: defaultdict[int, List[Tuple[int, int]]] = defaultdict(list)
        out_degree = {node: 0 for node in nodes}
        for conn in filtered_conn:
            u, out_port, v, in_port = conn
            graph_inputs[v].append((u, in_port))
            out_degree[u] += 1
        
        output_nodes = [node for node in nodes if out_degree[node] == 0]
        visited = set()
        result_list = []
        
        def sort_node(v):
            if v in visited:
                return
            if v in graph_inputs:
                inputs = graph_inputs[v]
                sorted_inputs = sorted(inputs, key=lambda x: x[1])
                for u, _ in sorted_inputs:
                    sort_node(u)
            visited.add(v)
            result_list.append(v)
        output_nodes_sorted = sorted(output_nodes)
        for node in output_nodes_sorted:
            sort_node(node)
        
        return result_list
    
    @staticmethod
    def pava_algorithm(fit_y: List[int | float], weights=None) -> List[float]:
        n = len(fit_y)
        if weights is None:
            weights = [1.0] * n
        
        blocks = [{'value': fit_y[i], 'weight': weights[i], 'indices': [i]} for i in range(n)]
        
        i = 0
        while i < len(blocks) - 1:
            if blocks[i]['value'] > blocks[i+1]['value']:
                total_weight = blocks[i]['weight'] + blocks[i+1]['weight']
                weighted_sum = blocks[i]['value'] * blocks[i]['weight'] + blocks[i+1]['value'] * blocks[i+1]['weight']
                merged_value = weighted_sum / total_weight
                merged_block = {
                    'value': merged_value,
                    'weight': total_weight,
                    'indices': blocks[i]['indices'] + blocks[i+1]['indices']
                }
                blocks[i] = merged_block
                del blocks[i+1]
                if i > 0:
                    i -= 1
            else:
                i += 1
        
        result = [0.0] * n
        for block in blocks:
            for idx in block['indices']:
                result[idx] = block['value']
        
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


class DataTool(object):
    @staticmethod
    def flatten_generator(iterable: Iterable)-> Generator[Any, Any, None]:
        for item in iterable:
            if isinstance(item, list):
                yield from DataTool.flatten_generator(item)
            else:
                yield item

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
    def get_median(data: List) -> float | int:
        if not data:
            raise ValueError("Empty data list.")
        temp = sorted(data)
        seq_length = len(temp)
        mid = seq_length // 2
        return temp[mid] if seq_length % 2 == 1 else (temp[mid] + temp[mid - 1]) / 2




