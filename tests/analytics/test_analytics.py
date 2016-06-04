''' Tests to check analytics gathering

'''

import sys

from flask import current_app,url_for
from sqlalchemy import and_,or_


from unifispot.client.models import Client,Wifisite,Voucher
from unifispot.analytics.models import Sitestat,Sitestatweek,Sitestatmonth
from unifispot.models import db
from unifispot.guest.models import Guest,Device,Guestsession,Guesttrack,Facebookauth,Smsdata
from hashids import Hashids
from random import randint
import time,uuid,arrow
import pytest
from unifispot.const import *
from unifispot.analytics.helpers import update_daily_stat,update_weekly_stat,update_monthly_stat
from tests.helpers.guest import randomMAC
from dateutil import tz
import random

from faker import Faker
fake = Faker()


@pytest.fixture(scope='function')
def populate_analytics(request):
    '''fixture used to populate guest_tracks to test analytics function

        
    '''
    site1        = Wifisite.query.filter_by(unifi_id='site1').first()  
    tracks  = []

    tzinfo = tz.gettz(site1.timezone)
    day_start   = arrow.now(tzinfo).floor('day').to('UTC')

    ap_mac =randomMAC()

    #create 20 tracks, starting from day start and spaced 1minutes apart
    for i in range(20):
        track = Guesttrack(ap_mac=ap_mac,device_mac=randomMAC(),site=site1,state=GUESTRACK_INIT,orig_url='',track_id=str(uuid.uuid4()))
        db.session.add(track)
        track.timestamp = day_start.replace(minutes=+i*1).naive
        tracks.append(track)
        #create device  
    db.session.commit() 

    day_start = arrow.now(tzinfo).floor('day').to('UTC').replace(days=-1)
    #create 20 tracks, starting from day start and spaced 1minutes apart on previous day
    for i in range(20):
        track = Guesttrack(ap_mac=ap_mac,device_mac=randomMAC(),site=site1,state=GUESTRACK_INIT,orig_url='',track_id=str(uuid.uuid4()))
        db.session.add(track)
        track.timestamp = day_start.replace(minutes=+i*1).naive
        tracks.append(track)
        #create device  
    db.session.commit() 

    day_start = arrow.now(tzinfo).floor('day').to('UTC').replace(days=+1)
    #create 20 tracks, starting from day start and spaced 1minutes apart on next day
    for i in range(20):
        track = Guesttrack(ap_mac=ap_mac,device_mac=randomMAC(),site=site1,state=GUESTRACK_INIT,orig_url='',track_id=str(uuid.uuid4()))
        db.session.add(track)
        track.timestamp = day_start.replace(minutes=+i*1).naive
        tracks.append(track)
        #create device  
    db.session.commit() 

@pytest.fixture(scope='function')
def populate_sitestats(request):
    '''fixture used to populate sitestat to test monthly/weekly analytics gathering

        
    '''
    site1        = Wifisite.query.filter_by(unifi_id='site1').first() 
    now = arrow.now()
    month_start = now.floor('month')
    days        = (now.ceil('month') - month_start).days
    for i in range(days):
        day_key = month_start.replace(days=i).floor('day').naive
        daystat = Sitestat(site_id=site1.id,date=day_key)
        daystat.num_visits     = 15
        daystat.num_likes      = 1
        daystat.num_checkins   = 2
        daystat.num_newlogins  = 7
        daystat.num_repeats    = 3
        daystat.num_emails     = 3
        daystat.num_fb         = 4
        daystat.num_vouchers   = 2
        daystat.num_phones     = 1
        db.session.add(daystat)
    db.session.commit()



def test_update_daily_stat1(session,populate_analytics):
    '''Check if update_daily_stat is able to gather correct analytics when 20 unique tracks are found'''
    site1 = Wifisite.query.filter_by(id=1).first()
    daydate = arrow.now()
    update_daily_stat(site1.id,daydate)
    sitestat = Sitestat.query.first()
 
    assert 0 == sitestat.get_total_logins(),'Num Logins is :%s instead of expected :%s' %(sitestat.get_total_logins(),0)
    assert 20 == sitestat.num_visits,'Num visits is :%s instead of expected :%s' %(sitestat.num_visits,20)


def test_update_daily_stat2(session,populate_analytics):
    '''Check if update_daily_stat is able to gather correct analytics when tracks which are closer in time are found'''
    site1 = Wifisite.query.filter_by(id=1).first()

    tzinfo = tz.gettz(site1.timezone)
    daydate  = arrow.now(tzinfo)
    starttime= daydate.floor('day').to('UTC')

    track1  = Guesttrack.query.first()
    #create similar tracks as track 1 with 5min timestamp difference
    for i in range(5):
        timestamp = starttime.replace(minute= 5 * i)
        track = Guesttrack(ap_mac=track1.ap_mac,device_mac=track1.device_mac,site=site1,state=GUESTRACK_INIT,orig_url='',track_id=str(uuid.uuid4()))       
        db.session.add(track)
        track.timestamp = timestamp.naive
        db.session.commit()

    
    update_daily_stat(site1.id,daydate)
    sitestat = Sitestat.query.first()
 
    assert 0 == sitestat.get_total_logins(),'Num Logins is :%s instead of expected :%s' %(sitestat.get_total_logins(),0)
    assert 20 == sitestat.num_visits,'Num visits is :%s instead of expected :%s' %(sitestat.num_visits,20)

