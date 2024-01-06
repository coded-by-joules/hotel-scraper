from main import main
import sys
import asyncio

if __name__ == '__main__':
    # Extract command-line arguments
    search_text = sys.argv[1]
    current_host = sys.argv[2]

    # Run the scraper asynchronously
    asyncio.run(main(search_text, current_host))
