from typing import List, Tuple, Dict
from collections import defaultdict

from header import Link
from parser import WorkflowReader, WorkflowWriter, Setting
from Utils import UtilsTool



class LogicalConfig(object):
    fixed_col_nodes = ("LoadImage", )
    def __init__(self, workflow_reader: WorkflowReader) -> None:
        self.workflow_reader = workflow_reader

    def add_intermediate_nodes(self, columns: List[List[int]]) -> None:
        max_span = max(Setting.max_span, 3)
        id_to_link = {link.link_id: link for link in self.workflow_reader.workflow_data.links}
        id_to_node = {node.id: node for node in self.workflow_reader.workflow_data.nodes}
        set_nodes: Dict[Tuple[int], int] = {}
        node_to_col: Dict[int, int] = self.workflow_reader.node_to_col(columns)
        for node in self.workflow_reader.workflow_data.nodes:
            if node.type != "SetNode":
                continue
            link = id_to_link[node.inputs[0]["link"]]
            set_nodes[(link.input_node_id, link.input_port)] = node.id
        workflow_writer = WorkflowWriter(self.workflow_reader.workflow_data)
        links = self.workflow_reader.workflow_data.links
        long_links_table: defaultdict[Tuple[int], List[Link]] = defaultdict(list)
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
                set_node_input = set_node.inputs[0]
                set_node_input["type"] = new_link.link_type
                set_node_input["name"] = new_link.link_type
            long_links_table[(input_node_id, input_port)].append(link)
        set_new_columns: defaultdict[int, list] = defaultdict(list)
        for k, v in set_nodes.items():
            input_node_id, _ = k
            new_col = node_to_col[input_node_id] + 1
            set_new_columns[new_col].append(v)
        set_new_columns = UtilsTool.merge_dict_by_key(set_new_columns, threshold=1)
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

    def column_forward(self, columns: List[List[int]], out_edges: defaultdict[int, List[int]], start=-1) -> None:
        if len(columns) < 3:
            return columns
        fixed_nodes = {
            node.id for node in self.workflow_reader.workflow_data.nodes
            if node.type in self.fixed_col_nodes
        }
        node_to_col = self.workflow_reader.node_to_col(columns)
        col_sets = [set(column) for column in columns]
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
        out_edges = defaultdict(list)
        for link in self.workflow_reader.workflow_data.links:
            out_edges[link.input_node_id].append(link.output_node_id)
        columns = UtilsTool.topological_sort(self.workflow_reader.workflow_data)
        self.column_forward(columns, out_edges, start=-1)
        if Setting.set_node:
            self.add_intermediate_nodes(columns)
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
    
    def modify_layout(self, columns: List[List[int]]) -> None:
        gap_x = Setting.gap_x
        gap_y = Setting.gap_y
        fixed_size = Setting.fixed_size
        if not self.is_valid_columns(columns):
            raise ValueError("The nodes in the columns are different from those in the nodes passed during initialization.")
        input_nodes = self.build_data()
        workflow_writer = WorkflowWriter(self.workflow_reader.workflow_data)
        id_to_node = workflow_writer.id_node_table
        positions: Dict[int, Tuple[int]] = {}
        prev_x: int = 0
        prev_max_width: int = 0
        if Setting.force_unfold:
            workflow_writer.unfold_all_nodes()
        for column in columns:
            x0 = prev_x + prev_max_width + (gap_x if prev_max_width > 0 else 0)
            col_widths = [WorkflowReader.real_size(id_to_node[node]).width for node in column]
            UtilsTool.exclude_outliers(col_widths)
            max_width = max(col_widths)
            offsets = []
            current_offset = 0
            for i, node in enumerate(column):
                node_obj = id_to_node[node]
                offsets.append(current_offset)
                node_height = WorkflowReader.real_size(node_obj).height
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
                if not fixed_size:
                    id_to_node[node].size.width = max_width
            prev_x = x0
            prev_max_width = max_width


