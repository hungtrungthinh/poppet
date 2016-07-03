from flask import Blueprint,render_template,jsonify,request,current_app,abort,redirect,url_for,flash
from functools import wraps
from sqlalchemy import and_,or_
import uuid
from functools import wraps
from facebook import get_user_from_cookie, GraphAPI
from .newcontroller import Controller
import datetime,time
import random
import arrow
from .models import Guest,Device,Guestsession,Guesttrack,Facebookauth,Smsdata
from .forms import FacebookTrackForm,generate_emailform,generate_voucherform,generate_smsform,PhonenumberForm
from .forms import CheckinForm
from unifispot.client.models import Landingpage
from unifispot.const import *
from unifispot.extensions import db
from unifispot.base.utils.helper import format_url
from unifispot.base.utils.forms import print_errors,get_errors
from unifispot.admin.models import Admin
from unifispot.superadmin.models import Account
from unifispot.tasks import celery_export_api,celery_send_sms
from unifispot.client.models import Wifisite,Voucher
from functools import wraps
import urllib
import validators
from urlparse import urlparse,parse_qs

bp = Blueprint('guest', __name__,template_folder='templates')



@bp.route('/s/<site_id>/',methods = ['GET', 'POST'])
def guest_portal(site_id):

    #-----code to handle CNA requests
    #If CNA bypassing is needed (Social authentication/Advertisement options enabled)
    #check for User agent and return success page if its CNA request
    #add logging as well

    #--get all URL parameters, expected URL format--
    device_mac = request.args.get('id')
    ap_mac   = request.args.get('ap')   
    orig_url = request.args.get('url')   
    demo     = request.args.get('demo')
    utcnow   = arrow.utcnow().naive
  
    if not device_mac or not ap_mac:
        current_app.logger.error("Guest portal called with empty ap_mac/user_mac URL:%s"%request.url)
        abort(404)
    landing_site    = None
    landing_site    = Wifisite.query.filter_by(unifi_id=site_id).first()
    if not landing_site:
        current_app.logger.error("Guest portal called with unknown UnifiID URL:%s"%request.url)
        abort(404)       

    #apple CNA bypass
    if landing_site.fb_login_en():
        ua = request.headers.get('User-Agent')
        if ua and 'CaptiveNetworkSupport' in ua:
            current_app.logger.debug('Wifiguest Log - Site ID:%s apple CNA detected, serve success page Guest with MAC:%s just visited from AP:%s'%(landing_site.id,device_mac,ap_mac))
            return '''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2//EN"><HTML><HEAD>
                        <TITLE>Success</TITLE></HEAD><BODY>Success</BODY></HTML>'''

    current_app.logger.debug('Wifiguest Log - Site ID:%s guest_portal Guest with MAC:%s just visited from AP:%s'%(landing_site.id,device_mac,ap_mac))
    ##-----------check for number of hits allowed per account TODO

    guest_device = None
    #create guest tracking entry
    track_id = str(uuid.uuid4())
    guest_track = Guesttrack(ap_mac=ap_mac,device_mac=device_mac,site=landing_site,state=GUESTRACK_INIT,orig_url=orig_url,track_id=track_id)
    if demo:
        guest_track.demo = 1
    db.session.add(guest_track)
    landing_site.guesttracks.append(guest_track)    

    #Check if the device was ever logged
    guest_device =  Device.query.filter(and_(Device.mac==device_mac,Device.site_id==landing_site.id)).first()
    #check for guest device
    if not guest_device:
        #device was never logged, create a new device and add a session
        guest_device = Device(mac=device_mac,site=landing_site,state=DEVICE_INIT)
        landing_site.devices.append(guest_device)
        if demo:
            guest_device.demo = 1            
        db.session.add(guest_device)
    db.session.commit()
    #session exists


    ###---------------TODO ADD Date/Time Limiting Code here----------------------------------------

    ###--------------Handle SCAN2LOGIN
    if landing_site.voucher_login_en() and orig_url and  validate_scan2login(orig_url):
        #get and validate voucher code
        return redirect(url_for('guest.scan2_login',track_id=guest_track.track_id),code=302) 
    

    ###----------------Code to show landing page------------------------------------------------------
    if landing_site.auth_method == AUTH_TYPE_EMAIL:
        #AUTH mode is set to email show the landing page with configured landing page
        return redirect(url_for('guest.email_login',track_id=guest_track.track_id),code=302)
  
    elif landing_site.auth_method == AUTH_TYPE_VOUCHER:
        #AUTH mode is set to voucher
        return redirect(url_for('guest.voucher_login',track_id=guest_track.track_id),code=302)  

    elif landing_site.auth_method == AUTH_TYPE_SOCIAL:
        #AUTH mode is set to voucher       
        return redirect(url_for('guest.social_login',track_id=guest_track.track_id),code=302)    

    elif landing_site.auth_method == AUTH_TYPE_SMS:
        #AUTH mode is set to voucher       
        return redirect(url_for('guest.sms_login',track_id=guest_track.track_id),code=302) 
               
    else:
        return redirect(url_for('guest.multi_login',track_id=guest_track.track_id),code=302) 


def validate_track(f):
    '''Decorator for validating guesttrack detials. It returns guest_track,wifisite and device objects

    '''
    @wraps(f)
    def decorated_function(*args, **kwargs):

        track_id=  kwargs.get('track_id')
        #get the function name used 
        fname = f.func_name
        #get and validated guesttrack
        guest_track = Guesttrack.query.filter_by(track_id=track_id).first()
        if not guest_track:
            current_app.logger.error("Called %s with wrong track ID:%s URL:%s"%(fname,track_id,request.url))
            abort(404)
        kwargs['guest_track'] = guest_track
        #get and validate wifisite
        landing_site = Wifisite.query.filter_by(id=guest_track.site_id).first()
        if not landing_site:
            current_app.logger.error("Called %s with trackid:%s not connected to any site URL:%s"%(fname,track_id,request.url))
            abort(404)  
        kwargs['landing_site'] = landing_site
        #get and validate device
        guest_device = Device.query.filter(and_(Device.site_id==landing_site.id,Device.mac==guest_track.device_mac)).first()
        if not guest_device:
            current_app.logger.error("Called %s with trackid:%s not connected to any device URL:%s"%(fname,track_id,request.url))
            abort(404)     
        kwargs['guest_device'] = guest_device     
        current_app.logger.debug('Wifiguest Log - Site ID:%s guest_device MAC:%s just visited %s'%(landing_site.id,guest_track.device_mac,request.url))

        #check if SMS validate enabled in this and do the needed validations
        if landing_site.smsauth and fname != 'authenticate_sms' and fname !='sms_send' \
                and guest_device.sms_confirm==0 and guest_device.demo==0:
            current_app.logger.debug('Wifiguest Log - Site ID:%s guest_device MAC:%s device not connected to phone number'%(landing_site.id,guest_track.device_mac))
            return redirect(url_for('guest.authenticate_sms',track_id=guest_track.track_id),code=302) 
  

        return f(*args, **kwargs)
    return decorated_function

