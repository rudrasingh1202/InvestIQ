import requests
import re
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    )
}

def clean_search_name(company_name: str) -> list:
    stop = {
        'limited', 'ltd', 'pvt', 'private', 'public',
        'and', 'the', 'of', 'for', 'india', 'indian',
        'company', 'co', 'corp', 'inc'
    }
    words = [
        w for w in company_name.split()
        if w.lower() not in stop and len(w) > 2
    ]
    return words[:4]


def search_chittorgarh(words: list) -> dict:
    result = {
        'price_band': None, 'open_date': None,
        'close_date': None, 'issue_size': None,
        'lot_size': None, 'listing_date': None,
        'found': False, 'source': 'chittorgarh.com'
    }
    try:
        pages = [
            "https://www.chittorgarh.com/ipo/ipo_subscription_status_live.asp",
            "https://www.chittorgarh.com/ipo/upcoming_ipo_india.asp",
            "https://www.chittorgarh.com/ipo/recent_ipo.asp",
        ]
        for page_url in pages:
            try:
                r = requests.get(
                    page_url, headers=HEADERS, timeout=8
                )
                if r.status_code != 200:
                    continue
                soup = BeautifulSoup(r.text, 'html.parser')

                # Find matching IPO link
                ipo_url = None
                for a in soup.find_all('a', href=True):
                    txt = a.get_text(strip=True).lower()
                    matches = sum(
                        1 for w in words if w.lower() in txt
                    )
                    if matches >= 1 and 'ipo' in a['href'].lower():
                        href = a['href']
                        ipo_url = (
                            href if href.startswith('http')
                            else f"https://www.chittorgarh.com{href}"
                        )
                        break

                if not ipo_url:
                    continue

                print(f"[InvestIQ] Chittorgarh IPO page: {ipo_url}")
                ir = requests.get(
                    ipo_url, headers=HEADERS, timeout=8
                )
                pt = ir.text
                soup2 = BeautifulSoup(pt, 'html.parser')
                text = soup2.get_text(separator=' ')

                # Extract price band
                pb = re.search(
                    r'[Pp]rice\s*[Bb]and\s*[:\-]?\s*'
                    r'₹?\s*([\d,]+)\s*(?:to|[-–])\s*₹?\s*([\d,]+)',
                    text
                )
                if pb:
                    result['price_band'] = (
                        f"₹{pb.group(1)} - ₹{pb.group(2)} per share"
                    )
                    result['found'] = True

                # Extract open date
                od = re.search(
                    r'(?:[Oo]pen|[Ss]tart)\s*[Dd]ate\s*[:\-]?\s*'
                    r'((?:\w+\s+)?\d{1,2}[,\s]+(?:Jan|Feb|Mar|Apr|'
                    r'May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*[,\s]+\d{4})',
                    text
                )
                if not od:
                    od = re.search(
                        r'(?:[Oo]pen|[Ss]tart)\s*[Dd]ate\s*[:\-]?\s*'
                        r'(\d{1,2}\s+\w+\s+\d{4})',
                        text
                    )
                if od:
                    result['open_date'] = od.group(1).strip()

                # Extract close date
                cd = re.search(
                    r'(?:[Cc]lose|[Ee]nd)\s*[Dd]ate\s*[:\-]?\s*'
                    r'(\d{1,2}\s+\w+\s+\d{4})',
                    text
                )
                if cd:
                    result['close_date'] = cd.group(1).strip()

                # Extract listing date
                ld = re.search(
                    r'[Ll]isting\s*[Dd]ate\s*[:\-]?\s*'
                    r'(\d{1,2}\s+\w+\s+\d{4})',
                    text
                )
                if ld:
                    result['listing_date'] = ld.group(1).strip()

                # Extract issue size
                sz = re.search(
                    r'[Ii]ssue\s*[Ss]ize\s*[:\-]?\s*'
                    r'₹?\s*([\d,\.]+)\s*(?:[Cc]r|[Cc]rore)',
                    text
                )
                if sz:
                    result['issue_size'] = (
                        f"₹{sz.group(1)} Crore"
                    )

                # Extract lot size
                ls = re.search(
                    r'[Ll]ot\s*[Ss]ize\s*[:\-]?\s*([\d,]+)\s*[Ss]hare',
                    text
                )
                if ls:
                    result['lot_size'] = ls.group(1)

                if result['found']:
                    break

            except Exception as e:
                print(f"[InvestIQ] Chittorgarh page error: {str(e)[:50]}")
                continue

    except Exception as e:
        print(f"[InvestIQ] Chittorgarh error: {str(e)[:60]}")

    return result


