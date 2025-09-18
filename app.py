# app.py - single-file Flask Library Management System (scaffolds templates/static/.env on first run)
# Requirements: Flask, flask-login, python-dotenv, pymongo, werkzeug
import os
import secrets
import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify, abort
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from bson.objectid import ObjectId

# Helper to get current ISO date string
def now_iso():
    return datetime.datetime.now().isoformat()


TEMPLATES = {
    'base.html': '''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block title %}Library{% endblock %}</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
<nav class="navbar navbar-expand-lg navbar-light bg-light">
  <div class="container">
    <a class="navbar-brand" href="{{ url_for('index') }}">Community Library</a>
    <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navCollapse">
      <span class="navbar-toggler-icon"></span>
    </button>
    <div class="collapse navbar-collapse" id="navCollapse">
      <ul class="navbar-nav me-auto mb-2 mb-lg-0">
        <li class="nav-item"><a class="nav-link" href="{{ url_for('catalog') }}">Catalog</a></li>
        <li class="nav-item"><a class="nav-link" href="{{ url_for('ebooks') }}">E-books</a></li>
        <li class="nav-item"><a class="nav-link" href="{{ url_for('donate') }}">Donate</a></li>
        <li class="nav-item"><a class="nav-link" href="{{ url_for('forum') }}">Forum</a></li>
        <li class="nav-item"><a class="nav-link" href="{{ url_for('events') }}">Events</a></li>
      </ul>
      <ul class="navbar-nav ms-auto">
        {% if current_user.is_authenticated %}
          <li class="nav-item"><a class="nav-link" href="{{ url_for('dashboard') }}">Dashboard</a></li>
          {% if current_user.is_admin %}
            <li class="nav-item"><a class="nav-link" href="{{ url_for('admin_dashboard') }}">Admin</a></li>
          {% endif %}
          <li class="nav-item"><a class="nav-link" href="{{ url_for('logout') }}">Logout</a></li>
        {% else %}
          <li class="nav-item"><a class="nav-link" href="{{ url_for('login') }}">Login</a></li>
          <li class="nav-item"><a class="nav-link" href="{{ url_for('register') }}">Register</a></li>
        {% endif %}
      </ul>
    </div>
  </div>
</nav>
<div class="container mt-4">
  {% with messages = get_flashed_messages() %}
    {% if messages %}
      <div class="alert alert-info">
        {% for m in messages %} {{ m }} <br> {% endfor %}
      </div>
    {% endif %}
  {% endwith %}
  {% block content %}{% endblock %}
</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
<script src="{{ url_for('static', filename='js/main.js') }}"></script>
</body>
</html>
''',
    'index.html': '''{% extends 'base.html' %}
{% block title %}Home - Community Library{% endblock %}
{% block content %}
<div class="row">
  <div class="col-md-8">
    <h2>Featured Books</h2>
    <div class="row">
    {% for b in featured %}
      <div class="col-md-4">
         <div class="card mb-3">
            <img src="{{ url_for('static', filename='images/' ~ b.image) }}" class="card-img-top" alt="cover">
            <div class="card-body">
              <h5 class="card-title">{{ b.title }}</h5>
              <p class="card-text">{{ b.author }}</p>
              <a href="{{ url_for('book_detail', book_id=b._id) }}" class="btn btn-primary btn-sm">View</a>
            </div>
         </div>
      </div>
    {% endfor %}
    </div>
  </div>
  <div class="col-md-4">
     <h4>Search</h4>
     <form action="{{ url_for('catalog') }}" method="get">
       <div class="input-group mb-3">
         <input name="q" class="form-control" placeholder="Search by title, author, isbn">
         <button class="btn btn-outline-secondary">Search</button>
       </div>
     </form>
     <h4>Announcements</h4>
     {% for e in events %}
       <div class="mb-2"><strong>{{ e.title }}</strong><br><small>{{ e.date }}</small><p>{{ e.description }}</p></div>
     {% endfor %}
  </div>
</div>
{% endblock %}''',
    'catalog.html': '''{% extends 'base.html' %}
{% block title %}Catalog{% endblock %}
{% block content %}
<h2>Catalog</h2>
<form class="mb-3" method="get">
<div class="input-group">
  <input type="text" name="q" class="form-control" placeholder="Search..." value="{{ request.args.get('q','') }}">
  <button class="btn btn-secondary">Search</button>
</div>
</form>
<div class="row mt-3">
{% for b in books %}
  <div class="col-md-3">
    <div class="card mb-3">
      <img src="{{ url_for('static', filename='images/' ~ b.image) }}" class="card-img-top">
      <div class="card-body">
        <h5 class="card-title">{{ b.title }}</h5>
        <p class="card-text">{{ b.author }}</p>
        <a href="{{ url_for('book_detail', book_id=b._id) }}" class="btn btn-sm btn-primary">View</a>
      </div>
    </div>
  </div>
{% endfor %}
</div>
{% endblock %}''',
    'book_detail.html': '''{% extends 'base.html' %}
{% block title %}{{ book.title }}{% endblock %}
{% block content %}
<div class="row">
  <div class="col-md-4"><img src="{{ url_for('static', filename='images/' ~ book.image) }}" class="img-fluid"></div>
  <div class="col-md-8">
    <h2>{{ book.title }}</h2>
    <p><strong>Author:</strong> {{ book.author }}</p>
    <p><strong>Category:</strong> {{ book.category }}</p>
    <p><strong>ISBN:</strong> {{ book.isbn }}</p>
    <p>{{ book.description }}</p>
    <p><strong>Available copies:</strong> {{ book.copies_available }}</p>
    {% if current_user.is_authenticated %}
      {% if book.copies_available | int > 0 %}
        <a href="{{ url_for('borrow', book_id=book._id) }}" class="btn btn-success">Borrow</a>
      {% else %}
        <a href="{{ url_for('reserve', book_id=book._id) }}" class="btn btn-warning">Reserve</a>
      {% endif %}
    {% else %}
      <a href="{{ url_for('login') }}" class="btn btn-primary">Login to borrow</a>
    {% endif %}
  </div>
</div>
{% endblock %}''',
    'register.html': '''{% extends 'base.html' %}{% block title %}Register{% endblock %}{% block content %}
<h2>Register</h2>
<form method="post">
  <div class="mb-3"><input class="form-control" name="username" placeholder="Username" required></div>
  <div class="mb-3"><input class="form-control" name="email" placeholder="Email" required></div>
  <div class="mb-3"><input class="form-control" name="password" placeholder="Password" type="password" required></div>
  <button class="btn btn-primary">Register</button>
</form>
{% endblock %}''',
    'login.html': '''{% extends 'base.html' %}{% block title %}Login{% endblock %}{% block content %}
<h2>Login</h2>
<form method="post">
  <div class="mb-3"><input class="form-control" name="email" placeholder="Email" required></div>
  <div class="mb-3"><input class="form-control" name="password" placeholder="Password" type="password" required></div>
  <button class="btn btn-primary">Login</button>
</form>
<p class="mt-3"><a href="{{ url_for('forgot_password') }}">Forgot password?</a></p>
{% endblock %}''',
    'forgot_password.html': '''{% extends 'base.html' %}{% block title %}Forgot Password{% endblock %}{% block content %}
<h2>Forgot Password</h2>
<form method="post">
  <div class="mb-3"><input class="form-control" name="email" placeholder="Your registered email" required></div>
  <button class="btn btn-warning">Request reset link</button>
</form>
<p class="mt-2 text-muted">A reset link will be printed to the console (local dev).</p>
{% endblock %}''',
    'dashboard.html': '''{% extends 'base.html' %}{% block title %}Dashboard{% endblock %}{% block content %}
<h2>Hi, {{ current_user.username }}</h2>
<h4>Borrowed books</h4>
<table class="table">
  <thead><tr><th>Title</th><th>Due</th><th>Status</th><th>Action</th></tr></thead>
  <tbody>
    {% for b in borrows %}
      <tr>
        <td>{{ b.title }}</td>
        <td>{{ b.due_date }}</td>
        <td>{% if b.returned_date %}Returned{% else %}Borrowed{% endif %}</td>
        <td>
          {% if not b.returned_date %}<a href="{{ url_for('return_book', borrow_id=b._id) }}" class="btn btn-sm btn-success">Return</a>{% endif %}
        </td>
      </tr>
    {% else %}<tr><td colspan=4>No borrowed books</td></tr>{% endfor %}
  </tbody>
</table>
<h4>Reservations</h4>
<ul>{% for r in reservations %}<li>{{ r.title }} (reserved on {{ r.date }})</li>{% else %}<li>No reservations</li>{% endfor %}</ul>
{% endblock %}''',
    'admin_dashboard.html': '''{% extends 'base.html' %}{% block title %}Admin Dashboard{% endblock %}{% block content %}
<h2>Admin</h2>
<div class="list-group">
  <a class="list-group-item" href="{{ url_for('manage_books') }}">Manage books</a>
  <a class="list-group-item" href="{{ url_for('reports') }}">Reports & Analytics</a>
  <a class="list-group-item" href="{{ url_for('events') }}">Manage events</a>
</div>
{% endblock %}''',
    'manage_books.html': '''{% extends 'base.html' %}{% block title %}Manage Books{% endblock %}{% block content %}
<h2>Add new book</h2>
<form method="post" enctype="multipart/form-data">
  <div class="mb-3"><input class="form-control" name="title" placeholder="Title" required></div>
  <div class="mb-3"><input class="form-control" name="author" placeholder="Author"></div>
  <div class="mb-3"><input class="form-control" name="category" placeholder="Category"></div>
  <div class="mb-3"><input class="form-control" name="isbn" placeholder="ISBN"></div>
  <div class="mb-3"><textarea class="form-control" name="description" placeholder="Short description"></textarea></div>
  <div class="mb-3"><input class="form-control" name="copies" placeholder="Copies" type="number" value="1"></div>
  <div class="mb-3"><input class="form-control" name="cover" type="file"></div>
  <div class="mb-3"><input class="form-control" name="ebook" type="file"></div>
  <button class="btn btn-primary">Add book</button>
</form>
<hr>
<h3>Existing books</h3>
<div class="row">{% for b in books %}
  <div class="col-md-3">
    <div class="card mb-2">
      <img src="{{ url_for('static', filename='images/' ~ b.image) }}" class="card-img-top">
      <div class="card-body">
        <h6>{{ b.title }}</h6>
        <p class="small">by {{ b.author }}</p>
        <form method="post" action="{{ url_for('delete_book', book_id=b._id) }}" onsubmit="return confirm('Delete?')"><button class="btn btn-sm btn-danger">Delete</button></form>
      </div>
    </div>
  </div>
{% endfor %}</div>
{% endblock %}''',
    'ebooks.html': '''{% extends 'base.html' %}{% block title %}E-books{% endblock %}{% block content %}
<h2>E-books & Digital Resources</h2>
<div class="row">
{% for e in ebooks %}
  <div class="col-md-4">
    <div class="card mb-3">
      <div class="card-body">
        <h5>{{ e.title }}</h5>
        <p>{{ e.author }}</p>
        <a href="{{ url_for('download_ebook', filename=e.filename) }}" class="btn btn-sm btn-primary">Download</a>
      </div>
    </div>
  </div>
{% else %}<p>No e-books yet.</p>{% endfor %}
</div>
{% endblock %}''',
    'donate.html': '''{% extends 'base.html' %}{% block title %}Donate{% endblock %}{% block content %}
<h2>Donate a book or funds</h2>
<form method="post" enctype="multipart/form-data">
  <div class="mb-3"><input class="form-control" name="donor_name" placeholder="Your name"></div>
  <div class="mb-3"><input class="form-control" name="book_title" placeholder="Book title (optional)"></div>
  <div class="mb-3"><input class="form-control" name="amount" placeholder="Monetary donation (optional)"></div>
  <div class="mb-3"><input class="form-control" name="photo" type="file"></div>
  <button class="btn btn-success">Donate</button>
</form>
<h3 class="mt-4">Recent donations</h3>
<ul>{% for d in donations %}<li>{{ d.donor_name }} donated {{ d.book_title or d.amount }}</li>{% else %}<li>No donations yet.</li>{% endfor %}</ul>
{% endblock %}''',
    'forum.html': '''{% extends 'base.html' %}{% block title %}Community Forum{% endblock %}{% block content %}
<h2>Forum</h2>
{% if current_user.is_authenticated %}
<form method="post"><div class="mb-3"><input class="form-control" name="title" placeholder="Post title" required></div><div class="mb-3"><textarea class="form-control" name="content" placeholder="Write..." required></textarea></div><button class="btn btn-primary">Post</button></form>
{% else %}<p><a href="{{ url_for('login') }}">Login</a> to post.</p>{% endif %}
<hr>
{% for p in posts %}
<div class="card mb-2"><div class="card-body"><h5>{{ p.title }}</h5><p class="small">by {{ p.author }} on {{ p.created }}</p><p>{{ p.content }}</p></div></div>
{% else %}<p>No posts yet.</p>{% endfor %}
{% endblock %}''',
    'events.html': '''{% extends 'base.html' %}{% block title %}Events & Announcements{% endblock %}{% block content %}
<h2>Events</h2>
{% if current_user.is_authenticated and current_user.is_admin %}
<form method="post"><div class="mb-3"><input class="form-control" name="title" placeholder="Event title"></div><div class="mb-3"><input class="form-control" name="date" placeholder="YYYY-MM-DD"></div><div class="mb-3"><textarea class="form-control" name="description"></textarea></div><button class="btn btn-primary">Add event</button></form><hr>{% endif %}
<ul>{% for e in events %}<li><strong>{{ e.title }}</strong> - {{ e.date }}<br>{{ e.description }}</li>{% else %}<li>No events</li>{% endfor %}</ul>
{% endblock %}''',
    'contact.html': '''{% extends 'base.html' %}{% block title %}Contact{% endblock %}{% block content %}
<h2>Contact & Support</h2>
<form method="post">
  <div class="mb-3"><input class="form-control" name="name" placeholder="Your name"></div>
  <div class="mb-3"><input class="form-control" name="email" placeholder="Your email"></div>
  <div class="mb-3"><textarea class="form-control" name="message" placeholder="How can we help?"></textarea></div>
  <button class="btn btn-primary">Send</button>
</form>
{% endblock %}''',
    'about.html': '''{% extends 'base.html' %}{% block title %}About{% endblock %}{% block content %}
<h2>About Community Library</h2>
<p>Our mission is to make books accessible to students who cannot afford them. This demo app gives a production-like skeleton you can extend.</p>
{% endblock %}''',
    'reports.html': '''{% extends 'base.html' %}{% block title %}Reports & Analytics{% endblock %}{% block content %}
<h2>Reports & Analytics</h2>
<ul>
  <li>Total users: {{ stats.users }}</li>
  <li>Total books: {{ stats.books }}</li>
  <li>Currently borrowed: {{ stats.borrowed }}</li>
</ul>
<h3>Top borrowed books</h3>
<ol>{% for b in top_books %}<li>{{ b.title }} — {{ b.count }} borrows</li>{% else %}<li>None</li>{% endfor %}</ol>
{% endblock %}'''
}

