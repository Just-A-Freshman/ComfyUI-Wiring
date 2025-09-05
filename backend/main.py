from src import parser, core, pos_caculate




if __name__ == "__main__":
    workflow_path = r"你的工作流文件.json"
    output_path = r"输出文件名.json"
    workflow_data = parser.WorkflowIO.import_file(workflow_path)
    workflow_reader = parser.WorkflowReader(workflow_data)
    workflow_writer = parser.WorkflowWriter(workflow_data)
    main_branch_order = core.MainBranchOrder(workflow_reader)
    pos_caculator = pos_caculate.NodePosCalculator(workflow_reader)
    # 将中间节点移除，如转接口Reroute;设置节点和获取节点。
    workflow_writer.remove_unnecessary_nodes()
    columns = main_branch_order.get_logic_order(nodes=[i.id for i in workflow_data.nodes])
    # 开启对齐节点尺寸
    workflow_writer.align_node_dimensions(columns)
    # 自动折叠不重要节点
    workflow_writer.fold_unimportant_node()
    # 使用强对齐计算器对逻辑节点进行布局
    # 一共有三类计算器，simple_align_calculator、average_align_calculator和highly_align_calculator
    # 参数传递含义一致
    pos_caculator.highly_align_calculator(columns, 0, 0, "center")
    workflow_writer.export_file(output_path)


