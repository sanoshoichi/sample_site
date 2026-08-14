import json
import sqlite3
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / 'schedule_data.db'

DEFAULT_STATE = {
    'candidateDates': ['2026-08-15', '2026-08-17', '2026-08-20'],
    'participantEntries': [
        { 'name': 'TESTUSER', 'slots': [] }
    ],
    'participantDraft': {}
}


def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        'CREATE TABLE IF NOT EXISTS app_state (id INTEGER PRIMARY KEY CHECK (id = 1), payload TEXT NOT NULL)'
    )
    row = conn.execute('SELECT payload FROM app_state WHERE id = 1').fetchone()
    if row is None:
        conn.execute(
            'INSERT INTO app_state (id, payload) VALUES (1, ?)',
            (json.dumps(DEFAULT_STATE, ensure_ascii=False),),
        )
    conn.commit()
    conn.close()


def read_state() -> dict:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute('SELECT payload FROM app_state WHERE id = 1').fetchone()
    conn.close()

    if row is None:
        return json.loads(json.dumps(DEFAULT_STATE, ensure_ascii=False))

    try:
        data = json.loads(row[0])
        if isinstance(data, dict) and isinstance(data.get('candidateDates'), list) and isinstance(data.get('participantEntries'), list):
            return data
    except json.JSONDecodeError:
        pass

    return json.loads(json.dumps(DEFAULT_STATE, ensure_ascii=False))


def write_state(state: dict) -> None:
    payload = json.dumps(state, ensure_ascii=False)
    conn = sqlite3.connect(DB_PATH)
    conn.execute('UPDATE app_state SET payload = ? WHERE id = 1', (payload,))
    conn.commit()
    conn.close()


class ScheduleHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/api/state':
            self.send_json(read_state())
            return

        target = parsed.path.strip('/') or 'index.html'
        file_path = ROOT / target
        if file_path.exists() and file_path.is_file():
            super().do_GET()
            return

        self.send_error(404, 'Not Found')

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != '/api/state':
            self.send_error(404, 'Not Found')
            return

        length = int(self.headers.get('Content-Length', '0'))
        raw_body = self.rfile.read(length)

        try:
            payload = json.loads(raw_body.decode('utf-8'))
        except json.JSONDecodeError:
            self.send_error(400, 'Invalid JSON payload')
            return

        if not isinstance(payload, dict):
            self.send_error(400, 'Payload must be an object')
            return

        candidate_dates = payload.get('candidateDates', [])
        participant_entries = payload.get('participantEntries', [])

        if not isinstance(candidate_dates, list) or not isinstance(participant_entries, list):
            self.send_error(400, 'candidateDates and participantEntries must be arrays')
            return

        write_state(payload)
        self.send_json({'ok': True})

    def send_json(self, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


if __name__ == '__main__':
    init_db()
    port = 8000
    server = ThreadingHTTPServer(('0.0.0.0', port), ScheduleHandler)
    print(f'Listening on http://0.0.0.0:{port}')
    server.serve_forever()
