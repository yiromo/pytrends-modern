"""
Proxy extension generator for Chrome/Chromium with automatic authentication
Creates a simple extension that handles proxy auth without any UI
"""

import os
import tempfile
import json


def create_proxy_extension(username: str, password: str, host: str, port: int) -> str:
    """
    Create a Chrome extension that automatically handles proxy authentication
    No UI, no dialogs - completely automatic
    
    Args:
        username: Proxy username
        password: Proxy password
        host: Proxy host/IP
        port: Proxy port
    
    Returns:
        Path to the extension folder (DrissionPage needs folder not ZIP)
    """
    
    # Create temp directory for extension
    extension_dir = tempfile.mkdtemp(prefix='proxy_auth_')
    
    # Manifest v3 - simple and clean
    manifest = {
        "manifest_version": 3,
        "name": "Auto Proxy Auth",
        "version": "1.0",
        "description": "Automatic proxy authentication",
        "permissions": [
            "webRequest",
            "webRequestAuthProvider"
        ],
        "host_permissions": [
            "<all_urls>"
        ],
        "background": {
            "service_worker": "background.js"
        }
    }
    
    # Background script - handles auth automatically
    background_js = f"""
// Automatic proxy authentication - no UI
chrome.webRequest.onAuthRequired.addListener(
    function(details) {{
        console.log('[Proxy Auth] Providing credentials for:', details.url);
        return {{
            authCredentials: {{
                username: "{username}",
                password: "{password}"
            }}
        }};
    }},
    {{urls: ["<all_urls>"]}},
    ["blocking"]
);

console.log('[Proxy Auth] Extension loaded - auth will be automatic');
"""
    
    # Write manifest
    with open(os.path.join(extension_dir, 'manifest.json'), 'w') as f:
        json.dump(manifest, f, indent=2)
    
    # Write background script
    with open(os.path.join(extension_dir, 'background.js'), 'w') as f:
        f.write(background_js)
    
    print(f"[Proxy Extension] Created at: {extension_dir}")
    print(f"[Proxy Extension] Username: {username}, Host: {host}:{port}")
    
    return extension_dir
