from flask import Flask, render_template, redirect, url_for, request, flash, session, g
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['DATABASE'] = os.path.join(app.root_path, 'users.db')

# Function to connect to the SQLite database
def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

# Function to initialize the database
def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

# Function to get the database connection
def get_db():
    if 'db' not in g:
        g.db = connect_db()
    return g.db

# Close the database connection when the app is teardown
@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'db'):
        g.db.close()

# Check if a user is logged in
@app.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
        g.user = query_db('SELECT * FROM users WHERE id = ?', [session['user_id']], one=True)

# Query the database
def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

# Initialize the database on app startup
if not os.path.exists(app.config['DATABASE']):
    init_db()

@app.route('/')
def home():
    return 'Welcome to the Home Page'

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if username already exists
        if query_db('SELECT * FROM users WHERE username = ?', [username], one=True):
            flash('Username already exists. Please choose a different one.', 'danger')
        else:
            # Hash the password before storing it in the database
            hashed_password = generate_password_hash(password, method='sha256')
            db = get_db()
            db.execute('INSERT INTO users (username, password) VALUES (?, ?)', [username, hashed_password])
            db.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = query_db('SELECT * FROM users WHERE username = ?', [username], one=True)

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password. Please try again.', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
