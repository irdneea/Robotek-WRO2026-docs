#!/usr/bin/env python3
"""Serve the repository for tools/assembly/render.html and save the PNGs it posts.

    python3 tools/assembly/save_server.py --out ~/Projects/Portfolio-Astro/public/learn/assembly --port 8766

Then open http://localhost:8766/tools/assembly/render.html: it renders every view and POSTs it to
/save?name=<file>.png; the files land in --out. Only names made of letters, digits, - and _ are
accepted.
"""
import argparse
import functools
import http.server
from pathlib import Path
import re
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[2]


class Handler(http.server.SimpleHTTPRequestHandler):
    out = None

    def do_POST(self):
        query = parse_qs(urlparse(self.path).query)
        name = (query.get('name') or [''])[0]
        if not re.fullmatch(r'[A-Za-z0-9_-]+\.png', name):
            self.send_error(400, 'bad name')
            return
        data = self.rfile.read(int(self.headers['Content-Length']))
        (self.out / name).write_bytes(data)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'ok')
        print('saved', name, len(data), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--port', type=int, default=8766)
    args = parser.parse_args()
    args.out = args.out.expanduser()
    args.out.mkdir(parents=True, exist_ok=True)
    Handler.out = args.out
    handler = functools.partial(Handler, directory=str(ROOT))
    http.server.ThreadingHTTPServer(('127.0.0.1', args.port), handler).serve_forever()


if __name__ == '__main__':
    main()
