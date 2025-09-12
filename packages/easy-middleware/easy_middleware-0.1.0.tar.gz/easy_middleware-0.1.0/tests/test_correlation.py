import re
from fastapi import FastAPI
from fastapi.testclient import TestClient
from easy_middleware import CorrelationIdMiddleware

def create_app():
    app = FastAPI()
    app.add_middleware(CorrelationIdMiddleware)

    @app.get("/")
    def hello():
        return {"msg": "ok"}

    return app

def test_correlation_id_header_added():
    app = create_app()
    client = TestClient(app)

    response = client.get("/")
    assert response.status_code == 200

    # Ensure header exists
    correlation_id = response.headers.get("X-Request-ID")
    assert correlation_id is not None
    assert re.match(r"^[a-f0-9-]{36}$", correlation_id)