CSS = '''body{padding-bottom:40px}.card-img-top{height:180px;object-fit:cover}.navbar-brand{font-weight:700}'''
JS = '''console.log('Library app loaded');'''

# ---------------------------
# Create folders & write templates/static files on first run
# ---------------------------
def create_project_structure():
    base = os.getcwd()
    os.makedirs(os.path.join(base, 'templates'), exist_ok=True)
    os.makedirs(os.path.join(base, 'static', 'images'), exist_ok=True)
    os.makedirs(os.path.join(base, 'static', 'css'), exist_ok=True)
    os.makedirs(os.path.join(base, 'static', 'js'), exist_ok=True)
    os.makedirs(os.path.join(base, 'static', 'ebooks'), exist_ok=True)

    for name, txt in TEMPLATES.items():
        path = os.path.join(base, 'templates', name)
        if not os.path.exists(path):
            with open(path, 'w', encoding='utf8') as f:
                f.write(txt)
    # write CSS and JS
    css_path = os.path.join(base, 'static', 'css', 'style.css')
    if not os.path.exists(css_path):
        with open(css_path, 'w', encoding='utf8') as f:
            f.write(CSS)
    js_path = os.path.join(base, 'static', 'js', 'main.js')
    if not os.path.exists(js_path):
        with open(js_path, 'w', encoding='utf8') as f:
            f.write(JS)
    # create a few placeholder SVG images
    for i in range(1,6):
        img_path = os.path.join(base, 'static', 'images', f'cover{i}.svg')
        if not os.path.exists(img_path):
            svg = f"""<svg xmlns='http://www.w3.org/2000/svg' width='400' height='600'>
  <rect width='100%' height='100%' fill='#e9ecef'/>
  <text x='50%' y='50%' dominant-baseline='middle' text-anchor='middle' font-family='Arial' font-size='22' fill='#6c757d'>Placeholder Book {i}</text>
</svg>"""
            with open(img_path, 'w', encoding='utf8') as f:
                f.write(svg)
    # create sample ebook file
    ebook_path = os.path.join(base, 'static', 'ebooks', 'sample_ebook.txt')
    if not os.path.exists(ebook_path):
        with open(ebook_path, 'w', encoding='utf8') as f:
            f.write('This is a sample ebook file. Replace with PDF/epub files.')
    # write requirements.txt
    req_path = os.path.join(base, 'requirements.txt')
    if not os.path.exists(req_path):
        with open(req_path, 'w', encoding='utf8') as f:
            f.write('\n'.join(['Flask', 'flask-login', 'python-dotenv', 'pymongo', 'werkzeug']))

