import os
from functools import wraps
from flask import request, abort
import google.auth.transport.requests
import google.oauth2.id_token


AUDIENCE = "https://game-descriptor-232474345248.europe-north1.run.app"
EXPECTED_EMAIL = os.environ.get("SCHEDULER_SERVICE_ACCOUNT_EMAIL")

def verify_oidc_token(f):
    """Decorator to verify GCP OIDC token from Authorization header."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            abort(403, "Missing or invalid Authorization header")

        token = auth_header.split(" ", 1)[1]
        request_adapter = google.auth.transport.requests.Request()
        try:
            id_info = google.oauth2.id_token.verify_oauth2_token(token, request_adapter, AUDIENCE)
        except Exception as e:
            abort(403, f"Invalid OIDC token: {e}")

        if id_info.get("email") != EXPECTED_EMAIL:
            abort(403, "Unauthorized service account")
        return f(*args, **kwargs)
    return decorated_function
