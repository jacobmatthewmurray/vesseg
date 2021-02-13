from flask import Blueprint


bp = Blueprint('auth',
               __name__,
               template_folder='templates',
               static_folder='static',
               url_prefix='/auth')


from . import routes