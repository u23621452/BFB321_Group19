"""Serves the OpenAPI description and a Swagger UI page that reads it."""
import os

from flask import Blueprint, current_app, render_template_string, send_from_directory

bp = Blueprint("api_docs", __name__)

SWAGGER_PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>StockFlow API docs</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.17.14/swagger-ui.css">
</head>
<body>
  <div id="swagger"></div>
  <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.17.14/swagger-ui-bundle.js"></script>
  <script>
    SwaggerUIBundle({ url: "/api/openapi.json", dom_id: "#swagger" });
  </script>
</body>
</html>"""


@bp.get("/api/openapi.json")
def openapi_json():
    docs_folder = os.path.join(current_app.root_path, "..", "docs")
    return send_from_directory(docs_folder, "openapi.json", mimetype="application/json")


@bp.get("/api/docs")
def swagger_ui():
    return render_template_string(SWAGGER_PAGE)