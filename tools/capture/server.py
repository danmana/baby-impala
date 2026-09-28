"""Clip sink for the capture mode (src/dev/capture.ts).

    python3 tools/capture/server.py [port]

The page renders each shot on virtual time, encodes it to H.264 itself
(WebCodecs) and posts the Annex B stream here a few MB at a time, in order.
On /end the stream is wrapped into .work/video/clips/<name>.mp4.

  POST /start?name=&fps=   open a clip
  POST /chunk              more of the stream
  POST /end                close it and mux
"""
import os
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, '.work', 'video', 'clips')
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
clip = {}


class Sink(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _reply(self, code=200, body=b'ok'):
        self.send_response(code)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._reply(204, b'')

    def do_POST(self):
        url = urlparse(self.path)
        n = int(self.headers.get('Content-Length') or 0)
        data = self.rfile.read(n) if n else b''
        if url.path == '/start':
            q = {k: v[0] for k, v in parse_qs(url.query).items()}
            os.makedirs(OUT, exist_ok=True)
            raw = os.path.join(OUT, q['name'] + '.h264')
            clip.update(name=q['name'], fps=q.get('fps', '60'), raw=raw, file=open(raw, 'wb'), bytes=0)
            print('start', q['name'], flush=True)
            return self._reply()
        if url.path == '/chunk':
            clip['file'].write(data)
            clip['bytes'] += len(data)
            return self._reply()
        if url.path == '/end':
            clip['file'].close()
            mp4 = clip['raw'][:-5] + '.mp4'
            r = subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-r', clip['fps'], '-i', clip['raw'],
                                '-c', 'copy', mp4], capture_output=True, text=True)
            if r.returncode == 0:
                os.remove(clip['raw'])
            print('end', clip['name'], f'{clip["bytes"] / 1e6:.1f} MB ->', mp4, r.stderr.strip(), flush=True)
            return self._reply(200 if r.returncode == 0 else 500, r.stderr.encode() or b'ok')
        self._reply(404, b'?')


ThreadingHTTPServer(('127.0.0.1', PORT), Sink).serve_forever()
