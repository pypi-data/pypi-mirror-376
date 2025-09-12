from fastapi import FastAPI
from fastapi.testclient import TestClient
from easy_middleware import RequestTimingMiddleware

def create_app():
    app = FastAPI()
    app.add_middleware(RequestTimingMiddleware)

    @app.get("/")
    def hello():
        return {"msg": "ok"}

    return app

def test_timing_header():
    app = create_app()
    client = TestClient(app)

    response = client.get("/")
    assert response.status_code == 200

    assert "X-Process-Time-ms" in response.headers
    process_time = float(response.headers["X-Process-Time-ms"])
    assert process_time >= 0
