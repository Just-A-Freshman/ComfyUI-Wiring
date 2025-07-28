from parser import WorkflowReader, WorkflowWriter
from core import LogicalConfig, CoordinateConfig



if __name__ == "__main__":
    workflow_path = r"你的工作流文件路径.json"     # 这里改成你自己的工作流文件路径
    output_path = r"输出工作流文件路径.json"
    workflow_reader = WorkflowReader(workflow_path)
    workflow_writer = WorkflowWriter(workflow_reader.workflow_data)
    logical_config = LogicalConfig(workflow_reader)
    coordinate_config = CoordinateConfig(workflow_reader)
    columns = logical_config.get_logic_config()
    node_coords = coordinate_config.modify_layout(columns)
    workflow_writer.export_file(output_path)
