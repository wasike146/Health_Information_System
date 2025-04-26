from flask import Flask, jsonify, request, abort, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'supersecretkey')

# Database connection
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('postgresql://health_db_4ltc_user:Gs5231Ec8eDpzQszYabfvbgzKdlyNO3N@dpg-d068vr9r0fns73fcg890-a/health_db_4ltc', 'postgresql+psycopg2://postgres:Wa20$$34@localhost/health_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    programs = db.relationship('Program', secondary='enrollments', backref='clients')

class Program(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class Enrollment(db.Model):
    __tablename__ = 'enrollments'
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), primary_key=True)
    program_id = db.Column(db.Integer, db.ForeignKey('program.id'), primary_key=True)

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
def home():
    query = request.args.get('query', '')
    if query:
        clients = Client.query.filter(
            (Client.name.ilike(f'%{query}%')) |
            (Client.client_id.ilike(f'%{query}%'))
        ).all()
    else:
        clients = Client.query.all()

    programs = Program.query.all()
    return render_template('index.html', clients=clients, programs=programs)

#login session
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['username'] = username
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

# logout session
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# Create a prohram
@app.route('/programs', methods=['POST'])
@login_required
def create_program():
    name = request.form.get('name')
    if not name:
        abort(400, 'Program name is required')
    if Program.query.filter_by(name=name).first():
        abort(400, 'Program already exists')
    new_program = Program(name=name)
    db.session.add(new_program)
    db.session.commit()
    return redirect(url_for('home'))

# register the client to the system
@app.route('/clients', methods=['POST'])
@login_required
def register_client():
    client_id = request.form.get('client_id')
    name = request.form.get('name')
    age = request.form.get('age')
    if not all([client_id, name, age]):
        abort(400, 'client_id, name, and age are required')
    if Client.query.filter_by(client_id=client_id).first():
        abort(400, 'Client already exists')
    new_client = Client(client_id=client_id, name=name, age=int(age))
    db.session.add(new_client)
    db.session.commit()
    return redirect(url_for('home'))

# code to enroll the client to a program
@app.route('/clients/<client_id>/enroll', methods=['POST'])
@login_required
def enroll_client(client_id):
    program_names = request.form.getlist('programs')
    client = Client.query.filter_by(client_id=client_id).first()
    if not client:
        abort(404, 'Client not found')
    if not program_names:
        abort(400, 'List of programs is required')
    for name in program_names:
        program = Program.query.filter_by(name=name).first()
        if not program:
            abort(400, f'Program "{name}" does not exist')
        if program not in client.programs:
            client.programs.append(program)
    db.session.commit()
    return redirect(url_for('home'))


# code to view client profile
@app.route('/clients/<client_id>', methods=['GET'])
@login_required
def view_client_profile(client_id):
    client = Client.query.filter_by(client_id=client_id).first()
    if not client:
        abort(404, 'Client not found')

    programs = Program.query.all()
    return render_template('client_profile.html', client=client, programs=programs)

# API endpoint to expose client profile
@app.route('/api/client/<client_id>', methods=['GET'])
def expose_client_api(client_id):
    client = Client.query.filter_by(client_id=client_id).first()
    if not client:
        abort(404, 'Client not found')
    return jsonify({
        'client_id': client.client_id,
        'name': client.name,
        'age': client.age,
        'enrolled_programs': [p.name for p in client.programs]
    })

if __name__ == '__main__':
    with app.app_context(): 
        db.create_all()
    app.run(debug=True)
