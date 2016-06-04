from functools import wraps
from flask import request, Response,Blueprint,render_template,jsonify,current_app,abort,redirect,url_for,make_response,flash
from flask_security import login_required,current_user,roles_accepted
from unifispot.extensions import db
from unifispot.base.utils.helper import format_url
from unifispot.base.utils.roles import admin_required
from unifispot.base.utils.forms import print_errors,get_errors
from unifispot.guest.models import Guest
from unifispot.base.utils.helper import register_api
from unifispot.base.utils.email import send_email
from unifispot.const import *
from sqlalchemy import and_,or_
import arrow
from dateutil import tz

from .models import Admin
from .apis import SettingsAPI,ClientAPI,UserAPI,AccesspointAPI,DevicesAPI,AdminAPI
from .forms import SettingsForm,UserForm
from unifispot.guest.views import get_landing_page
from unifispot.guest.models import Guestsession
from unifispot.guest.forms import FacebookTrackForm,generate_emailform,generate_voucherform,generate_smsform

from unifispot.client.models import Wifisite,Landingpage,Voucher
from unifispot.client.forms import WifiSiteForm,LandingPageForm,SimpleLandingPageForm,LandingFilesForm,VoucherForm

bp = Blueprint('admin', __name__,template_folder='templates')

register_api(bp,SettingsAPI,'settings_api','/settings/api/',login_required)
register_api(bp,ClientAPI,'client_api','/client/api/',login_required)
register_api(bp,AdminAPI,'admin_api','/admins/api/',login_required)
register_api(bp,UserAPI,'user_api','/user/api/',login_required)
register_api(bp,AccesspointAPI,'ap_api','/ap/api/',login_required)
register_api(bp,DevicesAPI,'device_api','/device/api/',login_required)




@bp.route('/')
@admin_required
def admin_index( ):
    #get all the sites

    #get APs

    #get users

    user_form = UserForm()
    site_form = WifiSiteForm()
    site_form.populate()
    return render_template('admin/dashboard.html',user_form=user_form,site_form=site_form)

@bp.route('/settings')
@admin_required
def admin_settings( ):
    #get all the sites
    settingsform = SettingsForm()
    settingsform.populate()    

    user_form = UserForm()
    site_form = WifiSiteForm()
    site_form.populate()    
    return render_template('admin/settings.html',settingsform=settingsform,user_form=user_form,site_form=site_form)


@bp.route('/site/<int:site_id>')
@admin_required
def admin_site(site_id):
    wifisite = Wifisite.query.filter_by(id=site_id).first()
    if not wifisite:
        current_app.logger.error("Trying to access unknown site ID:%s"%request.url)
        abort(404)
    user_form = UserForm()    
    site_form = WifiSiteForm()
    site_form.populate()
    return render_template('admin/site.html',user_form=user_form,site_form=site_form,site_id=site_id,wifisite=wifisite)
    

@bp.route('/landing/<int:site_id>')
@admin_required
def admin_landing(site_id):
    wifisite = Wifisite.query.filter_by(id=site_id).first()
    if not wifisite:
        current_app.logger.error("Trying to access unknown site ID:%s"%request.url)
        abort(404)
    user_form = UserForm()    
    site_form = WifiSiteForm()
    site_form.populate()
    landingpageform = LandingPageForm()
    landingpageform.populate(site_id)    
    landingpageid = wifisite.default_landing
    simplelandingpageform = SimpleLandingPageForm()
    simplelandingpageform.populate()
    landingfilesform = LandingFilesForm()
    return render_template('admin/landing.html',user_form=user_form,site_form=site_form,site_id=site_id,
        landingpageform=landingpageform,landingpageid=landingpageid,simplelandingpageform=simplelandingpageform,
        landingfilesform=landingfilesform,wifisite=wifisite)

