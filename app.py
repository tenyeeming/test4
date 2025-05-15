from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote, urljoin

app = Flask(__name__)

# Yahoo News Search
def search_yahoo_news(keyword, limit):
    query = quote(keyword)
    url = f'https://tw.news.yahoo.com/search?p={query}'
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')

    items = soup.find_all('li', class_='StreamMegaItem')
    result = []
    for idx, item in enumerate(items[:limit]):
        a_tag = item.find('a')
        img_tag = item.find('img')

        if a_tag and a_tag.get('href'):
            full_url = urljoin('https://tw.news.yahoo.com', a_tag['href'])
            title = a_tag.get_text(strip=True)
            img_url = img_tag['src'] if img_tag and img_tag.get('src') else ''

            result.append({
                'title': title,
                'url': full_url,
                'img_url': img_url
            })

    return result

# PTS News Search (公視)
def search_pts_news(keyword, limit):
    url = f"https://news.pts.org.tw/search/{quote(keyword)}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')

        items = soup.find_all('li', class_='row')
        result = []

        for item in items[:limit]:
            a_tag = item.find('a', href=True)
            title_tag = item.find('div', class_='title') or item.find('h2')
            img_tag = item.find('img')

            if a_tag:
                news_link = urljoin('https://news.pts.org.tw', a_tag['href'])
                title = title_tag.get_text(strip=True) if title_tag else '無標題'
                img_link = img_tag['src'] if img_tag and img_tag.get('src') else ''

                result.append({
                    'title': title,
                    'url': news_link,
                    'img_url': img_link
                })

        return result
    except Exception as e:
        print(f"PTS爬蟲錯誤: {e}")
        return []

# Liberty Times Search (自由時報)
def get_ltn_search_results(keyword, limit=5):
    base_url = "https://search.ltn.com.tw/list?keyword="
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        search_url = f"{base_url}{quote(keyword)}"
        response = requests.get(search_url, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')

        # 兩種可能的結構都嘗試抓取
        articles = soup.select('ul.list > li, div.whitecon > ul > li')[:limit]
        
        results = []
        for article in articles:
            title_tag = article.find('a', class_='tit') or article.find('h3') or article.find('a')
            img_tag = article.find('img')
            
            if title_tag:
                title = title_tag.get_text(strip=True)
                link = title_tag.get('href', '')
                
                if link and not link.startswith('http'):
                    link = urljoin('https://news.ltn.com.tw', link)
                
                img_url = ''
                if img_tag:
                    img_url = img_tag.get('data-src') or img_tag.get('src') or ''
                    if img_url and not img_url.startswith('http'):
                        img_url = urljoin('https://news.ltn.com.tw', img_url)

                results.append({
                    'title': title,
                    'url': link,
                    'img_url': img_url
                })

        return results
    except Exception as e:
        print(f"LTN爬蟲錯誤: {e}")
        return []

# TVBS News Search
def search_tvbs_news(keyword, limit):
    BASE_URL = "https://news.tvbs.com.tw"
    url = f"{BASE_URL}/news/searchresult/{quote(keyword)}/news"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8'

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            news_items = soup.find_all("li")

            results = []
            for item in news_items:
                if len(results) >= limit:
                    break

                a_tag = item.find("a", href=True)
                title_tag = item.find("h2") or item.find("h3")
                img_tag = item.find("img")

                if a_tag and title_tag:
                    title = title_tag.get_text(strip=True)
                    link = urljoin(BASE_URL, a_tag["href"])
                    img_url = ''

                    if img_tag:
                        img_url = img_tag.get("data-original") or img_tag.get("src") or ''
                        if img_url and not img_url.startswith('http'):
                            img_url = urljoin(BASE_URL, img_url)

                    results.append({
                        'title': title,
                        'url': link,
                        'img_url': img_url
                    })

            return results
        else:
            print(f"TVBS 爬蟲回傳錯誤碼: {response.status_code}")
            return []
    except Exception as e:
        print(f"TVBS爬蟲錯誤: {e}")
        return []

@app.route('/', methods=['GET', 'POST'])
def index():
    links = []
    keyword = ''
    source = 'yahoo'
    limit = 5

    if request.method == 'POST':
        keyword = request.form.get('keyword', '').strip()
        source = request.form.get('source', 'yahoo')
        limit_input = request.form.get('limit', '5')

        try:
            limit = max(1, min(20, int(limit_input)))
        except ValueError:
            limit = 5

        if keyword:
            if source == 'yahoo':
                links = search_yahoo_news(keyword, limit)
            elif source == 'pts':
                links = search_pts_news(keyword, limit)
            elif source == 'ltn':
                links = get_ltn_search_results(keyword, limit)
            elif source == 'tvbs':
                links = search_tvbs_news(   keyword, limit)

    return render_template('index.html', links=links, keyword=keyword, source=source, limit=limit)

if __name__ == '__main__':
    app.run(debug=True)