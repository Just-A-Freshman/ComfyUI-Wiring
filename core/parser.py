from typing import Dict, List, Tuple, Iterable, Sequence, Optional, Literal, Set, Any
from collections import OrderedDict
from pathlib import Path
import json
import copy


from .setting import NodeOptions, COLLAPSE_WIDTH, COLLAPSE_HEIGHT, TEMPLATE
from .Utils import DataTool, AlgorithmTool
from .header import WorkflowData, Node, NodeSize, Link



class WorkflowGraph(object):
    def __init__(self, workflow_data: WorkflowData) -> None:
        self.workflow_data = workflow_data
        self.id_to_node = {node.id: node for node in self.workflow_data.nodes}
        self.id_to_link = {link.link_id: link for link in self.workflow_data.links}
    
    @staticmethod
    def node_to_col(columns: List[List[int]]) -> Dict[int, int]:
        node_to_col: Dict[int, int] = {}
        for col_idx, col_nodes in enumerate(columns):
            for node in col_nodes:
                node_to_col[node] = col_idx
        return node_to_col
    
    def build_graph(
            self, 
            nodes: Sequence[int] | None = None, 
            links: Iterable[Tuple[int, int]] | None = None,
            output_graph: bool = True
        ) -> Dict[int, list[int]]:
        nodes = nodes if nodes else [node.id for node in self.workflow_data.nodes]
        links = links if links else [(i.input_node_id, i.output_node_id) for i in self.workflow_data.links]
        edges = {node: [] for node in nodes}
        for input_node_id, output_node_id in links:
            if input_node_id not in nodes or output_node_id not in nodes:
                continue
            if output_graph:
                edges[input_node_id].append(output_node_id)
            else:
                edges[output_node_id].append(input_node_id)
        return edges
   

