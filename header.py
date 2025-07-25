from dataclasses import dataclass
from typing import List, Dict, Any, Self




@dataclass
class NodePos:
    x: int
    y: int

    @classmethod
    def from_dict(cls, pos_dict: Dict[str, float]) -> Self:
        return cls(
            x=int(pos_dict["0"]),
            y=int(pos_dict["1"])
        )
    
    @property
    def __dict__(self) -> Dict[str, int]:
        return {"0": self.x, "1": self.y}

    

@dataclass
class NodeSize:
    width: int
    height: int

    @classmethod
    def from_dict(cls, size_dict: Dict[str, float]) -> Self:
        return cls(
            width=int(size_dict["0"]),
            height=int(size_dict["1"])
        )
    
    @property
    def __dict__(self) -> Dict[str, int]:
        return {"0": self.width, "1": self.height}


@dataclass
class Node:
    id: int
    type: str
    pos: NodePos
    size: NodeSize
    inputs: List
    outputs: List
    flags: Dict
    title: str
    widgets_values: List[str | int | float]

    @classmethod
    def from_dict(cls, node_dict: Dict[str, Any]) -> Self:
        return cls(
            id=node_dict["id"],
            type=node_dict["type"],
            pos=NodePos.from_dict(node_dict["pos"]),
            size=NodeSize.from_dict(node_dict["size"]),
            inputs=node_dict["inputs"],
            outputs=node_dict["outputs"],
            flags=node_dict.get("flags"),
            title=node_dict.get("title"),
            widgets_values=node_dict.get("widgets_values")
        )


@dataclass
class Link:
    link_id: int
    input_node_id: int
    input_port: int
    output_node_id: int
    output_port: int
    link_type: str

    @classmethod
    def from_list(cls, link_list: List[Any]) -> Self:
        return cls(
            link_id=link_list[0],
            input_node_id=link_list[1],
            input_port=link_list[2],
            output_node_id=link_list[3],
            output_port=link_list[4],
            link_type=link_list[5]
        )



@dataclass
class WorkflowData:
    nodes: List[Node]
    links: List[Link]
    last_node_id: int
    last_link_id: int
    raw_data: dict

    @classmethod
    def from_dict(cls, workflow_dict: Dict[str, Any]) -> Self:
        return cls(
            nodes=[Node.from_dict(node) for node in workflow_dict["nodes"]],
            links=[Link.from_list(link) for link in workflow_dict["links"]],
            last_node_id=workflow_dict["last_node_id"],
            last_link_id=workflow_dict["last_link_id"],
            raw_data=workflow_dict
        )
