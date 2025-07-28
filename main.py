from parser import WorkflowReader, WorkflowWriter, Setting
from core import LogicalConfig, CoordinateConfig



if __name__ == "__main__":
    Setting.load_setting()
    workflow_path = r"workflow_test/4.json"
    output_path = r"D:\Users\pbl\Desktop\output.json"
    workflow_reader = WorkflowReader(workflow_path)
    workflow_writer = WorkflowWriter(workflow_reader.workflow_data)
    logical_config = LogicalConfig(workflow_reader)
    coordinate_config = CoordinateConfig(workflow_reader)
    columns = logical_config.get_logic_config()
    node_coords = coordinate_config.modify_layout(columns)
    workflow_writer.export_file(output_path)
