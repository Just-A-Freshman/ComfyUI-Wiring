from typing import List, Tuple, Dict
from collections import defaultdict

from header import Link
from parser import WorkflowReader, WorkflowWriter
from Utils import UtilsTool



class LogicalConfig(object):
    fixed_col_nodes = ("LoadImage", )
    def __init__(self, workflow_reader: WorkflowReader) -> None:
        self.workflow_reader = workflow_reader

    def build_data(self) -> Tuple[Dict[int, int], defaultdict[int, List[int]]]:
        """构建入度字典和出边字典"""
        in_degree = {node.id: 0 for node in self.workflow_reader.workflow_data.nodes}
        out_edges = defaultdict(list)  # eg: {4: [3, 6, 7, 8], 5: [3]} -  {node_id: [out_node_id, ...]}
        
        for link in self.workflow_reader.workflow_data.links:
            if link.input_node_id in in_degree and link.output_node_id in in_degree:
                out_edges[link.input_node_id].append(link.output_node_id)
                in_degree[link.output_node_id] += 1
        return in_degree, out_edges

    @staticmethod
    def build_columns(in_degree: Dict[int, int], out_edges: defaultdict[int, List[int]]) -> List[List[int]]:
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

    def add_intermediary_node(self, columns: List[List[int]], out_edges: defaultdict[int, List[int]], min_interval: int, min_connect: int):
        workflow_writer = WorkflowWriter(self.workflow_reader.workflow_data)
        if min_interval >= len(columns) - 2:
            return columns

    def column_forward(self, columns: List[List[int]], out_edges: defaultdict[int, List[int]], start=-1) -> None:
        if len(columns) < 3:
            return columns
        fixed_nodes = {
            node.id for node in self.workflow_reader.workflow_data.nodes
            if node.type in self.fixed_col_nodes
        }
        node_to_col: Dict[int] = {}
        col_sets = [set(column) for column in columns]
        for col_idx, col_nodes in enumerate(columns):
            for node in col_nodes:
                node_to_col[node] = col_idx
        
        start_col = len(columns) - 2 if start == -1 else start

        for col_idx in range(start_col, -1, -1):
            col_nodes = columns[col_idx].copy()
            if not col_nodes:
                continue
                
            for node in col_nodes:
                if node not in out_edges or node in fixed_nodes:
                    continue
                    
                min_output_col = float('inf')
                for out_node in out_edges[node]:
                    out_col = node_to_col[out_node]
                    if out_col > col_idx and out_col < min_output_col:
                        min_output_col = out_col
                
                if min_output_col != float('inf') and min_output_col > col_idx + 1:
                    min_output_col: int
                    columns[col_idx].remove(node)
                    new_col = min_output_col - 1
                    columns[new_col].append(node)
                    node_to_col[node] = new_col
                    col_sets[col_idx].remove(node)
                    col_sets[new_col].add(node)
        
        return [col for col in columns if col]

    def normalize_relations(self, left_col: List[int], right_col: List[int]) -> Tuple[List[int], List[List[int]]]:
        """将节点间的多连接简化为单连接，并为每个连接创建唯一节点"""
        node_links: defaultdict[int, List[Link]] = defaultdict(list)
        for link in self.workflow_reader.workflow_data.links:
            if link.input_node_id in left_col and link.output_node_id in right_col:
                node_links[link.output_node_id].append(link)

        new_right_col = []
        new_node_id = max(max(left_col), max(right_col)) + 1
        normalized_links = []
        
        for node in right_col.copy():
            new_right_col.append(node)
            links = node_links[node]
            if len(links) == 0:
                continue
            sorted_links = sorted(links, key=lambda x: x.output_port)
            first_link, *extra_links = sorted_links
            normalized_links.append((first_link.input_node_id, node))
            for link in extra_links:
                normalized_links.append((link.input_node_id, new_node_id))
                new_right_col.append(new_node_id)
                new_node_id += 1
        
        return new_right_col, normalized_links

    @staticmethod
    def minimize_crossings(left_col: List[int], right_col: List[int], relations: List[List[int]]) -> List:
        """使用重心法最小化左右两列之间的交叉"""
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

    def up_down_adjust(self, columns: List[List[int]]) -> None:
        """逐层调整节点顺序以最小化交叉"""
        if len(columns) < 2:
            return
        for col in range(len(columns) - 2, -1, -1):
            left_col = columns[col]
            right_col = columns[col + 1]
            right_col, normalize_links = self.normalize_relations(left_col, right_col)
            columns[col] = self.minimize_crossings(left_col, right_col, normalize_links)

    def get_logic_config(self) -> List[List[int]]:
        in_degree, out_edges = self.build_data()
        columns = self.build_columns(in_degree, out_edges)
        self.column_forward(columns, out_edges, start=-1)
        self.up_down_adjust(columns)
        return columns


