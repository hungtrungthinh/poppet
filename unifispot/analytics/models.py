from unifispot.models import User
from unifispot.extensions import db
from flask_security import current_user
from flask import current_app
from unifispot.const import AUTH_TYPE_BYPASS,FACEBOOK_LIKE_OFF,FACEBOOK_POST_OFF
from sqlalchemy import and_,or_
from flask_security.utils import encrypt_password

import arrow,math,datetime


from unifispot.const import *
from unifispot.base.utils.helper import dict_normalise_values


class Sitestat(db.Model):
    ''' Class to represent daily statistics

    '''
    id              = db.Column(db.Integer, primary_key=True)   
    site_id         = db.Column(db.Integer, db.ForeignKey('wifisite.id'))  
    date            = db.Column(db.DateTime,index=True)   #used as key
    num_visits      = db.Column(db.Integer,default=0)
    num_newlogins   = db.Column(db.Integer,default=0)
    num_repeats     = db.Column(db.Integer,default=0)
    num_emails      = db.Column(db.Integer,default=0)
    num_fb          = db.Column(db.Integer,default=0)
    num_vouchers    = db.Column(db.Integer,default=0)
    num_phones      = db.Column(db.Integer,default=0)
    num_checkins    = db.Column(db.Integer,default=0)
    num_likes       = db.Column(db.Integer,default=0)
    avg_time        = db.Column(db.Integer,default=0)
    avg_data        = db.Column(db.Integer,default=0)
    last_updated    = db.Column(db.DateTime,default=datetime.datetime.utcnow,index=True)

 
    def get_total_logins(self):
        '''returns total logins for the day '''
 
        return self.num_newlogins + self.num_repeats

    def __add__(self,other):
        '''Add two sitestat objects, used for calculating weekly and monthly status

        '''
        return Sitestat(num_visits= int(self.num_visits) + int(other.num_visits),
                       num_newlogins= self.num_newlogins + other.num_newlogins,
                       num_repeats = self.num_repeats + other.num_repeats,
                       num_emails =  self.num_emails + other.num_emails,
                       num_fb = self.num_fb + other.num_fb,
                       num_vouchers = self.num_vouchers + other.num_vouchers,
                       num_phones = self.num_phones + other.num_phones,
                       num_checkins = self.num_checkins + other.num_checkins,
                       num_likes = self.num_likes + other.num_likes)
       
    @classmethod
    def get_dashboard_stats(cls,daystats):
        logins = []
        newlogins = []
        likes = []
        checkins = []
        maxlogin = 0
        maxsocial = 0
        total_visits = 0
        total_logins = 0
        total_likes = 0
        total_checkins = 0
        total_emails    = 0
        total_vouchers    = 0
        total_fbs    = 0
        total_phones = 0

        for daystat in daystats:
            timestamp = arrow.get(daystat.date).timestamp * 1000
            today_logins = daystat.get_total_logins()
            today_newlogins = daystat.num_newlogins

            total_visits += daystat.num_visits
            total_logins += today_logins
            total_likes += daystat.num_likes
            total_checkins += daystat.num_checkins
            total_emails += daystat.num_emails
            total_vouchers += daystat.num_vouchers
            total_fbs += daystat.num_fb
            total_phones += daystat.num_phones

            logins.append([timestamp,today_logins])
            newlogins.append([timestamp,today_newlogins])
            likes.append([timestamp,daystat.num_likes])
            checkins.append([timestamp,daystat.num_checkins])

            if today_logins > maxlogin:
                maxlogin = today_logins
            if daystat.num_likes > maxsocial:
                maxsocial = daystat.num_likes
            if daystat.num_checkins > maxsocial:
                maxsocial = daystat.num_checkins

        return {'status': 1,'logins':logins,'newlogins':newlogins,'maxlogin':maxlogin,
                'total_visits':total_visits,'total_logins':total_logins,'total_likes':total_likes,
                'total_checkins':total_checkins,'total_emails':total_emails,'total_phones':total_phones,
                'total_fbs':total_fbs,'total_vouchers':total_vouchers,'likes':likes,'checkins':checkins,
                'maxsocial':maxsocial}

    @classmethod
    def get_combine_stats(cls,daystats):
        logins = {}
        newlogins = {}
        likes = {}
        checkins = {}
        maxlogin = 0
        maxsocial = 0
        total_visits = 0
        total_logins = 0
        total_likes = 0
        total_checkins = 0
        total_emails    = 0
        total_vouchers    = 0
        total_fbs    = 0
        total_phones = 0

        def dict_to_list(dict):
            lst = []
            for key in sorted(dict):
                lst.append([key,dict[key]])
            return lst

        for daystat in daystats:
            timestamp = arrow.get(daystat.date).timestamp * 1000
            today_logins = daystat.get_total_logins()
            today_newlogins = daystat.num_newlogins
            total_visits += daystat.num_visits
            total_logins += today_logins
            total_likes += daystat.num_likes
            total_checkins += daystat.num_checkins
            total_emails += daystat.num_emails
            total_vouchers += daystat.num_vouchers
            total_fbs += daystat.num_fb
            total_phones += daystat.num_phones



            #update daily like/checkin/login/newlogins
            if logins.get(timestamp):
                logins[timestamp] += today_logins
            else:
                logins[timestamp] = today_logins

            if newlogins.get(timestamp):
                newlogins[timestamp] += today_newlogins
            else:
                newlogins[timestamp] = today_newlogins

            if likes.get(timestamp):
                likes[timestamp] += daystat.num_likes
            else:
                likes[timestamp] = daystat.num_likes

            if checkins.get(timestamp):
                checkins[timestamp] += daystat.num_checkins
            else:
                checkins[timestamp] = daystat.num_checkins

            maxlogin = max(logins.values())
            maxsocial = max(max(checkins.values()),max(likes.values()))

        return {'status': 1,'logins':dict_to_list(logins),'newlogins':dict_to_list(newlogins),'maxlogin':maxlogin,
                'total_visits':total_visits,'total_logins':total_logins,'total_likes':total_likes,
                'total_checkins':total_checkins,'total_emails':total_emails,'total_phones':total_phones,
                'total_fbs':total_fbs,'total_vouchers':total_vouchers,'likes':dict_to_list(likes),
                'checkins':dict_to_list(checkins),'maxsocial':maxsocial}