def validate_datause(f):
    '''Decorator for validating datause. It aborts a request if monthly data limit is above limit

    '''
    #Validate that client is trying to view only the sites owned by him
    @wraps(f)
    def decorated_function(*args, **kwargs):
        guest_device = kwargs.get('guest_device')
        landing_site = kwargs.get('landing_site')
        if not guest_device or not landing_site:
            current_app.logger.error("Called validate_datause wihtout guest_device/landing_site ")
            abort(404)     
        if landing_site.enable_session_limit and guest_device.get_monthly_usage() >= landing_site.monthly_data_limit:
            current_app.logger.debug('Wifiguest Log - Site ID:%s guest_device MAC:%s exceeded the monthly data limit:%s'%(landing_site.id,guest_device.mac,landing_site.monthly_data_limit))
            return 'Looks like you have exceed your monthly free bandwidth'
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/auth/guest/<track_id>')
@validate_track
def authorize_guest(track_id,guest_track,landing_site,guest_device):
    '''Function called after respective auth mechanisms are completed
    
       This function send API commands to controller, redirect user to correct URL
    '''   

    #validate guest_track
    if  not guest_track.is_authorized():
        current_app.logger.error('Wifiguest Log - Site ID:%s guest_device MAC:%s tried to \
            %s without being authorized'%(landing_site.id,guest_track.device_mac,request.url))
        flash("Something went wrong, please try again")
        return redirect(url_for('guest.multi_login',track_id=guest_track.track_id),code=302)
    
    speed_ul = 0
    speed_dl = 0
    bytes_t  = 0
    
    if guest_track.state == GUESTRACK_VOUCHER_AUTH:
        voucher = Voucher.query.filter(and_(Voucher.id ==guest_device.voucher_id,Voucher.site_id==landing_site.id)).first()
        if not voucher:
            current_app.logger.error('Wifiguest Log - Site ID:%s guest_device MAC:%s tried to \
                %s with GUESTRACK_VOUCHER_AUTH but no proper voucher '%(landing_site.id,guest_track.device_mac,request.url))
            flash("Something went wrong, please try again")
            return redirect(url_for('guest.multi_login',track_id=guest_track.track_id),code=302)
        duration = guest_track.duration
        speed_ul = voucher.speed_ul or 0
        speed_dl = voucher.speed_dl or 0
        bytes_t  = voucher.data_available()
    else:
        duration = landing_site.session_timelimit or 60   
        if landing_site.enable_session_limit:
            bytes_t = landing_site.daily_data_limit    


    #create a new session
    guest_session = Guestsession(site=landing_site,device=guest_device)
    guest_session.state = guest_track.state
    guest_session.mac   = guest_device.mac
    guest_session.guesttracks.append(guest_track)
    db.session.add(guest_session)
    guest_track.session_id = guest_session.id   
    if guest_track.state == GUESTRACK_VOUCHER_AUTH:
        voucher.sessions.append(guest_session)
        guest_session.voucher_id = voucher.id

    db.session.commit()

    if not current_app.config['NO_UNIFI'] :
        #code to send auth command to controller
        account = Account().query.filter_by(id=guest_session.site.account_id).first()
        settings = account.get_settings()
        try:
            c =  Controller(settings['unifi_server'], settings['unifi_user'], settings['unifi_pass'],'8443','v4',guest_track.site.unifi_id)       
            c.authorize_guest(guest_track.device_mac,duration,ap_mac=guest_track.ap_mac,up_bandwidth=speed_ul,
                down_bandwidth=speed_dl,byte_quota=bytes_t)    
        except:
            current_app.logger.exception('Wifiguest Log - Site ID:%s guest_device MAC:%s tried to \
                %s with  but exception while connecting to controller '%(landing_site.id,guest_track.device_mac,request.url))
            abort(500)


    #time.sleep(5)
    #Code to handle guest after successful login 
    
    #if guest_track.site.redirect_method == REDIRECT_ORIG_URL and guest_track.orig_url:
        #return redirect(format_url(guest_track.orig_url),code=302)
    #elif guest_track.site.redirect_url:
        #redirect User to default URL if configured
       # return redirect(format_url(guest_track.site.redirect_url),code=302)
    #else:
        #redirect user to google.com
    redirect_url    = landing_site.redirect_url or 'http://www.unifispot.com'
    landing_page    = Landingpage.query.filter_by(id=landing_site.default_landing).first()
    return render_template('guest/%s/show_message.html'%landing_site.template,landing_site=landing_site,landing_page=landing_page,redirect_url=redirect_url)

