import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.environ.get('SECRET_KEY', 'supersecretkey123')
DATABASE_USER = os.environ.get('DB_USER', 'root')
DATABASE_PASSWORD = os.environ.get('DB_PASSWORD', '')
DATABASE_HOST = os.environ.get('DB_HOST', '127.0.0.1')
DATABASE_PORT = os.environ.get('DB_PORT') or '3306'
DATABASE_NAME = os.environ.get('DB_NAME', 'toplanches')

DATABASE_URI = (
    f'mysql+pymysql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}'
)

# Delivery fee rules example. Admin can change in the UI or in the database.
DEFAULT_DELIVERY_FEE = 5.00

# Supported roles
ROLE_ADMIN = 'admin'
ROLE_CLIENT = 'client'
ROLE_DELIVERY = 'delivery'
DEBUG = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
