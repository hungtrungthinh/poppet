from flask import Blueprint,render_template,jsonify,request,current_app,abort,redirect,url_for
from flask_security import login_required,current_user,roles_accepted
from unifispot.extensions import db
from functools import wraps
from unifispot.base.utils.helper import register_api
from .models import Superadmin,Account
from .forms import UserForm,AccountForm,AdminForm
from .apis import AccountAPI,AdminAPI,NotificationAPI
from unifispot.base.utils.roles import superadmin_required,admin_required
from unifispot.admin.forms import SettingsForm

bp = Blueprint('superadmin', __name__,template_folder='templates')

register_api(bp,AccountAPI,'accounts_api','/accounts/api/',superadmin_required)
register_api(bp,AdminAPI,'admin_api','/admins/api/',superadmin_required)
register_api(bp,NotificationAPI,'notification_api','/notifications/api/',login_required)


@bp.route('/')
@superadmin_required
def superadmin_index( ):
    user_form = UserForm()
    return render_template('superadmin/dashboard.html',user_form=user_form)



@bp.route('/accounts')
@superadmin_required
def superadmin_accounts( ):
    user_form = UserForm()
    account_form = AccountForm()
    account_form.populate()
    return render_template('superadmin/accounts.html',user_form=user_form,account_form=account_form)


@bp.route('/admins')
@superadmin_required
def superadmin_admins( ):
    user_form = UserForm()
    admin_form = AdminForm()
    admin_form.populate()    
    return render_template('superadmin/admins.html',user_form=user_form,admin_form=admin_form)


@bp.route('/firstrun')
@admin_required
def firstrun( ):
    account = Account.query.filter_by(id=current_user.account_id).first()
    if not account:
        app.logger.error("No account found!! Something is wrong")
        abort(404)
    if account.firstrun != 1:
        #First time running
        return redirect(url_for('home'))    
    user_form = UserForm()
    settings_form = SettingsForm()


    return render_template('superadmin/firstrun.html',user_form=user_form,settings_form=settings_form)   