class WorkflowIO(WorkflowGraph):
    def __init__(self, workflow_data: WorkflowData) -> None:
        super().__init__(workflow_data)
        self.workflow_template = self.load_workflow_template()

    def load_workflow_template(self) -> Dict[str, Dict]:
        with open(TEMPLATE, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def import_file(workflow_path: str) -> WorkflowData:
        WorkflowValidator.verify_workflow_file(workflow_path)
        with open(workflow_path, 'r', encoding='utf-8') as f:
            try:
                workflow_dict = json.load(f)
                workflow_data = WorkflowData.from_dict(workflow_dict)
                return workflow_data
            except Exception as e:
                raise ValueError(f"Failed to parse workflow file: {e}")
            
    def export_file(self, output_path: str, overwrite_raw_data: bool = False) -> None:
        out_edges = self.build_graph()
        orders = DataTool.flatten_generator(AlgorithmTool.topological_sort(out_edges))
        order_table = {node_id: order for order, node_id in enumerate(orders)}
        
        raw_data = self.workflow_data.raw_data
        if not overwrite_raw_data:
            raw_data = raw_data.copy()
            raw_data["nodes"] = raw_data["nodes"].copy()
        
        nodes_template = self.workflow_template["nodes"]
        raw_id_nodes: Dict[int, Dict] = {node["id"]: node for node in raw_data["nodes"]}
        for new_node in self.workflow_data.nodes:
            node_type = new_node.type
            new_node_dict: dict = WorkflowReader.asdict(new_node)
            new_node_dict["order"] = order_table[new_node.id]
            if new_node.id in raw_id_nodes:
                raw_id_nodes[new_node.id].update(new_node_dict)
            else:
                template: Dict = nodes_template.get(node_type, {})
                if not template:
                    raise KeyError(f"type: {node_type} not found in nodes template.")
                template_copy = template.copy()
                template_copy.update(new_node_dict)
                raw_data["nodes"].append(template_copy)

        raw_data["nodes"] = [node for node in raw_data["nodes"] if node["id"] in self.id_to_node]
        raw_data["links"] = [
            [link.link_id, link.input_node_id, link.input_port, 
            link.output_node_id, link.output_port, link.link_type]
            for link in self.workflow_data.links
        ]
        raw_data["groups"] = [WorkflowReader.asdict(group) for group in self.workflow_data.groups]
        raw_data["last_node_id"] = self.workflow_data.last_node_id
        raw_data["last_link_id"] = self.workflow_data.last_link_id
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(raw_data, f, ensure_ascii=False)


class WorkflowValidator(WorkflowIO):
    def __init__(self, workflow_data: WorkflowData) -> None:
        super().__init__(workflow_data)

    @staticmethod
    def verify_workflow_file(workflow_path: str | Path) -> None:
        path = Path(workflow_path)
        if not path.exists():
            raise FileNotFoundError(f"Not found file: {workflow_path}")
        elif path.is_dir() or not path.suffix == ".json":
            raise TypeError(f"Not a json file: {workflow_path}")
        
    def is_valid_link(self, link: Link) -> bool:
        nodes = set(node.id for node in self.workflow_data.nodes)
        if link.input_node_id not in nodes or link.output_node_id not in nodes:
            return False
        if link.input_node_id == link.output_node_id:
            return False
        if link.input_port < 0 or link.output_port < 0:
            return False
        for i in self.workflow_data.links:
            if (i.input_node_id == link.input_node_id and 
                i.input_port == link.input_port and 
                i.output_node_id == link.output_node_id and 
                i.output_port == link.output_port):
                return False
        return True


class WorkflowReader(WorkflowIO):
    def __init__(self, workflow_data: WorkflowData) -> None:
        super().__init__(workflow_data)

    def search_links(
        self,
        input_node_id: Optional[int] = None,
        input_port: Optional[int] = None,
        output_node_id: Optional[int] = None,
        output_port: Optional[int] = None,
        type: Optional[str] = None,
    ) -> List[Link]:
        results = list()
        search_criteria = []
        if input_node_id is not None:
            search_criteria.append(('input_node_id', input_node_id))
        if input_port is not None:
            search_criteria.append(('input_port', input_port))
        if output_node_id is not None:
            search_criteria.append(('output_node_id', output_node_id))
        if output_port is not None:
            search_criteria.append(('output_port', output_port))
        if type is not None:
            search_criteria.append(('type', type))

        if not search_criteria:
            return list()
        for link in self.workflow_data.links:
            match = True
            for attr_name, target_value in search_criteria:
                attr_value = getattr(link, attr_name)
                if attr_value != target_value:
                    match = False
                    break
            
            if match:
                results.append(link)
        
        return results

    def trace_node(
        self,
        start_node: Node,
        target_interface_type: str,
        direction: Literal["forward", "backward"] = "backward",
    ) -> Optional[Tuple[Node, int]]:
        
        if direction not in ["forward", "backward"]:
            raise ValueError("direction must be either 'forward' or 'backward'")
        queue: List[Node] = [start_node]
        visited: set[int] = {start_node.id}
        if direction == "forward":
            graph = self.build_graph(output_graph=True)
            interface = "inputs"
        else:
            graph = self.build_graph(output_graph=False)
            interface = "outputs"
        while queue:
            current_node = queue.pop(0)
            if current_node != start_node:
                for idx, port_info in enumerate(getattr(current_node, interface)):
                    if port_info["type"] == target_interface_type:
                        return current_node, idx
            neighbor_ids = graph[current_node.id]
            for neighbor_id in neighbor_ids:
                if neighbor_id in self.id_to_node and neighbor_id not in visited:
                    neighbor_node = self.id_to_node[neighbor_id]
                    visited.add(neighbor_id)
                    queue.append(neighbor_node)
        return None

    @staticmethod
    def real_size(node: Node) -> NodeSize:
        if node.flags and node.flags.get("collapsed", False):
            return NodeSize(width=COLLAPSE_WIDTH, height=COLLAPSE_HEIGHT)
        return node.size
    
    @staticmethod
    def asdict(obj) -> OrderedDict | Any:
        try:
            obj_vars: Dict = vars(obj)
        except TypeError:
            return obj
        return OrderedDict({k: WorkflowReader.asdict(v) for k, v in obj_vars.items() if v is not None})


class WorkflowWriter(WorkflowIO):
    def __init__(self, workflow_data: WorkflowData) -> None:
        super().__init__(workflow_data)
        self.workflow_validator = WorkflowValidator(workflow_data)

    def fold_unimportant_node(self) -> None:
        for node in self.workflow_data.nodes:
            if node.flags is None:
                node.flags = {}
            node.flags["collapsed"] = False
            if node.type in NodeOptions.fixed_unfold_nodes:
                continue
            if node.type in NodeOptions.fixed_fold_nodes:
                node.flags["collapsed"] = True
            if len(node.inputs) == 0 or len(node.inputs) > 2 or len(node.outputs) != 1:
                continue
            node.flags["collapsed"] = True

    def align_node_dimensions(self, columns: List[List[int]]) -> None:
        id_to_node = self.id_to_node
        columns_objectification = [[id_to_node[j] for j in i] for i in columns]
        for column in columns_objectification:
            max_width = max(min(max([i.size.width for i in column]), 450), 150)
            for node in column:
                node.size.width = max_width

    def create_node(self, type: str, **kwargs) -> Node:
        nodes_template = self.workflow_template["nodes"]
        if type not in nodes_template:
            raise KeyError("No such a node template, you need to config in config/template.json")
        self.workflow_data.last_node_id += 1
        node_template: Dict = copy.deepcopy(nodes_template[type])
        node_template.update(kwargs, id=self.workflow_data.last_node_id)
        node = Node.from_dict(node_template)
        self.workflow_data.nodes.append(node)
        # 更新 id_to_node 映射
        self.id_to_node[node.id] = node
        return node

    def create_link(self, input_node_id: int, input_port: int, output_node_id: int, output_port: int) -> Link | None:
        new_link = Link(0, input_node_id, input_port, output_node_id, output_port, "")
        if not self.workflow_validator.is_valid_link(new_link):
            return
        workflow_reader = WorkflowReader(self.workflow_data)
        old_links = workflow_reader.search_links(output_node_id=output_node_id, output_port=output_port)
        self.remove_links(*old_links)
        input_node = self.id_to_node[input_node_id]
        output_node = self.id_to_node[output_node_id]
        link_type = input_node.outputs[input_port].get("type", "*")
        if link_type == "*":
            link_type = output_node.inputs[output_port].get("type", "*")
        self.workflow_data.last_link_id += 1
        new_link.link_id = self.workflow_data.last_link_id
        new_link.link_type = link_type
        self.workflow_data.links.append(new_link)
        # 更新 id_to_link 映射
        self.id_to_link[new_link.link_id] = new_link
        input_node_links = input_node.outputs[input_port]["links"]
        if isinstance(input_node_links, list):
            input_node.outputs[input_port]["links"].append(self.workflow_data.last_link_id)
        else:
            input_node.outputs[input_port]["links"] = [self.workflow_data.last_link_id]
        output_node.inputs[output_port]["link"] = self.workflow_data.last_link_id
        return new_link

    def remove_links(self, *links: Link) -> None:
        link_ids_to_remove = {link.link_id for link in links}
        for link_id in link_ids_to_remove:
            if link_id not in self.id_to_link:
                continue
            link = self.id_to_link[link_id]
            input_node = self.id_to_node[link.input_node_id]
            output_node = self.id_to_node[link.output_node_id]
            if link.link_id in input_node.outputs[link.input_port]["links"]:
                input_node.outputs[link.input_port]["links"].remove(link.link_id)
            if output_node.inputs[link.output_port]["link"] == link.link_id:
                output_node.inputs[link.output_port]["link"] = None
            self.workflow_data.links.remove(link)
            self.id_to_link.pop(link.link_id)

    def remove_nodes(self, *nodes: Node) -> None:
        workflow_reader = WorkflowReader(self.workflow_data)
        for node in nodes:
            old_input_links = workflow_reader.search_links(input_node_id=node.id)
            old_output_links = workflow_reader.search_links(output_node_id=node.id)
            for output_link in old_input_links:
                result = workflow_reader.trace_node(node, output_link.link_type)
                if not result:
                    continue
                new_in_node, new_in_port = result
                self.create_link(
                    new_in_node.id, new_in_port,
                    output_link.output_node_id, output_link.output_port
                )
            self.remove_links(*old_input_links)
            self.remove_links(*old_output_links)
            self.workflow_data.nodes.remove(node)
            self.id_to_node.pop(node.id)
            
    def remove_unnecessary_nodes(self) -> None:
        wait_to_remove = [node for node in self.workflow_data.nodes if node.type == "Reroute"]
        all_set_nodes_map: Dict[str, Link] = {}
        for node in self.workflow_data.nodes:
            if node.type != "SetNode":
                continue
            if node.widgets_values:
                set_node_label = str(node.widgets_values[0])
                link = self.id_to_link.get(node.inputs[0].get("link", -1))
                if link:
                    all_set_nodes_map[set_node_label] = link
            wait_to_remove.append(node)
        
        for node in self.workflow_data.nodes:
            if node.type != "GetNode":
                continue
            wait_to_remove.append(node)
            if not (node.widgets_values and node.widgets_values[0] in all_set_nodes_map):
                continue
            set_node_link = all_set_nodes_map[node.widgets_values[0]]
            get_node_outputs = node.outputs[0].get("links", [])
            if not get_node_outputs:
                wait_to_remove.append(node)
                continue
            for link_id in get_node_outputs:
                link = self.id_to_link.get(link_id)
                if link:
                    self.create_link(set_node_link.input_node_id, set_node_link.input_port, link.output_node_id, link.output_port)
        if self.workflow_data.extra.get("reroutes"):
            # 这里图方便直接强改了
            self.workflow_data.raw_data["extra"]["reroutes"] = []
        self.remove_nodes(*wait_to_remove)

    def remove_nail(self) -> None:
        for node in self.workflow_data.nodes:
            if not node.flags:
                continue
            node.flags["pinned"] = False

