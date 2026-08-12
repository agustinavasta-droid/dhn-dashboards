import json
from pathlib import Path

with open('pdf_data.json', encoding='utf-8') as f:
    data = json.load(f)

data_json = json.dumps(data, ensure_ascii=False)

TEMPLATE_PATH = Path(__file__).parent / "template.html"
html = TEMPLATE_PATH.read_text(encoding='utf-8')

html_out = html.replace('__DATA_JSON__', data_json)
with open('/root/proyectos/dhn/index.html','w',encoding='utf-8') as f:
    f.write(html_out)
print("bytes:", len(html_out))
