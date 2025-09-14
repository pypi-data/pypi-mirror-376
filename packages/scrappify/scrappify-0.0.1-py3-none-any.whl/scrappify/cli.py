import argparse
import sys
from . import download, scrap
from .core.utils import url
from .patterns import pattern, file_type

def main():
    parser = argparse.ArgumentParser(description="Scrappify - Download websites and extract content")
    parser.add_argument('url', help='URL to process')
    parser.add_argument('-o', '--output', default='downloaded_site', help='Output directory')
    parser.add_argument('-t', '--type', help='File type to filter (e.g., js, css, pdf) or category (image, document)')
    parser.add_argument('-p', '--pattern', help='Pattern to search for (regex or predefined: email, phone, etc.)')
    parser.add_argument('-w', '--workers', type=int, default=10, help='Number of concurrent workers')
    parser.add_argument('-d', '--depth', type=int, default=1, help='Crawl depth (1 = current page only)')
    parser.add_argument('--list-patterns', action='store_true', help='List available predefined patterns')
    parser.add_argument('--list-types', action='store_true', help='List available file type categories')
    
    args = parser.parse_args()
    
    if args.list_patterns:
        print("Available predefined patterns:")
        for key in pattern.keys():
            print(f"  {key}: {pattern[key]}")
        return
    
    if args.list_types:
        print("Available file type categories:")
        for key, value in file_type.items():
            if isinstance(value, list):
                print(f"  {key}: {', '.join(value)}")
            else:
                print(f"  {key}: {value}")
        return
    
    try:
        validated_url = url(args.url)
        selected_file_type = None
        selected_pattern = None
        
        if args.type:
            if args.type in file_type:
                selected_file_type = file_type[args.type]
            else:
                selected_file_type = args.type
        
        if args.pattern:
            if args.pattern in pattern:
                selected_pattern = pattern[args.pattern]
            else:
                selected_pattern = args.pattern
        
        if selected_file_type or selected_pattern:
            result = download(
                validated_url, 
                file_type=selected_file_type, 
                pattern=selected_pattern, 
                output_dir=args.output, 
                max_workers=args.workers,
                depth=args.depth
            )
            
            if selected_pattern:
                print(f"Found {len(result)} pattern matches")
            else:
                print(f"Downloaded {len(result)} files")
        else:
            result = download(
                validated_url, 
                output_dir=args.output, 
                max_workers=args.workers,
                depth=args.depth
            )
            print(f"Downloaded {len(result)} files")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()