from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import io
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# PostgreSQL connection settings
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+pg8000://<USERNAME>:<PASSWORD>@<HOST>/<DATABASE_NAME>'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    student_id = db.Column(db.String(150), unique=True, nullable=False)

class Registration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course = db.Column(db.String(50), nullable=False)

ADMIN_USERNAME = 'klc'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username, password=password).first()
    if user:
        session['user_id'] = user.id
        session['username'] = user.username
        return redirect(url_for('courses'))
    else:
        return "Invalid credentials"

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        student_id = request.form['student_id']

        existing_user = User.query.filter((User.username == username) | (User.student_id == student_id)).first()
        if existing_user:
            flash("Username or Student ID already exists. Please try again with a different one.", "error")
            return redirect(url_for('signup'))

        new_user = User(username=username, password=password, name=name, student_id=student_id)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('signup.html')

@app.route('/courses')
def courses():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template('courses.html')

@app.route('/register_course', methods=['POST'])
def register_course():
    course = request.form['course']
    registration = Registration(user_id=session['user_id'], course=course)
    db.session.add(registration)
    db.session.commit()
    return "Registration Completed"

@app.route('/export')
def export():
    if 'user_id' not in session:
        return redirect(url_for('index'))

    user = User.query.get(session['user_id'])
    if user.username != ADMIN_USERNAME:
        return "Unauthorized access", 403

    registrations = Registration.query.all()
    data = [
        {
            'Student ID': User.query.get(reg.user_id).student_id,
            'Name': User.query.get(reg.user_id).name,
            'Course': reg.course,
            'Registration Time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        for reg in registrations
    ]
    df = pd.DataFrame(data)
    output = io.BytesIO()
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"registrations_{current_time}.xlsx"

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Registrations')
    output.seek(0)

    return send_file(output, download_name=filename, as_attachment=True)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
