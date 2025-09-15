# Flask-Sentry

[Sentry](https://sentry.io/) and [Spotlight](https://spotlightjs.com/) integration for Flask.

 - Configure and initialize Sentry SDK for Flask and the browser
 - Spotlight integration
 - Properly handle debug mode

## Installation

    pip install flask-sentry

## Usage

```python
from flask import app
from flask_sentry import Sentry

app = Flask(__name__)
Sentry(app, dsn="http://DSN")
```

Use `init_sentry()` in your template:

```jinja
<!DOCTYPE html>
<html>
    <head>
        {{ init_sentry() }}
    </head>
</html>
```

## Using spotlight

Install spotlight:

    npm install @spotlightjs/spotlight

Run spotlight before starting your app:

    flask spotlight

Include the spotlight init script in your template, either using `init_sentry()` or only spotlight using `init_spotlight()`.

```jinja
<!DOCTYPE html>
<html>
    <head>
        {{ init_spotlight() }}
    </head>
</html>
```

Will only render something if spotlight is enabled.

Spotlight is automatically enabled in debug mode when a spotlight server is detected. Otherwise, spotlight is disabled.

## Configuration

| Config key | Extension argument | Description | Default |
| --- | --- | --- | --- |
| SENTRY_DSN | dsn | Sentry DSN | |
| SENTRY_* | **kwargs | Any options available in the sentry_sdk.init() function | |
| SENTRY_DEBUG_ENABLED | debug_enabled | Whether to enable sending to the dsn in debug | False |
| SPOTLIGHT_URL | spotlight_url | True or a spotlight url to enable spotlight | True |
| SPOTLIGHT_DETECT | detect_spotlight | Whether to detect if the spotlight sidecar is running before enabling spotlight | True |
| SPOTLIGHT_CMD | spotlight_cmd | The spotlight cmd to launch the sidecar | npx @spotlightjs/spotlight |
| SPOTLIGHT_SCRIPT | spotlight_script | The spotlight script in the browser | Currently recommended url |
| SENTRY_BROWSER | browser | Whether to enable sentry sdk in the browser | True |
| SENTRY_BROWSER_OPTIONS | browser_options | Options for the browser sdk | {} |
| SENTRY_BROWSER_TRACING | browser_tracing | Whether to enable tracing in the browser | True |
| SENTRY_BROWSER_REPLAY | browser_replay | Whether to enable session replay in the browser | True |
| SENTRY_BROWSER_SCRIPT | browser_script | Sentry sdk script url (do not load script if None) | Currently recommended url |
| SENTRY_BROWSER_SCRIPT_INTEGRITY | browser_script_integrity | Integrity hash for the sdk script | Hash for currently recommended url |