# ---------------------------
# .env creation & DB init
# ---------------------------
def ensure_env():
    env_path = os.path.join(os.getcwd(), '.env')
    if not os.path.exists(env_path):
        secret = secrets.token_hex(16)
        default = [
            f'MONGODB_URI=mongodb://localhost:27017',
            f'MONGO_DB_NAME=library_db',
            f'SECRET_KEY={secret}'
        ]
        with open(env_path, 'w', encoding="utf8") as f:
            f.write('\n'.join(default))
        print('Created .env with default local MongoDB URI (mongodb://localhost:27017). Edit it if needed.')

create_project_structure()
ensure_env()

# load .env
load_dotenv()
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'library_db')
SECRET_KEY = os.getenv('SECRET_KEY') or secrets.token_hex(16)

# connect to MongoDB
client = MongoClient(MONGODB_URI)
db = client[MONGO_DB_NAME]

# ---------------------------
# Flask app + Login manager
# ---------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'static', 'images')
app.config['EBOOK_FOLDER'] = os.path.join(os.getcwd(), 'static', 'ebooks')

login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, doc):
        self.doc = doc
        self.id = str(doc['_id'])
        self.username = doc.get('username')
        self.email = doc.get('email')
        self.is_admin = doc.get('is_admin', False)

@login_manager.user_loader
def load_user(user_id):
    try:
        doc = db.users.find_one({'_id': ObjectId(user_id)})
        if doc:
            return User(doc)
    except Exception:
        return None
    return None

