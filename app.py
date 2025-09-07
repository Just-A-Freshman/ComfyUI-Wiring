import os
import json
from pathlib import Path
from typing import Literal, Dict, Any


from flask import Flask, Response, render_template, jsonify, send_file, request
from werkzeug.utils import secure_filename


from core.parser import WorkflowIO, WorkflowReader, WorkflowWriter
from core.setting import NodeOptions
from core.core import StandardOrder, MainBranchShader
from core.pos_caculate import NodePosCalculator, GroupPosCalulator


current_dir = Path(__file__).parent.absolute()
app = Flask(
    __name__,
    template_folder = current_dir / "web" / "templates",
    static_folder = current_dir / "web" / "static"
)
app.config['temp'] = Path('temp')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
os.makedirs(app.config['temp'], exist_ok=True)


@app.route('/')
def index() -> str:
    return render_template(r"index.html")


@app.route('/generate', methods=['POST'])
def generate_layout() -> tuple[Response, Literal[400]] | Response | tuple[Response, Literal[500]]:
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    temp_filename = "input.json" if file.filename is not None else ""
    filename = secure_filename(temp_filename)
    input_path = app.config['temp'] / filename
    file.save(input_path)
    config: Dict[str, Any] = json.loads(request.form.get('config', '{}'))
    NodeOptions.update_setting({
        'gap_x': config.get('gap_x', 100),
        'gap_y': config.get('gap_y', 100),
        'same_column_stacking_strength': config.get('same_column_stacking_strength', 1),
        'layout_calculator': config.get('layout_calculator', 'highly_align'),
        'remove_intermediate_nodes': config.get('remove_intermediate_nodes', True),
        'set_color_for_main_path': config.get('set_color_for_main_path', True)
    })
    try:
        workflow_data = WorkflowIO.import_file(input_path)
        workflow_reader = WorkflowReader(workflow_data)
        workflow_writer = WorkflowWriter(workflow_data)
        standard_order = StandardOrder(workflow_reader)
        main_branch_shader = MainBranchShader(workflow_reader)
        group_caculator = GroupPosCalulator(workflow_reader)
        pos_caculator = NodePosCalculator(workflow_reader)
        orig_groups = group_caculator.get_orig_groups()
        if NodeOptions.remove_intermediate_nodes:
            workflow_writer.remove_unnecessary_nodes()
        columns = standard_order.get_logic_order(nodes=[i.id for i in workflow_data.nodes])
        workflow_writer.align_node_dimensions(columns)
        workflow_writer.fold_unimportant_node()
        pos_caculator.modify_node_layout(columns, align=NodeOptions.calculator_align, method=NodeOptions.layout_calculator)
        group_caculator.modify_group_layout(orig_groups)
        if NodeOptions.set_color_for_main_path:
            main_branch_shader.set_color_for_main_path(list(workflow_reader.id_to_node.keys()))
        if NodeOptions.remove_nails:
            workflow_writer.remove_nail()
        output_filename = "output.json"
        output_path = app.config['temp'] / output_filename
        workflow_writer.export_file(output_path)
        with open(output_path, 'r', encoding='utf-8') as f:
            preview_data = json.load(f)
        return jsonify({
            'success': True,
            'download_url': f'/download/{output_filename}',
            'preview_data': preview_data
        })
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500


@app.route('/download/<filename>')
def download_file(filename: str) -> tuple[Response, Literal[404]] | Response:
    output_path: Path = app.config['temp'] / "output.json"
    if not output_path.exists():
        return jsonify({'error': 'File not found'}), 404
    return send_file(output_path, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=False)

