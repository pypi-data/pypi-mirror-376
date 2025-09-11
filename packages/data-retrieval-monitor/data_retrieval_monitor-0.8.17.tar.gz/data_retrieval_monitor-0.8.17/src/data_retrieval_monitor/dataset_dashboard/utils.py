from datetime import datetime, timezone
import pytz

def px(n: int) -> str:
    return f"{int(n)}px"

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def to_local_str(iso_str: str | None, tz_name: str) -> str:
    if not iso_str:
        return "-"
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        if not dt.tzinfo:
            from datetime import timezone as tz
            dt = dt.replace(tzinfo=tz.utc)
        return dt.astimezone(pytz.timezone(tz_name)).strftime("%Y-%m-%d %H:%M:%S %Z")
    except Exception:
        return str(iso_str)
 

# dataset_dashboard/constants.py
from typing import Tuple, Dict

# exact order (worst → best). keep 'other' at the end.
JOB_STATUS_ORDER = [
    "failed", "overdue", "manual", "retrying", "running",
    "allocated", "queued", "waiting", "succeeded", "other"
]

JOB_COLORS: Dict[str, str] = {
    "waiting":   "#F0E442",
    "retrying":  "#E69F00",
    "running":   "#56B4E9",
    "failed":    "#D55E00",
    "overdue":   "#A50E0E",
    "manual":    "#808080",
    "allocated": "#7759C2",
    "queued":    "#6C757D",
    "succeeded": "#009E73",
    "other":     "#999999",
}

JOB_SCORES: Dict[str, float] = {
    "failed": -1.0, "overdue": -0.8, "retrying": -0.3, "running": 0.5,
    "allocated": 0.2, "queued": 0.1, "waiting": 0.0, "manual": 0.2,
    "succeeded": 1.0, "other": 0.0,
}

def _hex_to_rgb(h: str) -> Tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

JOB_RGB = {k: _hex_to_rgb(v) for k, v in JOB_COLORS.items()}

# --- NEW: light-touch canonicalization map (all keys *lowercase*) ---
# We only map common variants; anything else falls back to 'other' safely.
STATUS_CANON: Dict[str, str] = {
    # success
    "success": "succeeded", "succeed": "succeeded", "ok": "succeeded", "done": "succeeded",
    # failure
    "fail": "failed", "error": "failed", "failed_job": "failed",
    # overdue / timeout
    "timeout": "overdue", "time_out": "overdue", "over_due": "overdue",
    # retrying
    "retry": "retrying", "retried": "retrying",
    # running
    "in_progress": "running", "processing": "running",
    # waiting / pending
    "pend": "waiting", "pending": "waiting",
    # queued / allocated
    "queue": "queued", "queued_up": "queued",
    "alloc": "allocated", "allocated_job": "allocated",
    # manual / paused
    "pause": "manual", "paused": "manual",
    # empty/unknown → handled in store as 'other'
}

import os
import pathlib
from dataclasses import dataclass, replace

# Safe default host/port if envs or constants are missing
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8090

# If you keep a PORT in constants, we’ll use it as a fallback default.
try:
    from .constants import PORT as CONST_PORT  # optional
except Exception:
    CONST_PORT = DEFAULT_PORT


def _get_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return str(v).strip().lower() in ("1", "true", "yes", "on")


def _get_int(name: str, default: int) -> int:
    v = os.getenv(name)
    if v is None:
        return default
    try:
        return int(v)
    except Exception:
        return default


@dataclass(frozen=True)
class AppConfig:
    # App
    app_title: str
    timezone: str
    refresh_ms: int

    # Server
    host: str
    port: int
    debug: bool
    use_reloader: bool

    # Data & store
    store_backend: str
    store_path: str
    default_owner: str
    default_mode: str
    log_root: pathlib.Path

    # UI caps
    max_left_width: int
    max_graph_width: int
    max_kpi_width: int

    # Injector
    ingest_enabled: bool
    ingest_period_sec: int  # clamped elsewhere by InjectorService

    # Clipboard behavior
    clipboard_fallback_open: bool

    # Environment label (shown in banner/status line)
    environment_label: str


