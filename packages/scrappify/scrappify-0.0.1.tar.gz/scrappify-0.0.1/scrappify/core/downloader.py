import os
import requests
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from .utils import ensure_directory, get_local_path, search_pattern_in_file

class Downloader:
    def __init__(self, output_dir="downloaded_site", max_workers=10):
        self.output_dir = output_dir
        self.max_workers = max_workers
        ensure_directory(output_dir)
    
    def download_file(self, url, base_url):
        try:
            response = requests.get(url, timeout=15, stream=True, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()
            
            file_path = get_local_path(self.output_dir, url, base_url)
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            return file_path
            
        except:
            return None
    
    def download_all(self, urls, base_url):
        downloaded_files = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_url = {executor.submit(self.download_file, url, base_url): url for url in urls}
            
            for future in as_completed(future_to_url):
                result = future.result()
                if result:
                    downloaded_files.append(result)
        
        return downloaded_files

def download(base_url, scrap_func=None, file_type=None, pattern=None, output_dir="downloaded_site", max_workers=10, depth=1):
    if scrap_func is None:
        from .scraper import scrap as scrap_func
    
    validated_url = url(base_url)
    downloader = Downloader(output_dir, max_workers)
    
    all_links = scrap_func(validated_url, depth=depth)
    
    if file_type:
        if isinstance(file_type, list):
            filtered_links = [link for link in all_links if any(link.endswith(f'.{ft}') for ft in file_type)]
        else:
            filtered_links = [link for link in all_links if link.endswith(f'.{file_type}')]
    else:
        filtered_links = all_links
    
    downloaded_files = downloader.download_all(filtered_links, validated_url)
    
    if pattern:
        pattern_results = []
        for file_path in downloaded_files:
            results = search_pattern_in_file(file_path, pattern)
            pattern_results.extend(results)
        
        for result in pattern_results:
            print(f"Found in {result['file']} at line {result['line']}:")
            print(f"  Match: {result['match']}")
            print(f"  Content: {result['content']}")
            print("-" * 50)
        
        return pattern_results
    
    return downloaded_files