import os
import uuid

import functions_framework
from flask import Request, jsonify
from renderer import draw_mermaid_diagram, draw_architecture_diagram, move_file_to_gcs

BUCKET_NAME = os.environ["BUCKET_NAME"]
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "playground-449613")


@functions_framework.http
def main(request: Request):
    body = request.get_json(silent=True) or {}
    diagram_type = body.get("type")   # "mermaid" or "architecture"
    code = body.get("code", "")
    output_format = body.get("format", "svg")
    title = body.get("title", "Untitled")

    if not diagram_type or not code:
        return jsonify({"error": "type and code are required"}), 400

    if diagram_type == "mermaid":
        result = draw_mermaid_diagram(code, output_format)
        if "error" in result:
            return jsonify({"error": result["error"]}), 422
        local_path = result["path"]
    elif diagram_type == "architecture":
        filename = str(uuid.uuid4())
        draw_architecture_diagram(title=title, code=code, filename=filename)
        local_path = filename + ".png"
    else:
        return jsonify({"error": f"Unknown type: {diagram_type}"}), 400

    blob = move_file_to_gcs(local_path, bucket_name=BUCKET_NAME, project_id=GCP_PROJECT_ID)
    return jsonify({"uri": f"gs://{blob.bucket.name}/{blob.name}", "title": title})