# ---------------------------
# helper utilities
# ---------------------------
def str_id(oid):
    return str(oid) if oid else None

def now_iso():
    return datetime.datetime.utcnow().isoformat()

# ---------------------------
# Routes
# ---------------------------
@app.route('/')
def index():
    featured_cursor = db.books.find().limit(6)
    featured = []
    for b in featured_cursor:
        b['_id'] = str(b['_id'])
        featured.append(b)
    events = list(db.events.find().sort('date', -1).limit(3))
    for e in events:
        e['date'] = e.get('date', 'n/a')
    return render_template('index.html', featured=featured, events=events)

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']
        if db.users.find_one({'email': email}):
            flash('Email already registered. Please login.')
            return redirect(url_for('login'))
        hashed = generate_password_hash(password)
        doc = {'username': username, 'email': email, 'password': hashed, 'is_admin': False, 'created': now_iso()}
        res = db.users.insert_one(doc)
        user = User(db.users.find_one({'_id': res.inserted_id}))
        login_user(user)
        flash('Welcome! Your account has been created.')
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        user_doc = db.users.find_one({'email': email})
        if user_doc and check_password_hash(user_doc['password'], password):
            user = User(user_doc)
            login_user(user)
            flash('Logged in successfully.')
            return redirect(url_for('index'))
        flash('Invalid credentials.')
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out.')
    return redirect(url_for('index'))

