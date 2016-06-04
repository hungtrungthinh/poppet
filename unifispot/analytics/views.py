from flask import Blueprint,render_template,jsonify,request,current_app,abort
from flask_security import login_required,current_user,roles_accepted
from unifispot.extensions import db
from functools import wraps
from unifispot.base.utils.helper import register_api
from .models import Sitestat
from .apis import SitestatAPI


bp = Blueprint('analytics', __name__,template_folder='templates')

register_api(bp,SitestatAPI,'sitestats_api','/sitestas/api/',login_required)


