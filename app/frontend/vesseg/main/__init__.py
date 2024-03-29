from flask import Blueprint, redirect, url_for, request
from flask_login import current_user

bp = Blueprint('main', __name__, template_folder='templates', static_folder='static')

@bp.before_request
def restrict_to_users():
    if not current_user.is_authenticated:
        if request.path.startswith('/download'):
            pass 
        else:
            return redirect(url_for('auth.login'))

from . import routes