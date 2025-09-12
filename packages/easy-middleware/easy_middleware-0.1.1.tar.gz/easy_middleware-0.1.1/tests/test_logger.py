from fastapi import FastAPI
from fastapi.testclient import TestClient
from easy_middleware import LoggerMiddleware

def create_app():
    app = FastAPI()
    app.add_middleware(LoggerMiddleware)

    @app.get("/hello")
    def hello():
        return {"msg": "ok"}

    return app

def test_logger_middleware_runs(caplog):
    app = create_app()
    client = TestClient(app)

    with caplog.at_level("INFO"):
        response = client.get("/hello")
        assert response.status_code == 200
        assert any("Incoming request" in msg for msg in caplog.messages)
        assert any("Completed response" in msg for msg in caplog.messages)
