from flask import Flask
from routes.auth import auth_bp
from routes.clients import client_bp
import os
from dotenv import load_dotenv
from flask_login import *
from supabase import create_client, Client
from routes.partners import partners_bp
from flask_wtf.csrf import CSRFProtect
from routes.expense import expense_bp
from waitress import  serve

# Load environment variables from .env file
load_dotenv()
csrf = CSRFProtect()
def create_app():
    app = Flask(__name__)
    
    # login_manager = LoginManager()
    # login_manager.login_view = 'routes.auth.login'  # Route name where users are redirected to login
    # login_manager.init_app(app)
 
    # Configuration settings
    app.config['SUPABASE_URL'] = os.getenv('SUPABASE_URL')
    app.config['SUPABASE_KEY'] = os.getenv('SUPABASE_KEY')
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')  # Required for session management
    
    # Register the authentication blueprint
  
    app.register_blueprint(expense_bp)

    app.register_blueprint(partners_bp)

    app.register_blueprint(auth_bp)
    app.register_blueprint(client_bp, url_prefix='/client')

    return app

if __name__ == '__main__':
    app = create_app()
    csrf.init_app(app)
    app.config['WTF_CSRF_ENABLED'] = False
    serve(app, host='0.0.0.0', port=8000)