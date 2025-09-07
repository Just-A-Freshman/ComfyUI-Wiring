from src import parser, core, pos_caculate
from src.setting import NodeOptions



if __name__ == "__main__":
    workflow_path = r"D:\Users\pbl\Desktop\高清换脸-在线生图海报换脸-V2.0 .json"
    output_path = r"D:\Users\pbl\Desktop\output.json"
    workflow_data = parser.WorkflowIO.import_file(workflow_path)
    workflow_reader = parser.WorkflowReader(workflow_data)
    workflow_writer = parser.WorkflowWriter(workflow_data)
    standard_order = core.StandardOrder(workflow_reader)
    main_branch_shader = core.MainBranchShader(workflow_reader)
    pos_caculator = pos_caculate.NodePosCalculator(workflow_reader)
    NodeOptions.same_column_stacking_strength = 2
    if NodeOptions.remove_intermediate_nodes:
        workflow_writer.remove_unnecessary_nodes()
    columns = standard_order.get_logic_order(nodes=[i.id for i in workflow_data.nodes])
    workflow_writer.align_node_dimensions(columns)
    workflow_writer.fold_unimportant_node()
    pos_caculator.modify_node_layout(columns, 0, 0, "center", method="highly_align")
    if NodeOptions.set_color_for_main_path:
        main_branch_shader.set_color_for_main_path(list(workflow_reader.id_to_node.keys()))
    if NodeOptions.remove_nails:
        workflow_writer.remove_nail()
    workflow_writer.export_file(output_path)


