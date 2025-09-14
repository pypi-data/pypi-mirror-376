import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from .utils import url

def scrap(base_url, same_domain_only=True, depth=1, current_depth=0, visited=None):
    if visited is None:
        visited = set()
    
    validated_url = url(base_url)
    
    if validated_url in visited or current_depth >= depth:
        return []
    
    visited.add(validated_url)
    
    try:
        response = requests.get(validated_url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        links = set()
        
        tags = soup.find_all(['a', 'link', 'script', 'img', 'source', 'audio', 'video', 'embed', 'iframe'])
        
        for tag in tags:
            link = None
            if tag.has_attr('href'):
                link = tag['href']
            elif tag.has_attr('src'):
                link = tag['src']
            elif tag.has_attr('data-src'):
                link = tag['data-src']
            
            if link:
                absolute_link = urljoin(validated_url, link)
                
                if not same_domain_only or absolute_link.startswith(validated_url):
                    links.add(absolute_link)
        
        all_links = list(links)
        
        if depth > 1 and current_depth < depth - 1:
            for link in list(links):
                if link.startswith(validated_url) and not link.endswith(('.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.pdf')):
                    try:
                        sub_links = scrap(link, same_domain_only, depth, current_depth + 1, visited)
                        all_links.extend(sub_links)
                    except:
                        continue
        
        return list(set(all_links))
        
    except:
        return []