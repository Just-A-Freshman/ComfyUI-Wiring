from src import parser, core, pos_caculate




if __name__ == "__main__":
    workflow_path = input("请输入文件路径:")
    output_path = r"D:\Users\pbl\Desktop\output.json"
    workflow_data = parser.WorkflowIO.import_file(workflow_path)
    workflow_reader = parser.WorkflowReader(workflow_data)
    workflow_writer = parser.WorkflowWriter(workflow_data)
    main_branch_order = core.MainBranchOrder(workflow_reader)
    pos_caculator = pos_caculate.NodePosCalculator(workflow_reader)
    workflow_writer.remove_unnecessary_nodes()
    columns = main_branch_order.get_logic_order(nodes=[i.id for i in workflow_data.nodes])
    workflow_writer.align_node_dimensions(columns)
    workflow_writer.fold_unimportant_node()
    print("""
        1、简单对齐布局器 -> 输入1
        2、平均对齐布局器 -> 输入2
        3、强化对齐布局器 -> 输入3
        其他键默认到3
    """)
    method = input("选择排布方法: ")
    if method == "1":
        pos_caculator.simple_align_caculator(columns, 0, 0, "center")
    elif method == "2":
        pos_caculator.average_align_caculator(columns, 0, 0, "center")
    else:
        pos_caculator.highly_align_cuculator(columns, 0, 0, "center")
    workflow_writer.export_file(output_path)
    print("处理完成!回车键继续...")
    input()