@app.route('/forgot-password', methods=['GET','POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        user = db.users.find_one({'email': email})
        if not user:
            flash('If that email exists, a reset link was generated (check console).')
            return redirect(url_for('login'))
        token = secrets.token_hex(16)
        db.users.update_one({'_id': user['_id']}, {'$set': {'reset_token': token, 'reset_token_expiry': (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).isoformat()}})
        reset_url = url_for('reset_password', token=token, _external=True)
        print('Password reset link (local dev):', reset_url)
        flash('Reset link generated and printed to console (local dev).')
        return redirect(url_for('login'))
    return render_template('forgot_password.html')

@app.route('/reset/<token>', methods=['GET','POST'])
def reset_password(token):
    user = db.users.find_one({'reset_token': token})
    if not user:
        flash('Invalid or expired token.')
        return redirect(url_for('login'))
    expiry_str = user.get('reset_token_expiry')
    if expiry_str and datetime.datetime.fromisoformat(expiry_str) < datetime.datetime.utcnow():
        flash('Token expired.')
        return redirect(url_for('forgot_password'))
    if request.method == 'POST':
        newpass = request.form['password']
        db.users.update_one({'_id': user['_id']}, {'$set': {'password': generate_password_hash(newpass)}, '$unset': {'reset_token': '', 'reset_token_expiry': ''}})
        flash('Password updated. Please login.')
        return redirect(url_for('login'))
    return '''
    <h3>Reset password for {}</h3>
    <form method="post"><input name="password" placeholder="New password"><button>Set</button></form>
    '''.format(user.get('email'))

@app.route('/catalog')
def catalog():
    q = request.args.get('q', '').strip()
    query = {}
    if q:
        regex = {'$regex': q, '$options': 'i'}
        query = {'$or': [{'title': regex}, {'author': regex}, {'isbn': regex}, {'category': regex}]}
    cursor = db.books.find(query)
    books = []
    for b in cursor:
        b['_id'] = str(b['_id'])
        books.append(b)
    return render_template('catalog.html', books=books)

@app.route('/book/<book_id>')
def book_detail(book_id):
    try:
        b = db.books.find_one({'_id': ObjectId(book_id)})
    except Exception:
        abort(404)
    if not b: abort(404)
    b['_id'] = str(b['_id'])
    return render_template('book_detail.html', book=b)

@app.route('/borrow/<book_id>', methods=['GET','POST'])
@login_required
def borrow(book_id):
    try:
        b = db.books.find_one({'_id': ObjectId(book_id)})
    except Exception:
        flash('Book not found'); return redirect(url_for('catalog'))
    if not b:
        flash('Book not found'); return redirect(url_for('catalog'))
    if b.get('copies_available', 0) < 1:
        flash('No copies available to borrow. You may reserve.'); return redirect(url_for('book_detail', book_id=book_id))
    borrow_doc = {
        'user_id': ObjectId(current_user.id),
        'book_id': b['_id'],
        'borrow_date': datetime.datetime.utcnow().isoformat(),
        'due_date': (datetime.datetime.utcnow() + datetime.timedelta(days=14)).isoformat(),
        'returned_date': None
    }
    db.borrows.insert_one(borrow_doc)
    db.books.update_one({'_id': b['_id']}, {'$inc': {'copies_available': -1}})
    flash('Book borrowed. Due in 14 days.')
    return redirect(url_for('dashboard'))

@app.route('/return/<borrow_id>')
@login_required
def return_book(borrow_id):
    try:
        bor = db.borrows.find_one({'_id': ObjectId(borrow_id)})
    except Exception:
        flash('Invalid borrow record'); return redirect(url_for('dashboard'))
    if not bor:
        flash('Invalid borrow record'); return redirect(url_for('dashboard'))
    if bor.get('returned_date'):
        flash('Already returned.'); return redirect(url_for('dashboard'))
    db.borrows.update_one({'_id': bor['_id']}, {'$set': {'returned_date': datetime.datetime.utcnow().isoformat()}})
    db.books.update_one({'_id': bor['book_id']}, {'$inc': {'copies_available': 1}})
    # compute fine
    due = datetime.datetime.fromisoformat(bor['due_date'])
    if datetime.datetime.utcnow() > due:
        days = (datetime.datetime.utcnow() - due).days
        fine = days * 5  # 5 units per day
        db.borrows.update_one({'_id': bor['_id']}, {'$set': {'fine': fine}})
        flash(f'Book returned. Late by {days} days. Fine: {fine} units.')
    else:
        flash('Book returned on time. Thank you!')
    return redirect(url_for('dashboard'))

# ------------------- DASHBOARD AND RESERVATION ROUTES -------------------

@app.route('/dashboard')
@login_required
def dashboard():
    # Fetch borrowed books
    borrows = []
    for b in db.borrows.find({'user_id': ObjectId(current_user.id)}):
        book = db.books.find_one({'_id': b['book_id']})
        borrows.append({
            '_id': str(b['_id']),
            'title': book['title'] if book else 'Unknown',
            'due_date': b.get('due_date'),
            'returned_date': b.get('returned_date')
        })

    # Fetch reservations
    reservations = []
    for r in db.reservations.find({'user_id': ObjectId(current_user.id)}):
        book = db.books.find_one({'_id': r['book_id']})
        reservations.append({
            '_id': str(r['_id']),
            'book_id': str(r['book_id']),
            'title': book['title'] if book else 'Unknown',
            'date': r.get('date'),
            'fulfilled': r.get('fulfilled', False)
        })

    # Fetch all books to allow new reservations
    books = []
    for b in db.books.find():
        # Skip if already reserved by user
        already_reserved = db.reservations.find_one({
            'user_id': ObjectId(current_user.id),
            'book_id': b['_id']
        })
        books.append({
            '_id': str(b['_id']),
            'title': b['title'],
            'reserved': bool(already_reserved)
        })

    return render_template('dashboard.html', borrows=borrows, reservations=reservations, books=books)


@app.route('/reserve/<book_id>', methods=['POST'])
@login_required
def reserve(book_id):
    # Check if already reserved
    existing = db.reservations.find_one({
        'user_id': ObjectId(current_user.id),
        'book_id': ObjectId(book_id)
    })
    if existing:
        flash('You have already reserved this book.')
        return redirect(url_for('dashboard'))

    db.reservations.insert_one({
        'user_id': ObjectId(current_user.id),
        'book_id': ObjectId(book_id),
        'date': now_iso(),
        'fulfilled': False
    })
    flash('Book reserved! You can manage your reservations from dashboard.')
    return redirect(url_for('dashboard'))


@app.route('/cancel_reservation/<reservation_id>', methods=['POST'])
@login_required
def cancel_reservation(reservation_id):
    res = db.reservations.find_one({'_id': ObjectId(reservation_id)})
    if not res or res['user_id'] != ObjectId(current_user.id):
        flash('Reservation not found or not authorized.')
        return redirect(url_for('dashboard'))

    db.reservations.delete_one({'_id': ObjectId(reservation_id)})
    flash('Reservation canceled.')
    return redirect(url_for('dashboard'))

@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        abort(403)
    return render_template('admin_dashboard.html')

@app.route('/admin/manage-books', methods=['GET','POST'])
@login_required
def manage_books():
    if not current_user.is_admin:
        abort(403)
    if request.method == 'POST':
        title = request.form.get('title') or 'Untitled'
        author = request.form.get('author') or ''
        category = request.form.get('category') or ''
        isbn = request.form.get('isbn') or ''
        description = request.form.get('description') or ''
        copies = int(request.form.get('copies') or 1)
        cover_file = request.files.get('cover')
        ebook_file = request.files.get('ebook')
        image_name = 'cover1.svg'
        if cover_file and cover_file.filename:
            filename = secure_filename(cover_file.filename)
            cover_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            cover_file.save(cover_path)
            image_name = filename
        ebook_name = None
        if ebook_file and ebook_file.filename:
            ebook_fn = secure_filename(ebook_file.filename)
            ebook_file.save(os.path.join(app.config['EBOOK_FOLDER'], ebook_fn))
            ebook_name = ebook_fn
        db.books.insert_one({'title': title, 'author': author, 'category': category, 'isbn': isbn, 'description': description, 'copies_total': copies, 'copies_available': copies, 'image': image_name, 'ebook': ebook_name})
        flash('Book added.')
        return redirect(url_for('manage_books'))
    books = []
    for b in db.books.find():
        b['_id'] = str(b['_id'])
        books.append(b)
    return render_template('manage_books.html', books=books)

@app.route('/admin/delete-book/<book_id>', methods=['POST'])
@login_required
def delete_book(book_id):
    if not current_user.is_admin:
        abort(403)
    try:
        db.books.delete_one({'_id': ObjectId(book_id)})
    except Exception:
        pass
    flash('Book deleted (if existed).')
    return redirect(url_for('manage_books'))

@app.route('/ebooks')
def ebooks():
    ebooks = []
    for b in db.books.find({'ebook': {'$exists': True, '$ne': None}}):
        ebooks.append({'title': b['title'], 'author': b.get('author',''), 'filename': b['ebook']})
    # also include static ebook samples
    for f in os.listdir(app.config['EBOOK_FOLDER']):
        if f not in [e['filename'] for e in ebooks]:
            ebooks.append({'title': 'Sample ebook', 'author': 'Library', 'filename': f})
    return render_template('ebooks.html', ebooks=ebooks)

@app.route('/ebooks/download/<path:filename>')
def download_ebook(filename):
    return send_from_directory(app.config['EBOOK_FOLDER'], filename, as_attachment=True)

@app.route('/donate', methods=['GET','POST'])
def donate():
    if request.method == 'POST':
        donor_name = request.form.get('donor_name')
        book_title = request.form.get('book_title') or None
        amount = request.form.get('amount') or None
        photo = request.files.get('photo')
        photo_name = None
        if photo and photo.filename:
            photo_name = secure_filename(photo.filename)
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_name))
        db.donations.insert_one({'donor_name': donor_name, 'book_title': book_title, 'amount': amount, 'photo': photo_name, 'date': now_iso()})
        flash('Thank you for your donation!')
        return redirect(url_for('donate'))
    donations = list(db.donations.find().sort('date', -1).limit(10))
    return render_template('donate.html', donations=donations)

