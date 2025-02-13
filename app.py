from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
import bcrypt
app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Session için gerekli

# Veritabanı oluştur (ilk çalıştırmada)
conn = sqlite3.connect('database.db')
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)')
cursor.execute('CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, user TEXT, content TEXT)')
conn.commit()
conn.close()

@app.route('/api/notes', methods=['GET'])
def api_notes():
    if 'username' not in session:
        return jsonify({"error": "Giriş yapmanız gerekiyor!"}), 401

    username = session['username']

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM notes WHERE user = ?', (username,))
    notes = cursor.fetchall()
    conn.close()

    # Veriyi JSON formatına dönüştür
    notes_list = []
    for note in notes:
        notes_list.append({
            "id": note[0],
            "user": note[1],
            "content": note[2]
        })

    return jsonify(notes_list)

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('notes'))
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Aynı kullanıcı var mı diye kontrol et
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    existing_user = cursor.fetchone()

    if existing_user:
        conn.close()
        return "Bu kullanıcı adı zaten alınmış! <a href='/'>Geri dön</a>"

    # Kayıt ekle
    cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
    conn.commit()
    conn.close()

    return "Kayıt Başarılı! <a href='/'>Giriş yap</a>"

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()

    if user and bcrypt.checkpw(password.encode('utf-8'), user[2]):
        session['username'] = username  # Kullanıcıyı oturuma al
        return redirect(url_for('notes'))
    else:
        return "Giriş Başarısız! <a href='/'>Tekrar dene</a>"
    
@app.route('/logout')
def logout():
    session.pop('username', None)  # Oturumu kapat
    return redirect(url_for('home'))

@app.route('/notes', methods=['GET', 'POST'])
def notes():
    if 'username' not in session:
        return redirect(url_for('home'))

    username = session['username']

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        content = request.form['content']
        cursor.execute('INSERT INTO notes (user, content) VALUES (?, ?)', (username, content))
        conn.commit()

    cursor.execute('SELECT * FROM notes WHERE user = ?', (username,))
    user_notes = cursor.fetchall()

    conn.close()

    return render_template('notes.html', notes=user_notes, username=username)

@app.route('/delete_note/<int:note_id>')
def delete_note(note_id):

    if 'username' not in session:
        return redirect(url_for('home'))

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('DELETE FROM notes WHERE id = ?', (note_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('notes'))

@app.route('/edit_note/<int:note_id>', methods=['GET', 'POST'])
def edit_note(note_id):
    if 'username' not in session:
        return redirect(url_for('home'))

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        new_content = request.form['content']
        cursor.execute('UPDATE notes SET content = ? WHERE id = ?', (new_content, note_id))
        conn.commit()
        conn.close()
        return redirect(url_for('notes'))

    cursor.execute('SELECT * FROM notes WHERE id = ?', (note_id,))
    note = cursor.fetchone()
    conn.close()

    return render_template('edit_note.html', note=note)


if __name__ == '__main__':
    app.run(debug=True)
