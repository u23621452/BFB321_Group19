"""Checks that docs/openapi.json describes the API that really exists."""
import json
import re

DOC_ROUTES = ("/api/docs", "/api/openapi.json")


def real_endpoints(app):
    found = set()
    for rule in app.url_map.iter_rules():
        if not rule.rule.startswith("/api") or rule.rule in DOC_ROUTES:
            continue
        path = re.sub(r"<(\w+)>", r"{\1}", rule.rule)     # <job_number> -> {job_number}
        for method in rule.methods - {"HEAD", "OPTIONS"}:
            found.add((method.lower(), path))
    return found


def test_openapi_file_is_served_and_valid_json(client):
    response = client.get("/api/openapi.json")
    assert response.status_code == 200
    assert json.loads(response.data)["openapi"].startswith("3.")


def test_docs_page_opens_without_login(client):
    assert client.get("/api/docs").status_code == 200


def test_every_endpoint_is_documented_and_nothing_extra(app, client):
    spec = client.get("/api/openapi.json").json
    documented = {(method, path) for path, ops in spec["paths"].items() for method in ops}
    assert documented == real_endpoints(app)