from src import parser, core, pos_caculate
from src.setting import NodeOptions



if __name__ == "__main__":
    workflow_path = r"你的工作流文件路径"
    output_path = r"新文件流输出路径"
    workflow_data = parser.WorkflowIO.import_file(workflow_path)
    workflow_reader = parser.WorkflowReader(workflow_data)
    workflow_writer = parser.WorkflowWriter(workflow_data)
    standard_order = core.StandardOrder(workflow_reader)
    main_branch_shader = core.MainBranchShader(workflow_reader)
    pos_caculator = pos_caculate.NodePosCalculator(workflow_reader)
    # 是否移除中间节点
    if NodeOptions.remove_intermediate_nodes:
        workflow_writer.remove_unnecessary_nodes()
    # 获取节点的逻辑顺序
    columns = standard_order.get_logic_order(nodes=[i.id for i in workflow_data.nodes])
    # 对齐节点尺寸
    workflow_writer.align_node_dimensions(columns)
    # 自动折叠不重要节点
    workflow_writer.fold_unimportant_node()
    # 计算节点位置，可选择不同的计算器，见method参数
    pos_caculator.modify_node_layout(columns, 0, 0, "center", method="highly_align")
    # 是否设置主路径颜色
    if NodeOptions.set_color_for_main_path:
        main_branch_shader.set_color_for_main_path(list(workflow_reader.id_to_node.keys()))
    # 是否移除节点上的钉子
    if NodeOptions.remove_nails:
        workflow_writer.remove_nail()
    workflow_writer.export_file(output_path)


