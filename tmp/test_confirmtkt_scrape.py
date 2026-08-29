import requests
import re
import json

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}

urls = [
    "https://www.confirmtkt.com/train-running-status/12302",
    "https://www.confirmtkt.com/train-running-status/12951",
    "https://www.confirmtkt.com/train-running-status/12626",
    "https://www.railyatri.in/live-train-status/12302",
    "https://www.trainman.in/train/12302"
]

for url in urls:
    try:
        r = requests.get(url, headers=headers, timeout=6)
        print(f"URL: {url} | Status: {r.status_code}")
        if r.status_code == 200:
            # Look for JSON scripts in HTML
            matches = re.findall(r'data\s*=\s*(\{.*?\});', r.text, re.DOTALL)
            if not matches:
                matches = re.findall(r'__INITIAL_STATE__\s*=\s*(\{.*?\});', r.text, re.DOTALL)
            if not matches:
                matches = re.findall(r'window\.data\s*=\s*(\{.*?\});', r.text, re.DOTALL)
            
            print(f"  Found script matches: {len(matches)}")
            if matches:
                print("  Match snippet:", matches[0][:300])
            else:
                print("  Snippet of HTML:", r.text[:500])
            print("="*60)
    except Exception as e:
        print(f"Error {url}: {e}")
