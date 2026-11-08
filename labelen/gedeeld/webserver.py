"""De kleine webserver van stap 2 en stap 3: alleen bereikbaar op de eigen computer."""

import webbrowser
from http.server import ThreadingHTTPServer


def run(handler, port: int, title: str) -> None:
    """Start de webserver op het eerste vrije adres vanaf `port` en open de pagina in de browser."""
    for candidate in range(port, port + 20):
        try:
            server = ThreadingHTTPServer(("127.0.0.1", candidate), handler)
            break
        except OSError:                                       # dit adres is al in gebruik
            continue
    else:
        raise SystemExit(f"Geen vrij adres gevonden vanaf poort {port}.")
    print(f"{title}. Open http://localhost:{candidate}")
    print("Stoppen: Ctrl+C")
    webbrowser.open(f"http://localhost:{candidate}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
