# ```
# The method is from StandardOrder
# ```
#     def add_intermediate_nodes(self, columns: List[List[int]]) -> None:
#         max_span = max(NodeOptions.max_span, 2)
#         id_to_link = self.workflow_reader.id_to_link
#         id_to_node = {node.id: node for node in self.workflow_reader.workflow_data.nodes}
#         set_nodes: Dict[Tuple[int, int], int] = {}
#         node_to_col: Dict[int, int] = self.workflow_reader.node_to_col(columns)
#         for node in self.workflow_reader.workflow_data.nodes:
#             if node.type != "SetNode":
#                 continue
#             link_id = node.inputs[0]["link"]
#             if link_id is None or link_id not in id_to_link:
#                 continue
#             link = id_to_link[link_id]
#             set_nodes[(link.input_node_id, link.input_port)] = node.id
#         workflow_writer = WorkflowWriter(self.workflow_reader.workflow_data)
#         links = self.workflow_reader.workflow_data.links
#         long_links_table: defaultdict[Tuple[int, int], List[Link]] = defaultdict(list)
#         for link in links.copy():
#             input_node_col = node_to_col.get(link.input_node_id)
#             output_node_col = node_to_col.get(link.output_node_id)
#             if input_node_col is None or output_node_col is None:
#                 continue
#             span = output_node_col - input_node_col
#             if span <= max_span:
#                 continue
#             input_node_id = link.input_node_id
#             input_port = link.input_port
#             if (input_node_id, input_port) not in set_nodes:
#                 input_node = id_to_node[input_node_id]
#                 set_node = workflow_writer.create_node(type="SetNode")
#                 node_name = f"{input_node.outputs[input_port]['name']}_{input_node.id}"
#                 set_node.widgets_values = [node_name]
#                 set_nodes[(input_node_id, input_port)] = set_node.id
#                 new_link = workflow_writer.create_link(input_node_id, input_port, set_node.id, 0)
#                 if new_link is None:
#                     continue
#                 set_node_input = set_node.inputs[0]
#                 set_node_input["type"] = new_link.link_type
#                 set_node_input["name"] = new_link.link_type
#             long_links_table[(input_node_id, input_port)].append(link)
#         set_new_columns: defaultdict[int, list] = defaultdict(list)
#         for k, v in set_nodes.items():
#             input_node_id, _ = k
#             new_col = node_to_col[input_node_id] + 1
#             set_new_columns[new_col].append(v)
#         set_new_columns = DataTool.merge_dict_by_key(set_new_columns, threshold=1)
#         count = 0
#         for col_idx, new_columns in set_new_columns.items():
#             columns.insert(col_idx + count, new_columns)
#             count += 1
#         node_to_col = self.workflow_reader.node_to_col(columns)
#         threshold = max_span // 2
#         id_to_node = {node.id: node for node in self.workflow_reader.workflow_data.nodes}
#         for (input_node_id, input_port), long_links in long_links_table.items():
#             link_length: List[int] = [
#                 node_to_col[long_link.output_node_id] - node_to_col[long_link.input_node_id]
#                 for long_link in long_links
#             ]
#             set_node_id = set_nodes[(input_node_id, input_port)]
#             set_node = id_to_node[set_node_id]
#             set_node_type = set_node.inputs[0]["type"]
#             while max(link_length) > threshold:
#                 temp_link_length = [i for i in link_length if i > 0]
#                 if temp_link_length:
#                     min_link_length = min(temp_link_length)
#                 else:
#                     break
#                 min_link_idx = link_length.index(min_link_length)
#                 min_long_link = long_links[min_link_idx]
#                 get_node_col = node_to_col[min_long_link.output_node_id] - 1
#                 get_node = workflow_writer.create_node(type="GetNode", widgets_values=set_node.widgets_values)
#                 get_node_output = get_node.outputs[0]
#                 get_node_output["type"] = get_node_output["name"] = set_node_type
#                 columns[get_node_col].append(get_node.id)
#                 link_length = [i - min_link_length for i in link_length]
#                 for idx, length in enumerate(link_length):
#                     if length > threshold or length < 0:
#                         continue
#                     link = long_links[idx]
#                     workflow_writer.create_link(get_node.id, 0, link.output_node_id, link.output_port)
