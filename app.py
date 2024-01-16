from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import random
import base64

app = Flask(__name__)
app.config['SECRET_KEY'] = 'allenSollyisliterallyallunisulli'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db'
db = SQLAlchemy(app)


def encrypt(num):
    num_str = str(num)
    encrypted_str = ''.join(chr((ord(char) + 42) % 256) for char in num_str)
    encoded_str = base64.urlsafe_b64encode(encrypted_str.encode()).decode()
    return encoded_str


def decrypt(encoded_str):
    try:
        encrypted_str = base64.urlsafe_b64decode(encoded_str.encode()).decode()
        decrypted_str = ''.join(chr((ord(char) - 42) % 256) for char in encrypted_str)
        return decrypted_str
    except:
        return encoded_str


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    code = db.Column(db.String(100), unique=True, nullable=False)
    opened = db.Column(db.Boolean, default=False)


def generate_access_code():
    return random.randint(1000, 9999)


def is_note_opened(note_id):
    return session.get(f'note_{note_id}_opened', False)


def mark_note_as_opened(note_id):
    session[f'note_{note_id}_opened'] = True


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/create_note', methods=['POST'])
def create_note():
    note_text = request.form.get('note_text')
    if Note.query.count() > 100:
        with app.app_context():
            db.session.query(Note).delete()
            db.session.commit()

    access_code = generate_access_code()
    while Note.query.filter_by(code=access_code).first():
        access_code = generate_access_code()

    with app.app_context():
        new_note = Note(text=note_text, code=access_code, opened=False)
        db.session.add(new_note)
        db.session.commit()
    access_code = encrypt(access_code)
    note_url = url_for('show_note', code=access_code, _external=True)

    return render_template('create_note.html', note_url=note_url)


@app.route('/note/<string:code>', methods=['GET', 'POST'])
def show_note(code):
    decrypted_code = decrypt(code)
    note = Note.query.filter_by(code=decrypted_code).first()

    if not note:
        return redirect(url_for('index'))

    if request.method == 'POST':
        entered_code = int(request.form.get('entered_code'))
        if entered_code == int(decrypted_code) and not is_note_opened(note.id):
            mark_note_as_opened(note.id)
            # print("entered here")
            return render_template('show_note.html', decrypted_code=decrypted_code, note=note, success=True)
        else:
            return render_template('show_note.html', decrypted_code=decrypted_code, note=note, success=False, status=True)

    return render_template('show_note.html', decrypted_code=decrypted_code, note=note, success=None)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run()
