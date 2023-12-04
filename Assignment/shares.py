from flask import Flask, request, jsonify, g, render_template
import sqlite3

app = Flask(__name__)
app.config['DATABASE'] = 'notes.db'

# Function to connect to the SQLite database
def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

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

# Initialize the database
def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

# Check if a user is logged in
@app.before_request
def before_request():
    g.user = None
    if 'user_id' in request.headers:
        g.user = request.headers['user_id']

# API endpoint to render the home page
@app.route('/')
def home():
    return render_template('home_index.html')

# API endpoint to render the create note page
@app.route('/create_note')
def create_note():
    return render_template('create_note.html')

# API endpoint to create a new note
@app.route('/notes', methods=['POST'])
def create_note_api():
    data = request.get_json()
    title = data.get('title')
    content = data.get('content')

    if title and content:
        db = get_db()
        db.execute('INSERT INTO notes (title, content, user_id) VALUES (?, ?, ?)', [title, content, g.user])
        db.commit()
        return jsonify({'message': 'Note created successfully'}), 201
    else:
        return jsonify({'error': 'Title and content are required'}), 400

# API endpoint to retrieve all notes for a user
@app.route('/notes', methods=['GET'])
def get_notes():
    db = get_db()
    notes = db.execute('SELECT * FROM notes WHERE user_id = ?', [g.user]).fetchall()
    notes_list = [{'id': note['id'], 'title': note['title'], 'content': note['content']} for note in notes]
    return jsonify(notes_list)

# API endpoint to render the edit note page
@app.route('/edit_note/<int:note_id>')
def edit_note_page(note_id):
    return render_template('edit_note.html', note_id=note_id)

# API endpoint to edit a note
@app.route('/notes/<int:note_id>', methods=['PUT'])
def edit_note_api(note_id):
    data = request.get_json()
    title = data.get('title')
    content = data.get('content')

    db = get_db()
    db.execute('UPDATE notes SET title = ?, content = ? WHERE id = ? AND user_id = ?', [title, content, note_id, g.user])
    db.commit()

    if db.total_changes > 0:
        return jsonify({'message': 'Note updated successfully'})
    else:
        return jsonify({'error': 'Note not found or you do not have permission to edit'}), 404

# API endpoint to render the delete note page
@app.route('/delete_note/<int:note_id>')
def delete_note_page(note_id):
    return render_template('delete_note.html', note_id=note_id)

# API endpoint to delete a note
@app.route('/notes/<int:note_id>', methods=['DELETE'])
def delete_note_api(note_id):
    db = get_db()
    db.execute('DELETE FROM notes WHERE id = ? AND user_id = ?', [note_id, g.user])
    db.commit()

    if db.total_changes > 0:
        return jsonify({'message': 'Note deleted successfully'})
    else:
        return jsonify({'error': 'Note not found or you do not have permission to delete'}), 404

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
