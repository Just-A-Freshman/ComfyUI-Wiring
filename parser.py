from typing import Dict, Any
from pathlib import Path
import json

from header import WorkflowData, Node, NodeSize



CONFIG = Path("config")
TEMPLATE = CONFIG / "template.json"
COLLAPSE_WIDTH = 160
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
    def real_size(node: Node) -> NodeSize:
        if node.flags.get("collapsed"):
            return NodeSize(width=COLLAPSE_WIDTH, height=COLLAPSE_HEIGHT)
        return node.size
    
    @staticmethod
    def asdict(obj) -> Dict | Any:
        try:
            obj_vars: Dict = vars(obj)
        except TypeError:
            return obj
        return {k: WorkflowReader.asdict(v) for k, v in obj_vars.items() if v is not None}



class WorkflowWriter(object):
    def __init__(self, workflow_data: WorkflowData) -> None:
        self.workflow_data = workflow_data
        self.workflow_template = self.load_workflow_template()

    def load_workflow_template(self) -> Dict[str, Dict]:
        with open(TEMPLATE, "r", encoding="utf-8") as f:
            nodes_template: Dict[str, Dict] = json.load(f)
            return nodes_template
        
    @property
    def id_node_table(self) -> Dict[int, Node]:
        return {node.id: node for node in self.workflow_data.nodes}

    def create_node(self, type, **kwargs):
        nodes_template = self.workflow_template["nodes"]
        if type not in nodes_template:
            raise KeyError("No such a node template, you need to config in config/template.json")
        self.last_node_id += 1
        node_template: Dict = nodes_template[type]
        node_template.update(kwargs, id=self.workflow_data.last_node_id)
        node = Node.from_dict(node_template)
        self.workflow_data.links.append(node)

    def create_link(
            self, 
            input_node_id: int, 
            input_port: int, 
            output_node_id: int, 
            output_port: int
        ) -> None:
        id_to_node = self.id_node_table
        if input_node_id not in id_to_node or output_node_id not in id_to_node:
            raise ValueError("Invalid input_node_id or output_node_id!")
        

    def export_file(self, output_path: str, overwrite_raw_data: bool = False) -> None:
        raw_data = self.workflow_data.raw_data if overwrite_raw_data else self.workflow_data.raw_data.copy()
        nodes_template = self.workflow_template["nodes"]
        raw_id_nodes: Dict[int, Dict] = {node["id"]: node for node in raw_data["nodes"]}
        new_id_nodes: Dict[int, Node] = {node.id: node for node in self.workflow_data.nodes}
        for id in new_id_nodes:
            new_node_dict: dict = WorkflowReader.asdict(new_id_nodes[id])
            if id in raw_id_nodes:
                raw_id_nodes[id].update(new_node_dict)
            else:
                node_type: str = new_id_nodes[id].type
                template: Dict = nodes_template.get(node_type)
                if template is None:
                    raise KeyError(f"type: {node_type} not found in  nodes template.")
                template = template.copy()
                template.update(new_node_dict)
                raw_data["nodes"].append(template)
        raw_data["last_node_id"] = self.workflow_data.last_node_id
        raw_data["last_link_id"] = self.workflow_data.last_link_id
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(raw_data, f, ensure_ascii=False, indent=4)
