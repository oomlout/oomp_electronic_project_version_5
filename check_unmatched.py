"""Summarize saved unmatched components in this project checkout."""
import yaml
from project_config import PROJECT_PARTS

totals=[]
for path in PROJECT_PARTS.glob('oomp_project_*/data/generated_data/unmatched_parts.yaml'):
    with path.open(encoding='utf-8') as source:
        data=yaml.safe_load(source) or {}
    totals.append((path.parents[2].name,len(data.get('components',[]))))
for identifier,count in sorted(totals,key=lambda item:(-item[1],item[0]))[:20]:
    print(f'{count:4d}  {identifier}')
print('Projects with unmatched:',sum(count>0 for _,count in totals))
print('Unmatched components:',sum(count for _,count in totals))
