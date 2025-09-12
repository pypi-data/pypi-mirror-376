from fastapi import FastAPI
from fastapi.testclient import TestClient
from easy_middleware import SecurityHeadersMiddleware

def create_app():
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/")
    def hello():
        return {"msg": "ok"}

    return app

def test_security_headers_present():
    app = create_app()
    client = TestClient(app)

    response = client.get("/")
    assert response.status_code == 200

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "max-age" in response.headers["Strict-Transport-Security"]
    assert "default-src" in response.headers["Content-Security-Policy"]
