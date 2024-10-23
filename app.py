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

# Helper function to extract BGG ID from the URL
def extract_bgg_id(bgg_url):
    match = re.search(r'boardgame/(\d+)', bgg_url)
    if match:
        return match.group(1)
    return None

# Helper function to fetch the game image from BoardGameGeek
def fetch_game_image(bgg_id):
    bgg_api_url = f'https://boardgamegeek.com/xmlapi2/thing?id={bgg_id}'
    response = requests.get(bgg_api_url)
    if response.status_code == 200:
        # Parse the XML response to get the image URL
        from xml.etree import ElementTree as ET
        root = ET.fromstring(response.content)
        image_url = root.find('./item/image').text
        return image_url
    return "https://via.placeholder.com/100"

# Main page - List of board games
@app.route('/')
def index():
    conn = get_db_connection()
    boardgames = conn.execute('SELECT * FROM boardgames').fetchall()
    conn.close()
    return render_template('index.html', boardgames=boardgames)

# Add a new board game
@app.route('/add', methods=('GET', 'POST'))
def add_game():
    if request.method == 'POST':
        # Fetch the game name, BGG URL, and owner from the form
        game_name = request.form['game_name']
        bgg_url = request.form['bgg_url']
        owner = request.form['owner']

        # Extract BGG ID from the provided URL
        bgg_id = extract_bgg_id(bgg_url)
        if not bgg_id:
            return "Invalid BoardGameGeek URL", 400

        # Fetch the game image from BoardGameGeek
        image_url = fetch_game_image(bgg_id)

        # Save the new board game into the database
        conn = get_db_connection()
        conn.execute('INSERT INTO boardgames (name, owner, bgg_url, image_url) VALUES (?, ?, ?, ?)',
                     (game_name, owner, bgg_url, image_url))
        conn.commit()
        conn.close()

        return redirect(url_for('index'))

    return render_template('add_game.html')

# Initialize the database (run once to create the table)
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