@bp.route('/tempauth/guest/<track_id>')
def temp_authorize_guest(track_id):
    '''Function for giving temporary internet access for a client, if TEMP_LOGIN_ENABLED set to True
    
       This function send API commands to controller, return ok
    '''
    if not current_app.config['TEMP_LOGIN_ENABLED']:
        return jsonify({'status':1,'msg': "TEMP Login Disabled"})

    #can't use validate_track as return values needed to be json objects
    guest_track = Guesttrack.query.filter_by(track_id=track_id).first()
    if not guest_track :
        current_app.logger.error("Called temp_authorize_guest with wrong track ID:%s"%track_id)
        return jsonify({'status':0,'msg': "Error"})
        
    if not guest_track.is_temp_authorized():
        current_app.logger.error("Called temp_authorize_guest with not authorized track ID:%s"%track_id)
        return jsonify({'status':0,'msg': "Error"})      

    landing_site = Wifisite.query.filter_by(id=guest_track.site_id).first()
    guest_device = Device.query.filter(and_(Device.site_id==landing_site.id,Device.mac==guest_track.device_mac)).first()


    current_app.logger.debug('Wifiguest Log - Site ID:%s temp_authorize_guest for MAC:%s'%(guest_track.site_id,guest_track.device_mac))
    #prevent misuse
    if guest_device.get_monthly_usage() >= landing_site.monthly_data_limit:
        current_app.logger.debug('Wifiguest Log - Site ID:%s guest_device MAC:%s exceeded the monthly data limit:%s'%(landing_site.id,guest_device.mac,landing_site.monthly_data_limit))
        return jsonify({'status':0,'msg': "Looks like you have exceed your monthly free bandwidth"})  
    #get all guest_tracks in last 5hrs
    last5hrs = arrow.utcnow().replace(hours=-5).naive
    tracks = Guesttrack.query.filter(and_(Guesttrack.site_id==guest_track.site_id,Guesttrack.device_mac==guest_track.device_mac,
                Guesttrack.timestamp>=last5hrs)).all()
    total_attemps = 0
    for track in tracks:
        total_attemps += track.temp_login

    if total_attemps >= 5 and guest_track.demo != 1 : 
        current_app.logger.info('Wifiguest Log - Site ID:%s temp_authorize_guest max tries reached for MAC:%s'%(guest_track.site_id,guest_track.device_mac))
        return jsonify({'status':0,'msg': "You have already used up temporary logins for today"})
    else:
        guest_track.temp_login += 1
        db.session.commit()
    #create a new session
    guest_session = Guestsession(site=landing_site,device=guest_device)
    guest_session.state = guest_track.state
    guest_session.mac   = guest_device.mac
    guest_session.guesttracks.append(guest_track)
    db.session.add(guest_session)
    guest_track.session_id = guest_session.id    
    db.session.commit()
    #get details from track ID and authorize
    if not current_app.config['NO_UNIFI'] :
        account = Account().query.filter_by(id=guest_session.site.account_id).first()
        settings = account.get_settings()   

        try:
            c =  Controller(settings['unifi_server'], settings['unifi_user'], settings['unifi_pass'],'8443','v4',guest_track.site.unifi_id)  
            c.authorize_guest(guest_track.device_mac,5,ap_mac=guest_track.ap_mac)    
        except:
            current_app.logger.exception('Exception occured while trying to authorize User')
            return jsonify({'status':0,'msg': "Error!!"})


        return jsonify({'status':1,'msg': "DONE"})
    else:
        return jsonify({'status':1,'msg': "DEBUG enabled"})

@bp.route('/social/guest/<track_id>',methods = ['GET', 'POST'])
@validate_track
@validate_datause
def social_login(track_id,guest_track,landing_site,guest_device):
    ''' Function to called if the site is configured with Social login    
    
    '''
    #
    #
    current_app.logger.debug('Wifiguest Log - Site ID:%s social_login for track ID:%s'%(guest_track.site_id,guest_track.id))
    #Check if the device already has a valid auth
    #if  guest_device.state == DEVICE_AUTH  and guest_device.demo == 0:
    #    #Device has a guest element and is authorized
    #    guest_track.state   = GUESTRACK_PREAUTH
    #    db.session.commit()
    #    #redirect to authorize_guest
    #    current_app.logger.debug('Wifiguest Log - Site ID:%s social_login for track ID:%s Device already authorized, #redirect to authorize_guest'%(guest_track.site_id,guest_track.id))
    #    return redirect(url_for('guest.authorize_guest',track_id=guest_track.track_id),code=302)
    #else:
    #show the configured landing page
    #social login should always be perfomed
    guest_track.state = GUESTRACK_SOCIAL_PREAUTH
    db.session.commit()       
    if landing_site.fb_appid:
        fb_appid= landing_site.fb_appid
    else:
        fb_appid = current_app.config['FB_APP_ID']
    landing_page = Landingpage.query.filter_by(id=landing_site.default_landing).first()
    return render_template('guest/%s/social_landing.html'%landing_site.template,landing_site=landing_site,landing_page=landing_page,app_id=fb_appid,track_id=track_id)   
        
