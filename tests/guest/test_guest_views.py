''' Tests to check Guest Views

'''

import sys

from flask import current_app,url_for
from sqlalchemy import and_,or_

from unifispot.admin.models import Admin
from unifispot.client.models import Client,Wifisite,Voucher
from unifispot.models import db
from unifispot.guest.models import Guest,Device,Guestsession,Guesttrack,Facebookauth,Smsdata
from hashids import Hashids
from random import randint
import time,uuid,arrow
import pytest
from unifispot.const import *
from tests.helpers.views import check_view_user_404,check_view_user_401
from tests.helpers.guest import check_email_login_page,randomMAC,get_guest_url,check_facebook_login_page,check_voucher_login_page
from tests.helpers.guest import check_phone_login_page,check_multi_login_page,check_404,check_url_responce,check_json_response
import random

from faker import Faker
fake = Faker()


@pytest.fixture(scope='function')
def guest_logged(request):
    '''fixture used to create a logged in instance of guest. It creates guesttrack,guestsession and guestdevice

        
    '''
    site1        = Wifisite.query.filter_by(unifi_id='site1').first()  
    mac = randomMAC()
    ap_mac1 = randomMAC()
    #create a track id, sesssion and device
    track_id = str(uuid.uuid4())
    guest_track = Guesttrack(ap_mac=ap_mac1,device_mac=mac,site=site1,state=GUESTRACK_INIT,orig_url='',track_id=track_id)
    db.session.add(guest_track)
    #create device  
    guest_device = Device(mac=mac,site=site1,state=DEVICE_INIT)
    site1.devices.append(guest_device)
    db.session.add(guest_device)
    db.session.commit() 


@pytest.fixture(scope='function')
def create_vouchers(request):
    '''fixture used to create a set of vouchers

        
    '''
    site1        = Wifisite.query.filter_by(unifi_id='site1').first()  
    batchid = str(uuid.uuid4())
    cnt = 0
    newitem = Voucher(bytes_t=1000)    
    newitem.duration_t = 3* 60 * 60 * 24   #3 days
    #create voucher
    random = randint(100, 999)  # randint is inclusive at both ends
    hashid = Hashids(salt=current_app.config['HASH_SALT'],min_length=10)
    newitem.voucher = hashid.encode(random,site1.id,site1.client_id)
    newitem.batchid = batchid
    newitem.site = site1                           
    db.session.add(newitem)
    db.session.commit() 


def fake_get_user_from_cookie():
    return {'uid':'122121212121212121212121221', 
                                'access_token':'aiodu2873rehiw8qa27erdh792y3h97yhwqe8eyhdiq87yhewq7i8wqw7'}

@pytest.fixture
def fake_facebook(monkeypatch):
    '''Monkey patch used to create fake API objects

    '''
    monkeypatch.setattr('facebook.get_user_from_cookie', fake_get_user_from_cookie)






def test_guest_portal1(session):
    '''Check if configuring different auth_methods gives out proper landing pages'''
    site1 = Wifisite.query.filter_by(id=1).first()
    mac = randomMAC()
    ap_mac = randomMAC()    
    site1.auth_method = AUTH_TYPE_SOCIAL + AUTH_TYPE_SMS + AUTH_TYPE_EMAIL +AUTH_TYPE_VOUCHER
    db.session.commit()
    url = get_guest_url(site1,mac,ap_mac,demo=0)
    check_multi_login_page(url)

    site1.auth_method = AUTH_TYPE_SOCIAL 
    db.session.commit()
    url = get_guest_url(site1,mac,ap_mac,demo=0)
    check_facebook_login_page(url)

    site1.auth_method = AUTH_TYPE_SMS 
    db.session.commit()
    url = get_guest_url(site1,mac,ap_mac,demo=0)
    check_phone_login_page(url)

    site1.auth_method = AUTH_TYPE_EMAIL 
    db.session.commit()
    url = get_guest_url(site1,mac,ap_mac,demo=0)
    check_email_login_page(url)

    site1.auth_method = AUTH_TYPE_VOUCHER 
    db.session.commit()
    url = get_guest_url(site1,mac,ap_mac,demo=0)
    check_voucher_login_page(url)



