import re

css_file = r'c:\Users\mende\OneDrive\Desktop\ADS\Faro-del-viajero\apps\gestion_viajes\static\gestion_viajes\css\detalle_viaje.css'
html_file = r'c:\Users\mende\OneDrive\Desktop\ADS\Faro-del-viajero\apps\gestion_viajes\templates\gestion_viajes\detalle_viaje.html'

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Font Family
    content = re.sub(r"font-family:\s*'[^']+',\s*sans-serif;?", r'font-family: var(--font-family-base);', content)

    # Font Weight
    content = re.sub(r'font-weight:\s*700;?', r'font-weight: var(--font-weight-bold);', content)
    content = re.sub(r'font-weight:\s*600;?', r'font-weight: var(--font-weight-semibold);', content)
    content = re.sub(r'font-weight:\s*400;?', r'font-weight: var(--font-weight-regular);', content)
    content = re.sub(r'font-weight:\s*bold;?', r'font-weight: var(--font-weight-bold);', content)

    # Font Size Mappings
    content = re.sub(r'font-size:\s*1\.1rem;?', r'font-size: var(--font-size-h2);', content)
    content = re.sub(r'font-size:\s*1rem;?', r'font-size: var(--font-size-body);', content)
    content = re.sub(r'font-size:\s*0\.92rem;?', r'font-size: var(--font-size-h3);', content)
    content = re.sub(r'font-size:\s*0\.875rem;?', r'font-size: var(--font-size-body);', content)
    content = re.sub(r'font-size:\s*0\.[0-8][0-9]*rem;?', r'font-size: var(--font-size-small);', content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

process_file(css_file)
process_file(html_file)
print('Done!')
