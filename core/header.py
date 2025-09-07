from dataclasses import dataclass, fields
from typing import List, Dict, Any, Self, Union


@dataclass
class NodeProperty:
    @classmethod
    def from_dict(cls, prop_dict: Dict[str, Any]) -> Self:
        # 如果字典无序，那是真没招了
        property = fields(cls)
        return cls(
            **{field.name: value for field, value in zip(property, prop_dict.values())}
        )
    
    @classmethod
    def from_list(cls, prop_list: List[Any]) -> Self:
        property = fields(cls)
        return cls(
            **{field.name: prop_list[i] for i, field in enumerate(property)}
        )
    
    @classmethod
    def from_data(cls, prop_data: Union[List[Any], Dict[str, Any]]):
        if isinstance(prop_data, dict):
            return cls.from_dict(prop_data)
        elif isinstance(prop_data, list):
            return cls.from_list(prop_data)
        else:
            raise TypeError(f"Unsupported type for {cls.__name__} creation")


@dataclass
class NodePos(NodeProperty):
    x: int
    y: int
 
    @property
    def __dict__(self) -> Dict[str, int]:
        return {"0": self.x, "1": self.y}


@dataclass
class NodeSize(NodeProperty):
    width: int
    height: int
    
    @property
    def __dict__(self) -> Dict[str, int]:
        return {"0": self.width, "1": self.height}


@dataclass
class Node:
    id: int
    type: str
    pos: NodePos
    size: NodeSize
    inputs: List[Dict[str, Any]]
    outputs: List[Dict[str, Any]]
    flags: Dict | None
    widgets_values: List[str | int | float] | None
    color: str
    bgcolor: str

    @classmethod
    def from_dict(cls, node_dict: Dict[str, Any]) -> Self:
        return cls(
            id=node_dict["id"],
            type=node_dict["type"],
            pos=NodePos.from_data(node_dict["pos"]),
            size=NodeSize.from_data(node_dict["size"]),
            inputs=node_dict.get("inputs", []),
            outputs=node_dict.get("outputs", []),
            flags=node_dict.get("flags"),
            widgets_values=node_dict.get("widgets_values"),
            color=node_dict.get("color", "#322"),
            bgcolor=node_dict.get("bgcolor", "#533")
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
    flags: Dict[str, Any]

    @classmethod
    def from_dict(cls, group_dict: Dict[str, Any]) -> Self:
        return cls(
            id=group_dict.get("id", 0),
            title=group_dict.get("title", ""),
            bounding=[int(i) for i in group_dict["bounding"]],
            color=group_dict.get("color", "#3f789e"),
            font_size=group_dict.get("font_size", 24),
            flags=group_dict.get("flags", {})
        )


@dataclass
class WorkflowData:
    nodes: List[Node]
    links: List[Link]
    groups: List[Group]
    extra: Dict[str, Any]
    last_node_id: int
    last_link_id: int
    raw_data: dict

    @classmethod
    def from_dict(cls, workflow_dict: Dict[str, Any]) -> Self:
        return cls(
            nodes=[Node.from_dict(node) for node in workflow_dict["nodes"]],
            links=[Link.from_list(link) for link in workflow_dict["links"]],
            groups=[Group.from_dict(group) for group in workflow_dict["groups"]],
            extra=workflow_dict.get("extra", {}),
            last_node_id=workflow_dict["last_node_id"],
            last_link_id=workflow_dict["last_link_id"],
            raw_data=workflow_dict
        )

