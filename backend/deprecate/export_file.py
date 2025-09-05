# def export_file(self, output_path: str, overwrite_raw_data: bool = False) -> None:
    #     orders = Tool.flatten_generator(Tool.topological_sort(self.workflow_data))
    #     order_table = {node_id: order for order, node_id in enumerate((orders))}
    #     raw_data = self.workflow_data.raw_data if overwrite_raw_data else self.workflow_data.raw_data.copy()
    #     nodes_template = self.workflow_template["nodes"]
    #     raw_id_nodes: Dict[int, Dict] = {node["id"]: node for node in raw_data["nodes"]}
    #     new_id_nodes: Dict[int, Node] = {node.id: node for node in self.workflow_data.nodes}
    #     for new_node in self.workflow_data.nodes:
    #         new_node_dict: dict = WorkflowReader.asdict(new_node)
    #         new_node_dict["order"] = order_table[new_node.id]
    #         if new_node.id in raw_id_nodes:
    #             raw_id_nodes[new_node.id].update(new_node_dict)
    #         else:
    #             node_type: str = new_id_nodes[new_node.id].type
    #             template: Dict = nodes_template.get(node_type, {})
    #             if not template:
    #                 raise KeyError(f"type: {node_type} not found in  nodes template.")
    #             raw_data["nodes"].append({**template, **new_node_dict})
    #     raw_data["links"] = [list(WorkflowReader.asdict(link).values()) for link in self.workflow_data.links]
    #     raw_data["groups"] = [WorkflowReader.asdict(group) for group in self.workflow_data.groups]
    #     raw_data["last_node_id"] = self.workflow_data.last_node_id
    #     raw_data["last_link_id"] = self.workflow_data.last_link_id
    #     with open(output_path, "w", encoding="utf-8") as f:
    #         json.dump(raw_data, f, ensure_ascii=False, indent=4)
