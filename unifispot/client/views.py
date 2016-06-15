from flask import Blueprint,render_template,jsonify,request,current_app,abort,make_response,flash
from flask_security import login_required,current_user,roles_accepted
from unifispot.extensions import db
from functools import wraps
from unifispot.base.utils.helper import register_api
from unifispot.base.utils.roles import client_required
from sqlalchemy import and_,or_
import arrow
import io,csv
from dateutil import tz

from .apis import WifisiteAPI,SiteFileAPI,LandingPageAPI,GuestdataAPI,VoucherAPI,GuestsessionAPI
from .models import Wifisite,Landingpage,Sitefile,Voucher
from .forms import WifiSiteForm,LandingPageForm,VoucherForm

from unifispot.admin.forms import UserForm
from unifispot.guest.models import Guesttrack,Guest,Device,Guestsession

bp = Blueprint('client', __name__,template_folder='templates')


register_api(bp,WifisiteAPI,'wifisite_api','/site/api/',login_required)
register_api(bp,SiteFileAPI,'sitefile_api','/site/<int:siteid>/file/api/',login_required)
register_api(bp,LandingPageAPI,'landingpage_api','/site/<int:siteid>/landing/api/',login_required)
register_api(bp,VoucherAPI,'voucher_api','/site/<int:siteid>/voucher/api/',login_required)
register_api(bp,GuestdataAPI,'guestdata_api','/guestdata/api/',login_required)
register_api(bp,GuestsessionAPI,'guestsession_api','/guestsession/api/',login_required)





@bp.route('/')
@bp.route('/<siteid>')
@client_required
def client_index(siteid=None):

    #Validate SiteID
    if not siteid:
        wifisite        = Wifisite.query.filter_by(client_id=current_user.id).first()
        if not wifisite:
            flash('No Site configured for client')
            abort(404) 
        siteid          = wifisite.id
    else:
        wifisite        = Wifisite.query.filter_by(id=siteid).first()
        if not wifisite or wifisite.client_id != current_user.id:
            current_app.logger.debug("Site Manage URL called with invalid paramters siteid:%s userid:%s"%(siteid,current_user.id))
            abort(404)

    site_count = Wifisite.query.filter_by(client_id=current_user.id).count()
    visit_count = Guesttrack.query.filter_by(site_id=wifisite.id).count()
    user_form = UserForm()
    site_form = WifiSiteForm()
    site_form.populate()
    
    return render_template("client/dashboard.html",siteid=siteid,user_form=user_form,site_form=site_form,site_count=site_count,visit_count=visit_count,wifisite=wifisite)



  
@bp.route('/guestdata')
@bp.route('/guestdata/<siteid>')
@client_required
def client_data(siteid=None):
    #Validate SiteID
    if not siteid:
        wifisite        = Wifisite.query.filter_by(client_id=current_user.id).first()
        siteid          = wifisite.id
    else:
        wifisite        = Wifisite.query.filter_by(id=siteid).first()
        if not wifisite or wifisite.client_id != current_user.id:
            current_app.logger.debug("Site Manage URL called with invalid paramters siteid:%s userid:%s"%(siteid,current_user.id))
            abort(404)
    
    user_form = UserForm()
    today     = arrow.now()
    startdate = today.replace(days=1 - today.day).format('DD/MM/YYYY')
    enddate   = today.format('DD/MM/YYYY')
    return render_template("client/data.html",siteid=siteid,user_form=user_form,wifisite=wifisite,enddate=enddate,startdate=startdate)