def test_guest_portal2(session):
    '''Check if guest_track creations are done properly or not'''
    site1 = Wifisite.query.filter_by(id=1).first()
    site1.auth_method = AUTH_TYPE_SOCIAL + AUTH_TYPE_SMS + AUTH_TYPE_EMAIL +AUTH_TYPE_VOUCHER
    db.session.commit()
    mac = randomMAC()
    ap_mac = randomMAC()
    url = get_guest_url(site1,mac,ap_mac,demo=0)
    check_multi_login_page(url)

    # test if the device is created for this user
    test_device  = Device.query.filter( and_(Device.mac==mac,Device.site_id==site1.id)).first()
    assert isinstance(test_device, Device), "Device is not created when a new user visits"   
    #same user visit multiple times without session expiry, no new sessions should be created
    time.sleep(1)
    check_multi_login_page(url)
    check_multi_login_page(url)
    check_multi_login_page(url)
    check_multi_login_page(url)
    num_device  = Device.query.filter( and_(Device.mac==mac,Device.site_id==site1.id)).count()
    assert num_device == 1 , "User visiting twice without session expiry: Device shouldn't be created twice"
    #
    assert 5 == Guesttrack.query.count() , "User visiting  without session expiry: Guesttrack should be created eachtime"   



def test_guest_portal3(session):
    '''Same user visiting multiple sites
    
    ''' 
    site1        = Wifisite.query.filter_by(unifi_id='site1').first() 
    site2        = Wifisite.query.filter_by(unifi_id='site2').first() 
    site3        = Wifisite.query.filter_by(unifi_id='site3').first() 
    site1.auth_method = AUTH_TYPE_SOCIAL + AUTH_TYPE_SMS + AUTH_TYPE_EMAIL +AUTH_TYPE_VOUCHER      
    site2.auth_method = AUTH_TYPE_SOCIAL + AUTH_TYPE_SMS + AUTH_TYPE_EMAIL +AUTH_TYPE_VOUCHER      
    site3.auth_method = AUTH_TYPE_SOCIAL + AUTH_TYPE_SMS + AUTH_TYPE_EMAIL +AUTH_TYPE_VOUCHER      
    mac = randomMAC()
    ap_mac1 = randomMAC()
    ap_mac2 = randomMAC()
    ap_mac3 = randomMAC()
    url1 = get_guest_url(site1,mac,ap_mac1,demo=0)    
    url2 = get_guest_url(site2,mac,ap_mac2,demo=0)    
    url3 = get_guest_url(site3,mac,ap_mac3,demo=0)    

    check_multi_login_page(url1)    
    check_multi_login_page(url1)    
    check_multi_login_page(url2)    
    check_multi_login_page(url2)    
    check_multi_login_page(url3)    
    check_multi_login_page(url3)    
    assert 2 == Guesttrack.query.filter_by(site_id=site1.id).count(), "Same device visiting 3 sites twice, 2 Guesttrack PER SITE  needed" 
    assert 2 == Guesttrack.query.filter_by(site_id=site2.id).count(), "Same device visiting 3 sites twice, 2 Guesttrack PER SITE needed" 
    assert 2 == Guesttrack.query.filter_by(site_id=site3.id).count(), "Same device visiting 3 sites twice, 2 Guesttrack PER SITE needed" 
    assert 3 == Device.query.count(), "Same device visiting 3 sites, 3 Device needed" 



def test_guest_portal4(session):
    '''User with demo flag set is visiting
    
    ''' 
    site1        = Wifisite.query.filter_by(unifi_id='site1').first() 
    site1.auth_method = AUTH_TYPE_SOCIAL + AUTH_TYPE_SMS + AUTH_TYPE_EMAIL +AUTH_TYPE_VOUCHER       
    mac = randomMAC()
    ap_mac1 = randomMAC()
    url1 = get_guest_url(site1,mac,ap_mac1,1)   
    check_multi_login_page(url1) 

    guest_track1   = Guesttrack.query.filter( and_(Guesttrack.device_mac==mac,Guesttrack.site_id==site1.id)).first()
    guest_device1  = Device.query.filter( and_(Device.mac==mac,Device.site_id==site1.id)).first()

    assert 1 == guest_track1.demo,'Demo flag is not set for guest_track for URL:%s'%url1
    assert 1 == guest_device1.demo,'Demo flag is not set for guest_device for URL:%s'%url1

def test_guest_portal_cna(session):
    '''Portal behaviour when CNA URL is called
    
    ''' 
    pass

