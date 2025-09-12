"""
Command Line Interface for YouTube Thumbnail Extractor
"""
import argparse
import sys
from typing import List
from .extract_thumbnails import YouTubeThumbnailExtractor


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="YouTube Thumbnail Extractor - Extract thumbnail URLs from YouTube videos"
    )
    parser.add_argument(
        '--url-file', 
        nargs='+', 
        help='File containing YouTube video URLs (one per line)'
    )
    parser.add_argument(
        '--urls',
        nargs='+',
        help='YouTube video URLs to extract thumbnails from'
    )
    parser.add_argument(
        '--quality', 
        choices=['maxresdefault', 'sddefault', 'hqdefault', 'mqdefault', 'default'], 
        default='hqdefault', 
        help='Preferred thumbnail quality (default: hqdefault)'
    )
    parser.add_argument(
        '--verify', 
        action='store_true', 
        help='Verify if the thumbnail URL exists'
    )
    parser.add_argument(
        '--output-format',
        choices=['url', 'json', 'table'],
        default='url',
        help='Output format (default: url)'
    )

    args = parser.parse_args()

    # Collect URLs
    urls: List[str] = []
    
    if args.url_file:
        for file_path in args.url_file:
            try:
                with open(file_path, 'r') as f:
                    file_urls = [line.strip() for line in f if line.strip()]
                    urls.extend(file_urls)
            except FileNotFoundError:
                print(f"Error: File '{file_path}' not found.", file=sys.stderr)
                sys.exit(1)
            except Exception as e:
                print(f"Error reading file '{file_path}': {e}", file=sys.stderr)
                sys.exit(1)
    
    if args.urls:
        urls.extend(args.urls)
    
    if not urls:
        print("Error: No URLs provided. Use --url-file or --urls", file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    # Extract thumbnails
    extractor = YouTubeThumbnailExtractor()
    
    print(f"Extracting thumbnails with quality '{args.quality}' and verify existence set to {args.verify}\n")
    
    thumbnails = extractor.extract_thumbnails(
        urls, 
        quality=args.quality, 
        verify_existence=args.verify
    )

    if not thumbnails:
        print("No valid thumbnails found.", file=sys.stderr)
        sys.exit(1)

    # Output results
    if args.output_format == 'url':
        for thumbnail in thumbnails:
            print(thumbnail.url)
    elif args.output_format == 'json':
        import json
        output = []
        for thumbnail in thumbnails:
            output.append({
                'video_id': thumbnail.video_id,
                'url': thumbnail.url,
                'maxresdefault': thumbnail.maxresdefault,
                'sddefault': thumbnail.sddefault,
                'hqdefault': thumbnail.hqdefault,
                'mqdefault': thumbnail.mqdefault,
                'default': thumbnail.default
            })
        print(json.dumps(output, indent=2))
    elif args.output_format == 'table':
        print(f"{'Video ID':<15} {'Quality':<15} {'URL'}")
        print("-" * 80)
        for thumbnail in thumbnails:
            print(f"{thumbnail.video_id:<15} {args.quality:<15} {thumbnail.url}")

    print(f"\nFound {len(thumbnails)} valid thumbnails out of {len(urls)} URLs.")


if __name__ == '__main__':
    main()