def load_config(cli: dict | None = None) -> AppConfig:
    """
    Builds AppConfig from environment variables, then applies CLI overrides (if provided).
    `cli` is typically vars(argparse_namespace).
    """
    period = _get_int("INGEST_PERIOD_SEC", 300)
    if period < 5:
        period = 5
    if period > 300:
        period = 300

    cfg = AppConfig(
        app_title=os.getenv("APP_TITLE", "Data Retrieval Monitor"),
        timezone=os.getenv("APP_TIMEZONE", "Europe/London"),
        refresh_ms=_get_int("REFRESH_MS", 1000),

        host=os.getenv("HOST", os.getenv("APP_HOST", DEFAULT_HOST)),
        port=_get_int("PORT", _get_int("APP_PORT", CONST_PORT)),
        debug=_get_bool("DEBUG", False),
        use_reloader=_get_bool("USE_RELOADER", True),

        store_backend=os.getenv("STORE_BACKEND", "memory"),
        store_path=os.getenv("STORE_PATH", "status_store.json"),
        default_owner=os.getenv("DEFAULT_OWNER", "QSG"),
        default_mode=os.getenv("DEFAULT_MODE", "live"),
        log_root=pathlib.Path(os.getenv("LOG_ROOT", "/tmp/drm-logs")).resolve(),

        max_left_width=_get_int("MAX_LEFT_WIDTH", 360),
        max_graph_width=_get_int("MAX_GRAPH_WIDTH", 420),
        max_kpi_width=_get_int("MAX_KPI_WIDTH", 220),

        ingest_enabled=_get_bool("INGEST_ENABLED", True),
        ingest_period_sec=period,

        clipboard_fallback_open=_get_bool("CLIPBOARD_FALLBACK_OPEN", False),
        environment_label=os.getenv("APP_ENV", os.getenv("ENVIRONMENT", "demo")),
    )

    # Apply CLI overrides (if provided)
    if cli:
        # Normalize owner → lower for key storage, you can still show label cased in UI.
        if cli.get("owner"):
            cfg = replace(cfg, default_owner=str(cli["owner"]))
        if cli.get("host"):
            cfg = replace(cfg, host=str(cli["host"]))
        if cli.get("port") is not None:
            cfg = replace(cfg, port=int(cli["port"]))
        if cli.get("debug") is not None:
            cfg = replace(cfg, debug=bool(cli["debug"]))
        if cli.get("no_reloader"):
            cfg = replace(cfg, use_reloader=False)

    return cfg


from __future__ import annotations

import argparse
from dash import Dash
import dash_bootstrap_components as dbc

from .config import load_config
from .dashboard import DashboardHost
from .inject import register_ingest_routes, register_callbacks


def create_app(cfg=None):
    """
    Factory that builds the Dash app + Flask server with the given config.
    """
    cfg = cfg or load_config()
    app = Dash(
        __name__,
        external_stylesheets=[dbc.themes.FLATLY],
        title=cfg.app_title,
        suppress_callback_exceptions=False,
    )

    # Host wires services + components and builds layout
    host = DashboardHost(app, cfg, make_items_callable=None)  # your injector may set a callable elsewhere
    app.layout = host.layout

    # Routes + callbacks
    register_ingest_routes(app.server, host)
    register_callbacks(app, cfg, host)

    # Start background services (injector etc.)
    host.start_services()

    return app, app.server


def _parse_args():
    p = argparse.ArgumentParser(description="Dataset Dashboard server")
    p.add_argument("--host", default=None, help="Host interface to bind (e.g., 0.0.0.0)")
    p.add_argument("--port", type=int, default=None, help="Port to bind")
    p.add_argument("--owner", default=None, help="Default owner key/label (e.g., qsg)")
    p.add_argument("--debug", action="store_true", help="Enable Flask/Dash debug")
    p.add_argument("--no-reloader", action="store_true", help="Disable autoreloader")
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    cfg = load_config(cli=vars(args))
    app, server = create_app(cfg)

    # Helpful banner in console
    print(
        f"[dashboard] {cfg.app_title} — http://{cfg.host}:{cfg.port} "
        f"(owner={cfg.default_owner}, mode={cfg.default_mode}, env={cfg.environment_label}, "
        f"debug={cfg.debug}, reloader={cfg.use_reloader})"
    )

    # Note: Dash reloader can start twice; if you use a background injector,
    #       consider running with --no-reloader in development.
    app.run(host=cfg.host, port=cfg.port, debug=cfg.debug, use_reloader=cfg.use_reloader)