def test_update_daily_stat3(session,populate_analytics):
    '''Check if update_daily_stat is able to gather correct analytics when tracks which are atleast 2hrs apart'''
    site1 = Wifisite.query.filter_by(id=1).first()

    tzinfo = tz.gettz(site1.timezone)
    daydate  = arrow.now(tzinfo)
    starttime= daydate.floor('day').to('UTC')

    track1  = Guesttrack.query.first()

    #create similar tracks as track 1 with 3hr timestamp difference
    for i in range(3):
        timestamp = starttime.replace(hours = + (3*i+3) )
        track = Guesttrack(ap_mac=track1.ap_mac,device_mac=track1.device_mac,site=site1,state=GUESTRACK_INIT,orig_url='',track_id=str(uuid.uuid4()))       
        db.session.add(track)
        track.timestamp = timestamp.naive
        db.session.commit()
  
    update_daily_stat(site1.id,daydate)
    sitestat = Sitestat.query.first()

    assert 0 == sitestat.get_total_logins(),'Num Logins is :%s instead of expected :%s' %(sitestat.get_total_logins(),0)
    assert 23 == sitestat.num_visits,'Num visits is :%s instead of expected :%s' %(sitestat.num_visits,20)

def test_update_daily_stat4(session,populate_analytics):
    '''Check if update_daily_stat is able to gather correct analytics when tracks different types of tracks are present'''
    site1 = Wifisite.query.filter_by(id=1).first()

    tzinfo = tz.gettz(site1.timezone)
    daydate  = arrow.now(tzinfo)
    starttime= daydate.floor('day').to('UTC')
    track1  = Guesttrack.query.first()

    #create 5 SMS tracks with unique MACs
    for i in range(5):
        timestamp = starttime.replace(hours = +5, minutes=+5*i )
        track = Guesttrack(ap_mac=track1.ap_mac,device_mac=randomMAC(),site=site1,state=GUESTRACK_INIT,orig_url='',track_id=str(uuid.uuid4()))       
        db.session.add(track)
        track.timestamp = timestamp.naive
        track.state = GUESTRACK_SMS_AUTH
        db.session.commit()

    #create 8 Email tracks with unique MACs
    for i in range(8):
        timestamp = starttime.replace(hours = +5, minutes=+5*i )
        track = Guesttrack(ap_mac=track1.ap_mac,device_mac=randomMAC(),site=site1,state=GUESTRACK_INIT,orig_url='',track_id=str(uuid.uuid4()))       
        db.session.add(track)
        track.timestamp = timestamp.naive
        track.state = GUESTRACK_EMAIL_AUTH
        db.session.commit()

    #create 4 Voucher tracks with unique MACs
    for i in range(4):
        timestamp = starttime.replace(hours = +5, minutes=+5*i )
        track = Guesttrack(ap_mac=track1.ap_mac,device_mac=randomMAC(),site=site1,state=GUESTRACK_INIT,orig_url='',track_id=str(uuid.uuid4()))       
        db.session.add(track)
        track.timestamp = timestamp.naive
        track.state = GUESTRACK_VOUCHER_AUTH
        db.session.commit()

    #create 11 returning tracks with unique MACs
    for i in range(11):
        timestamp = starttime.replace(hours = +5, minutes=+5*i )
        track = Guesttrack(ap_mac=track1.ap_mac,device_mac=randomMAC(),site=site1,state=GUESTRACK_INIT,orig_url='',track_id=str(uuid.uuid4()))       
        db.session.add(track)
        track.timestamp = timestamp.naive
        track.state = GUESTRACK_PREAUTH
        db.session.commit()

    #create 20 FB tracks with unique MACs
    for i in range(20):
        timestamp = starttime.replace(hours = +5, minutes=+5*i )
        track = Guesttrack(ap_mac=track1.ap_mac,device_mac=randomMAC(),site=site1,state=GUESTRACK_INIT,orig_url='',track_id=str(uuid.uuid4()))       
        db.session.add(track)
        track.timestamp = timestamp.naive
        track.state = GUESTRACK_SOCIAL_AUTH
        db.session.commit()        
  
    update_daily_stat(site1.id,daydate)
    sitestat = Sitestat.query.first()

    assert 48 == sitestat.get_total_logins(),'Num Logins is :%s instead of expected :%s' %(sitestat.get_total_logins(),48)
    assert 68 == sitestat.num_visits,'Num visits is :%s instead of expected :%s' %(sitestat.num_visits,68)
    assert 11 == sitestat.num_repeats,'num_repeats is :%s instead of expected :%s' %(sitestat.num_repeats,11)
    assert 8 == sitestat.num_emails,'num_emails is :%s instead of expected :%s' %(sitestat.num_emails,8)
    assert 20 == sitestat.num_fb,'num_fb is :%s instead of expected :%s' %(sitestat.num_fb,20)
    assert 4 == sitestat.num_vouchers,'num_vouchers is :%s instead of expected :%s' %(sitestat.num_vouchers,20)
    assert 5 == sitestat.num_phones,'num_phones is :%s instead of expected :%s' %(sitestat.num_phones,5)