@bp.route('/facebook/check/<track_id>/',methods = ['GET', 'POST'])
@validate_track
@validate_datause
def facebook_login(track_id,guest_track,landing_site,guest_device):
    ''' Function to called after guest has logged in using JS/oauth

    '''
    code  = request.args.get('code')
    access_token = None
    fb_appid = landing_site.fb_appid or current_app.config['FB_APP_ID']   
    fb_app_secret = landing_site.fb_app_secret or current_app.config['FB_APP_SECRET']    
    if code:
        #URL called after OAuth
        redirect_uri = url_for('guest.facebook_login',track_id=track_id,_external=True)
        try:
            at  = GraphAPI().get_access_token_from_code(code, redirect_uri, fb_appid, fb_app_secret)
            access_token = at['access_token']
            graph = GraphAPI(access_token)
            profile = graph.get_object("me",fields='name,email,first_name,last_name,gender,birthday')
            if not profile:
                #
                #User is not logged into DB app, redirect to social login page
                current_app.logger.debug('Wifiguest Log - Site ID:%s guest_device MAC:%s facebook_login  empty profile, redirecting to social_login %s'%(landing_site.id,guest_track.device_mac,request.url))            
                return redirect(url_for('guest.multi_login',track_id=track_id),code=302)
        except:
            current_app.logger.exception('Wifiguest Log - Site ID:%s guest_device MAC:%s facebook_login exception while getting access_token redirecting to social_login %s'%(landing_site.id,guest_track.device_mac,request.url))            
            return redirect(url_for('guest.multi_login',track_id=track_id),code=302)
        
    else:
        #URL could be called by JS, check for cookies
        #
        try:
            check_user_auth = get_user_from_cookie(cookies=request.cookies, app_id=fb_appid,app_secret=fb_app_secret)
            access_token = check_user_auth['access_token']
            graph = GraphAPI(access_token) 
            profile = graph.get_object("me",fields='name,email,first_name,last_name,gender,birthday')
            if not check_user_auth or not check_user_auth['uid'] or not profile:
                #
                #User is not logged into DB app, redirect to social login page
                current_app.logger.debug('Wifiguest Log - Site ID:%s guest_device MAC:%s facebook_login  Used not logged in, redirecting to social_login %s'%(landing_site.id,guest_track.device_mac,request.url))            
                return redirect(url_for('guest.multi_login',track_id=track_id),code=302)
        except:
            current_app.logger.exception('Wifiguest Log - Site ID:%s guest_device MAC:%s facebook_login exception while get_user_from_cookie redirecting to social_login %s'%(landing_site.id,guest_track.device_mac,request.url))            
            return redirect(url_for('guest.multi_login',track_id=track_id),code=302)

    #check this FB profile already added into our DB,else add it
    profile_check = Facebookauth.query.filter(and_(Facebookauth.profile_id==profile['id'],Facebookauth.site_id==landing_site.id)).first()
    if not profile_check:
        profile_check = Facebookauth()
        profile_check.profile_id    = profile['id']
        profile_check.token         = access_token
        profile_check.site = landing_site
        db.session.add(profile_check)
        db.session.commit()
        current_app.logger.debug('Wifiguest Log - Site ID:%s facebook_login  adding new FB profile ID:%s for track ID:%s'%(guest_track.site_id,profile_check.id,guest_track.id))
    else:
        #update access token
        profile_check.token         = access_token
        
        db.session.commit()
        current_app.logger.debug('Wifiguest Log - Site ID:%s facebook_login  already added FB profile ID:%s for track ID:%s'%(guest_track.site_id,profile_check.id,guest_track.id))
    #profile already added to DB, check if the user had already authorized the site
    guest_check = Guest.query.filter(and_(Guest.site_id==landing_site.id,Guest.fb_profile==profile_check.id)).first()
    if not guest_check:
        guest_check = Guest()
        guest_check.firstname   = profile.get('first_name')
        guest_check.lastname    = profile.get('last_name')
        guest_check.email       = profile.get('email')       
        gender                  = profile.get('gender')
        if gender:
            guest_check.gender  = 1 if gender == 'male' else 2
        dob                     = profile.get('birthday')
        if dob:
            #convert MM-DD-YYY to DD-MM-YYYY
            guest_check.dob = arrow.get(dob,'MM/DD/YYYY').format('DD/MM/YYYY')

        guest_check.site_id     = landing_site.id
        guest_check.facebookauth = profile_check           
        profile_check.guests.append(guest_check)
        db.session.add(guest_check)
        db.session.commit()
        #New guest added create task for API export
        celery_export_api.delay(guest_check.id)     
        current_app.logger.debug('Wifiguest Log - Site ID:%s facebook_login  adding new Guest:%s for track ID:%s'%(guest_track.site_id,guest_check.id,guest_track.id))       
    else:
        current_app.logger.debug('Wifiguest Log - Site ID:%s facebook_login  already added Guest:%s for track ID:%s'%(guest_track.site_id,guest_check.id,guest_track.id))          
    #
    #even if guest entry was already added, assign the guest to device
    guest_device.guest  = guest_check
    guest_check.devices.append(guest_device)
    db.session.commit()   
    #check if checkin is enabled and/or like is enabled
    if landing_site.auth_fb_post == 1:
        #redirect to checkin
        return redirect(url_for('guest.social_action_checkin',track_id=guest_track.track_id),code=302)
    elif landing_site.auth_fb_like == 1 and guest_check.fb_liked !=1:
        #redirect to like
        return redirect(url_for('guest.social_action_like',track_id=guest_track.track_id),code=302)
    else:
        #redirect to 
        #mark sessions as authorized
        guest_track.state   = GUESTRACK_SOCIAL_AUTH
        guest_device.state  = DEVICE_AUTH
        db.session.commit()
        return redirect(url_for('guest.authorize_guest',track_id=guest_track.track_id),code=302)