@bp.route('/preview/<int:site_id>')
@admin_required
def admin_landing_preview(site_id):
    wifisite = Wifisite.query.filter_by(id=site_id).first()
    if not wifisite:
        current_app.logger.error("Trying to access unknown site ID:%s"%request.url)
        abort(404)
    if wifisite.auth_method == AUTH_TYPE_EMAIL:
        email_form = generate_emailform(wifisite)
        return get_landing_page(site_id=site_id,email_form=email_form)
    elif wifisite.auth_method == AUTH_TYPE_SOCIAL:
        return get_landing_page(site_id=site_id,font_list=font_list,app_id=wifisite.fb_appid)
    elif wifisite.auth_method == AUTH_TYPE_VOUCHER:
        voucher_form = generate_voucherform(wifisite)
        return get_landing_page(site_id=site_id,font_list=font_list,voucher_form=voucher_form,wifisite=wifisite)
    elif wifisite.auth_method == AUTH_TYPE_SMS:
        sms_form = generate_smsform(wifisite)
        return get_landing_page(site_id=site_id,font_list=font_list,sms_form=sms_form,wifisite=wifisite)
    else:
        return get_landing_page(site_id=wifisite.id,landing_site=wifisite)        




@bp.route('/clients/')
@admin_required
def admin_clients():
    user_form = UserForm()    
    site_form = WifiSiteForm()
    site_form.populate()
    newuser_form = UserForm()
    newuser_form.populate()    
    return render_template('admin/clients.html',user_form=user_form,site_form=site_form,newuser_form=newuser_form)



@bp.route('/admins/')
@admin_required
def admin_admins():
    user_form = UserForm()    
    site_form = WifiSiteForm()
    site_form.populate()
    admin_form = UserForm()
    admin_form.populate()    
    return render_template('admin/admins.html',user_form=user_form,site_form=site_form,admin_form=admin_form)


@bp.route('/guestdata/<site_id>')
@admin_required
def client_data(site_id=None):
    #Validate SiteID
    wifisite        = Wifisite.query.filter_by(id=site_id).first()
    if not wifisite:
        current_app.logger.debug("Site Manage URL called with invalid paramters site_id:%s userid:%s"%(site_id,current_user.id))
        abort(404)
    
    user_form = UserForm()
    site_form = WifiSiteForm()
    site_form.populate()    
    today     = arrow.now()
    startdate = today.replace(days=1 - today.day).format('DD/MM/YYYY')
    enddate   = today.format('DD/MM/YYYY')    
    return render_template("admin/data.html",site_id=site_id,site_form=site_form,user_form=user_form,wifisite=wifisite,
        enddate=enddate,startdate=startdate)


@bp.route('/guestdata/<site_id>/download')
@admin_required
def admin_data_download(site_id=None):
    #Validate SiteID
    wifisite        = Wifisite.query.filter_by(id=site_id).first()
    if not wifisite:
        current_app.logger.debug("Site Manage URL called with invalid paramters site_id:%s userid:%s"%(site_id,current_user.id))
        abort(404)
    #get startdate and end date for filtering      
    r_startdate = request.values.get('startdate')
    r_enddate = request.values.get('enddate')
    today     = arrow.now()
    if r_startdate and r_enddate:
        startdate =  arrow.get(r_startdate,'DD/MM/YYYY')
        enddate =  arrow.get(r_enddate,'DD/MM/YYYY')            
    else:
        startdate = today.replace(days=1 - today.day)
        enddate = today.replace(days=1)    

    #get all entries within given period
    entries = Guest.query.filter(and_(Guest.site_id==wifisite.id,Guest.demo ==0, 
                    Guest.created_at >= startdate,Guest.created_at <= enddate)).all()

    csvList = '\n'.join(','.join(row.to_list()) for row in entries) 

    # We need to modify the response, so the first thing we 
    # need to do is create a response out of the CSV string
    response = make_response(csvList)
    # This is the key: Set the right header for the response
    # to be downloaded, instead of just printed on the browser
    response.headers["Content-Disposition"] = "attachment; filename=report.csv"
    return response