def test_update_daily_stat5(session,populate_analytics):
    '''Check if update_daily_stat is updating same entry even after updating timezone'''
    site1 = Wifisite.query.filter_by(id=1).first()
    daydate = arrow.now()
    #run daily_stats 
    update_daily_stat(site1.id,daydate)

    #update timezone
    site1.timezone = 'US/Pacific'
    db.session.commit()
    #run daily_stats 
    update_daily_stat(site1.id,daydate)

    sitestat = Sitestat.query.first()
 
    assert 1 == Sitestat.query.count(),'Sitestat count is not 1'
    assert 0 == sitestat.get_total_logins(),'Num Logins is :%s instead of expected :%s' %(sitestat.get_total_logins(),0)
    assert 20 == sitestat.num_visits,'Num visits is :%s instead of expected :%s' %(sitestat.num_visits,20)

def test_update_weekly_stat(session,populate_sitestats):
    '''Check if update_weekly_stat is updating same entry even after updating timezone'''
    site1 = Wifisite.query.filter_by(id=1).first()
    daydate = arrow.now()
    #run daily_stats 
    update_weekly_stat(site1.id,daydate)

    weekstat = Sitestatweek.query.first()
 
    assert 1    == Sitestatweek.query.count(),'Sitestat count is not 1'
    assert 70   == weekstat.get_total_logins(),'Num Logins is :%s instead of expected :%s' %(weekstat.get_total_logins(),70)
    assert 105  == weekstat.num_visits,'Num visits is :%s instead of expected :%s' %(weekstat.num_visits,105)    
    assert 7    == weekstat.num_likes,'num_likes is :%s instead of expected :%s' %(weekstat.num_likes,7)    
    assert 7    == weekstat.num_likes,'num_likes is :%s instead of expected :%s' %(weekstat.num_likes,7)    
    assert 14   == weekstat.num_checkins,'num_checkins is :%s instead of expected :%s' %(weekstat.num_checkins,14)    
    assert 49   == weekstat.num_newlogins,'num_newlogins is :%s instead of expected :%s' %(weekstat.num_newlogins,49)    
    assert 21   == weekstat.num_repeats,'num_repeats is :%s instead of expected :%s' %(weekstat.num_repeats,21)    
    assert 21   == weekstat.num_emails,'num_emails is :%s instead of expected :%s' %(weekstat.num_emails,21)    
    assert 28   == weekstat.num_fb,'num_fb is :%s instead of expected :%s' %(weekstat.num_fb,28)    
    assert 14   == weekstat.num_vouchers,'num_vouchers is :%s instead of expected :%s' %(weekstat.num_vouchers,14)    
    assert 7   == weekstat.num_phones,'num_phones is :%s instead of expected :%s' %(weekstat.num_emails,7)    



def test_update_monthly_stat(session,populate_sitestats):
    '''Check if update_monthly_stat is updating same entry even after updating timezone'''
    site1 = Wifisite.query.filter_by(id=1).first()
    daydate = arrow.now()
    days        = (daydate.ceil('month') - daydate.floor('month')).days    
    #run daily_stats 
    update_monthly_stat(site1.id,daydate)

    monthstat = Sitestatmonth.query.first()
 
    assert 1            == Sitestatmonth.query.count(),'Sitestatmonth count is not 1'
    assert 10* days     == monthstat.get_total_logins(),'Num Logins is :%s instead of expected :%s' %(monthstat.get_total_logins(),10* days )
    assert 15* days     == monthstat.num_visits,'Num visits is :%s instead of expected :%s' %(monthstat.num_visits,15* days )    
    assert 1* days     == monthstat.num_likes,'num_likes is :%s instead of expected :%s' %(monthstat.num_likes,1* days)    
    assert 2* days     == monthstat.num_checkins,'num_checkins is :%s instead of expected :%s' %(monthstat.num_checkins,2* days)    
    assert 7* days     == monthstat.num_newlogins,'num_newlogins is :%s instead of expected :%s' %(monthstat.num_newlogins,7* days)    
    assert 3* days     == monthstat.num_repeats,'num_repeats is :%s instead of expected :%s' %(monthstat.num_repeats,3* days)    
    assert 3* days     == monthstat.num_emails,'num_emails is :%s instead of expected :%s' %(monthstat.num_emails,3* days)    
    assert 4* days     == monthstat.num_fb,'num_fb is :%s instead of expected :%s' %(monthstat.num_fb,4* days)    
    assert 2* days     == monthstat.num_vouchers,'num_vouchers is :%s instead of expected :%s' %(monthstat.num_vouchers,2* days )    
    assert 1* days     == monthstat.num_phones,'num_phones is :%s instead of expected :%s' %(monthstat.num_emails,1* days )