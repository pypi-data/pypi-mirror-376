import sentry_sdk
import subprocess
import urllib.request
import shlex
import json
import typing as t
from markupsafe import Markup
from dataclasses import dataclass


SDK_OPTIONS = (
    "debug",
    "release",
    "environment",
    "sample_rate",
    "error_sampler",
    "max_breadcrumbs",
    "attach_stacktrace",
    "send_default_pii",
    "event_scrubber",
    "include_source_context",
    "include_local_variables",
    "server_name",
    "in_app_include",
    "in_app_exclude",
    "max_request_body_size",
    "max_value_length",
    "ca_certs",
    "send_client_reports",
)

FORWARD_SDK_OPTIONS_TO_BROWSER = ("release", "environment")


@dataclass
class SentryState:
    dsn: str
    sdk_options: t.Mapping[str, t.Any]
    debug_enabled: bool
    spotlight_url: t.Union[str, bool]
    spotlight_cmd: t.Union[str, t.List[str]]
    spotlight_script: str
    browser: bool
    browser_options: t.Optional[t.Mapping[str, t.Any]]
    browser_script: str
    browser_script_integrity: str
    enabled: bool


class Sentry:
    def __init__(self, app, **kwargs):
        if app:
            self.init_app(app, **kwargs)

    def init_app(
        self,
        app,
        dsn=None,
        debug_enabled=False,
        spotlight_url=True,
        detect_spotlight=True,
        spotlight_cmd="npx @spotlightjs/spotlight",
        spotlight_script="https://unpkg.com/@spotlightjs/overlay@latest/dist/sentry-spotlight.js",
        browser=True,
        browser_options=None,
        browser_tracing=True,
        browser_replay=True,
        browser_script="https://browser.sentry-cdn.com/10.11.0/bundle.tracing.min.js",
        browser_script_integrity="sha384-9NAiK1AuyTecuSh07sZ3VSsLVUCGVbYkmYBckFl45/Pc9zmEizUJZcWxqxV08oe+",
        **sdk_options,
    ):
        self.app = app

        spotlight_url = app.config.get("SPOTLIGHT_URL", spotlight_url)
        if app.debug and spotlight_url and app.config.get("SPOTLIGHT_DETECT", detect_spotlight):
            try:
                urllib.request.urlopen(
                    "http://localhost:8969" if spotlight_url is True else spotlight_url
                )
                app.logger.info("Spotlight server is detected, enalbing spotlight.")
            except urllib.error.HTTPError:
                pass
            except:
                spotlight_url = None
        elif not app.debug:
            spotlight_url = None

        for opt in SDK_OPTIONS:
            if f"SENTRY_{opt.upper()}" in self.app.config:
                sdk_options[opt] = self.app.config[f"SENTRY_{opt.upper()}"]

        browser_options = app.config.get("SENTRY_BROWSER_OPTIONS", browser_options) or {}
        for opt in FORWARD_SDK_OPTIONS_TO_BROWSER:
            if opt in sdk_options:
                browser_options.setdefault(opt, sdk_options[opt])
        if app.config.get("SENTRY_BROWSER_TRACING", browser_tracing):
            browser_options.setdefault("integrations", []).append(
                "Sentry.browserTracingIntegration()"
            )
            browser_options.setdefault(
                "tracePropagationTargets",
                ["localhost", app.config.get("SERVER_NAME") or "localhost:5000"],
            )
            if not app.debug:
                browser_options.setdefault("tracesSampleRate", 0.1)
        if app.config.get("SENTRY_BROWSER_REPLAY", browser_replay):
            browser_options.setdefault("integrations", []).append("Sentry.replayIntegration()")
            if not app.debug:
                browser_options.setdefault("replaysSessionSampleRate", 0.1)
                browser_options.setdefault("replaysOnErrorSampleRate", 1.0)

        self.state = state = SentryState(
            dsn=app.config.get("SENTRY_DSN", dsn),
            sdk_options=sdk_options,
            debug_enabled=app.config.get("SENTRY_DEBUG_ENABLED", debug_enabled),
            spotlight_url=spotlight_url,
            spotlight_cmd=app.config.get("SPOTLIGHT_CMD", spotlight_cmd),
            spotlight_script=app.config.get("SPOTLIGHT_SCRIPT", spotlight_script),
            browser=app.config.get("SENTRY_BROWSER", browser),
            browser_options=browser_options,
            browser_script=app.config.get("SENTRY_BROWSER_SCRIPT", browser_script),
            browser_script_integrity=app.config.get(
                "SENTRY_BROWSER_SCRIPT_INTEGRITY", browser_script_integrity
            ),
            enabled=False,
        )
        app.extensions["sentry"] = state

        if state.dsn and (not app.debug or state.debug_enabled):
            state.sdk_options["dsn"] = state.dsn
            state.enabled = True
        if state.spotlight_url:
            state.sdk_options.update(spotlight=spotlight_url)
            if not state.enabled:
                state.enabled = True
                state.sdk_options.update(enable_tracing=True, profiles_sample_rate=1.0)

        if state.enabled:
            sentry_sdk.init(**state.sdk_options)

        app.jinja_env.globals.update(
            init_sentry=self.init_frontend, init_spotlight=self.init_spotlight
        )

        @app.cli.command()
        def spotlight():
            """Start the Spotlight sidecar"""
            subprocess.run(
                shlex.split(state.spotlight_cmd)
                if isinstance(state.spotlight_cmd, str)
                else state.spotlight_cmd
            )

    def init_frontend(self):
        if not self.state.enabled:
            return ""

        html = ""
        if self.state.browser:
            if self.state.browser_script:
                script_attrs = {
                    "src": self.state.browser_script,
                    "integrity": self.state.browser_script_integrity,
                    "crossorigin": "anonymous",
                }
                html = "<script %s></script>\n" % " ".join(
                    f'{k}="{v}"' for k, v in script_attrs.items() if v
                )
            browser_options = dict(
                self.state.browser_options, dsn=self.state.sdk_options.get("dsn", "__DSN__")
            )
            integrations = browser_options.pop("integrations", [])
            init_options = json.dumps(browser_options)[1:-1]
            if integrations:
                init_options += ', "integrations": [%s]' % ", ".join(integrations)
            html += "<script>Sentry.init({%s});</script>\n" % init_options

        return Markup(html) + self.init_spotlight()

    def init_spotlight(self):
        if not self.state.spotlight_url or not self.state.spotlight_script:
            return ""
        return Markup(
            """
            <script>
                if (typeof window.process === 'undefined') {
                    window.process = { env: { NODE_ENV: 'development' } };
                }
            </script>
            <script type="module">
                import * as Spotlight from '%s';
                Spotlight.init();
            </script>
        """
            % self.state.spotlight_script
        )

    def __getattr__(self, name):
        return getattr(sentry_sdk, name)
