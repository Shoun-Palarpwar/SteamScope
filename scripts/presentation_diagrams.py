"""Create diagram coordinates and labels from the verified schema snapshot."""
import json
from pathlib import Path

folder = Path(__file__).resolve().parents[1] / 'frontend/src/presentation'
evidence = json.loads((folder / 'evidence.json').read_text())
tables = {t['name']: t for t in evidence['tables']}
refs = ['developer', 'publisher', 'genre', 'tag', 'category', 'platform', 'language']
catalog = {'game': (20, 270), 'game_screenshot': (20, 705), 'review': (430, 705)}
for i, ref in enumerate(refs):
    catalog['game_' + ref] = (430, 10 + i * 95)
    catalog[ref] = (860, 10 + i * 95)
player = {'game': (20, 65), 'user': (860, 65), 'library': (430, 10),
    'wishlist': (430, 145), 'purchase': (430, 280), 'user_activity': (430, 415),
    'achievement': (20, 450), 'user_achievement': (430, 600)}


def graph(layout, height):
    nodes = []
    for name, (x, y) in layout.items():
        table = tables[name]
        pk = [c['name'] for c in table['columns'] if c['key'] == 'PRI']
        fk = [r['child_key'] for r in evidence['foreign_keys'] if r['child'] == name]
        fields = ['PK: ' + ', '.join(pk)]
        if fk:
            fields.append('FK: ' + ', '.join(fk))
        elif any(c['name'] == 'name' for c in table['columns']):
            fields.append('name')
        if name == 'library':
            fields.append('is_favorite, added_at')
        nodes.append(dict(name=name, x=x, y=y, width=280, height=90, fields=fields, count=table['count']))
    edges = [r for r in evidence['foreign_keys'] if r['child'] in layout and r['parent'] in layout]
    return dict(width=1170, height=height, nodes=nodes, edges=edges)

graphs = dict(catalog=graph(catalog, 810), player=graph(player, 710))
names = {n['name'] for g in graphs.values() for n in g['nodes']}
edges = {e['name'] for g in graphs.values() for e in g['edges']}
assert names == set(tables), 'A table is missing from the diagrams'
assert edges == {e['name'] for e in evidence['foreign_keys']}, 'A foreign key is missing'
(folder / 'diagrams.json').write_text(json.dumps(graphs, indent=2) + '\n')
print(f'Diagrams cover all {len(names)} tables and {len(edges)} foreign keys.')
