from flask import Flask, render_template
import requests 
from bs4 import BeautifulSoup
import sqlite3
import json
from urllib.parse import urljoin
from flask import send_from_directory
import os

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
# Initialize database
def init_db():
    with sqlite3.connect('articles.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS articles(
            headline TEXT,
            link TEXT UNIQUE,
            published_date TEXT,
            article_text TEXT
        )
        ''')
        conn.commit()

def scrape_articles():
    url = 'https://timesofindia.indiatimes.com/topic/medical/news'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = []
        
        for article in soup.find_all('div', class_='uwU81'):
            relative_link = article.find("a")["href"]
            link = urljoin('https://timesofindia.indiatimes.com', relative_link)
            headline = article.find('div', class_='fHv_i o58kM').get_text(strip=True)
            published_date = article.find('div', class_='ZxBIG').get_text(strip=True)
            articles.append({
                "headline": headline,
                "link": link,
                "published_date": published_date
            })
        
        return articles
    except Exception as e:
        print(f"Error scraping articles: {e}")
        return []

def get_article_text(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        content = soup.find("div", class_="_s30J clearfix")
        return content.get_text(separator="\n").strip() if content else None
    except Exception as e:
        print(f"Error fetching article text from {url}: {e}")
        return None

def process_articles(articles):
    processed = []
    for article in articles:
        try:
            article_text = get_article_text(article['link'])
            if article_text:
                article['article_text'] = article_text
                processed.append(article)
        except Exception as e:
            print(f"Error processing {article['link']}: {e}")
    return processed

def save_articles_to_db(articles):
    with sqlite3.connect('articles.db') as conn:
        cursor = conn.cursor()
        for article in articles:
            cursor.execute('SELECT 1 FROM articles WHERE headline = ?', (article['headline'],))
            exists = cursor.fetchone()

            if not exists:
                try:
                    cursor.execute('''
                    INSERT OR IGNORE INTO articles(headline, link, published_date, article_text)
                    VALUES(?,?,?,?)
                    ''', (
                        article['headline'],
                        article['link'],
                        article['published_date'],
                        article['article_text']
                    ))
                except sqlite3.Error as e:
                    print(f"Error saving article to DB: {e}")
        conn.commit()

def export_articles_to_json():
    try:
        with sqlite3.connect('articles.db') as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM articles ORDER BY published_date DESC')
            articles = cursor.fetchall()
        
        with open('static/articles.json', 'w', encoding='utf-8') as f:
            json.dump([dict(article) for article in articles], f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error exporting articles to JSON: {e}")

init_db()
@app.route("/")
def extract_update_db():
    try:
        news_headlines = scrape_articles()
        processed_articles = process_articles(news_headlines)
        save_articles_to_db(processed_articles)
        export_articles_to_json()
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Medical News Updater</title>
            <link rel="stylesheet" href="/static/css/style.css">
        </head>
        <body>
            <div class="container">
                <h1>Medical News Update Complete</h1>
                <p>Articles have been successfully scraped and updated.</p>
                <a href="/news" class="news-button">View Medical News</a>
            </div>
        </body>
        </html>
        '''
    except Exception as e:
        return f"An error occurred: {str(e)}", 500
    
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route("/news")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)