@bp.route('/vouchers/<site_id>')
@admin_required
def client_vouchers(site_id=None):
    #Validate SiteID
    wifisite        = Wifisite.query.filter_by(id=site_id).first()
    if not wifisite:
        current_app.logger.debug("Site Manage URL called with invalid paramters site_id:%s userid:%s"%(site_id,current_user.id))
        abort(404)

    user_form = UserForm()
    voucher_form = VoucherForm()
    voucher_form.populate()
    site_form = WifiSiteForm()
    site_form.populate()    
    return render_template("admin/vouchers.html",site_id=site_id,site_form=site_form,user_form=user_form,wifisite=wifisite,voucher_form=voucher_form)


@bp.route('/vouchers/<site_id>/print')
@admin_required
def client_print(site_id=None):
    #Validate SiteID
    wifisite        = Wifisite.query.filter_by(id=site_id).first()
    if not wifisite:
        current_app.logger.debug("Site Manage URL called with invalid paramters site_id:%s userid:%s"%(site_id,current_user.id))
        abort(404)
    if wifisite.account_id != current_user.account_id:
        current_app.logger.debug("User ID:%s trying to access Site ID:%s vouchers which donot belong to him"%(current_user.id,site_id))   
        abort(401)
    vouchers = Voucher.query.filter(and_(Voucher.site_id==site_id,Voucher.used == False)).all()
    return render_template("admin/print.html",vouchers=vouchers)


@bp.route('/guestsession/<site_id>')
@admin_required
def admin_sessions(site_id=None):
    #Validate SiteID
    wifisite        = Wifisite.query.filter_by(id=site_id).first()
    if not wifisite:
        current_app.logger.debug("Site Manage URL called with invalid paramters site_id:%s userid:%s"%(site_id,current_user.id))
        abort(404)
    
    user_form = UserForm()
    site_form = WifiSiteForm()
    site_form.populate()    
    today     = arrow.now()
    startdate = today.replace(days=1 - today.day).format('DD/MM/YYYY')
    enddate   = today.format('DD/MM/YYYY')    
    return render_template("admin/sessions.html",site_id=site_id,site_form=site_form,user_form=user_form,wifisite=wifisite,
        enddate=enddate,startdate=startdate)


@bp.route('/guestsession/<siteid>/download')
@admin_required
def admin_session_download(siteid=None):
    #Validate SiteID
    wifisite        = Wifisite.query.filter_by(id=siteid).first()
    if not wifisite:
        current_app.logger.debug("Site Manage URL called with invalid paramters site_id:%s userid:%s"%(site_id,current_user.id))
        abort(404)

    #get startdate and end date for filtering      
    r_startdate = request.values.get('startdate')
    r_enddate = request.values.get('enddate')
    today     = arrow.now(wifisite.timezone)
    if r_startdate and r_enddate:
        tzinfo = tz.gettz(wifisite.timezone)
        startdate =  arrow.get(r_startdate,'DD/MM/YYYY',tzinfo=tzinfo)
        enddate =  arrow.get(r_enddate,'DD/MM/YYYY',tzinfo=tzinfo)            
    else:
        startdate = today.replace(days=1 - today.day)
        enddate = today.replace(days=1)

    #get all entries within given period
    entries = Guestsession.query.filter(and_(Guestsession.site_id==wifisite.id, 
                    Guestsession.starttime >= startdate,Guestsession.starttime <= enddate)).all()

    csvList = '\n'.join(','.join(row.to_list()) for row in entries) 

    # We need to modify the response, so the first thing we 
    # need to do is create a response out of the CSV string
    response = make_response(csvList)
    # This is the key: Set the right header for the response
    # to be downloaded, instead of just printed on the browser
    response.headers["Content-Disposition"] = "attachment; filename=report.csv"
    return response