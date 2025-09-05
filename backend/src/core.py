from typing import List, Tuple, Dict
from collections import defaultdict

from .header import Link
from .parser import WorkflowReader, WorkflowWriter
from .Utils import DataTool, AlgorithmTool
from .setting import NodeOptions


class Order(object):
    def __init__(self, workflow_reader: WorkflowReader) -> None:
        self.workflow_reader = workflow_reader

    def get_logic_order(self) -> List[List[int]]:
        return []



class StandardOrder(Order):
    fixed_col_nodes = ("LoadImage", )
    def __init__(self, workflow_reader: WorkflowReader) -> None:
        super().__init__(workflow_reader)

    def add_intermediate_nodes(self, columns: List[List[int]]) -> None:
        max_span = max(NodeOptions.max_span, 2)
        id_to_link = self.workflow_reader.id_to_link
        id_to_node = {node.id: node for node in self.workflow_reader.workflow_data.nodes}
        set_nodes: Dict[Tuple[int, int], int] = {}
        node_to_col: Dict[int, int] = self.workflow_reader.node_to_col(columns)
        for node in self.workflow_reader.workflow_data.nodes:
            if node.type != "SetNode":
                continue
            link_id = node.inputs[0]["link"]
            if link_id is None or link_id not in id_to_link:
                continue
            link = id_to_link[link_id]
            set_nodes[(link.input_node_id, link.input_port)] = node.id
        workflow_writer = WorkflowWriter(self.workflow_reader.workflow_data)
        links = self.workflow_reader.workflow_data.links
        long_links_table: defaultdict[Tuple[int, int], List[Link]] = defaultdict(list)
        for link in links.copy():
            input_node_col = node_to_col.get(link.input_node_id)
            output_node_col = node_to_col.get(link.output_node_id)
            if input_node_col is None or output_node_col is None:
                continue
            span = output_node_col - input_node_col
            if span <= max_span:
                continue
            input_node_id = link.input_node_id
            input_port = link.input_port
            if (input_node_id, input_port) not in set_nodes:
                input_node = id_to_node[input_node_id]
                set_node = workflow_writer.create_node(type="SetNode")
                node_name = f"{input_node.outputs[input_port]['name']}_{input_node.id}"
                set_node.widgets_values = [node_name]
                set_nodes[(input_node_id, input_port)] = set_node.id
                new_link = workflow_writer.create_link(input_node_id, input_port, set_node.id, 0)
                if new_link is None:
                    continue
                set_node_input = set_node.inputs[0]
                set_node_input["type"] = new_link.link_type
                set_node_input["name"] = new_link.link_type
            long_links_table[(input_node_id, input_port)].append(link)
        set_new_columns: defaultdict[int, list] = defaultdict(list)
        for k, v in set_nodes.items():
            input_node_id, _ = k
            new_col = node_to_col[input_node_id] + 1
            set_new_columns[new_col].append(v)
        set_new_columns = DataTool.merge_dict_by_key(set_new_columns, threshold=1)
        count = 0
        for col_idx, new_columns in set_new_columns.items():
            columns.insert(col_idx + count, new_columns)
            count += 1
        node_to_col = self.workflow_reader.node_to_col(columns)
        threshold = max_span // 2
        id_to_node = {node.id: node for node in self.workflow_reader.workflow_data.nodes}
        for (input_node_id, input_port), long_links in long_links_table.items():
            link_length: List[int] = [
                node_to_col[long_link.output_node_id] - node_to_col[long_link.input_node_id]
                for long_link in long_links
            ]
            set_node_id = set_nodes[(input_node_id, input_port)]
            set_node = id_to_node[set_node_id]
            set_node_type = set_node.inputs[0]["type"]
            while max(link_length) > threshold:
                temp_link_length = [i for i in link_length if i > 0]
                if temp_link_length:
                    min_link_length = min(temp_link_length)
                else:
                    break
                min_link_idx = link_length.index(min_link_length)
                min_long_link = long_links[min_link_idx]
                get_node_col = node_to_col[min_long_link.output_node_id] - 1
                get_node = workflow_writer.create_node(type="GetNode", widgets_values=set_node.widgets_values)
                get_node_output = get_node.outputs[0]
                get_node_output["type"] = get_node_output["name"] = set_node_type
                columns[get_node_col].append(get_node.id)
                link_length = [i - min_link_length for i in link_length]
                for idx, length in enumerate(link_length):
                    if length > threshold or length < 0:
                        continue
                    link = long_links[idx]
                    workflow_writer.create_link(get_node.id, 0, link.output_node_id, link.output_port)

    def column_forward(self, columns: List[List[int]]) -> None:
        if len(columns) < 3:
            return
        nodes = list(DataTool.flatten_generator(columns))
        in_edges = self.workflow_reader.build_graph(nodes, output_graph=False)
        out_edges = self.workflow_reader.build_graph(nodes, output_graph=True)
        id_to_node = self.workflow_reader.id_to_node
        node_to_col = self.workflow_reader.node_to_col(columns)

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
                if len(min_col_out_nodes) == 1 and len(in_edges[min_col_out_nodes[0]]) == 1:
                    move_new_col += 1
                columns[col_idx].remove(node)
                columns[move_new_col].append(node)
                node_to_col[node] = move_new_col
        columns[:] = [col for col in columns if col]

    def normalize_relations(self, left_col: List[int], right_col: List[int]) -> Tuple[List[int], list[Tuple[int, int]]]:
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

    def build_group_nodes_map(self, column: List[int], outer_links: List[Tuple[int, int]], start_id: int) -> tuple[dict[int, List[int]], list[Tuple[int, int]]]:
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
        # if NodeOptions.set_node:
        #     self.add_intermediate_nodes(columns)
        self.up_down_adjust(columns)
        return columns




class MainBranchOrder:
    def __init__(self, workflow_reader: WorkflowReader):
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

    def get_logic_order(self, nodes) -> List[List[int]]:
        # main_path = self.find_main_path(nodes)
        main_path = nodes
        standard_order = StandardOrder(self.workflow_reader)
        result = standard_order.get_logic_order(main_path)
        print(result)
        return result
