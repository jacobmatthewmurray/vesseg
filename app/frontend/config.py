from os import environ, path
from dotenv import load_dotenv

basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, '.env')) 


class ProdConfig:
    """Basic Configuration."""

    SECRET_KEY = environ.get('SECRET_KEY')
    DATA_PATH = environ.get('DATA_PATH', '/data')
    REDIS_URL = environ.get('REDIS_URL') 
    REDIS_QUEUE = environ.get('REDIS_QUEUE', 'vesseg')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + path.join(DATA_PATH, 'db', 'vesseg.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False


class DevConfig:

    """Development Configuration."""

    SECRET_KEY = 'secret_key'

    DATA_PATH = '/Users/jacobmurray/projects/vesseg/data'
    
    REDIS_URL = 'redis://'
    REDIS_QUEUE = 'vesseg'

    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + path.join(DATA_PATH, 'db', 'vesseg.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True