def test_authorize_guest1(session):
    ''' authorize_guest with invalid parameters '''
    site1        = Wifisite.query.filter_by(unifi_id='site1').first() 
    site1.auth_method = AUTH_TYPE_SOCIAL + AUTH_TYPE_SMS + AUTH_TYPE_EMAIL +AUTH_TYPE_VOUCHER       
    mac = randomMAC()
    ap_mac1 = randomMAC()
    url1 = get_guest_url(site1,mac,ap_mac1,1)  

    #invalid guestrack id
    check_404(url_for('guest.authorize_guest',track_id=str(uuid.uuid4())))

    #test valid trackid but no device
    track_id = str(uuid.uuid4())
    guest_track = Guesttrack(ap_mac=ap_mac1,device_mac=mac,site=site1,state=GUESTRACK_INIT,orig_url='',track_id=track_id)
    db.session.add(guest_track)
    db.session.commit()
    check_404(url_for('guest.authorize_guest',track_id=track_id))


    #Create device but not authorized 
    guest_device = Device(mac=mac,site=site1,state=DEVICE_INIT)
    site1.devices.append(guest_device)
    db.session.add(guest_device)
    guest_track.state   = GUESTRACK_NO_AUTH
    guest_device.state  = DEVICE_AUTH   
    db.session.commit()    
    check_404(url_for('guest.authorize_guest',track_id=track_id))

    #ensure that no sessions are created
    assert 0 == Guestsession.query.count(),"Guestsessions are created even though authorize_guest is not called properly"


def test_authorize_guest2(session):
    ''' authorize_guest check if parameters are correctly configured '''
    #create a guest visitor
    site1 = Wifisite.query.filter_by(id=1).first()
    mac = randomMAC()
    ap_mac = randomMAC()    
    site1.auth_method = AUTH_TYPE_SOCIAL + AUTH_TYPE_SMS + AUTH_TYPE_EMAIL +AUTH_TYPE_VOUCHER
    db.session.commit()
    url = get_guest_url(site1,mac,ap_mac,demo=0)
    check_multi_login_page(url)  

    guest_track = Guesttrack.query.first()  

    #authorize session
    guest_track.state = GUESTRACK_SOCIAL_AUTH
    
    auth_url = url_for('guest.authorize_guest',track_id =guest_track.track_id)
    result = current_app.test_client().get(auth_url,follow_redirects=True)
    assert '200 OK' == result.status, 'authorize_guest  getting:%s instead of  200 OK while trying to View URL:%s'%(result.status,url)

    #check if guest_session is created
    guest_session = Guestsession.query.first()
    assert isinstance(guest_session,Guestsession) ,'Guestsession is not created when calling authorize_guest'
    assert guest_session.state == GUESTRACK_SOCIAL_AUTH, " guest_session state is not GUESTRACK_SOCIAL_AUTH"




def test_temp_authorize_guest1(session):
    ''' authorize_guest with invalid parameters '''
    site1        = Wifisite.query.filter_by(unifi_id='site1').first() 
    site1.auth_method = AUTH_TYPE_SOCIAL + AUTH_TYPE_SMS + AUTH_TYPE_EMAIL +AUTH_TYPE_VOUCHER       
    mac = randomMAC()
    ap_mac1 = randomMAC()
    url1 = get_guest_url(site1,mac,ap_mac1,1)  

    auth_pass_status = {'status':1,'msg': "DEBUG enabled"}
    auth_fail_status = {'status':0,'msg': "Error"}
    auth_fail_status1 = {'status':0,'msg': "You have already used up temporary logins for today"}

    #invalid guestrack id
    check_json_response(url_for('guest.temp_authorize_guest',track_id=str(uuid.uuid4())),auth_fail_status)

    #test valid trackid but not pre_auth
    track_id = str(uuid.uuid4())
    guest_track = Guesttrack(ap_mac=ap_mac1,device_mac=mac,site=site1,state=GUESTRACK_INIT,orig_url='',track_id=track_id)
    db.session.add(guest_track)
    db.session.commit()
    check_json_response(url_for('guest.temp_authorize_guest',track_id=track_id),auth_fail_status)

    #Create device and authorize session
    guest_device = Device(mac=mac,site=site1,state=DEVICE_INIT)
    site1.devices.append(guest_device)
    db.session.add(guest_device)
    guest_track.state = GUESTRACK_SOCIAL_PREAUTH
    db.session.commit() 
    check_json_response(url_for('guest.temp_authorize_guest',track_id=track_id),auth_pass_status)

    #check if guest_session is created
    guest_session = Guestsession.query.first()
    assert isinstance(guest_session,Guestsession) ,'Guestsession is not created when calling authorize_guest'
    assert guest_session.state == GUESTRACK_SOCIAL_PREAUTH, " guest_session state is not GUESTRACK_SOCIAL_PREAUTH"

    #make max number of tries   
    check_json_response(url_for('guest.temp_authorize_guest',track_id=track_id),auth_pass_status)
    check_json_response(url_for('guest.temp_authorize_guest',track_id=track_id),auth_pass_status)
    check_json_response(url_for('guest.temp_authorize_guest',track_id=track_id),auth_pass_status)
    check_json_response(url_for('guest.temp_authorize_guest',track_id=track_id),auth_pass_status)
    check_json_response(url_for('guest.temp_authorize_guest',track_id=track_id),auth_fail_status1)


