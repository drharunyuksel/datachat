"""
HTML templates for Vanna Agents servers.
"""

from typing import Optional


def get_vanna_component_script(
    dev_mode: bool = False,
    static_path: str = "/static",
    cdn_url: str = "https://img.vanna.ai/vanna-components.js",
) -> str:
    """Get the script tag for loading Vanna web components.

    Args:
        dev_mode: If True, load from local static files
        static_path: Path to static assets in dev mode
        cdn_url: CDN URL for production

    Returns:
        HTML script tag for loading components
    """
    if dev_mode:
        return (
            f'<script type="module" src="{static_path}/vanna-components.js"></script>'
        )
    else:
        return f'<script type="module" src="{cdn_url}"></script>'


def get_index_html(
    dev_mode: bool = False,
    static_path: str = "/static",
    cdn_url: str = "https://img.vanna.ai/vanna-components.js",
    api_base_url: str = "",
) -> str:
    """Generate index HTML with configurable component loading.

    Args:
        dev_mode: If True, load components from local static files
        static_path: Path to static assets in dev mode
        cdn_url: CDN URL for production components
        api_base_url: Base URL for API endpoints

    Returns:
        Complete HTML page as string
    """
    component_script = get_vanna_component_script(dev_mode, static_path, cdn_url)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DataChat</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        html, body {{ height: 100%; overflow: hidden; }}
        body {{ background: #f5f5f5; }}
        vanna-chat {{ display: block; width: 100%; height: 100vh; }}
    </style>
    {component_script}
</head>
<body>
    <vanna-chat
        api-base="{api_base_url}"
        sse-endpoint="{api_base_url}/api/vanna/v2/chat_sse"
        ws-endpoint="{api_base_url}/api/vanna/v2/chat_websocket"
        poll-endpoint="{api_base_url}/api/vanna/v2/chat_poll">
    </vanna-chat>
</body>
</html>"""


# Backward compatibility - default production HTML
INDEX_HTML = get_index_html()
