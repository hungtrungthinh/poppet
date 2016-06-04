from unifispot.guest.models import Guest,Smsdata,Guestsession,Guesttrack
import arrow
from flask import current_app
from sqlalchemy import and_,or_
from .models import Sitestat
from unifispot.const import GUESTRACK_VOUCHER_AUTH,GUESTRACK_SMS_AUTH,GUESTRACK_EMAIL_AUTH,GUESTRACK_PREAUTH,GUESTRACK_SOCIAL_AUTH
from unifispot.extensions import db


def update_daily_stat(siteid,daydate):
    '''Update daily status of a particular site on the given date.

        siteid => siteid
        daydate => arrow date with timezone

        Creates/updates an entry in Sitestat corresponding to given date start (on site's timezone/logical time)

    '''
    day_start   = daydate.floor('day').to('UTC').naive
    day_end     = daydate.ceil('day').to('UTC').naive

    tracks_dict     = {}
    num_visits      = 0
    login_types     = {'email':0,'fb':0,'phone':0,'voucher':0,'returning':0}
    num_checkins    = 0
    num_likes       = 0

    def update_login_type(track):
        #global login_types
        if track.state == GUESTRACK_SMS_AUTH:
            login_types['phone'] += 1
        elif track.state == GUESTRACK_EMAIL_AUTH:
            login_types['email'] += 1
        elif track.state == GUESTRACK_VOUCHER_AUTH:
            login_types['voucher'] += 1
        elif track.state == GUESTRACK_SOCIAL_AUTH:
            login_types['fb'] += 1
        elif track.state == GUESTRACK_PREAUTH:
            login_types['returning'] += 1   

        if track.fb_liked == 1:
            num_likes += 1         
        if track.fb_posted == 1:
            num_likes += 1     


    tracks = Guesttrack.query.filter(and_(Guesttrack.site_id==siteid,Guesttrack.timestamp>=day_start,
                    Guesttrack.timestamp<=day_end)).all()

    current_app.logger.debug('Getting all tracks for site:%s from:%s to :%s'%(siteid,day_start,day_end))

    #iterate through tracks and identify unique ones
    for track in tracks:
        #current_app.logger.debug('Processing guesttrack:%s timestamp:%s'%(track.id,track.timestamp))
        prv_track = tracks_dict.get(track.device_mac)
        if prv_track:
            #track already added,check time difference
            prv_time = arrow.get(prv_track)
            new_time = arrow.get(track.timestamp)
            time_diff = (new_time - prv_time).seconds
            if time_diff > 2*3600:
                #more than 2 hrs difference
                num_visits += 1
                tracks_dict[track.device_mac] = new_time
                update_login_type(track)
            elif time_diff > 0:
                #update mac time
                tracks_dict[track.device_mac] = new_time
        else:
            num_visits += 1
            tracks_dict[track.device_mac] = arrow.get(track.timestamp)
            update_login_type(track)

    num_newlogins = login_types['phone'] + login_types['email'] +login_types['fb'] +login_types['voucher'] 


    day_key = daydate.floor('day').naive
    #check if sitestat entry already exists for this site on the date
    check_sitestat = Sitestat.query.filter_by(site_id=siteid,date=day_key).first()
    if not check_sitestat:
        #add new entry
        sitestat = Sitestat(site_id=siteid,date=day_key,num_visits=num_visits,num_newlogins=num_newlogins,
                            num_repeats=login_types['returning'],num_emails=login_types['email'],
                            num_fb=login_types['fb'],num_vouchers=login_types['voucher'],
                            num_phones=login_types['phone'],num_likes=num_likes,num_checkins=num_checkins)

        db.session.add(sitestat)
        db.session.commit()

    else:
        #update
        check_sitestat.num_visits=num_visits
        check_sitestat.num_likes=num_likes
        check_sitestat.num_checkins=num_checkins
        check_sitestat.num_newlogins=num_newlogins
        check_sitestat.num_repeats=login_types['returning']
        check_sitestat.num_emails=login_types['email']
        check_sitestat.num_fb=login_types['fb']
        check_sitestat.num_vouchers=login_types['voucher']
        check_sitestat.num_phones=login_types['phone']
        check_sitestat.last_updated = arrow.utcnow().naive
        db.session.commit()

