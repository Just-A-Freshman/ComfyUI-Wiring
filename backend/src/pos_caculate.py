from typing import List, Literal, Set, Tuple
from collections import defaultdict, deque

from .header import Node
from .parser import WorkflowReader, WorkflowWriter
from .Utils import DataTool, AlgorithmTool
from .setting import NodeOptions, GroupOptions



class GroupPosCalulator(object):
    def __init__(self, workflow_reader: WorkflowReader) -> None:
        self.workflow_reader = workflow_reader

    def get_orig_groups(self) -> defaultdict[int, list[Node]]:
        contain_table: defaultdict[int, list[Node]] = defaultdict(list)
        nodes = self.workflow_reader.workflow_data.nodes
        for group in self.workflow_reader.workflow_data.groups:
            box = group.bounding
            group_coord = (box[0], box[1], box[0] + box[2], box[1] + box[3])
            for node in nodes:
                node_coord = (node.pos.x, node.pos.y, node.pos.x + node.size.width, node.pos.y + node.size.height)
                S_node = node.size.width * node.size.height
                intersect_area = AlgorithmTool.rectangle_intersection_area(node_coord, group_coord)
                if intersect_area / S_node > GroupOptions.group_contain_propertion:
                    contain_table[group.id].append(node)
        return contain_table

    def modify_group_layout(self, orig_groups: defaultdict[int, list[Node]]) -> None:
        group_opt = GroupOptions
        workflow_writer = WorkflowWriter(self.workflow_reader.workflow_data)
        id_to_group = {group.id: group for group in workflow_writer.workflow_data.groups}
        undistributed_y_offset = 1
        for group_id, group in orig_groups.items():
            min_x = min(node.pos.x for node in group)
            min_y = min(node.pos.y for node in group)
            max_x = max(node.pos.x + node.size.width for node in group)
            max_y = max(node.pos.y + node.size.height for node in group)
            new_group = []
            for node in self.workflow_reader.workflow_data.nodes:
                node_coord = (node.pos.x, node.pos.y, node.pos.x + node.size.width, node.pos.y + node.size.height)
                S_node: int = max(node.size.width * node.size.height, 1)
                intersect_area = AlgorithmTool.rectangle_intersection_area(node_coord, (min_x, min_y, max_x, max_y))
                if intersect_area / S_node > group_opt.group_contain_propertion:
                    new_group.append(node)
            if not new_group:
                continue
            group_obj = id_to_group[group_id]
            if len(group) / len(new_group) > group_opt.same_group_node_propertion:
                heading_size = group_obj.font_size * group_opt.heading_size_multiplier
                group_obj.bounding = [
                    min_x - group_opt.padding, min_y - heading_size, 
                    max_x - min_x + group_opt.padding * 2, max_y - min_y + heading_size
                ]
            else:
                group_obj.bounding = [
                    group_opt.undistrubuted_x, undistributed_y_offset * group_opt.undistrubuted_y_step,
                    group_opt.undistrubuted_width, group_opt.undistrubuted_height
                ]
                undistributed_y_offset += 1