def test_social_login1(session):
    '''Test social_login view with in valid parameters and non authorized device

     '''

    site1        = Wifisite.query.filter_by(unifi_id='site1').first() 
    site1.auth_method = AUTH_TYPE_SOCIAL      
    mac = randomMAC()
    ap_mac1 = randomMAC()
    url1 = get_guest_url(site1,mac,ap_mac1,1)      

    #invalid guestrack id
    check_404(url_for('guest.social_login',track_id=str(uuid.uuid4())))

    #test valid trackid but no session
    track_id = str(uuid.uuid4())
    guest_track = Guesttrack(ap_mac=ap_mac1,device_mac=mac,site=site1,state=GUESTRACK_INIT,orig_url='',track_id=track_id)
    db.session.add(guest_track)
    db.session.commit()
    check_404(url_for('guest.social_login',track_id=track_id))    


    #Create device 
    guest_device = Device(mac=mac,site=site1,state=DEVICE_INIT)
    site1.devices.append(guest_device)
    db.session.add(guest_device)
    db.session.commit() 
    check_url_responce(url_for('guest.social_login',track_id=track_id),'Login Using Facebook')   

    #validate guesttrack
    guest_track =  Guesttrack.query.first()
    assert GUESTRACK_SOCIAL_PREAUTH == guest_track.state, "Guesttrack state is not GUESTRACK_SOCIAL_PREAUTH"


def test_social_login2(session,guest_logged):
    '''Test social_login view with pre authorized guest

     '''
    site1               = Wifisite.query.filter_by(unifi_id='site1').first() 
    site1.auth_method   = AUTH_TYPE_SOCIAL    
    guest_device        = Device.query.first()  
    mac                 = guest_device.mac
    guest_device.state  = DEVICE_AUTH 
    guest_track         = Guesttrack.query.first()
    db.session.commit()     
    ap_mac1             = randomMAC() 

    check_url_responce(url_for('guest.social_login',track_id=guest_track.track_id),'Login Using Facebook') 


def test_facebook_login1(session):
    '''Test facebook_login view with in valid parameters

     '''

    site1        = Wifisite.query.filter_by(unifi_id='site1').first() 
    site1.auth_method = AUTH_TYPE_SOCIAL      
    mac = randomMAC()
    ap_mac1 = randomMAC()
    url1 = get_guest_url(site1,mac,ap_mac1,1)      

    #invalid guestrack id
    check_404(url_for('guest.facebook_login',track_id=str(uuid.uuid4())))

    #test valid trackid but no session
    track_id = str(uuid.uuid4())
    guest_track = Guesttrack(ap_mac=ap_mac1,device_mac=mac,site=site1,state=GUESTRACK_INIT,orig_url='',track_id=track_id)
    db.session.add(guest_track)
    db.session.commit()
    check_404(url_for('guest.facebook_login',track_id=track_id))    


    #Create device 
    guest_device = Device(mac=mac,site=site1,state=DEVICE_INIT)
    site1.devices.append(guest_device)
    db.session.add(guest_device)
    db.session.commit() 
    check_facebook_login_page(url_for('guest.facebook_login',track_id=track_id))   


def test_facebook_login2(fake_facebook,session,guest_logged):
    '''Test facebook_login view with mocked logged in guest

     '''
    pass


def test_email_login1(session):
    '''Test email_login view with in valid parameters

     '''

    site1        = Wifisite.query.filter_by(unifi_id='site1').first() 
    site1.auth_method = AUTH_TYPE_EMAIL     
    mac = randomMAC()
    ap_mac1 = randomMAC()
   

    #invalid guestrack id
    check_404(url_for('guest.email_login',track_id=str(uuid.uuid4())))

    #test valid trackid but no session
    track_id = str(uuid.uuid4())
    guest_track = Guesttrack(ap_mac=ap_mac1,device_mac=mac,site=site1,state=GUESTRACK_INIT,orig_url='',track_id=track_id)
    db.session.add(guest_track)
    db.session.commit()
    check_404(url_for('guest.email_login',track_id=track_id))    

    #Create device 
    guest_device = Device(mac=mac,site=site1,state=DEVICE_INIT)
    site1.devices.append(guest_device)
    db.session.add(guest_device)
    db.session.commit() 
    check_email_login_page(url_for('guest.email_login',track_id=track_id))   

