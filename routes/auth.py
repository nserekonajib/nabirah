from flask import Blueprint, request, redirect, url_for, flash, render_template, session
from supabase import create_client, Client
import os
from dotenv import load_dotenv
from functools import wraps

load_dotenv()

# Initialize Supabase client
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

auth_bp = Blueprint('auth', __name__)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Please login first.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/')
@login_required
def index():
    return redirect(url_for('auth.dashboard'))

@auth_bp.route('/dashboard')
@login_required
def dashboard():
    user_data = session.get('user')
    return render_template('dashboard.html', user=user_data)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('auth.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            user = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if user:
                session['user'] = {
                    'email': user.user.email,
                    'id': user.user.id,
                    'access_token': user.session.access_token
                }
                flash('Login successful!', 'success')
                return redirect(url_for('auth.dashboard'))
        except Exception as e:
            flash('Login failed. Please check your credentials.', 'danger')
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user' in session:
        return redirect(url_for('auth.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            user = supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            
            if user:
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('auth.login'))
        except Exception as e:
            flash('Registration failed. Please try again.', 'danger')
    
    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    supabase.auth.sign_out()
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))