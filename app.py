import os

from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
#from sqlalchemy import text
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wedding.db'
app.config['SECRET_KEY'] = 'your_secret_key'  # Change this to a random secret key
db = SQLAlchemy(app)


with app.app_context():
    # Check if the 'attending' column already exists
    result = db.session.execute(text("PRAGMA table_info(guest)"))
    columns = [row[1] for row in result.fetchall()]

    if 'attending' not in columns:
        db.session.execute(text('ALTER TABLE guest ADD COLUMN attending BOOLEAN DEFAULT NULL'))

    # Check if the 'diet_requirements' column already exists
    if 'diet_requirements' not in columns:
        db.session.execute(text('ALTER TABLE guest ADD COLUMN diet_requirements VARCHAR(100) DEFAULT NULL'))

    db.session.commit()
class Guest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    attending = db.Column(db.Boolean, default=None)
    diet_requirements = db.Column(db.String(100), nullable=True)

# Create the database tables
with app.app_context():
    db.create_all()

def create_test_user():
    with app.app_context():
        # Check if the user already exists
        existing_user = Guest.query.filter_by(email='test@example.com').first()

        if not existing_user:
            # User doesn't exist, so create and add the user
            test_user = Guest(name='Test User', email='test@example.com', password=generate_password_hash('testpassword'))
            db.session.add(test_user)
            db.session.commit()

create_test_user()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        guest = Guest.query.filter_by(email=email).first()

        if guest and check_password_hash(guest.password, password):
            session['guest_id'] = guest.id
            flash('Login successful', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'error')

    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'guest_id' in session:
        guest_id = session['guest_id']
        guest = Guest.query.get(guest_id)

        if request.method == 'POST':
            # Update attendance and diet requirements based on the form submission
            attending = request.form.get('attending')
            diet_requirements = request.form.get('diet_requirements')

            guest.attending = attending == 'accept'
            guest.diet_requirements = diet_requirements if attending == 'accept' else None

            db.session.commit()
            flash('Your response has been recorded', 'success')

        return render_template('dashboard.html', guest=guest)
    else:
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('guest_id', None)
    flash('You have been logged out', 'success')
    return redirect(url_for('login'))

if 'FLASK_ENV' in app.config and app.config['FLASK_ENV'] == 'production':
    import multiprocessing
    workers = multiprocessing.cpu_count() * 2 + 1
    bind_address = '0.0.0.0:5000'
    os.system(f"gunicorn -w {workers} -b {bind_address} app:app")
else:
    app.run(debug=True)