def test_email_login2(fake_facebook,session,guest_logged):
    '''Test email_login view with pre authorized device

     '''
    site1           = Wifisite.query.filter_by(unifi_id='site1').first() 
    guest_track     = Guesttrack.query.first()
    guest_device    = Device.query.first()
    guest_device.state = DEVICE_AUTH
    db.session.commit()
    
    url = url_for('guest.email_login',track_id=guest_track.track_id)
    result = current_app.test_client().get(url,follow_redirects=False)
    auth_url = url_for('guest.authorize_guest',track_id=guest_track.track_id, _external=True)
    assert auth_url == result.location, "UE gets redirected to :%s instead of expected :%s"%(result.location,auth_url)

    guest_track =  Guesttrack.query.first()
    assert GUESTRACK_PREAUTH == guest_track.state, "Guesttrack state is not GUESTRACK_PREAUTH"


def test_email_login3(fake_facebook,session,guest_logged):
    '''Test email_login view with guest enetering data

    '''
    site1           = Wifisite.query.filter_by(unifi_id='site1').first() 
    guest_track     = Guesttrack.query.first()
    guest_device   = Device.query.first()
    url = url_for('guest.email_login',track_id=guest_track.track_id)   

    firstname   = fake.first_name() 
    lastname    = fake.last_name() 
    email       = fake.email()
    form_data = {'firstname':firstname,'email':email,'lastname':lastname}


    url = url_for('guest.email_login',track_id=guest_track.track_id)
    result = current_app.test_client().post(url,follow_redirects=False,data=form_data)
    auth_url = url_for('guest.authorize_guest',track_id=guest_track.track_id, _external=True)
    assert auth_url == result.location, "UE gets redirected to :%s instead of expected :%s"%(result.location,auth_url)  
    #check if guest is created
    guest = Guest.query.first().to_dict()
    assert form_data['firstname'] == guest['firstname'],\
            'Guest firstname not matching expected:%s getting:%s'%(form_data['firstname'],guest['firstname'])
    assert form_data['lastname'] == guest['lastname'],\
            'Guest lastname not matching Expected:%s Got: %s'%(form_data['lastname'],guest['lastname'])
    assert form_data['email'] == guest['email'],\
            'Guest email not matching Expected:%s Got: %s'%(form_data['email'],guest['email'])

    assert site1.id == guest['site_id'], "Giest site_id not matching expected:%s got:%s"%(site1.id,guest['site_id'])

    guest_track =  Guesttrack.query.first()
    assert GUESTRACK_EMAIL_AUTH == guest_track.state, "Guesttrack state is not GUESTRACK_EMAIL_AUTH"



def test_voucher_login1(session,create_vouchers):
    '''Test voucher_login view with in valid parameters

     '''

    site1        = Wifisite.query.filter_by(unifi_id='site1').first() 
    site1.auth_method = AUTH_TYPE_EMAIL     
    mac = randomMAC()
    ap_mac1 = randomMAC()
   

    #invalid guestrack id
    check_404(url_for('guest.voucher_login',track_id=str(uuid.uuid4())))

    #test valid trackid but no session
    track_id = str(uuid.uuid4())
    guest_track = Guesttrack(ap_mac=ap_mac1,device_mac=mac,site=site1,state=GUESTRACK_INIT,orig_url='',track_id=track_id)
    db.session.add(guest_track)
    db.session.commit()
    check_404(url_for('guest.voucher_login',track_id=track_id))    

    #Create device 
    guest_device = Device(mac=mac,site=site1,state=DEVICE_INIT)
    site1.devices.append(guest_device)
    db.session.add(guest_device)
    db.session.commit() 
    check_voucher_login_page(url_for('guest.voucher_login',track_id=track_id))   

def test_voucher_login2(session,create_vouchers,guest_logged):
    '''Test voucher_login view with pre authorized guest with non expired voucher

     '''
    site1           = Wifisite.query.filter_by(unifi_id='site1').first() 
    guest_track     = Guesttrack.query.first()
    guest_device    = Device.query.first()
    voucher         = Voucher.query.first()

    #device and used voucher
    used_at = arrow.utcnow().replace(days=2).datetime
    guest_device.state = DEVICE_VOUCHER_AUTH
    voucher.device_id = guest_device.id
    voucher.used = True
    voucher.used_at = used_at    

    #create a session representing old session
    guest_session = Guestsession(site=site1,device=guest_device)
    guest_session.state = GUESTRACK_VOUCHER_AUTH
    guest_session.mac   = guest_device.mac
    guest_session.guesttracks.append(guest_track)
    db.session.add(guest_session)
    guest_track.session_id = guest_session.id  

    #fake variables for session
    guest_session.starttime = used_at
    guest_session.lastseen = used_at
    guest_session.data_used = 500000

    db.session.commit()    

    url = url_for('guest.voucher_login',track_id=guest_track.track_id)      
    result = current_app.test_client().post(url,follow_redirects=False)
    auth_url = url_for('guest.authorize_guest',track_id=guest_track.track_id, _external=True)
    assert auth_url == result.location, "UE gets redirected to :%s instead of expected :%s"%(result.location,auth_url)     