class NodePosCalculator(object):
    def __init__(self, workflow_reader: WorkflowReader) -> None:
        self.workflow_reader = workflow_reader

    def get_adjoin_links(self, columns: List[List[int]], diff: int = 2) -> Set[Tuple[int, int]]:
        node_to_col = self.workflow_reader.node_to_col(columns)
        ajoin_links = set()
        for link in self.workflow_reader.workflow_data.links:
            input_col = node_to_col.get(link.output_node_id, 0)
            output_col = node_to_col.get(link.input_node_id, 0)
            if input_col == output_col:
                continue
            if output_col - input_col < diff:
                ajoin_links.add((link.input_node_id, link.output_node_id))
        return ajoin_links

    def get_accumulate_offsets(self, column: List[Node]) -> List[int]:
        gap_y = NodeOptions.gap_y
        offsets: List[int] = []
        current_offset = 0
        for node in column:
            offsets.append(current_offset)
            current_offset += (self.workflow_reader.real_size(node).height + gap_y)
        offsets.append(current_offset)
        return offsets

    def align_pos(self, node_id: int, align: str) -> int | float:
        node = self.workflow_reader.id_to_node[node_id]
        if align == "top":
            return node.pos.y
        elif align == "center":
            return node.pos.y + WorkflowReader.real_size(node).height / 2
        elif align == "bottom":
            return node.pos.y + WorkflowReader.real_size(node).height
        else:
            raise ValueError("Cannot recognize the align type.")

    def align_line(self, align: str, base_y, accumulate_offsets: int | float) -> float | int:
        if align == "top":
            return base_y
        elif align == "center":
            return base_y - accumulate_offsets // 2
        elif align == "bottom":
            return base_y - accumulate_offsets
        else:
            raise ValueError("Cannot recognize the align type.")

    def simple_align_calculator(
            self, 
            columns: List[List[int]],
            base_x: int = 0,
            base_y: int = 0,
            align: Literal["top", "center", "bottom"] = "top"
        ) -> None:
        gap_x = NodeOptions.gap_x
        columns_objectification = [[self.workflow_reader.id_to_node[j] for j in i] for i in columns]
        x0 = base_x
        for column in columns_objectification:
            offsets = self.get_accumulate_offsets(column)
            max_width = 0
            y0 = self.align_line(align, base_y, offsets[-1])
            for idx, node in enumerate(column):
                node.pos.x = x0
                node.pos.y = int(y0 + offsets[idx])
                max_width = max(max_width, WorkflowReader.real_size(node).width)
            x0 += (max_width + gap_x)

    def average_align_calculator(
            self, 
            columns: List[List[int]],
            base_x: int = 0,
            base_y: int = 0,
            align: Literal["top", "center", "bottom"] = "center"
        ) -> None:
        gap_x = NodeOptions.gap_x
        nodes = list(DataTool.flatten_generator(columns))
        adjoin_links = self.get_adjoin_links(columns)
        input_edges = self.workflow_reader.build_graph(nodes=nodes, links=adjoin_links, output_graph=False)
        columns_objectification = [[self.workflow_reader.id_to_node[j] for j in i] for i in columns]
        x0 = base_x
        for column in columns_objectification:
            offsets = self.get_accumulate_offsets(column)
            y0 = self.align_line(align, base_y, offsets[-1])
            desired_y_list = []
            for node in column:
                input_nodes = input_edges[node.id]
                if not input_nodes:
                    desired_y = None
                else:
                    dest_node_pos = [self.align_pos(i, "center") for i in input_nodes]
                    desired_y = DataTool.get_median(dest_node_pos)
                desired_y_list.append(desired_y)
            total_diff = [des_y - offsets[i] for i, des_y in enumerate(desired_y_list) if des_y is not None]
            start_y = int(sum(total_diff) / len(total_diff) if total_diff else y0)
            for idx, node in enumerate(column):
                node.pos.x = x0
                node.pos.y = start_y + offsets[idx]
            col_widths = [WorkflowReader.real_size(node).width for node in column]
            x0 += (max(col_widths) + gap_x)

    def highly_align_calculator(
            self, 
            columns: List[List[int]], 
            base_x: int = 0, 
            base_y: int = 0, 
            align: Literal["top", "center", "bottom"] = "top"
        ) -> None:
        gap_x = NodeOptions.gap_x
        gap_y = NodeOptions.gap_y
        nodes = list(DataTool.flatten_generator(columns))
        adjoin_links = self.get_adjoin_links(columns)
        input_edges = self.workflow_reader.build_graph(nodes=nodes, links=adjoin_links, output_graph=False)
        columns_objectification = [[self.workflow_reader.id_to_node[j] for j in i] for i in columns]
        x0 = base_x
        for column in columns_objectification:
            locate_nodes: List[Node] = []
            k: List[int] = []
            desired_y_list: List[float] = []
            ki = 0
            for node in column:
                input_nodes = input_edges[node.id]
                block_height = WorkflowReader.real_size(node).height + gap_y
                if input_nodes:
                    desired_y = DataTool.get_median([self.align_pos(i, "center") for i in input_nodes])
                    desired_y_list.append(desired_y)
                    k.append(ki)
                    locate_nodes.append(node)
                    ki = block_height
                else:
                    ki += block_height
            if len(k) > 1:
                k = k[1:]
                n = len(desired_y_list)
                c = [0] * n
                for i in range(1, n):
                    c[i] = c[i-1] + k[i-1]
                m_prime = [desired_y_list[i] - c[i] for i in range(n)]
                z = AlgorithmTool.pava_algorithm(m_prime)
                x = [z[i] + c[i] for i in range(n)]
            else:
                x = desired_y_list
            y_position = deque([])
            start_pos = 0
            if locate_nodes:
                start_pos = column.index(locate_nodes[0])
                if start_pos != 0:
                    unlimited_nodes = column[:start_pos]
                    current_y_offset = x[0]
                    for node in unlimited_nodes[::-1]:
                        current_y_offset -= (WorkflowReader.real_size(node).height + gap_y)
                        y_position.appendleft(current_y_offset)
            accumulate_offset = self.get_accumulate_offsets(column)[-1]
            current_y_offset = self.align_line(align, base_y, accumulate_offset)
            idx = 0
            for node in column[start_pos:]:
                if node in locate_nodes:
                    current_y_offset = x[idx]
                    y_position.append(current_y_offset)
                    idx += 1
                else:
                    y_position.append(current_y_offset)
                current_y_offset += (WorkflowReader.real_size(node).height + gap_y)
            for node, y0 in zip(column, y_position):
                node.pos.x = x0
                node.pos.y = y0
            col_widths = [WorkflowReader.real_size(node).width for node in column]
            x0 += (max(col_widths) + gap_x)


