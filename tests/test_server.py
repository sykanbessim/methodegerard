import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server

class GerardTests(unittest.TestCase):
    def race(self):
        return {'name': 'Test', 'horses': [{'number': '1', 'name': 'A', 'scores': {k: 10 for k, _, _ in server.CRITERIA}}]}

    def test_full_score(self):
        self.assertEqual(server.ranking(self.race())[0]['note'], 100)

    def test_missing_not_renormalized(self):
        r = self.race()
        r['horses'][0]['scores'] = {'classe': 10}
        row = server.ranking(r)[0]
        self.assertEqual((row['note'], row['coverage']), (20, 20))

    def test_custom_weights(self):
        r = self.race()
        r['weights'] = {k: 0 for k, _, _ in server.CRITERIA}
        r['weights']['classe'] = 2
        r['horses'][0]['scores']['classe'] = 7
        self.assertEqual(server.ranking(r)[0]['note'], 70)

    def test_invalid_and_duplicate(self):
        r = self.race()
        r['horses'][0]['scores']['classe'] = 11
        with self.assertRaises(ValueError): server.validate(r)
        r = self.race()
        r['horses'].append(r['horses'][0].copy())
        with self.assertRaises(ValueError): server.validate(r)

    def test_sqlite_persistence(self):
        original = server.DB
        try:
            with tempfile.TemporaryDirectory() as directory:
                server.DB = Path(directory) / 'test.sqlite3'
                with server.connect() as con: con.execute('INSERT INTO races(payload) VALUES (?)', ('{"name":"Persistée"}',))
                with server.connect() as con: self.assertIn('Persistée', con.execute('SELECT payload FROM races').fetchone()[0])
        finally: server.DB = original

    def test_horse_profile_validation_and_persistence(self):
        profile = server.validate_horse({'name': 'Sultan du Nord', 'scores': {'classe': '8.5'}, 'trainer': 'J.-M. Bazire'})
        self.assertEqual(profile['scores']['classe'], 8.5)
        with self.assertRaises(ValueError):
            server.validate_horse({'name': '', 'scores': {}})
        original = server.DB
        try:
            with tempfile.TemporaryDirectory() as directory:
                server.DB = Path(directory) / 'test.sqlite3'
                with server.connect() as con:
                    con.execute('INSERT INTO horses(name, payload) VALUES (?, ?)', ('Sultan du Nord', '{"name":"Sultan du Nord"}'))
                with server.connect() as con:
                    self.assertEqual(con.execute('SELECT name FROM horses').fetchone()[0], 'Sultan du Nord')
        finally:
            server.DB = original

    def test_jockey_profile_validation(self):
        jockey = server.validate_jockey({'name': 'M. Abrivard', 'age': '42', 'weight': '56.5', 'successRate': '18.2', 'roles': ['jockey', 'owner', 'unknown']})
        self.assertEqual(jockey['roles'], ['jockey', 'owner'])
        self.assertEqual(jockey['successRate'], 18.2)
        with self.assertRaises(ValueError):
            server.validate_jockey({'name': 'A', 'softRate': 101})

if __name__ == '__main__': unittest.main()