def test_voucher_login3(session,create_vouchers,guest_logged):
    '''Test voucher_login view with pre authorized guest with voucher expired date

     '''
    site1           = Wifisite.query.filter_by(unifi_id='site1').first() 
    guest_track     = Guesttrack.query.first()
    guest_device    = Device.query.first()
    voucher         = Voucher.query.first()

    #device and used voucher
    used_at = arrow.utcnow().replace(days=-4).naive
    guest_device.state = DEVICE_VOUCHER_AUTH
    voucher.device_id = guest_device.id
    voucher.used = True
    voucher.used_at = used_at    

    #create a session representing old session
    guest_session = Guestsession(site=site1,device=guest_device)
    guest_session.state = GUESTRACK_VOUCHER_AUTH
    guest_session.mac   = guest_device.mac
    guest_session.guesttracks.append(guest_track)
    db.session.add(guest_session)
    guest_track.session_id = guest_session.id  

    #fake variables for session
    guest_session.starttime = used_at
    guest_session.lastseen = used_at
    guest_session.data_used = 500000

    db.session.commit()    

    url = url_for('guest.voucher_login',track_id=guest_track.track_id)      
    result = current_app.test_client().post(url,follow_redirects=True)

    assert '<input class="form-control input-guest" id="voucher" name="voucher" type="text" value="">' in result.data,\
                'Voucher Login button not seen  at  URL:%s'%(url)    

    assert 'Looks like your Voucher have expired' in result.data,"Voucher expiry mflash message not found"

def test_voucher_login4(session,create_vouchers,guest_logged):
    '''Test voucher_login view with pre authorized guest with voucher of expired data use

     '''
    site1           = Wifisite.query.filter_by(unifi_id='site1').first() 
    guest_track     = Guesttrack.query.first()
    guest_device    = Device.query.first()
    voucher         = Voucher.query.first()

    #device and used voucher
    used_at = arrow.utcnow().replace(days=-2).naive
    guest_device.state = DEVICE_VOUCHER_AUTH
    voucher.device_id = guest_device.id
    voucher.used = True
    voucher.used_at = used_at    

    #create a session representing old session
    guest_session = Guestsession(site=site1,device=guest_device)
    guest_session.state = GUESTRACK_VOUCHER_AUTH
    guest_session.mac   = guest_device.mac
    guest_session.guesttracks.append(guest_track)
    db.session.add(guest_session)
    guest_track.session_id = guest_session.id  
    voucher.sessions.append(guest_session)
    guest_session.voucher_id = voucher.id

    #fake variables for session
    guest_session.starttime = used_at
    guest_session.lastseen = used_at
    guest_session.data_used = 1040000000

    db.session.commit()    

    url = url_for('guest.voucher_login',track_id=guest_track.track_id)      
    result = current_app.test_client().post(url,follow_redirects=True)

    assert '<input class="form-control input-guest" id="voucher" name="voucher" type="text" value="">' in result.data,\
                'Voucher Login button not seen  at  URL:%s'%(url)    

    assert 'Looks like your Voucher have expired' in result.data,"Voucher expiry mflash message not found"

def test_voucher_login5(session,create_vouchers,guest_logged):
    '''Test voucher_login view by entering voucher

     '''
    site1           = Wifisite.query.filter_by(unifi_id='site1').first() 
    guest_track     = Guesttrack.query.first()
    guest_device    = Device.query.first()
    voucher         = Voucher.query.first()
    url = url_for('guest.voucher_login',track_id=guest_track.track_id)   

    firstname   = fake.first_name() 
    lastname    = fake.last_name() 
    email       = fake.email()
    form_data = {'firstname':firstname,'email':email,'lastname':lastname,'voucher':voucher.voucher}    

    result = current_app.test_client().post(url,follow_redirects=False,data=form_data)
    auth_url = url_for('guest.authorize_guest',track_id=guest_track.track_id, _external=True)
    assert auth_url == result.location, "UE gets redirected to :%s instead of expected :%s"%(result.location,auth_url)  
    #check if guest is created
    guest = Guest.query.first().to_dict()
    assert form_data['firstname'] == guest['firstname'],\
            'Guest firstname not matching expected:%s getting:%s'%(form_data['firstname'],guest['firstname'])
    assert form_data['lastname'] == guest['lastname'],\
            'Guest lastname not matching Expected:%s Got: %s'%(form_data['lastname'],guest['lastname'])

    assert site1.id == guest['site_id'], "Giest site_id not matching expected:%s got:%s"%(site1.id,guest['site_id'])

    guest_track =  Guesttrack.query.first()
    assert GUESTRACK_VOUCHER_AUTH == guest_track.state, "Guesttrack state is not GUESTRACK_VOUCHER_AUTH"
    assert voucher.time_available() == guest_track.duration, "Guesttrack duration is not expected "


