''' Helper functions for Guest '''
from flask import current_app,url_for
import random
from unifispot.const import *
from urlparse import urlparse

def randomMAC():
    mac= [ 0x00, 0x16, 0x3e,
        random.randint(0x00, 0x7f),
        random.randint(0x00, 0xff),
        random.randint(0x00, 0xff) ]
    return ':'.join(map(lambda x: "%02x" % x, mac))



def get_guest_url(site,mac,ap_mac,demo=0):

    base_url = url_for('guest.guest_portal',site_id=site.unifi_id)
    if demo == 0:
        guest_url = '%s?id=%s&ap=%s'%(base_url,mac,ap_mac)
    else:
        guest_url = '%s?id=%s&ap=%s&demo=1'%(base_url,mac,ap_mac)
    return guest_url


def check_email_login_page(url,extrafields=[]):
    ''' Visit the URL and follow directs, and ensure that page returned have email login form'''
    result = current_app.test_client().get(url,follow_redirects=True)
    assert '200 OK' == result.status, 'Current user  getting:%s instead of  200 OK while trying to View URL:%s'%(result.status,url)
    assert '<input class="form-control input-guest" id="email" name="email" type="text" value="">' in result.data,\
            'Email field is not found for check_email_login_page at  URL:%s'%(url)
    for field in extrafields:
        assert '<input class="form-control input-guest" id="%s" name="%s" type="text" value="">'%(field,field) in result.data,\
                'Email field is not found for check_email_login_page at  URL:%s'%(url)

def check_facebook_login_page(url):
    ''' Visit the URL and follow directs, and ensure that page returned have FB login form'''
    result = current_app.test_client().get(url,follow_redirects=True)
    assert '200 OK' == result.status, 'Current user  getting:%s instead of  200 OK while trying to View URL:%s'%(result.status,url)
    assert 'Login Using Facebook' in result.data,\
            'Facebook Login button not seen  check_facebook_login_page at  URL:%s'%(url)



def check_voucher_login_page(url,extrafields=[]):
    ''' Visit the URL and follow directs, and ensure that page returned have voucher login form'''
    result = current_app.test_client().get(url,follow_redirects=True)
    assert '200 OK' == result.status, 'Current user  getting:%s instead of  200 OK while trying to View URL:%s'%(result.status,url)
    assert '<input class="form-control input-guest" id="voucher" name="voucher" type="text" value="">' in result.data,\
            'Voucher field is not found for check_voucher_login_page at  URL:%s'%(url)
    for field in extrafields:
        assert '<input class="form-control input-guest" id="%s" name="%s" type="text" value="">'%(field,field) in result.data,\
                'Extra field is not found for check_voucher_login_page at  URL:%s'%(url)


def check_phone_login_page(url,extrafields=[]):
    ''' Visit the URL and follow directs, and ensure that page returned have Phone login form'''
    result = current_app.test_client().get(url,follow_redirects=True)
    assert '200 OK' == result.status, 'Current user  getting:%s instead of  200 OK while trying to View URL:%s'%(result.status,url)
    assert '<input class="form-control input-guest" id="phonenumber" name="phonenumber" type="text" value="">' in result.data,\
            'Phone field is not found for check_email_login_page at  URL:%s'%(url)
    for field in extrafields:
        assert '<input class="form-control input-guest" id="%s" name="%s" type="text" value="">'%(field,field) in result.data,\
                'Extra field is not found for check_phone_login_page at  URL:%s'%(url)

def check_multi_login_page(url,auth_method=AUTH_TYPE_SOCIAL + AUTH_TYPE_SMS + AUTH_TYPE_EMAIL +AUTH_TYPE_VOUCHER ):
    ''' Visit the URL and follow directs, and ensure that page returned have multi login form'''
    result = current_app.test_client().get(url,follow_redirects=True)
    assert '200 OK' == result.status, 'Current user  getting:%s instead of  200 OK while trying to View URL:%s'%(result.status,url)
    if auth_method &AUTH_TYPE_SOCIAL:
        assert 'Login Using FB' in result.data,\
                'Facebook Login button not seen  check_multi_login_page at  URL:%s'%(url)
    if auth_method &AUTH_TYPE_SMS:
        assert 'Login Using Phone' in result.data,\
                'Phone Login button not seen  check_multi_login_page at  URL:%s'%(url)
    if auth_method &AUTH_TYPE_EMAIL:
        assert 'Login Using Email' in result.data,\
                'Email Login button not seen  check_multi_login_page at  URL:%s'%(url)
    if auth_method &AUTH_TYPE_VOUCHER:
        assert 'Login Using Voucher' in result.data,\
                'Voucher Login button not seen  check_multi_login_page at  URL:%s'%(url)                                


def check_404(url):
    ''' Visit the URL and follow directs, and ensure URL returns 404'''
    result = current_app.test_client().get(url,follow_redirects=True)
    assert '404 NOT FOUND' == result.status, 'Current user  getting:%s instead of  404 NOT FOUND while trying to View URL:%s'%(result.status,url)    

def check_url_responce(url,msg=None):
    ''' Visit the URL and follow directs, and check if the page contains given text'''
    result = current_app.test_client().get(url,follow_redirects=True)
    assert '200 OK' == result.status, 'Current user  getting:%s instead of  200 OK while trying to View URL:%s'%(result.status,url)
    if msg:
        assert msg in result.data,'MSG:%s is not found for check_email_login_page at  URL:%s'%(msg,url)        


def check_json_response(url,resp=None):
    ''' Visit the URL and follow directs, and check if the json response is as expected'''    
    result = current_app.test_client().get(url,follow_redirects=True)
    assert '200 OK' == result.status, 'Current user  getting:%s instead of  200 OK while trying to View URL:%s'%(result.status,url)
    if resp:
        assert resp ==  result.json,'JSON :%s received instead of expected:%s for URL:%s'%(result.json,resp,url)        