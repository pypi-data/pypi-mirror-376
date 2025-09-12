"""HTML templates for self-hosted proxy."""


def get_homepage_html(model: str, host: str, port: int) -> str:
    """Generate homepage HTML for self-hosted proxy."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenBridge</title>
    <style>
        body {{
            font-family: system-ui, sans-serif;
            max-width: 600px;
            margin: 2rem auto;
            padding: 1rem;
            line-height: 1.5;
        }}
        .status {{
            color: #059669;
            font-weight: 500;
        }}
        code {{
            background: #f5f5f5;
            padding: 0.2rem 0.4rem;
            border-radius: 3px;
            font-family: monospace;
        }}
    </style>
</head>
<body>
    <h1>OpenBridge</h1>
    <p class="status">✓ Running on {host}:{port}</p>
    
    <p><strong>Model:</strong> {model}</p>
    <p><strong>Endpoint:</strong> <code>http://{host}:{port}/v1/messages</code></p>
    
    <p>Set environment variable:</p>
    <code>ANTHROPIC_BASE_URL=http://{host}:{port}/</code>
</body>
</html>"""