@bp.route('/facebook/checkin/<track_id>/',methods = ['GET', 'POST'])
@validate_track
@validate_datause
def social_action_checkin(track_id,guest_track,landing_site,guest_device):
    guest_check = Guest.query.filter_by(id=guest_device.guest_id,site_id=landing_site.id).first()    
    if not guest_check :
        current_app.logger.error('Wifiguest Log - Site ID:%s social_action_checkin  called with device not associated to guest for track ID:%s'%(guest_track.site_id,guest_track.id))
        return redirect(url_for('guest.multi_login',track_id=track_id),code=302)

    code  = request.args.get('code')
    access_token = None
    fb_appid = landing_site.fb_appid or current_app.config['FB_APP_ID']   
    fb_app_secret = landing_site.fb_app_secret or current_app.config['FB_APP_SECRET']
    redirect_uri = url_for('guest.social_action_checkin',track_id=track_id,_external=True)    
    if code:
        #URL called after OAuth        
        try:
            at  = GraphAPI().get_access_token_from_code(code, redirect_uri, fb_appid, fb_app_secret)
            access_token = at['access_token']
            graph = GraphAPI(access_token)
            permissions = graph.get_connections("me","permissions")
        except:
            current_app.logger.exception('Wifiguest Log - Site ID:%s guest_device MAC:%s social_action_checkin exception while getting access_token redirecting to social_action_checkin %s'%(landing_site.id,guest_track.device_mac,request.url))            
            return redirect(url_for('guest.social_action_checkin',track_id=track_id),code=302)
    else:
        profile_check = Facebookauth.query.filter_by(id=guest_check.fb_profile).first()

        if not profile_check :
            current_app.logger.error('Wifiguest Log - Site ID:%s social_action_checkin  called with device not associated to profile_check for track ID:%s'%(guest_track.site_id,guest_track.id))
            return redirect(url_for('guest.multi_login',track_id=track_id),code=302)
        try:
            graph = GraphAPI(profile_check.token)
            permissions = graph.get_connections("me","permissions")

        except:
            current_app.logger.exception('Wifiguest Log - Site ID:%s guest_device MAC:%s social_action_checkin exception while trying to get permissions %s'%(landing_site.id,guest_track.device_mac,request.url))            
            return redirect(url_for('guest.multi_login',track_id=track_id),code=302)

    #check if the user has granted publish_permissions
    publish_permission = False
    for perm in permissions['data']:
        if perm.get('permission') == 'publish_actions' and perm.get('status') == 'granted':    
            publish_permission = True

    if not publish_permission:
        current_app.logger.debug('Wifiguest Log - Site ID:%s social_action_checkin called without guest giving publish_permission redo Oauth track ID:%s'%(guest_track.site_id,guest_track.id))
        params={'client_id':fb_appid,'redirect_uri':redirect_uri,'scope':'publish_actions '}
        url = 'https://www.facebook.com/dialog/oauth?'+urllib.urlencode(params)
        return redirect(url,code=302)

    form1 = CheckinForm()

    if form1.validate_on_submit():
        #try to do checkin
        try:
            fb_page = landing_site.fb_page or current_app.config['FB_PAGE_URL'] 
            page_info = graph.get_object(fb_page,fields='description,name,location,picture')
            print page_info['id'] 
            print graph.put_wall_post(message=form1.message.data,attachment={'place':page_info['id']})
        except:
            current_app.logger.exception('Wifiguest Log - Site ID:%s social_action_checkin exception while checkinfor track ID:%s'%(guest_track.site_id,guest_track.id))
        else:
            guest_check = Guest.query.filter_by(id=guest_device.guest_id,site_id=landing_site.id).first()
            if not guest_check:
                current_app.logger.error('Wifiguest Log - Site ID:%s social_action_checkin  called with device not associated to guest for track ID:%s'%(guest_track.site_id,guest_track.id))
                abort(404)            
            guest_track.fb_posted   = 1
            guest_check.fb_posted   = 1
            db.session.commit()
            if landing_site.auth_fb_like == 1 and guest_check.fb_liked !=1:
                #redirect to like
                return redirect(url_for('guest.social_action_like',track_id=guest_track.track_id),code=302)
            else:
                guest_track.state       = GUESTRACK_SOCIAL_AUTH     
                guest_device.state  = DEVICE_AUTH  
                db.session.commit() 
                return redirect(url_for('guest.authorize_guest',track_id=guest_track.track_id),code=302)    



    # show page asking user to checkin
    current_app.logger.debug('Wifiguest Log - Site ID:%s social_action_checkin  new guest show page to checkin for track ID:%s'%(guest_track.site_id,guest_track.id))
    landing_page = Landingpage.query.filter_by(id=landing_site.default_landing).first()
    fb_page = landing_site.fb_page or current_app.config['FB_PAGE_URL'] 
    page_info = graph.get_object(fb_page,fields='location,name')     
    loc = page_info['location']
    location = ' %s - %s %s %s'%(page_info.get('name',''),loc.get('street',''),loc.get('city',''),loc.get('country',''))
    return render_template("guest/%s/fb_checkin.html"%landing_site.template,landing_page = landing_page,font_list=font_list,app_id=fb_appid,track_id=track_id,
        fb_page=fb_page,location=location,form1=form1)


@bp.route('/facebook/like/<track_id>',methods = ['GET', 'POST'])
@validate_track
@validate_datause
def social_action_like(track_id,guest_track,landing_site,guest_device):
    #fbtrackform = FacebookTrackForm()
    auth_like = None
    auth_post = None
    #if fbtrackform.validate_on_submit():
    if request.method == 'POST':
        auth_like = request.form['authlike']
        
    guest_check = Guest.query.filter_by(id=guest_device.guest_id,site_id=landing_site.id).first()
    if not guest_check:
        current_app.logger.error('Wifiguest Log - Site ID:%s social_action_like  called with device not associated to guest for track ID:%s'%(guest_track.site_id,guest_track.id))
        abort(404)
                
    if auth_like == '1' :
        #quick hack to test for liking and posting, guest has skipped the liking, allow
        #internet for now and ask next time
        current_app.logger.debug('Wifiguest Log - Site ID:%s social_action_like  guest decided to skip  like for track ID:%s'%(guest_track.site_id,guest_track.id))
    elif auth_like == '2':
        #user has liked the page mark track and guest as liked               
        current_app.logger.debug('Wifiguest Log - Site ID:%s social_action_like  guest liked now for track ID:%s'%(guest_track.site_id,guest_track.id))
        guest_track.fb_liked = 1
        guest_check.fb_liked = 1
        db.session.commit()
    else:
        # show page asking user to like
        current_app.logger.debug('Wifiguest Log - Site ID:%s social_action_like  new guest show page to like for track ID:%s'%(guest_track.site_id,guest_track.id))
        landing_page = Landingpage.query.filter_by(id=landing_site.default_landing).first()
        fb_page = landing_site.fb_page or current_app.config['FB_PAGE_URL']
        fb_appid = landing_site.fb_appid or current_app.config['FB_APP_ID']   
        return render_template("guest/%s/fb_like.html"%landing_site.template,landing_page = landing_page,font_list=font_list,app_id=fb_appid,track_id=track_id,fb_page=fb_page)

    #mark sessions as authorized
    guest_track.state   = GUESTRACK_SOCIAL_AUTH
    if guest_track.fb_liked == 1 : # if guest has full filled all the social login criterias,mark the device as authed
        guest_device.state  = DEVICE_AUTH
    db.session.commit()
    return redirect(url_for('guest.authorize_guest',track_id=guest_track.track_id),code=302)
    

