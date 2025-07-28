from typing import Dict, List, Any
from collections import OrderedDict
from pathlib import Path
import json
import copy

from Utils import UtilsTool
from header import WorkflowData, Node, NodeSize, Link


CONFIG = Path("config")
TEMPLATE = CONFIG / "template.json"
COLLAPSE_WIDTH = 150
COLLAPSE_HEIGHT = 30


class WorkflowReader(object):
    def __init__(self, workflow_path: str) -> None:
        self.workflow_data = self.import_file(workflow_path)

    @staticmethod
    def is_valid_workflow_file(workflow_path) -> None:
        path = Path(workflow_path)
        if not path.exists():
            raise FileNotFoundError(f"Not found file: {workflow_path}")
        elif path.is_dir() or not path.suffix == ".json":
            raise TypeError(f"Not a json file: {workflow_path}")
        
    def import_file(self, workflow_path) -> WorkflowData:
        self.is_valid_workflow_file(workflow_path)
        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow_dict = json.load(f)
            workflow_data = WorkflowData.from_dict(workflow_dict)
            return workflow_data
        
    @staticmethod
    def node_to_col(columns) -> Dict[int, int]:
        node_to_col: Dict[int, int] = {}
        for col_idx, col_nodes in enumerate(columns):
            for node in col_nodes:
                node_to_col[node] = col_idx
        return node_to_col
        
    @staticmethod
    def real_size(node: Node) -> NodeSize:
        if node.flags.get("collapsed"):
            return NodeSize(width=COLLAPSE_WIDTH, height=COLLAPSE_HEIGHT)
        return node.size
    
    @staticmethod
    def asdict(obj) -> OrderedDict | Any:
        try:
            obj_vars: Dict = vars(obj)
        except TypeError:
            return obj
        return OrderedDict({k: WorkflowReader.asdict(v) for k, v in obj_vars.items() if v is not None})



class WorkflowWriter(object):
    def __init__(self, workflow_data: WorkflowData) -> None:
        self.workflow_data = workflow_data
        self.workflow_template = self.load_workflow_template()

    @property
    def id_node_table(self) -> Dict[int, Node]:
        return {node.id: node for node in self.workflow_data.nodes}

    def load_workflow_template(self) -> Dict[str, Dict]:
        with open(TEMPLATE, "r", encoding="utf-8") as f:
            return json.load(f)

    def is_valid_link(self, input_node_id: int, input_port: int, output_node_id: int, output_port: int) -> bool:
        id_to_node = self.id_node_table
        if input_node_id not in id_to_node or output_node_id not in id_to_node:
            raise ValueError("Invalid input_node_id or output_node_id!")
        if input_node_id == output_node_id:
            raise ValueError("Cannot link a node to itself!")
        if input_port < 0 or output_port < 0:
            raise ValueError("Port numbers must be non-negative integers!")
        for link in self.workflow_data.links:
            if (link.input_node_id == input_node_id and 
                link.input_port == input_port and 
                link.output_node_id == output_node_id and 
                link.output_port == output_port):
                return False
        return True

    def remove_exist_link(self, output_node_id: int, output_port: int) -> None:
        target_link = None
        for link in self.workflow_data.links:
            if link.output_node_id == output_node_id and link.output_port == output_port:
                target_link = link
                break
        
        if not target_link:
            return
        
        input_node = self.id_node_table.get(target_link.input_node_id)
        output_node = self.id_node_table.get(target_link.output_node_id)
        
        if not input_node or not output_node:
            # 节点不存在，说明链接本身也是无效的，可以移除
            self.workflow_data.links.remove(target_link)
            return
        
        for output in input_node.outputs:
            output_links: List = output.get("links")
            if output_links is None:
                continue
            if target_link.link_id in output_links:
                output_links.remove(target_link.link_id)
                if not output_links:
                    output["links"] = None
                break
        
        for input_port in output_node.inputs:
            if input_port.get("link") == target_link.link_id:
                input_port["link"] = None
                break

        self.workflow_data.links.remove(target_link)

    def create_node(self, type: str, **kwargs) -> Node:
        nodes_template = self.workflow_template["nodes"]
        if type not in nodes_template:
            raise KeyError("No such a node template, you need to config in config/template.json")
        self.workflow_data.last_node_id += 1
        node_template: Dict = copy.deepcopy(nodes_template[type])
        node_template.update(kwargs, id=self.workflow_data.last_node_id)
        node = Node.from_dict(node_template)
        self.workflow_data.nodes.append(node)
        return node

    def create_link(self, input_node_id: int, input_port: int, output_node_id: int, output_port: int) -> Link:
        if not self.is_valid_link(input_node_id, input_port, output_node_id, output_port):
            return
        self.remove_exist_link(output_node_id, output_port)
        input_node = self.id_node_table[input_node_id]
        output_node = self.id_node_table[output_node_id]
        link_type = input_node.outputs[input_port].get("type", "*")
        self.workflow_data.last_link_id += 1
        link_list = [
            self.workflow_data.last_link_id,
            input_node_id, input_port, 
            output_node_id, output_port, link_type
        ]
        new_link = Link.from_list(link_list)
        self.workflow_data.links.append(new_link)
        input_node_links = input_node.outputs[input_port]["links"]
        if isinstance(input_node_links, list):
            input_node_links.append(self.workflow_data.last_link_id)
        else:
            input_node.outputs[input_port]["links"] = [self.workflow_data.last_link_id]
        output_node.inputs[output_port]["link"] = self.workflow_data.last_link_id
        return new_link

    def export_file(self, output_path: str, overwrite_raw_data: bool = False) -> None:
        orders = UtilsTool.flatten_generator(UtilsTool.topological_sort(self.workflow_data))
        order_table = {node_id: order for order, node_id in enumerate((orders))}
        raw_data = self.workflow_data.raw_data if overwrite_raw_data else self.workflow_data.raw_data.copy()
        nodes_template = self.workflow_template["nodes"]
        raw_id_nodes: Dict[int, Dict] = {node["id"]: node for node in raw_data["nodes"]}
        new_id_nodes: Dict[int, Node] = {node.id: node for node in self.workflow_data.nodes}
        for new_node in self.workflow_data.nodes:
            new_node_dict: dict = WorkflowReader.asdict(new_node)
            new_node_dict["order"] = order_table[new_node.id]
            if new_node.id in raw_id_nodes:
                raw_id_nodes[new_node.id].update(new_node_dict)
            else:
                node_type: str = new_id_nodes[new_node.id].type
                template: Dict = nodes_template.get(node_type)
                if template is None:
                    raise KeyError(f"type: {node_type} not found in  nodes template.")
                raw_data["nodes"].append({**template, **new_node_dict})
        raw_data["links"] = [list(WorkflowReader.asdict(link).values()) for link in self.workflow_data.links]
        raw_data["last_node_id"] = self.workflow_data.last_node_id
        raw_data["last_link_id"] = self.workflow_data.last_link_id
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(raw_data, f, ensure_ascii=False, indent=4)
