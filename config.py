import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.environ.get('SECRET_KEY', 'supersecretkey123')
DATABASE_URL = os.environ.get('DATABASE_URL', '').strip()
DATABASE_USER = os.environ.get('DB_USER', 'root')
DATABASE_PASSWORD = os.environ.get('DB_PASSWORD', '')
DATABASE_HOST = os.environ.get('DB_HOST', '127.0.0.1')
DATABASE_PORT = os.environ.get('DB_PORT') or '3306'
DATABASE_NAME = os.environ.get('DB_NAME', 'toplanches')
DATABASE_QUERY = os.environ.get('DB_QUERY', '').strip()
RESERVED_SYSTEM_SCHEMAS = {'sys', 'mysql', 'information_schema', 'performance_schema'}
HAS_DB_COMPONENTS = any(os.environ.get(key) for key in ('DB_HOST', 'DB_USER', 'DB_NAME', 'DB_PORT', 'DB_PASSWORD'))

if DATABASE_NAME.lower() in RESERVED_SYSTEM_SCHEMAS:
    DATABASE_NAME = 'toplanches'

if HAS_DB_COMPONENTS:
    encoded_user = quote_plus(DATABASE_USER)
    encoded_password = quote_plus(DATABASE_PASSWORD)
    encoded_name = quote_plus(DATABASE_NAME)
    database_base_uri = f'mysql+pymysql://{encoded_user}:{encoded_password}@{DATABASE_HOST}:{DATABASE_PORT}/{encoded_name}'
    DATABASE_URI = f'{database_base_uri}?{DATABASE_QUERY}' if DATABASE_QUERY else database_base_uri
elif DATABASE_URL:
    DATABASE_URI = DATABASE_URL
else:
    encoded_user = quote_plus(DATABASE_USER)
    encoded_password = quote_plus(DATABASE_PASSWORD)
    encoded_name = quote_plus(DATABASE_NAME)
    database_base_uri = f'mysql+pymysql://{encoded_user}:{encoded_password}@{DATABASE_HOST}:{DATABASE_PORT}/{encoded_name}'
    DATABASE_URI = f'{database_base_uri}?{DATABASE_QUERY}' if DATABASE_QUERY else database_base_uri

# Delivery fee rules example. Admin can change in the UI or in the database.
DEFAULT_DELIVERY_FEE = 5.00

# Supported roles
ROLE_ADMIN = 'admin'
ROLE_CLIENT = 'client'
ROLE_DELIVERY = 'delivery'
DEBUG = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
