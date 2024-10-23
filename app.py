from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import requests
import re

app = Flask(__name__)
DATABASE = 'boardgames.db'

# Helper function to connect to the database
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Helper function to fetch game details from BoardGameGeek
def get_boardgame_details(bgg_url):
    # Extract the game ID from the BoardGameGeek URL using regex
    match = re.search(r'boardgamegeek\.com/boardgame/(\d+)', bgg_url)
    if match:
        game_id = match.group(1)
        bgg_api_url = f"https://boardgamegeek.com/xmlapi2/thing?id={game_id}&stats=1"
        response = requests.get(bgg_api_url)
        
        if response.status_code == 200:
            # Simple parsing of XML to get the title and image (assuming the API returns XML)
            # Using regex to extract title and image from response.text
            title_match = re.search(r'<name type="primary" .* value="([^"]+)"', response.text)
            image_match = re.search(r'<image>([^<]+)</image>', response.text)

            if title_match and image_match:
                title = title_match.group(1)
                image_url = image_match.group(1)
                return title, image_url

    return None, None

# Route: Main page - List of board games
@app.route('/')
def index():
    conn = get_db_connection()
    boardgames = conn.execute('SELECT * FROM boardgames').fetchall()
    conn.close()
    return render_template('index.html', boardgames=boardgames)

# Route: Add a new board game
@app.route('/add', methods=('GET', 'POST'))
def add_game():
    if request.method == 'POST':
        bgg_url = request.form['bgg_url']
        owner = request.form['owner']

        # Fetch game details from BoardGameGeek
        title, image_url = get_boardgame_details(bgg_url)

        if title and image_url:
            conn = get_db_connection()
            conn.execute('INSERT INTO boardgames (name, owner, bgg_url, image_url) VALUES (?, ?, ?, ?)',
                         (title, owner, bgg_url, image_url))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))

    return render_template('add_game.html')

# Initialize the database
def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS boardgames (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            owner TEXT NOT NULL,
            bgg_url TEXT NOT NULL,
            image_url TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
