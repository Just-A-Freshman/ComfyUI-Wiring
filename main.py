from parser import WorkflowReader, WorkflowWriter, Setting
from core import LogicalConfig, CoordinateConfig



if __name__ == "__main__":
    Setting.load_setting()
    workflow_path = r"你的工作流路径.json"
    output_path = r"你的输出工作流路径.json"
    workflow_reader = WorkflowReader(workflow_path)
    workflow_writer = WorkflowWriter(workflow_reader.workflow_data)
    logical_config = LogicalConfig(workflow_reader)
    coordinate_config = CoordinateConfig(workflow_reader)
    columns = logical_config.get_logic_config()
    node_coords = coordinate_config.modify_layout(columns)
    workflow_writer.export_file(output_path)
