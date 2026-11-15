"""Publish component usage without modifying the electronics repository."""
import json
from html import escape
from urllib.parse import quote
from project_config import ROOT, COMPONENT_PARTS, PROJECT_PARTS, COMPONENT_URL, PROJECT_URL

def generate_usage():
    from kicad_agents.project_usage_action import build_usage_index
    index,unavailable=build_usage_index(PROJECT_PARTS)
    target=ROOT/'usage'
    target.mkdir(exist_ok=True)
    previous=target/'index.json'
    if previous.is_file():
        saved=json.loads(previous.read_text(encoding='utf-8'))
        for identifier,rows in saved.get('usage',{}).items():
            for row in rows:
                if row['project_id'] in unavailable:
                    row=dict(row,extraction_available=False)
                    index.setdefault(identifier,[]).append(row)
    # A single landing page supports every ID, including future components.
    payload={'schema_version':1,'usage':index,'unavailable_projects':unavailable}
    (target/'index.json').write_text(json.dumps(payload,indent=2),encoding='utf-8')
    safe=json.dumps(payload).replace('<','\\u003c')
    page='''<!doctype html><meta charset="utf-8"><title>OOMP component project usage</title>
<h1>Used in projects</h1><p><a href="PROJECT_NAVIGATION">Project catalogue</a></p>
<p id="component"></p><p id="coverage"></p><ul id="projects"></ul>
<script>const data=PAYLOAD; const id=decodeURIComponent(location.hash.slice(1));
document.getElementById('component').textContent=id || 'Choose a component from the electronics catalogue.';
const rows=data.usage[id]||[];
document.getElementById('coverage').textContent=(rows.length?'':'No confirmed usage recorded. ')+
(data.unavailable_projects.length?'Coverage is incomplete: '+data.unavailable_projects.length+' projects have no extracted data.':'');
for(const row of rows){const li=document.createElement('li'),a=document.createElement('a');
a.href=row.oomp_url; a.textContent=row.name+' ('+row.quantity+')'+(row.extraction_available===false?' — previous extraction; current data unavailable':'');li.append(a);document.getElementById('projects').append(li);}
</script>'''.replace('PAYLOAD',safe).replace('PROJECT_NAVIGATION',escape(PROJECT_URL+'/tree/main/navigation',quote=True))
    (target/'index.html').write_text(page,encoding='utf-8')
    print('Usage index:',len(index),'components;',len(unavailable),'unavailable projects')
    return payload

if __name__=='__main__': generate_usage()
