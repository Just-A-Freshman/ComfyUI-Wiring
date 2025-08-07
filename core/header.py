from dataclasses import dataclass
from typing import List, Dict, Any, Self, Union




@dataclass
class NodePos:
    x: int
    y: int

    @classmethod
    def from_dict(cls, pos_dict: Dict[str, float]) -> Self:
        return cls(
            x=int(pos_dict.get("0", 0)),
            y=int(pos_dict.get("1", 0))
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
    inputs: List[Dict]
    outputs: List[Dict]
    flags: Dict | None
    widgets_values: List[str | int | float] | None

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
    def from_list(cls, link_list: List[Union[int, str]]) -> Self:
        if len(link_list) != 6:
            raise ValueError(f"link_list must contain exactly 6 elements, got {len(link_list)}")
        return cls(
            link_id=int(link_list[0]),
            input_node_id=int(link_list[1]),
            input_port=int(link_list[2]),
            output_node_id=int(link_list[3]),
            output_port=int(link_list[4]),
            link_type=str(link_list[5])
        )


@dataclass
class Group:
    id: int
    title: str
    bounding: list[int]
    color: str
    font_size: int
    flags: Dict[str, Any] | None

    @classmethod
    def from_dict(cls, group_dict: Dict[str, Any]) -> Self:
        return cls(
            id=group_dict["id"],
            title=group_dict["title"],
            bounding=[int(i) for i in group_dict["bounding"]],
            color=group_dict["color"],
            font_size=group_dict["font_size"],
            flags=group_dict.get("flags")
        )



@dataclass
class WorkflowData:
    nodes: List[Node]
    links: List[Link]
    groups: List[Group]
    last_node_id: int
    last_link_id: int
    raw_data: dict

    @classmethod
    def from_dict(cls, workflow_dict: Dict[str, Any]) -> Self:
        return cls(
            nodes=[Node.from_dict(node) for node in workflow_dict["nodes"]],
            links=[Link.from_list(link) for link in workflow_dict["links"]],
            groups=[Group.from_dict(group) for group in workflow_dict["groups"]],
            last_node_id=workflow_dict["last_node_id"],
            last_link_id=workflow_dict["last_link_id"],
            raw_data=workflow_dict
        )

