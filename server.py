#!/usr/bin/env python3
"""Application locale Gérard — uniquement la bibliothèque standard Python."""
import json
import sqlite3
import argparse
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

ROOT = Path(__file__).resolve().parent
DB = ROOT / 'data' / 'gerard.sqlite3'
CRITERIA = [('classe', 'Classe affrontée', 20), ('forme', 'Forme récente', 15), ('vitesse', 'Vitesse comparable', 15), ('confrontations', 'Confrontations', 10), ('valeur', 'Valeur handicap', 8), ('poids', 'Poids et décharges', 7), ('corde', 'Corde', 5), ('terrain', 'Terrain', 5), ('distance', 'Distance', 5), ('parcours', 'Aptitude au parcours', 3), ('tactique', 'Profil tactique', 3), ('age_sexe', 'Âge / sexe', 2), ('entourage', 'Entourage', 2)]

def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    con.execute('CREATE TABLE IF NOT EXISTS races (id INTEGER PRIMARY KEY, payload TEXT NOT NULL, updated TEXT DEFAULT CURRENT_TIMESTAMP)')
    return con

def validate(race):
    if not isinstance(race, dict) or not str(race.get('name', '')).strip():
        raise ValueError('Le nom de la course est obligatoire.')
    weights = race.get('weights', {})
    for key, _, default in CRITERIA:
        w = weights.get(key, default)
        if isinstance(w, bool) or not isinstance(w, (int, float)) or not 0 <= w <= 100:
            raise ValueError('Les coefficients doivent être compris entre 0 et 100.')
    if sum(weights.get(k, d) for k, _, d in CRITERIA) <= 0:
        raise ValueError('Au moins un coefficient doit être positif.')
    horses = race.get('horses', [])
    if not isinstance(horses, list) or len(horses) > 100:
        raise ValueError('Maximum 100 chevaux par course.')
    numbers = set()
    for horse in horses:
        number = str(horse.get('number', '')).strip()
        if not horse.get('name', '').strip() or not number.isdigit() or int(number) < 1 or int(number) in numbers:
            raise ValueError('Chaque cheval doit avoir un nom et un numéro positif unique.')
        numbers.add(int(number))
        for key, _, _ in CRITERIA:
            v = horse.get('scores', {}).get(key)
            if v is not None and (isinstance(v, bool) or not isinstance(v, (int, float)) or not 0 <= v <= 10):
                raise ValueError('Les évaluations doivent être comprises entre 0 et 10.')
    return race

def ranking(race):
    weights = {k: race.get('weights', {}).get(k, d) for k, _, d in CRITERIA}
    total = sum(weights.values())
    results = []
    for horse in race.get('horses', []):
        scores = horse.get('scores', {})
        covered = sum(w for k, w in weights.items() if scores.get(k) is not None)
        # Les critères inconnus contribuent zéro : note minimale documentée.
        details = {k: round((scores.get(k) or 0) / 10 * w / total * 100, 2) for k, w in weights.items()}
        score = round(sum((scores.get(k) or 0) / 10 * w / total * 100 for k, w in weights.items()), 2)
        results.append(dict(horse, note=score, coverage=round(covered / total * 100), details=details))
    return sorted(results, key=lambda h: (-h['note'], int(h['number'])))

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / 'frontend'), **kwargs)

    def reply(self, value, status=200):
        body = json.dumps(value, ensure_ascii=False, allow_nan=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == '/api/config':
            return self.reply(CRITERIA)
        if self.path == '/api/races':
            with connect() as con:
                rows = con.execute('SELECT id, payload, updated FROM races ORDER BY id DESC').fetchall()
            return self.reply([dict(json.loads(p), id=i, updated=u) for i, p, u in rows])
        if self.path.startswith('/api/'):
            return self.reply({'error': 'Page inconnue'}, 404)
        super().do_GET()

    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            if not 0 < length <= 1000000:
                raise ValueError('Requête vide ou trop volumineuse.')
            race = validate(json.loads(self.rfile.read(length)))
            if self.path == '/api/rank':
                return self.reply(ranking(race))
            if self.path != '/api/races':
                return self.reply({'error': 'Page inconnue'}, 404)
            ident = race.pop('id', None)
            race.pop('updated', None)
            with connect() as con:
                payload = json.dumps(race, ensure_ascii=False, allow_nan=False)
                if ident is None:
                    ident = con.execute('INSERT INTO races(payload) VALUES (?)', (payload,)).lastrowid
                else:
                    cursor = con.execute('UPDATE races SET payload=?, updated=CURRENT_TIMESTAMP WHERE id=?', (payload, ident))
                    if not cursor.rowcount:
                        return self.reply({'error': 'Course introuvable'}, 404)
            self.reply({'id': ident})
        except (ValueError, TypeError, AttributeError) as exc:
            self.reply({'error': str(exc)}, 400)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    connect().close()
    print(f'Méthodologie Gérard : http://127.0.0.1:{args.port}', flush=True)
    ThreadingHTTPServer(('127.0.0.1', args.port), Handler).serve_forever()