def test_sms_send1(session,guest_logged):
    '''Test sms_send view by calling without phone number

     '''    
    site1           = Wifisite.query.filter_by(unifi_id='site1').first() 
    guest_track     = Guesttrack.query.first()
    guest_device    = Device.query.first()   
    
    url = url_for('guest.sms_send',track_id=guest_track.track_id) 
    result = current_app.test_client().post(url,follow_redirects=True,data={}) 

    msg_nophone = {'status':0,'msg':"Please Provide a Valid Mobile Number"}

    assert msg_nophone == result.json ,\
            'Found msg :%s instead of :%s '%(result.json,msg_nophone)

def test_sms_send2(session,guest_logged):
    '''Test sms_send view by calling with phone number on new device

     '''    
    site1           = Wifisite.query.filter_by(unifi_id='site1').first() 
    guest_track     = Guesttrack.query.first()
    guest_device    = Device.query.first()   
    
    msg= {'status':1,'msg':"Code has been send to the mobile"}
    url = url_for('guest.sms_send',track_id=guest_track.track_id) 
    result = current_app.test_client().post(url,follow_redirects=True,data={'phonenumber':'+123456780'}) 
    assert msg == result.json ,\
            'Found msg :%s instead of :%s  while trying to send SMS'%(result.json,msg) 


    assert 1 == Smsdata.query.count() , "Smsdata is not created even after providing valid phonenumber"


def test_sms_send3(session,guest_logged):
    '''Test sms_send view by calling with same phone/device multiple times

     '''    
    site1           = Wifisite.query.filter_by(unifi_id='site1').first() 
    guest_track     = Guesttrack.query.first()
    guest_device    = Device.query.first()   
    
    msg= {'status':1,'msg':"Code has been send to the mobile"}
    url = url_for('guest.sms_send',track_id=guest_track.track_id) 
    result = current_app.test_client().post(url,follow_redirects=True,data={'phonenumber':'+123456780'}) 
    assert msg == result.json ,\
            'Found msg :%s instead of :%s  while trying to send SMS'%(result.json,msg) 

    #immediate calling without delay
    msg_wait = {'status':0,'msg':"Wait for atleast 30sec before trying again"}
    result = current_app.test_client().post(url,follow_redirects=True,data={'phonenumber':'+123456780'}) 
    assert msg_wait == result.json ,\
            'Found msg :%s instead of :%s  while trying to send SMS'%(result.json,msg_wait) 
    #fake 30sec over
    smsdata = Smsdata.query.first()
    smsdata.timestamp = arrow.utcnow().replace(seconds=-31).naive
    db.session.commit()
    result = current_app.test_client().post(url,follow_redirects=True,data={'phonenumber':'+123456780'}) 
    assert msg == result.json ,\
            'Found msg :%s instead of :%s  while trying to send SMS'%(result.json,msg) 

    assert 1 == Smsdata.query.count() , "Smsdata is not created even after providing valid phonenumber"
    assert 2 == Smsdata.query.first().send_try , "Smsdata.send_try is not increamented after two trials"