class CoordinateConfig(object):
    def __init__(self, workflow_reader: WorkflowReader) -> None:
        self.workflow_reader = workflow_reader

    def build_data(self) -> defaultdict[int, list]:
        input_nodes: defaultdict[int, list] = defaultdict(list)
        for link in self.workflow_reader.workflow_data.links:
            input_nodes[link.output_node_id].append(link.input_node_id)
        return input_nodes
    
    def is_valid_columns(self, columns) -> bool:
        node_id_list = set(node.id for node in self.workflow_reader.workflow_data.nodes)
        columns_1d = UtilsTool.flatten_generator(columns)
        for node_id in columns_1d:
            if node_id not in node_id_list:
                return False
        return True
    
    def modify_layout(self, columns: List[List[int]], gap_x=100, gap_y=100):
        if not self.is_valid_columns(columns):
            raise ValueError("The nodes in the columns are different from those in the nodes passed during initialization.")
        input_nodes = self.build_data()
        workflow_writer = WorkflowWriter(self.workflow_reader.workflow_data)
        id_to_node = workflow_writer.id_node_table
        positions: Dict[int, Tuple[int]] = {}
        prev_x: int = 0
        prev_max_width: int = 0
        for column in columns:
            x0 = prev_x + prev_max_width + (gap_x if prev_max_width > 0 else 0)
            col_widths = [WorkflowReader.real_size(id_to_node[node]).width for node in column]
            UtilsTool.exclude_outliers(col_widths)
            max_width = max(col_widths)
            offsets = []
            current_offset = 0
            for i, node in enumerate(column):
                offsets.append(current_offset)
                node_height = WorkflowReader.real_size(id_to_node[node]).height
                current_offset += node_height + (gap_y if i < len(column) - 1 else 0)
 
            desired_y_list = []
            for node in column:
                desired_y = None
                if node not in input_nodes:
                    desired_y_list.append(desired_y)
                    continue
                
                centers = []
                for in_node in input_nodes[node]:
                    if in_node in positions:
                        in_y = positions[in_node][1]
                        in_height = WorkflowReader.real_size(id_to_node[in_node]).height
                        centers.append(in_y + in_height / 2)
                if centers:
                    ideal_center = (min(centers) + max(centers)) / 2
                    node_height = WorkflowReader.real_size(id_to_node[node]).height
                    desired_y = ideal_center - node_height / 2
                desired_y_list.append(desired_y)
            
            total_diff = [des_y - offsets[i] for i, des_y in enumerate(desired_y_list) if des_y is not None]
            y0 = sum(total_diff) / len(total_diff) if total_diff else 0
            
            
            for i, node in enumerate(column):
                y_pos = y0 + offsets[i]
                positions[node] = (x0, y_pos)
                id_to_node[node].pos.x = x0
                id_to_node[node].pos.y = y_pos
                id_to_node[node].size.width = max_width
            
            prev_x = x0
            prev_max_width = max_width


