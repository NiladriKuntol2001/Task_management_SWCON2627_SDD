"""Rebuild swagger.html from openapi.yaml (run after editing the spec):
    python docs/api/build_swagger_html.py
The spec is embedded in the page, so it opens straight from disk (no server needed)."""
import json
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
spec = yaml.safe_load((HERE / "openapi.yaml").read_text(encoding="utf-8"))
page = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>StudyFlow API — Swagger UI</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.17.14/swagger-ui.css">
  <style>body { margin: 0; background: #fff; } .swagger-ui .topbar { display: none; }</style>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.17.14/swagger-ui-bundle.js"></script>
  <script>
    window.ui = SwaggerUIBundle({
      spec: __SPEC__,
      dom_id: "#swagger-ui",
      deepLinking: true,
      docExpansion: "list",
      defaultModelsExpandDepth: 0,
      tryItOutEnabled: false
    });
  </script>
</body>
</html>
""".replace("__SPEC__", json.dumps(spec, ensure_ascii=False))
(HERE / "swagger.html").write_text(page, encoding="utf-8")
print("wrote", HERE / "swagger.html")