def test_sms_send4(session,guest_logged):
    '''Test sms_send view by calling with same phone/device more than bi-hourly limit

     '''    
    site1           = Wifisite.query.filter_by(unifi_id='site1').first() 
    guest_track     = Guesttrack.query.first()
    guest_device    = Device.query.first()   
    
    msg= {'status':1,'msg':"Code has been send to the mobile"}
    url = url_for('guest.sms_send',track_id=guest_track.track_id) 
    result = current_app.test_client().post(url,follow_redirects=True,data={'phonenumber':'+123456780'}) 
    assert msg == result.json ,\
            'Found msg :%s instead of :%s  while trying to send SMS'%(result.json,msg) 
    #fake limit over
    smsdata = Smsdata.query.first()       
    smsdata.send_try = 6     
    db.session.commit()
    result = current_app.test_client().post(url,follow_redirects=True,data={'phonenumber':'+123456780'}) 
    wait_msg = 'Looks like SMS network is having issues,please wait for'
    assert wait_msg in result.json['msg'] ,\
            'Found msg :%s instead of :%s  while trying to send SMS'%(result.json['msg'],wait_msg) 
    #recovering after 2hrs
    smsdata.timestamp = arrow.utcnow().replace(hours=-2).naive
    db.session.commit()
    result = current_app.test_client().post(url,follow_redirects=True,data={'phonenumber':'+123456780'}) 
    assert msg == result.json ,\
            'Found msg :%s instead of :%s  while trying to send SMS'%(result.json,msg)     
    assert 1 == Smsdata.query.first().send_try , "Smsdata.send_try is not resetting after 2 hrs"


def test_authenticate_sms1(session,guest_logged):
    '''Test authenticate_sms view by calling with pre authenticated device

     '''    
    site1           = Wifisite.query.filter_by(unifi_id='site1').first() 
    guest_track     = Guesttrack.query.first()
    guest_device    = Device.query.first()   

    guest_device.sms_confirm = 1
    db.session.commit()

    url = url_for('guest.authenticate_sms',track_id=guest_track.track_id) 

    result = current_app.test_client().post(url,follow_redirects=False)
    auth_url = url_for('guest.multi_login',track_id=guest_track.track_id, _external=True)
    assert auth_url == result.location, "UE gets redirected to :%s instead of expected :%s"%(result.location,auth_url) 

def test_authenticate_sms2(session,guest_logged):
    '''Test authenticate_sms view by calling with  demo device

     '''    
    site1           = Wifisite.query.filter_by(unifi_id='site1').first() 
    guest_track     = Guesttrack.query.first()
    guest_device    = Device.query.first()   

    guest_device.demo = 1
    db.session.commit()

    url = url_for('guest.authenticate_sms',track_id=guest_track.track_id) 

    result = current_app.test_client().get(url,follow_redirects=True)
    assert "<button type=\"submit\" class=\"btn btn-guest \" id='loginsms' >Login</button>" in result.data,\
                'login sms button is not found when calling authenticate_sms with demo device'



def test_authenticate_sms3(session,guest_logged):
    '''Test authenticate_sms view by calling with  new device

     '''    
    site1           = Wifisite.query.filter_by(unifi_id='site1').first() 
    guest_track     = Guesttrack.query.first()
    guest_device    = Device.query.first()   


    url = url_for('guest.authenticate_sms',track_id=guest_track.track_id) 

    result = current_app.test_client().get(url,follow_redirects=True)
    assert "<button type=\"submit\" class=\"btn btn-guest \" id='loginsms' >Login</button>" in result.data,\
                'login sms button is not found when calling authenticate_sms with demo device'

def test_authenticate_sms4(session,guest_logged):
    '''Test authenticate_sms view by posting empty form

     '''    
    site1           = Wifisite.query.filter_by(unifi_id='site1').first() 
    guest_track     = Guesttrack.query.first()
    guest_device    = Device.query.first()   


    url = url_for('guest.authenticate_sms',track_id=guest_track.track_id) 

    result = current_app.test_client().post(url,follow_redirects=True,data=None)
    assert "<button type=\"submit\" class=\"btn btn-guest \" id='loginsms' >Login</button>" in result.data,\
                'login sms button is not found when calling authenticate_sms with demo device'

def test_authenticate_sms5(session,guest_logged):
    '''Test authenticate_sms view by posting correctly

     '''    
    site1           = Wifisite.query.filter_by(unifi_id='site1').first() 
    guest_track     = Guesttrack.query.first()
    guest_device    = Device.query.first()   

    phonenumber = '+123456789'
    smsdata = Smsdata(phonenumber=phonenumber,device=guest_device)
    db.session.add(smsdata)  
    guest_device.smsdatas.append(smsdata)
    smsdata.authcode = random.randrange(10000,99999,1)
    db.session.commit()
    url = url_for('guest.authenticate_sms',track_id=guest_track.track_id) 

    result = current_app.test_client().post(url,follow_redirects=False,data={'phonenumber':phonenumber,'authcode':smsdata.authcode})
    auth_url = url_for('guest.multi_login',track_id=guest_track.track_id, _external=True)
    assert auth_url == result.location, "UE gets redirected to :%s instead of expected :%s"%(result.location,auth_url) 

    assert 1 == guest_device.sms_confirm, 'sms_confirm is not set after submit'