@app.route('/forum', methods=['GET','POST'])
def forum():
    if request.method == 'POST':
        if not current_user.is_authenticated:
            flash('Login to post.')
            return redirect(url_for('login'))
        title = request.form.get('title'); content = request.form.get('content')
        db.forum_posts.insert_one({'title': title, 'content': content, 'author': current_user.username, 'created': now_iso()})
        flash('Posted.')
        return redirect(url_for('forum'))
    posts = list(db.forum_posts.find().sort('_id', -1).limit(50))
    return render_template('forum.html', posts=posts)

@app.route('/events', methods=['GET','POST'])
def events():
    if request.method == 'POST':
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        title = request.form.get('title'); date = request.form.get('date'); description = request.form.get('description')
        db.events.insert_one({'title': title, 'date': date, 'description': description})
        flash('Event added.')
        return redirect(url_for('events'))
    events = list(db.events.find().sort('date', -1).limit(20))
    return render_template('events.html', events=events)

@app.route('/contact', methods=['GET','POST'])
def contact():
    if request.method == 'POST':
        db.contact_messages.insert_one({'name': request.form.get('name'), 'email': request.form.get('email'), 'message': request.form.get('message'), 'date': now_iso()})
        flash('Message sent.')
        return redirect(url_for('contact'))
    return render_template('contact.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/reports')