@bp.route('/email/guest/<track_id>',methods = ['GET', 'POST'])
@validate_track
@validate_datause
def email_login(track_id,guest_track,landing_site,guest_device):
    ''' Function to called if the site is configured with Social login    
    
    '''    

    #Check if the device already has a valid auth
    if  guest_device.state == DEVICE_AUTH and guest_device.demo == 0:
        #Device has a guest element and is authorized
        guest_track.state   = GUESTRACK_PREAUTH
        db.session.commit()
        #redirect to authorize_guest
        return redirect(url_for('guest.authorize_guest',track_id=guest_track.track_id),code=302)
    else:
        #show the configured landing page
        email_form = generate_emailform(landing_site)
        if email_form.validate_on_submit():
            newguest = Guest()
            newguest.populate_from_email_form(email_form,landing_site.emailformfields)
            newguest.site = landing_site
            db.session.add(newguest)
            db.session.commit()
            #New guest added create task for API export
            celery_export_api.delay(newguest.id)
            guest_track.state   = GUESTRACK_EMAIL_AUTH
            guest_device.guest  = newguest
            newguest.demo       = guest_track.demo
            newguest.devices.append(guest_device)
            guest_device.state  = DEVICE_AUTH
            db.session.commit()
            current_app.logger.debug('Wifiguest Log - Site ID:%s email_login  new guest track ID:%s'%(guest_track.site_id,guest_track.id))
            return redirect(url_for('guest.authorize_guest',track_id=guest_track.track_id),code=302)
        landing_page = Landingpage.query.filter_by(id=landing_site.default_landing).first()
        return render_template('guest/%s/email_landing.html'%landing_site.template,landing_site=landing_site,landing_page=landing_page,email_form=email_form)   
        

@bp.route('/voucher/guest/<track_id>',methods = ['GET', 'POST'])
@validate_track
def voucher_login(track_id,guest_track,landing_site,guest_device):
    ''' Function to called if the site is configured with Voucher login    
    
    '''
        
    #Check if the device already has a valid auth
    if  guest_device.voucher_id and guest_device.demo == False:
        #Device has a voucher element and is authorized before
        #check if the voucher is valid still
        #get latest voucher 
        voucher = Voucher.query.filter(and_(Voucher.id==guest_device.voucher_id,Voucher.site_id==landing_site.id)).first()
        if voucher and voucher.check_validity() :
            guest_track.duration = voucher.time_available()
            guest_track.state   = GUESTRACK_VOUCHER_AUTH
            db.session.commit()
            #redirect to authorize_guest
            current_app.logger.debug('Wifiguest Log - Site ID:%s voucher_login MAC:%s already authenticated voucher for track ID:%s'%(guest_track.site_id,guest_device.mac,guest_track.id))
            return redirect(url_for('guest.authorize_guest',track_id=guest_track.track_id),code=302)
        else:
            current_app.logger.debug('Wifiguest Log - Site ID:%s voucher_login MAC:%s expired previous voucher for track ID:%s'%(guest_track.site_id,guest_device.mac,guest_track.id))
            guest_device.state = DEVICE_INIT
            db.session.commit()
            flash("Looks like your Voucher have expired", 'danger')
            
    voucher_form = generate_voucherform(landing_site)
    if voucher_form.validate_on_submit():
        #validate voucher
        voucher = Voucher.query.filter(and_(Voucher.site_id== landing_site.id,Voucher.voucher==voucher_form.voucher.data)).first()
        if voucher and voucher.uses_available() > 0 and voucher.check_validity():
            #valid voucher available
            newguest = Guest()
            newguest.populate_from_email_form(voucher_form,landing_site.emailformfields)
            newguest.site = landing_site
            db.session.add(newguest)
            db.session.commit()
            #New guest added create task for API export
            celery_export_api.delay(newguest.id)            
            #mark sessions as authorized
            guest_track.duration = voucher.time_available()
            guest_track.state   = GUESTRACK_VOUCHER_AUTH
            guest_device.guest  = newguest
            newguest.demo        = guest_track.demo
            newguest.devices.append(guest_device)
            voucher.devices.append(guest_device)
            guest_device.voucher_id = voucher.id
            voucher.used = True
            voucher.used_at = arrow.utcnow().naive
            guest_device.state  = DEVICE_VOUCHER_AUTH
            db.session.commit()
            current_app.logger.debug('Wifiguest Log - Site ID:%s voucher_login MAC:%s new guest:%s  for track ID:%s'%(guest_track.site_id,guest_device.mac,newguest.id,guest_track.id))           
            return redirect(url_for('guest.authorize_guest',track_id=guest_track.track_id),code=302)
        else:           
            current_app.logger.debug('Wifiguest Log - Site ID:%s voucher_login MAC:%s  in valid vouher value:%s for track ID:%s'%(guest_track.site_id,guest_device.mac,voucher_form.voucher.data,guest_track.id))
            flash(u'Invalid Voucher ID', 'danger')       
    
    landing_page = Landingpage.query.filter_by(id=landing_site.default_landing).first()
    return render_template('guest/%s/voucher_landing.html'%landing_site.template,landing_site=landing_site,landing_page=landing_page,voucher_form=voucher_form)   
    
