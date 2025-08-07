import os
import json
from pathlib import Path
from typing import Literal


from flask import Flask, Response, render_template, jsonify, send_file, request
from werkzeug.utils import secure_filename


from core.parser import WorkflowReader, WorkflowWriter
from core.Utils import NodeOptions
from core.core import LogicalConfig, CoordinateConfig



current_dir = Path(__file__).parent.absolute()
app = Flask(
    __name__,
    template_folder = current_dir / "web" / "templates",
    static_folder = current_dir / "web" / "static"
)
app.config['temp'] = Path('temp')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
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
    config: dict = json.loads(request.form.get('config', '{}'))
    NodeOptions.update_setting({
        'gap_x': config.get('gap_x', 100),
        'gap_y': config.get('gap_y', 100),
        'max_span': config.get('max_span', 6),
        'size_align': config.get('size_align', True),
        'set_node': config.get('set_node', True),
        'force_unfold': config.get('force_unfold', True)
    })
    
    try:
        workflow_reader = WorkflowReader(input_path)
        workflow_writer = WorkflowWriter(workflow_reader.workflow_data)
        
        logical_config = LogicalConfig(workflow_reader)
        coordinate_config = CoordinateConfig(workflow_reader)
        
        columns = logical_config.get_logic_config()
        coordinate_config.modify_layout(columns)
        output_filename = f"output.json"
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
    output_path: Path = app.config['temp'] / filename
    if not output_path.exists():
        return jsonify({'error': 'File not found'}), 404
    return send_file(output_path, as_attachment=True)


if __name__ == '__main__':
    app.run()
