import os
import re
from urllib.parse import urlparse, urljoin

def url(link):
    if not link.startswith(('http://', 'https://')):
        link = 'https://' + link
    return link.rstrip('/')

def ensure_directory(path):
    os.makedirs(path, exist_ok=True)

def get_local_path(base_path, url_path, base_url):
    parsed_url = urlparse(url_path)
    parsed_base = urlparse(base_url)
    
    if parsed_url.netloc != parsed_base.netloc:
        full_path = os.path.join(base_path, parsed_url.netloc, parsed_url.path.lstrip('/'))
    else:
        relative_path = url_path.replace(base_url, '').lstrip('/')
        full_path = os.path.join(base_path, relative_path)
    
    if not os.path.splitext(full_path)[1]:
        if full_path.endswith('/'):
            full_path = os.path.join(full_path, 'index.html')
        else:
            full_path += '/index.html'
    
    dir_path = os.path.dirname(full_path)
    ensure_directory(dir_path)
    
    return full_path

def search_pattern_in_file(file_path, pattern):
    results = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            matches = re.finditer(pattern, content)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                line_start = content.rfind('\n', 0, match.start()) + 1
                line_end = content.find('\n', match.start())
                if line_end == -1:
                    line_end = len(content)
                line_content = content[line_start:line_end].strip()
                
                results.append({
                    'file': file_path,
                    'line': line_num,
                    'match': match.group(),
                    'content': line_content
                })
    except:
        pass
    return results