def search_ipowatch(words: list) -> dict:
    result = {
        'price_band': None, 'open_date': None,
        'close_date': None, 'issue_size': None,
        'lot_size': None, 'listing_date': None,
        'found': False, 'source': 'ipowatch.in'
    }
    try:
        pages = [
            "https://ipowatch.in/ipo-subscription-status/",
            "https://ipowatch.in/upcoming-ipo/",
            "https://ipowatch.in/",
        ]
        for page_url in pages:
            try:
                r = requests.get(
                    page_url, headers=HEADERS, timeout=8
                )
                if r.status_code != 200:
                    continue
                soup = BeautifulSoup(r.text, 'html.parser')

                ipo_url = None
                for a in soup.find_all('a', href=True):
                    txt = a.get_text(strip=True).lower()
                    matches = sum(
                        1 for w in words if w.lower() in txt
                    )
                    if matches >= 1:
                        href = a['href']
                        if href.startswith('http'):
                            ipo_url = href
                        elif href.startswith('/'):
                            ipo_url = f"https://ipowatch.in{href}"
                        if ipo_url:
                            break

                if not ipo_url:
                    continue

                print(f"[InvestIQ] IPOWatch page: {ipo_url}")
                ir = requests.get(
                    ipo_url, headers=HEADERS, timeout=8
                )
                text = BeautifulSoup(
                    ir.text, 'html.parser'
                ).get_text(separator=' ')

                pb = re.search(
                    r'[Pp]rice\s*[Bb]and\s*[:\-]?\s*'
                    r'₹?\s*([\d,]+)\s*(?:to|[-–])\s*₹?\s*([\d,]+)',
                    text
                )
                if pb:
                    result['price_band'] = (
                        f"₹{pb.group(1)} - ₹{pb.group(2)} per share"
                    )
                    result['found'] = True

                od = re.search(
                    r'[Oo]pen\s*[Dd]ate\s*[:\-]?\s*'
                    r'(\d{1,2}\s+\w+\s+\d{4})',
                    text
                )
                if od:
                    result['open_date'] = od.group(1).strip()

                cd = re.search(
                    r'[Cc]lose\s*[Dd]ate\s*[:\-]?\s*'
                    r'(\d{1,2}\s+\w+\s+\d{4})',
                    text
                )
                if cd:
                    result['close_date'] = cd.group(1).strip()

                ld = re.search(
                    r'[Ll]isting\s*[Dd]ate\s*[:\-]?\s*'
                    r'(\d{1,2}\s+\w+\s+\d{4})',
                    text
                )
                if ld:
                    result['listing_date'] = ld.group(1).strip()

                sz = re.search(
                    r'[Ii]ssue\s*[Ss]ize\s*[:\-]?\s*'
                    r'₹?\s*([\d,\.]+)\s*(?:[Cc]r|[Cc]rore)',
                    text
                )
                if sz:
                    result['issue_size'] = f"₹{sz.group(1)} Crore"

                ls = re.search(
                    r'[Ll]ot\s*[Ss]ize\s*[:\-]?\s*([\d,]+)',
                    text
                )
                if ls:
                    result['lot_size'] = ls.group(1)

                if result['found']:
                    break

            except Exception as e:
                print(
                    f"[InvestIQ] IPOWatch page error: {str(e)[:50]}"
                )
                continue

    except Exception as e:
        print(f"[InvestIQ] IPOWatch error: {str(e)[:60]}")

    return result


