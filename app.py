import logging
from datetime import datetime

from flask import Flask, render_template

from config import load_config
from dashboard.view import build_dashboard_model
from homeassistant.client import HassClient

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s")

app = Flask(__name__)
CONFIG = load_config()
_client = HassClient(CONFIG)


@app.route("/")
def home():
    """
    Renders the dashboard or an offline page.

    Returns:
      str: The rendered HTML page.
    """
    if not _client.is_reachable():
        return render_template(
            "offline.html",
            refresh=CONFIG.page_refresh_interval_seconds,
            time=datetime.now().strftime("%H:%M"),
        )

    return render_template(
        "dashboard.html",
        **build_dashboard_model(_client, CONFIG, datetime.now()),
    )


@app.route("/health")
def health():
    """
    Liveness probe for the dashboard server itself.

    Independent of Home Assistant, so a transient HA outage does not fail
    container or load-balancer health checks.

    Returns:
      tuple: A small JSON body and HTTP 200.
    """
    return {"status": "ok"}, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=CONFIG.server_port, debug=True)