@bp.route('/scan2login/guest/<track_id>',methods = ['GET', 'POST'])
@validate_track
def scan2_login(track_id,guest_track,landing_site,guest_device):
    ''' Function to called if voucher login is configured and scan2login URL is detected   
    
    '''
    #Check if the device already has a valid auth
    if  guest_device.voucher_id and guest_device.demo == False:
        #Device has a voucher element and is authorized before
        #check if the voucher is valid still
        #get latest voucher 
        voucher = Voucher.query.filter(and_(Voucher.id==guest_device.voucher_id,Voucher.site_id==landing_site.id)).first()
        if voucher and voucher.check_validity() :
            guest_track.duration = voucher.time_available()
            guest_track.state   = GUESTRACK_VOUCHER_AUTH
            db.session.commit()
            #redirect to authorize_guest
            current_app.logger.debug('Wifiguest Log - Site ID:%s voucher_login MAC:%s already authenticated voucher for track ID:%s'%(guest_track.site_id,guest_device.mac,guest_track.id))
            return redirect(url_for('guest.authorize_guest',track_id=guest_track.track_id),code=302)
        else:
            current_app.logger.debug('Wifiguest Log - Site ID:%s voucher_login MAC:%s expired previous voucher for track ID:%s'%(guest_track.site_id,guest_device.mac,guest_track.id))
            guest_device.state = DEVICE_INIT
            db.session.commit()
            flash("Looks like your Voucher have expired", 'danger')

    voucher_code = validate_scan2login(guest_track.orig_url)
    #validate voucher
    voucher = Voucher.query.filter(and_(Voucher.site_id==landing_site.id,Voucher.voucher==voucher_code)).first()
    if voucher and voucher.uses_available() > 0 and voucher.check_validity():
        #valid voucher available
        newguest = Guest()
        newguest.site = landing_site
        db.session.add(newguest)
        db.session.commit()           
        #mark sessions as authorized
        guest_track.duration = voucher.time_available()
        guest_track.state   = GUESTRACK_VOUCHER_AUTH
        guest_device.guest  = newguest
        newguest.demo        = guest_track.demo
        newguest.devices.append(guest_device)
        voucher.device_id = guest_device.id
        voucher.used = True
        voucher.used_at = arrow.utcnow().datetime
        guest_device.state  = DEVICE_VOUCHER_AUTH
        db.session.commit()
        current_app.logger.debug('Wifiguest Log - Site ID:%s voucher_login MAC:%s new guest:%s  for track ID:%s'%(guest_track.site_id,guest_device.mac,newguest.id,guest_track.id))           
        return redirect(url_for('guest.authorize_guest',track_id=guest_track.track_id),code=302)
    else:           
        current_app.logger.debug('Wifiguest Log - Site ID:%s voucher_login MAC:%s  in valid vouher value:%s for track ID:%s'%(guest_track.site_id,guest_device.mac,voucher_form.voucher.data,guest_track.id))
        flash(u'Invalid Voucher ID', 'danger')

    landing_page = Landingpage.query.filter_by(id=landing_site.default_landing).first()
    return render_template('guest/%s/voucher_landing.html'%landing_site.template,landing_site=landing_site,landing_page=landing_page,voucher_form=voucher_form)   


@bp.route('/sms/guest/<track_id>',methods = ['GET', 'POST'])
@validate_track
@validate_datause
def sms_login(track_id,guest_track,landing_site,guest_device):
    ''' Function to called if the site is configured with SMS login    
    
    '''     
    sms_form = generate_smsform(landing_site)
    if sms_form.validate_on_submit():
        #check if number validation is needed
        #TO DO
        #check_auth = Smsdata.query.filter_by(site_id=landing_site.id,phonenumber=sms_form.phonenumber.data,authcode=sms_form.authcode.data).first()
        #if check_auth and check_auth.status != SMS_CODE_USED :
        guest_check = Guest()
        guest_check.populate_from_email_form(sms_form,landing_site.emailformfields)
        guest_check.site_id     = landing_site.id
        guest_check.demo        = guest_track.demo
        db.session.add(guest_check)
        #New guest added create task for API export
        celery_export_api.delay(guest_check.id)            
        #mark sessions as authorized
        guest_track.state   = GUESTRACK_SMS_AUTH
        guest_device.state  = DEVICE_AUTH
        guest_device.guest  = guest_check
        guest_check.devices.append(guest_device)
        #check_auth.status = SMS_CODE_USED
        db.session.commit()
        current_app.logger.debug('Wifiguest Log - Site ID:%s sms_login new guest ID :%s for track ID:%s'%(guest_track.site_id,guest_check.id,guest_track.id))
        return redirect(url_for('guest.authorize_guest',track_id=guest_track.track_id),code=302)       
    #else:
        #print_errors(form)            
    
    landing_page = Landingpage.query.filter_by(id=landing_site.default_landing).first()
    return render_template('guest/%s/sms_landing.html'%landing_site.template,landing_site=landing_site,landing_page=landing_page,sms_form=sms_form)

@bp.route('/multi/guest/<track_id>',methods = ['GET', 'POST'])
@validate_track
def multi_login(track_id,guest_track,landing_site,guest_device):
    '''  View to show correct landing page   
    
    '''    
    if landing_site.fb_appid:
        fb_appid= landing_site.fb_appid
    else:
        fb_appid = current_app.config['FB_APP_ID']    
    ###----------------Code to show landing page------------------------------------------------------
    if landing_site.auth_method == AUTH_TYPE_EMAIL:
        #AUTH mode is set to email show the landing page with configured landing page
        return redirect(url_for('guest.email_login',track_id=guest_track.track_id),code=302)
        abort(404)   
    elif landing_site.auth_method == AUTH_TYPE_VOUCHER:
        #AUTH mode is set to voucher
        return redirect(url_for('guest.voucher_login',track_id=guest_track.track_id),code=302)  

    elif landing_site.auth_method == AUTH_TYPE_SOCIAL:
        #AUTH mode is set to voucher       
        return redirect(url_for('guest.social_login',track_id=guest_track.track_id),code=302)    

    elif landing_site.auth_method == AUTH_TYPE_SMS:
        #AUTH mode is set to voucher       
        return redirect(url_for('guest.sms_login',track_id=guest_track.track_id),code=302) 
    else:    
        guest_track.state = GUESTRACK_SOCIAL_PREAUTH
        db.session.commit()           
        return get_landing_page(site_id=landing_site.id,landing_site=landing_site,track_id=guest_track.track_id,app_id=fb_appid)


@bp.route('/sms/auth/<track_id>',methods = ['GET', 'POST'])
@validate_track
def authenticate_sms(track_id,guest_track,landing_site,guest_device):
    ''' View for authenticating guest's phone number before proceeding with further auth 
    
    '''
    #Check if the device already validated
    if  guest_device.sms_confirm == 1 and guest_device.demo == 0:
        return redirect(url_for('guest.multi_login',track_id=guest_track.track_id),code=302) 

    phoneform = PhonenumberForm()
    if phoneform.validate_on_submit():
        phonenumber   = phoneform.phonenumber.data
        authcode   = phoneform.authcode.data
        smsdata  = Smsdata.query.filter_by(device_id=guest_device.id,phonenumber=phonenumber,authcode=authcode).first()
        if smsdata:
            guest_device.sms_confirm = 1
            db.session.commit()
            current_app.logger.debug('Wifiguest Log - Site ID:%s authenticate_sms MAC:%s valid Phonenumber:%s \
                        authcode:%s'%(landing_site.id,guest_track.device_mac,phonenumber,authcode))   
            return redirect(url_for('guest.multi_login',track_id=guest_track.track_id),code=302) 

        else:
            current_app.logger.debug('Wifiguest Log - Site ID:%s authenticate_sms MAC:%s no SMSDATA found'%(landing_site.id,guest_track.device_mac))   
            flash("Wrong Phonenumber/auth code", 'danger')
    else:
        form_errors = get_errors(phoneform)
        current_app.logger.debug('Wifiguest Log - Site ID:%s authenticate_sms MAC:%s phoneform.errors:%s'%(landing_site.id,guest_track.device_mac,form_errors))   

    landing_page = Landingpage.query.filter_by(id=landing_site.default_landing).first()

    return render_template('guest/%s/sms_auth.html'%landing_site.template,landing_site=landing_site,landing_page=landing_page,phoneform=phoneform,track_id=track_id)          


