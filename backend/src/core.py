from typing import List, Tuple, Dict
from collections import defaultdict

from .parser import WorkflowReader
from .Utils import DataTool, AlgorithmTool
from .setting import NodeOptions



class StandardOrder(object):
    fixed_col_nodes: Tuple = ("LoadImage", )
    same_column_stacking_strength_table: Dict[int, Tuple[int, int]] = {
        0: (0, 0),
        1: (1, 1),
        2: (2, 1),
        3: (3, 1),
        4: (3, 2),
        5: (3, 3),
        6: (4, 4),
        7: (5, 5)
    }
    def __init__(self, workflow_reader: WorkflowReader) -> None:
        self.workflow_reader = workflow_reader

    def column_forward(self, columns: List[List[int]]) -> None:
        if len(columns) < 3:
            return
        nodes = list(DataTool.flatten_generator(columns))
        in_edges = self.workflow_reader.build_graph(nodes, output_graph=False)
        out_edges = self.workflow_reader.build_graph(nodes, output_graph=True)
        id_to_node = self.workflow_reader.id_to_node
        node_to_col = self.workflow_reader.node_to_col(columns)
        (x0, x1) = StandardOrder.same_column_stacking_strength_table.get(NodeOptions.same_column_stacking_strength, (1, 1))
        for col_idx in range(len(columns) - 2, -1, -1):
            for node in columns[col_idx].copy():
                out_nodes = out_edges.get(node, [])
                if id_to_node[node].type in self.fixed_col_nodes or not out_nodes:
                    continue
                col_to_out_nodes = defaultdict(list)
                for out_node in out_nodes:
                    col_to_out_nodes[node_to_col[out_node]].append(out_node)
                move_new_col: int = min(col_to_out_nodes.keys()) - 1
                min_col_out_nodes = col_to_out_nodes[move_new_col + 1]
                if len(min_col_out_nodes) <= x0 and all(len(in_edges[i]) <= x1 for i in min_col_out_nodes):
                    move_new_col += 1
                columns[col_idx].remove(node)
                columns[move_new_col].append(node)
                node_to_col[node] = move_new_col
        columns[:] = [col for col in columns if col]

    def normalize_relations(self, left_col: List[int], right_col: List[int]) -> Tuple[List[int], List[Tuple[int, int]]]:
        # Normalize connection sections by creating virtual right nodes
        virtual_right_col = []
        virtual_normalize_connections: list[Tuple[int, int]] = list()
        virtual_node_id = max(max(left_col), max(right_col)) + 1
        right_port_map: defaultdict[int, List[Tuple]] = defaultdict(list)
        for link in self.workflow_reader.workflow_data.links:
            if link.input_node_id in left_col and link.output_node_id in right_col:
                right_port_map[link.output_node_id].append((link.input_node_id, link.output_port))
        for r in right_col:
            node_links = right_port_map[r]
            if not node_links:
                virtual_right_col.append(r)
            elif len(node_links) == 1:
                virtual_normalize_connections.append((node_links[0][0], r))
                virtual_right_col.append(r)
            else:
                sorted_ports = sorted(node_links, key=lambda x: x[1])
                for input_node_id, _ in sorted_ports:
                    virtual_right_col.append(virtual_node_id)
                    virtual_normalize_connections.append((input_node_id, virtual_node_id))
                    virtual_node_id += 1
        return virtual_right_col, virtual_normalize_connections

    def build_group_nodes_map(self, column: List[int], outer_links: List[Tuple[int, int]], start_id: int) -> Tuple[Dict[int, List[int]], List[Tuple[int, int]]]:
        group_nodes = dict()
        graph = self.workflow_reader.build_graph(column)
        inner_link = [
            (i.input_node_id, i.input_port, i.output_node_id, i.output_port)
            for i in self.workflow_reader.workflow_data.links
        ]
        # groups指这些节点间有直接或间接的关系
        groups = AlgorithmTool.group_connected_nodes(graph)
        for group in groups:
            result = AlgorithmTool.branched_sort(group, inner_link)
            for idx, outer_link in enumerate(outer_links.copy()):
                if outer_link[0] in group:
                    outer_links[idx] = (start_id, outer_link[1])
            group_nodes[start_id] = list(DataTool.flatten_generator(result))
            start_id += 1
        return group_nodes, outer_links
    
    def up_down_adjust(self, columns: List[List[int]]) -> None:
        if len(columns) < 2:
            return
        for col in range(len(columns) - 2, -1, -1):
            left_col = columns[col]
            right_col = columns[col + 1]
            virtual_right_col, virtual_links = self.normalize_relations(left_col, right_col)
            group_node_start_id = max(max(left_col), max(virtual_right_col)) + 1
            group_nodes_map, group_links = self.build_group_nodes_map(left_col, virtual_links, group_node_start_id)
            sorted_res = AlgorithmTool.gravity_sort(list(group_nodes_map.keys()), virtual_right_col, group_links)
            columns[col] = list(DataTool.flatten_generator(group_nodes_map[i] for i in sorted_res))

    def get_logic_order(self, nodes: List[int]) -> List[List[int]]:
        out_edges = self.workflow_reader.build_graph(nodes)
        columns = AlgorithmTool.topological_sort(out_edges)
        self.column_forward(columns)
        self.up_down_adjust(columns)
        return columns



class MainBranchShader:
    def __init__(self, workflow_reader: WorkflowReader) -> None:
        self.workflow_reader = workflow_reader
    
    def find_main_path(self, nodes: List[int]) -> List[int]:
        links = [(i.input_node_id, i.output_node_id) for i in self.workflow_reader.workflow_data.links]
        graph = self.workflow_reader.build_graph(nodes=nodes, links=links, output_graph=True)
        
        topological_layers = AlgorithmTool.topological_sort(graph)
        topological_order = list(DataTool.flatten_generator(topological_layers))
        output_nodes = [k for k, v in graph.items() if len(v) == 0]
        dp = {node: 1 for node in nodes}
        prev = {node: None for node in nodes}
        
        for node in topological_order:
            for neighbor in graph.get(node, []):
                if dp[neighbor] < dp[node] + 1:
                    dp[neighbor] = dp[node] + 1
                    prev[neighbor] = node
        
        if output_nodes:
            end_node = max(output_nodes, key=lambda node: dp[node])
        else:
            end_node = max(dp.items(), key=lambda x: x[1])[0]
        
        main_path = []
        current = end_node
        while current is not None:
            main_path.append(current)
            current = prev.get(current)
        main_path.reverse()
        return main_path

    def set_color_for_main_path(self, nodes: List[int]) -> None:
        color = NodeOptions.main_path_color
        bgcolor = NodeOptions.main_path_bg_color
        main_path = set(self.find_main_path(nodes))
        for node in self.workflow_reader.workflow_data.nodes:
            if node.id in main_path:
                node.color = color
                node.bgcolor = bgcolor

