from flask import Flask, render_template, request
import sqlite3
import feedparser
import random
import threading
import time

app = Flask(__name__)

DB_PATH = 'database.db'

RSS_FEEDS = {
    'technology': 'http://feeds.bbci.co.uk/news/technology/rss.xml',
    'sports': 'http://feeds.bbci.co.uk/sport/rss.xml',
    'world': 'http://feeds.bbci.co.uk/news/world/rss.xml'
}

# --- Funzioni Utility ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    summary TEXT,
                    link TEXT,
                    image_url TEXT,
                    category TEXT,
                    published TEXT
                )''')
    conn.commit()
    conn.close()

def simple_rewrite(text):
    return text.replace('BBC', 'NewsBot')

def fetch_and_store_articles():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    for category, url in RSS_FEEDS.items():
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]:
            title = simple_rewrite(entry.title)
            summary = simple_rewrite(entry.summary)
            link = entry.link
            image_url = f"https://picsum.photos/seed/{random.randint(1,1000)}/600/400"
            published = entry.published

            c.execute("SELECT COUNT(*) FROM articles WHERE link=?", (link,))
            if c.fetchone()[0] == 0:
                c.execute("INSERT INTO articles (title, summary, link, image_url, category, published) VALUES (?, ?, ?, ?, ?, ?)",
                          (title, summary, link, image_url, category, published))
    conn.commit()
    conn.close()

def schedule_fetch():
    while True:
        fetch_and_store_articles()
        time.sleep(3600)  # 1 ora

# --- Rotte Flask ---
@app.route('/')
def home():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM articles ORDER BY published DESC LIMIT 10")
    articles = c.fetchall()
    conn.close()
    return render_template('home.html', articles=articles)

@app.route('/category/<cat>')
def category(cat):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM articles WHERE category=? ORDER BY published DESC", (cat,))
    articles = c.fetchall()
    conn.close()
    return render_template('category.html', articles=articles, category=cat)

@app.route('/article/<int:article_id>')
def article(article_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM articles WHERE id=?", (article_id,))
    article = c.fetchone()
    conn.close()
    return render_template('article.html', article=article)

# --- Avvio diretto ---
init_db()
threading.Thread(target=schedule_fetch, daemon=True).start()
