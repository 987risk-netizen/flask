from flask import Flask, render_template, request, flash, redirect, url_for, session
import mysql.connector
from datetime import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv


load_dotenv()

app = Flask(__name__, static_folder='static')


app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here-change-in-production')



MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'root')
MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE', 'zenathia_db')
MYSQL_PORT = int(os.environ.get('MYSQL_PORT', '3306'))


def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            port=MYSQL_PORT
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        return None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/registration')
def registration():

    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('registration.html')

@app.route('/register', methods=['POST'])
def register():

    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')
    

    if not name or not email or not password:
        flash('All fields are required!')
        return redirect(url_for('registration'))
    
    if password != confirm_password:
        flash('Passwords do not match!')
        return redirect(url_for('registration'))
    
    if len(password) < 6:
        flash('Password must be at least 6 characters long!')
        return redirect(url_for('registration'))
    

    hashed_password = generate_password_hash(password)
    

    try:
        connection = get_db_connection()
        if not connection:
            flash('Database connection failed!')
            return redirect(url_for('registration'))
            
        cursor = connection.cursor()
        

        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            flash('Email already registered! Please login.')
            cursor.close()
            connection.close()
            return redirect(url_for('registration'))
        

        query = """
            INSERT INTO users (name, email, password, created_at)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (name, email, hashed_password, datetime.now()))
        connection.commit()
        
        flash('Registration successful! Please login.')
        cursor.close()
        connection.close()
        return redirect(url_for('registration'))
        
    except mysql.connector.Error as err:
        flash(f'Registration failed: {err}')
        if connection:
            connection.close()
        return redirect(url_for('registration'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('registration'))
    
    try:
        connection = get_db_connection()
        if not connection:
            flash('Database connection failed!')
            return redirect(url_for('registration'))
            
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
        user = cursor.fetchone()
        cursor.close()
        connection.close()
        
        if not user:
            session.clear()
            return redirect(url_for('registration'))
            
        return render_template('dashboard.html', user=user)
        
    except mysql.connector.Error as err:
        flash(f'Error: {err}')
        return redirect(url_for('registration'))

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    
    if not email or not password:
        flash('Email and password are required!')
        return redirect(url_for('registration'))
    
    try:
        connection = get_db_connection()
        if not connection:
            flash('Database connection failed!')
            return redirect(url_for('registration'))
            
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        connection.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password!')
            return redirect(url_for('registration'))
            
    except mysql.connector.Error as err:
        flash(f'Login failed: {err}')
        return redirect(url_for('registration'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('registration'))

if __name__ == '__main__':
    app.run(debug=True)