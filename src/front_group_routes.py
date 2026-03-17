from flask import jsonify, request, session
import requests


def register_group_routes(app, *, port_agent: int, internal_token: str) -> None:
    """Register group-chat proxy routes for Flask frontend."""

    def _group_auth_headers():
        user_id = session.get("user_id", "")
        return {
            "Authorization": "Bearer {token}:{user}".format(token=internal_token, user=user_id),
        }

    @app.route("/proxy_groups", methods=["GET"])
    def proxy_list_groups():
        try:
            r = requests.get(
                "http://127.0.0.1:{port}/groups".format(port=port_agent),
                headers=_group_auth_headers(),
                timeout=10,
            )
            return jsonify(r.json()), r.status_code
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/proxy_groups", methods=["POST"])
    def proxy_create_group():
        try:
            headers = _group_auth_headers()
            headers["Content-Type"] = "application/json"
            r = requests.post(
                "http://127.0.0.1:{port}/groups".format(port=port_agent),
                json=request.get_json(silent=True),
                headers=headers,
                timeout=10,
            )
            return jsonify(r.json()), r.status_code
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/proxy_groups/<group_id>", methods=["GET"])
    def proxy_get_group(group_id):
        try:
            r = requests.get(
                "http://127.0.0.1:{port}/groups/{group_id}".format(port=port_agent, group_id=group_id),
                headers=_group_auth_headers(),
                timeout=10,
            )
            return jsonify(r.json()), r.status_code
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/proxy_groups/<group_id>", methods=["PUT"])
    def proxy_update_group(group_id):
        try:
            headers = _group_auth_headers()
            headers["Content-Type"] = "application/json"
            r = requests.put(
                "http://127.0.0.1:{port}/groups/{group_id}".format(port=port_agent, group_id=group_id),
                json=request.get_json(silent=True),
                headers=headers,
                timeout=10,
            )
            return jsonify(r.json()), r.status_code
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/proxy_groups/<group_id>", methods=["DELETE"])
    def proxy_delete_group(group_id):
        try:
            r = requests.delete(
                "http://127.0.0.1:{port}/groups/{group_id}".format(port=port_agent, group_id=group_id),
                headers=_group_auth_headers(),
                timeout=10,
            )
            return jsonify(r.json()), r.status_code
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/proxy_groups/<group_id>/messages", methods=["GET"])
    def proxy_group_messages(group_id):
        try:
            after_id = request.args.get("after_id", "0")
            r = requests.get(
                "http://127.0.0.1:{port}/groups/{group_id}/messages".format(
                    port=port_agent,
                    group_id=group_id,
                ),
                params={"after_id": after_id},
                headers=_group_auth_headers(),
                timeout=10,
            )
            return jsonify(r.json()), r.status_code
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/proxy_groups/<group_id>/messages", methods=["POST"])
    def proxy_post_group_message(group_id):
        try:
            headers = _group_auth_headers()
            headers["Content-Type"] = "application/json"
            r = requests.post(
                "http://127.0.0.1:{port}/groups/{group_id}/messages".format(
                    port=port_agent,
                    group_id=group_id,
                ),
                json=request.get_json(silent=True),
                headers=headers,
                timeout=10,
            )
            return jsonify(r.json()), r.status_code
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/proxy_groups/<group_id>/mute", methods=["POST"])
    def proxy_mute_group(group_id):
        try:
            r = requests.post(
                "http://127.0.0.1:{port}/groups/{group_id}/mute".format(port=port_agent, group_id=group_id),
                headers=_group_auth_headers(),
                timeout=10,
            )
            return jsonify(r.json()), r.status_code
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/proxy_groups/<group_id>/unmute", methods=["POST"])
    def proxy_unmute_group(group_id):
        try:
            r = requests.post(
                "http://127.0.0.1:{port}/groups/{group_id}/unmute".format(port=port_agent, group_id=group_id),
                headers=_group_auth_headers(),
                timeout=10,
            )
            return jsonify(r.json()), r.status_code
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/proxy_groups/<group_id>/mute_status", methods=["GET"])
    def proxy_group_mute_status(group_id):
        try:
            r = requests.get(
                "http://127.0.0.1:{port}/groups/{group_id}/mute_status".format(
                    port=port_agent,
                    group_id=group_id,
                ),
                headers=_group_auth_headers(),
                timeout=10,
            )
            return jsonify(r.json()), r.status_code
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/proxy_groups/<group_id>/sessions", methods=["GET"])
    def proxy_group_sessions(group_id):
        try:
            r = requests.get(
                "http://127.0.0.1:{port}/groups/{group_id}/sessions".format(port=port_agent, group_id=group_id),
                headers=_group_auth_headers(),
                timeout=15,
            )
            return jsonify(r.json()), r.status_code
        except Exception as e:
            return jsonify({"sessions": [], "error": str(e)}), 500