@bp.route('/sms/send/<track_id>',methods = [ 'POST'])
@validate_track
def sms_send(track_id,guest_track,landing_site,guest_device):
    ''' Function to called for sending sms auth code  
    
    '''
    phonenumber = request.form.get('phonenumber')
    if not phonenumber:
        current_app.logger.debug('Wifiguest Log - Site ID:%s sms_send MAC:%s  no phonenumber'%(landing_site.id,guest_track.device_mac))
        return jsonify({'status':0,'msg':"Please Provide a Valid Mobile Number"})   

    smsdata  = Smsdata.query.filter_by(device_id=guest_device.id,phonenumber=phonenumber).first()
    if not smsdata:
        smsdata = Smsdata(phonenumber=phonenumber,device=guest_device)
        db.session.add(smsdata)  
        guest_device.smsdatas.append(smsdata)
        db.session.commit()
    #
    time_now  = datetime.datetime.utcnow() 
    time_diff = time_now - smsdata.timestamp
    #check if the mobile number was already used
    #also check how many times the user has asked for SMS
    if smsdata.status == SMS_DATA_NEW:
        #generate code 
        smsdata.authcode = random.randrange(10000,99999,1)
        current_app.logger.debug('Wifiguest Log - Site ID:%s sms_send MAC:%s  new authcode:%s for :%s'%(landing_site.id,guest_track.device_mac,smsdata.authcode,phonenumber))   
    elif smsdata.status == SMS_CODE_SEND:
        #reset send_try if last send is more than 2hrs long       
        if time_diff.total_seconds() > 2*60*60:
            smsdata.send_try = 0
            current_app.logger.debug('Wifiguest Log - Site ID:%s sms_send MAC:%s  smsdata.send_try  resetting for :%s'%(landing_site.id,guest_track.device_mac,phonenumber))   
        elif smsdata.send_try > 5 and  (time_diff.total_seconds() < 2*60*60 ):
            wait_time = int((2*60*60 - time_diff.total_seconds() )/60)
            current_app.logger.debug('Wifiguest Log - Site ID:%s sms_send MAC:%s  smsdata.send_try > 5 for :%s'%(landing_site.id,guest_track.device_mac,phonenumber))   
            return jsonify({'status':0,'msg':"Looks like SMS network is having issues,please wait for %s minutes"%wait_time})
        elif smsdata.send_try !=0 and time_diff.total_seconds() < 30:
            current_app.logger.debug('Wifiguest Log - Site ID:%s sms_send MAC:%s  time_diff.total_seconds() < 30 for :%s'%(landing_site.id,guest_track.device_mac,phonenumber))
            return jsonify({'status':0,'msg':"Wait for atleast 30sec before trying again"})
    smsdata.timestamp = time_now
    smsdata.status = SMS_CODE_SEND
    smsdata.send_try = smsdata.send_try + 1
    db.session.commit()
    celery_send_sms.delay(smsdata.id)
    current_app.logger.debug('Wifiguest Log - Site ID:%s sms_send MAC:%s SMS AUTH code for:%s is :%s'%(landing_site.id,guest_track.device_mac,phonenumber,smsdata.authcode))   
    return jsonify({'status':1,'msg':"Code has been send to the mobile"})
    

def get_landing_page(site_id,landing_page=None,landing_site=None,**kwargs):

    ''' Function to return configured landing page for a particular site    
    
    '''
    try:
        if not landing_site:
            landing_site = Wifisite.query.filter_by(id=site_id).first()
            current_app.logger.debug("SITE ID:%s"%landing_site.default_landing)
        if not landing_page:
            landing_page = Landingpage.query.filter_by(id=landing_site.default_landing).first()
    except:
        current_app.logger.exception("Exception while getting landing page/site for siteid:%s"%site_id)

    if not landing_site or not landing_page :
        #Given invalid site_id
        current_app.logger.info("Unknown landing_site or page specified n URL:%s"%request.url)
        abort(404)
    if landing_site.auth_method == AUTH_TYPE_SOCIAL:
        return render_template('guest/%s/social_landing.html'%landing_site.template,landing_site=landing_site,landing_page=landing_page,**kwargs)
    elif landing_site.auth_method == AUTH_TYPE_EMAIL:
        return render_template('guest/%s/email_landing.html'%landing_site.template,landing_site=landing_site,landing_page=landing_page,**kwargs)   
    elif landing_site.auth_method == AUTH_TYPE_VOUCHER:
        return render_template('guest/%s/voucher_landing.html'%landing_site.template,landing_site=landing_site,landing_page=landing_page,**kwargs)          

    elif landing_site.auth_method == AUTH_TYPE_SMS:
        return render_template('guest/%s/sms_landing.html'%landing_site.template,landing_site=landing_site,landing_page=landing_page,**kwargs)          
    else:
        return render_template('guest/%s/multi_landing.html'%landing_site.template,landing_site=landing_site,landing_page=landing_page,**kwargs)          
 


def validate_scan2login(url):
    '''Function to validate client's URL and check if its scan2login URL

    '''
    if not validators.url(url):
        return False

    parsed = urlparse(url)

    if not parsed.netloc == 'scan2log.in':
        return False

    voucher_code =  parse_qs(parsed.query).get('voucher')

    if voucher_code:
        return voucher_code
    else:
        return False