@login_required
def reports():
    if not current_user.is_admin:
        abort(403)
    stats = {
        'users': db.users.count_documents({}),
        'books': db.books.count_documents({}),
        'borrowed': db.borrows.count_documents({'returned_date': None})
    }
    # top borrowed books
    pipeline = [
        {'$group': {'_id': '$book_id', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}},
        {'$limit': 10}
    ]
    top = []
    for doc in db.borrows.aggregate(pipeline):
        b = db.books.find_one({'_id': doc['_id']}) if doc['_id'] else None
        if b:
            top.append({'title': b['title'], 'count': doc['count']})
    return render_template('reports.html', stats=stats, top_books=top)

# ---------------------------
# Create a default admin & sample books if empty
# ---------------------------
def seed_defaults():
    if db.users.count_documents({}) == 0:
        print('No users found. Creating default admin -> email: admin@local, password: admin123')
        db.users.insert_one({'username': 'admin', 'email': 'admin@local', 'password': generate_password_hash('admin123'), 'is_admin': True, 'created': now_iso()})
    if db.books.count_documents({}) == 0:
        for i in range(1,6):
            db.books.insert_one({'title': f'Sample Book {i}', 'author': 'Author '+str(i), 'category': 'General', 'isbn': f'ISBN{i}', 'description': 'This is a sample book.', 'copies_total': 3, 'copies_available': 3, 'image': f'cover{i}.svg', 'ebook': None})

seed_defaults()

if __name__ == '__main__':
    print('Starting Flask app. Open http://127.0.0.1:5000')
    app.run(debug=True)
