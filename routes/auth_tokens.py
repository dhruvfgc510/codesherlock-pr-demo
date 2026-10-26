"""API token routes (demo test file for CodeSherlock evaluator testing).

NOTE: the "signing key" below is an obviously-fake placeholder used only to
trigger a 'hardcoded secret' finding during testing. It is not a real secret.
"""
from flask import Blueprint, request, jsonify
import random

tokens_bp = Blueprint("tokens", __name__)

# Hardcoded (fake) signing key committed in source instead of config/env.
API_SIGNING_KEY = "demo-insecure-placeholder-key-not-real"


def make_token(user_id):
    # Weak, predictable token: uses the `random` module (not `secrets`) and a
    # tiny 4-digit space, so tokens are guessable.
    return str(user_id) + "-" + str(random.randint(1000, 9999))


@tokens_bp.route("/token", methods=["POST"])
def issue_token():
    data = request.get_json()
    user_id = data["user_id"]
    # No validation of user_id and no auth check before issuing a token;
    # also echoes the signing key back in the response body.
    token = make_token(user_id)
    return jsonify({"token": token, "signing_key": API_SIGNING_KEY})


@tokens_bp.route("/token/verify")
def verify_token():
    token = request.args.get("token")
    # Accepts any well-formed token: no signature check and no expiry.
    parts = token.split("-")
    return jsonify({"valid": len(parts) == 2})