@bp.route('/guestdata/<siteid>/download')
@client_required
def client_data_download(siteid=None):
    #Validate SiteID
    wifisite        = Wifisite.query.filter_by(id=siteid).first()
    if not wifisite or wifisite.client_id != current_user.id:
        current_app.logger.debug("Site Manage URL called with invalid paramters siteid:%s userid:%s"%(siteid,current_user.id))
        abort(404)

    #get startdate and end date for filtering      
    r_startdate = request.values.get('startdate')
    r_enddate = request.values.get('enddate')
    tzinfo = tz.gettz(wifisite.timezone)
    today     = arrow.now(tzinfo)
    if r_startdate and r_enddate:        
        startdate =  arrow.get(r_startdate,'DD/MM/YYYY',tzinfo=tzinfo)
        enddate =  arrow.get(r_enddate,'DD/MM/YYYY',tzinfo=tzinfo)            
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

@bp.route('/vouchers')
@bp.route('/vouchers/<siteid>')
@client_required
def client_vouchers(siteid=None):
    #Validate SiteID
    if not siteid:
        wifisite        = Wifisite.query.filter_by(client_id=current_user.id).first()
        siteid          = wifisite.id
    else:
        wifisite        = Wifisite.query.filter_by(id=siteid).first()
        if not wifisite or wifisite.client_id != current_user.id:
            current_app.logger.debug("Site Manage URL called with invalid paramters siteid:%s userid:%s"%(siteid,current_user.id))
            abort(404)
    
    user_form = UserForm()
    voucher_form = VoucherForm()
    voucher_form.populate()
    
    return render_template("client/vouchers.html",siteid=siteid,user_form=user_form,wifisite=wifisite,voucher_form=voucher_form)


@bp.route('/vouchers/<siteid>/print')
@client_required
def client_print(siteid=None):
    #Validate SiteID
    wifisite        = Wifisite.query.filter_by(id=siteid).first()
    if not wifisite or wifisite.client_id != current_user.id:
        current_app.logger.debug("Site Manage URL called with invalid paramters siteid:%s userid:%s"%(siteid,current_user.id))
        abort(404)
    vouchers = Voucher.query.filter(and_(Voucher.site_id==siteid,Voucher.used == False)).all()
    print vouchers
    return render_template("client/print.html",vouchers=vouchers)

@bp.route('/guestsession')
@bp.route('/guestsession/<siteid>')
@client_required
def client_session(siteid=None):
    #Validate SiteID
    if not siteid:
        wifisite        = Wifisite.query.filter_by(client_id=current_user.id).first()
        siteid          = wifisite.id
    else:
        wifisite        = Wifisite.query.filter_by(id=siteid).first()
        if not wifisite or wifisite.client_id != current_user.id:
            current_app.logger.debug("Site Manage URL called with invalid paramters siteid:%s userid:%s"%(siteid,current_user.id))
            abort(404)
    
    user_form = UserForm()
    today     = arrow.now()
    startdate = today.replace(days=1 - today.day).format('DD/MM/YYYY')
    enddate   = today.format('DD/MM/YYYY')
    return render_template("client/sessions.html",siteid=siteid,user_form=user_form,wifisite=wifisite,enddate=enddate,startdate=startdate)



@bp.route('/guestsession/<siteid>/download')
@client_required
def client_session_download(siteid=None):
    #Validate SiteID
    wifisite        = Wifisite.query.filter_by(id=siteid).first()
    if not wifisite or wifisite.client_id != current_user.id:
        current_app.logger.debug("Site Manage URL called with invalid paramters siteid:%s userid:%s"%(siteid,current_user.id))
        abort(404)

    #get startdate and end date for filtering      
    r_startdate = request.values.get('startdate')
    r_enddate = request.values.get('enddate')
    today     = arrow.now(wifisite.timezone)
    if r_startdate and r_enddate:
        tzinfo = tz.gettz(wifisite.timezone)
        startdate =  arrow.get(r_startdate,'DD/MM/YYYY',tzinfo=tzinfo).floor('day')
        enddate =  arrow.get(r_enddate,'DD/MM/YYYY',tzinfo=tzinfo).ceil('day')            
    else:
        startdate = today.replace(days=1 - today.day).floor('day')
        enddate = today.replace(days=1).ceil('day') 

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