def search_investorgain(words: list) -> dict:
    result = {
        'price_band': None, 'open_date': None,
        'close_date': None, 'issue_size': None,
        'found': False, 'source': 'investorgain.com'
    }
    try:
        url = (
            "https://investorgain.com/report/"
            "live-ipo-gmp/317/ipo/"
        )
        r = requests.get(url, headers=HEADERS, timeout=8)
        if r.status_code != 200:
            return result

        soup = BeautifulSoup(r.text, 'html.parser')
        rows = soup.find_all('tr')

        for row in rows:
            cells = row.find_all('td')
            if not cells:
                continue
            txt = cells[0].get_text(strip=True).lower()
            matches = sum(1 for w in words if w.lower() in txt)
            if matches < 1:
                continue

            # Found matching row - get link
            link = row.find('a', href=True)
            if not link:
                continue
            href = link['href']
            ipo_url = (
                href if href.startswith('http')
                else f"https://investorgain.com{href}"
            )
            ir = requests.get(
                ipo_url, headers=HEADERS, timeout=8
            )
            text = BeautifulSoup(
                ir.text, 'html.parser'
            ).get_text(separator=' ')

            pb = re.search(
                r'[Pp]rice\s*[Bb]and\s*[:\-]?\s*'
                r'₹?\s*([\d,]+)\s*(?:to|[-–])\s*₹?\s*([\d,]+)',
                text
            )
            if pb:
                result['price_band'] = (
                    f"₹{pb.group(1)} - ₹{pb.group(2)} per share"
                )
                result['found'] = True

            od = re.search(
                r'[Oo]pen\s*[:\-]?\s*(\d{1,2}\s+\w+\s+\d{4})',
                text
            )
            if od:
                result['open_date'] = od.group(1).strip()

            cd = re.search(
                r'[Cc]lose\s*[:\-]?\s*(\d{1,2}\s+\w+\s+\d{4})',
                text
            )
            if cd:
                result['close_date'] = cd.group(1).strip()

            break

    except Exception as e:
        print(f"[InvestIQ] Investorgain error: {str(e)[:60]}")

    return result


def fetch_missing_ipo_data(company_name: str) -> dict:
    words = clean_search_name(company_name)
    print(f"[InvestIQ] Searching web for: {words}")

    empty = {
        'price_band': None, 'open_date': None,
        'close_date': None, 'issue_size': None,
        'lot_size': None, 'listing_date': None,
        'found': False, 'source': None
    }

    # Try all 3 sources in order
    for search_fn, name in [
        (search_chittorgarh, 'chittorgarh'),
        (search_ipowatch, 'ipowatch'),
        (search_investorgain, 'investorgain'),
    ]:
        try:
            result = search_fn(words)
            if result.get('found'):
                print(
                    f"[InvestIQ] Found data from {name}: "
                    f"price={result.get('price_band')}"
                )
                return result
        except Exception as e:
            print(f"[InvestIQ] {name} failed: {str(e)[:50]}")
            continue

    print("[InvestIQ] No web data found from any source")
    return empty


def calculate_pe_from_price(
    price_str: str, eps_str: str
) -> str:
    try:
        prices = re.findall(r'[\d,]+(?:\.\d+)?', price_str)
        eps_nums = re.findall(r'[\d.]+', eps_str)
        if not prices or not eps_nums:
            return 'N/A'
        cap = float(prices[-1].replace(',', ''))
        eps = float(eps_nums[0])
        if eps > 0 and cap > 0:
            return f"{round(cap/eps, 1):.1f}x"
    except:
        pass
    return 'N/A'


def calculate_issue_size_from_shares(
    shares_str: str, price_str: str
) -> str:
    try:
        shares = float(
            re.findall(r'[\d,]+', shares_str)[0].replace(',','')
        )
        prices = re.findall(r'[\d,]+(?:\.\d+)?', price_str)
        cap = float(prices[-1].replace(',', ''))
        crore = (shares * cap) / 1e7
        return f"₹{crore:,.2f} Crore"
    except:
        return None
