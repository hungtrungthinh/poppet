from unifispot.extensions import db
import datetime
import uuid
from unifispot.const import *
from sqlalchemy_utils import ArrowType
from sqlalchemy import and_,or_
import arrow
import math

class Guest(db.Model):
    ''' Class to represent guest profile, it will be filled fully/partially depending upon site configuration

    '''
    id          = db.Column(db.Integer, primary_key=True)
    site_id     = db.Column(db.Integer, db.ForeignKey('wifisite.id')) 
    firstname   = db.Column(db.String(60))
    lastname    = db.Column(db.String(60))
    age         = db.Column(db.Integer,index=True)
    gender      = db.Column(db.Integer,index=True)
    state       = db.Column(db.Integer,index=True)
    email       = db.Column(db.String(60))
    phonenumber = db.Column(db.String(15))
    agerange    = db.Column(db.String(15))
    devices     = db.relationship('Device', backref='guest',lazy='dynamic')
    fb_profile  = db.Column(db.Integer, db.ForeignKey('facebookauth.id'))
    fb_liked    = db.Column(db.Integer)
    fb_posted   = db.Column(db.Integer)
    created_at  = db.Column(db.DateTime,default=datetime.datetime.utcnow,index=True)
    apisync     = db.Column(db.Integer,index=False)  #Flag to be set after syncing to API
    synchedat   = db.Column(db.DateTime,index=True) #synched time in UTC
    demo        = db.Column(db.Boolean(),default=0,index=True)
    newsletter  = db.Column(db.Boolean(),default=0,index=True)
    dob         = db.Column(db.String(15))
    details     = db.Column(db.Text)

    def get_device_phonenumber(self):
        for device in self.devices:
            phonenumber = device.get_phonenumber()
            if phonenumber:
                return phonenumber
        return ''

    def get_gender(self):
        if self.gender == 1 :
            return 'M'
        elif self.gender == 2:
            return 'F'
        else:
            return 'N/A'

    def populate_from_email_form(self,form,form_fields):
        details = ''
        if hasattr(form,'email'):
            self.email = form.email.data        
        if hasattr(form,'firstname'):
            self.firstname = form.firstname.data
        if hasattr(form,'lastname'):
            self.lastname = form.lastname.data
        if hasattr(form,'phonenumber'):
            self.phonenumber = form.phonenumber.data
        if hasattr(form,'dob'):
            self.dob = form.dob.data    
        if hasattr(form,'newsletter'):
            self.newsletter = form.newsletter.data                       
        if hasattr(form,'extra1'):
            details += '%s:%s  '%(form.extra1.label.text,form.extra1.data)
        if hasattr(form,'extra2'):
            details += '%s:%s'%(form.extra2.label.text,form.extra2.data)    
        self.details = details          

    def search_query(self,term,offset=0,limit=10,sort=None,modal_filters=None):
        main_query = Guest.query.filter(and_(Guest.site_id==modal_filters['siteid'],Guest.demo ==0, 
                    Guest.created_at >= modal_filters['startdate'],Guest.created_at <= modal_filters['enddate']))
        if term:
            result_qry = main_query
        else:
            result_qry = main_query
        result_qry = result_qry.distinct( )
        total = result_qry.count()
        if sort['column'] == "0" :
            if sort['order'] == "desc":
                results_ord = result_qry.order_by(Guest.firstname.desc())
            else:
                results_ord = result_qry.order_by(Guest.firstname.asc())
        elif sort['column'] == "1" :
            if sort['order'] == "desc":
                results_ord = result_qry.order_by(Guest.lastname.desc())
            else:
                results_ord = result_qry.order_by(Guest.lastname.asc())       
        elif sort['column'] == "2" :
            if sort['order'] == "desc":
                results_ord = result_qry.order_by(Guest.age.desc())
            else:
                results_ord = result_qry.order_by(Guest.age.asc())  
        elif sort['column'] == "3" :
            if sort['order'] == "desc":
                results_ord = result_qry.order_by(Guest.gender.desc())
            else:
                results_ord = result_qry.order_by(Guest.gender.asc())  
        elif sort['column'] == "4" :
            if sort['order'] == "desc":
                results_ord = result_qry.order_by(Guest.phonenumber.desc())
            else:
                results_ord = result_qry.order_by(Guest.phonenumber.asc())  
        elif sort['column'] == "5" :
            if sort['order'] == "desc":
                results_ord = result_qry.order_by(Guest.email.desc())
            else:
                results_ord = result_qry.order_by(Guest.email.asc())   
        elif sort['column'] == "6" :
            if sort['order'] == "desc":
                results_ord = result_qry.order_by(Guest.created_at.desc())
            else:
                results_ord = result_qry.order_by(Guest.created_at.asc())                                  
        else:
            results_ord = result_qry.order_by(Guest.firstname.asc())  
        results = results_ord.offset(offset).limit(limit).all()
        print {'total':total,'results':results}
        return {'total':total,'results':results}


    def to_table_row(self):
        created_at = self.created_at.strftime("%d/%m/%Y") if self.created_at else ''
        phonenumber = self.phonenumber if self.phonenumber else self.get_device_phonenumber()
        newsletter = 'yes' if self.newsletter else 'no'
        return {'firstname':self.firstname,'age':self.age,'email':self.email,
                'lastname':self.lastname,'phonenumber':self.phonenumber,
                'id':self.id,'gender':self.get_gender(),'created_at':created_at,'site_id':self.site_id,
                'newsletter':self.newsletter,'dob':self.dob,'details':self.details,'agerange':self.agerange
                }

    def to_dict(self):
        created_at = self.created_at.strftime("%d/%m/%Y") if self.created_at else ''
        phonenumber = self.phonenumber if self.phonenumber else self.get_device_phonenumber()
        newsletter = 'yes' if self.newsletter else 'no'
        return {'firstname':self.firstname,'age':self.age,'email':self.email,
                'lastname':self.lastname,'phonenumber':self.phonenumber,
                'id':self.id,'gender':self.get_gender(),'created_at':created_at,'site_id':self.site_id,
                'newsletter':self.newsletter,'dob':self.dob,'details':self.details,'agerange':self.agerange
                }     

    def to_list(self):
        created_at = self.created_at.strftime("%d/%m/%Y") if self.created_at else ''
        phonenumber = self.phonenumber if self.phonenumber else self.get_device_phonenumber()
        newsletter = 'yes' if self.newsletter else 'no'
        #convert to list add replace None by ''
        list_to_clean =  [self.firstname,self.lastname,self.email,created_at,phonenumber,self.age,self.get_gender(),\
                        newsletter,self.dob,self.agerange,self.details]           
        return [x.encode('ascii','ignore') if x else '' for x in list_to_clean]

    def get_csv_headers(self):
        return ['Firstname','Lastname','Email','Created On','Phone','Age','Gender',"Newsletter",'DOB','Age Range','Details']

class Device(db.Model):
    ''' Class to represent guest's device, each guest can have multiple devices attached to his account

    '''
    id          = db.Column(db.Integer, primary_key=True)
    mac         = db.Column(db.String(30),index=True)
    hostname    = db.Column(db.String(60),index=True)
    state       = db.Column(db.Integer)
    created_at  = db.Column(db.DateTime,default=datetime.datetime.utcnow,index=True)
    guest_id    = db.Column(db.Integer, db.ForeignKey('guest.id'))
    site_id     = db.Column(db.Integer, db.ForeignKey('wifisite.id'))
    sessions    = db.relationship('Guestsession', backref='device',lazy='dynamic')
    smsdatas    = db.relationship('Smsdata', backref='device',lazy='dynamic')
    expires_at  = db.Column(db.DateTime)          #Expiry time for last used voucher  
    demo        = db.Column(db.Integer,default=0,index=True)
    sms_confirm = db.Column(db.Integer,default=0,index=True) #used to verify if the device's phone number is confirmed
    voucher_id  = db.Column(db.Integer,index=True) #last used voucher id

    def get_monthly_usage(self):
        '''Returns the total monthly free data usage for this device

            Excludes voucher usage
        '''
        firstday    = arrow.now(self.site.timezone).floor('month').to('UTC').naive
        sessions    = Guestsession.query.filter(and_(Guestsession.device_id==self.id,
                        Guestsession.starttime >= firstday)).all()
        total_data  = 0
        for session in sessions:
            if session.state != GUESTRACK_VOUCHER_AUTH and session.data_used:
                total_data += int(session.data_used)

        #convert bytes to Mb

        data_mb = int(math.ceil((total_data/1024000.0)))
        return data_mb

    def get_phonenumber(self):
        '''Returns the phonenumber connected to this account

        '''
        return ';'.join([x.phonenumber for x in self.smsdatas])

    def get_voucher(self):
        '''Returns a valid voucher id if any associated with this device, if nothing found returns None

        '''
        for voucher in self.vouchers:
            if voucher.check_validity():
                return voucher.id

        return None



class Guestsession(db.Model):
    ''' Class to represent guest session. Each session is associated to a Guest and will have a state associated with it.

    '''
    id          = db.Column(db.Integer, primary_key=True)
    site_id     = db.Column(db.Integer, db.ForeignKey('wifisite.id'))
    device_id   = db.Column(db.Integer, db.ForeignKey('device.id'))
    voucher_id  = db.Column(db.Integer, db.ForeignKey('voucher.id'))
    starttime   = db.Column(db.DateTime,default=datetime.datetime.utcnow,index=True)
    lastseen    = db.Column(db.DateTime,index=True,default=datetime.datetime.utcnow)
    stoptime    = db.Column(db.DateTime,index=True)   #Time at which session is stopped, to be filled by session updator
    expiry      = db.Column(db.DateTime,index=True,default=datetime.datetime.utcnow)   #predicted expiry time,default to 60 minutes
    temp_login  = db.Column(db.Integer,default=0)
    duration    = db.Column(db.Integer,default=60)
    ban_ends    = db.Column(db.DateTime,index=True)
    data_used   = db.Column(db.String(20),default=0)            #Data used up in this session
    state       = db.Column(db.Integer)
    mac         = db.Column(db.String(30),index=True)
    d_updated   = db.Column(db.String(20))            #data updated last
    guesttracks = db.relationship('Guesttrack', backref='guestsession',lazy='dynamic')
    demo        = db.Column(db.Integer,default=0,index=True)
    obj_id      = db.Column(db.String(30),index=True)  #_id of document in guest collection of unifi

    #Search option with paging and sorting, uses LIKE on INDEXED fields 
    #and return num of total results  as well as number of rows controlled by paging
    def search_query(self,term,offset=0,limit=10,sort=None,modal_filters=None):
        main_query = Guestsession.query.filter(and_(Guestsession.site_id==modal_filters['siteid'],
                    Guestsession.starttime >= modal_filters['startdate'],Guestsession.starttime <= modal_filters['enddate'],
                    Guestsession.obj_id != None))
        if term:
            result_qry = main_query
        else:
            result_qry = main_query
        result_qry = result_qry.distinct( )
        total = result_qry.count()
        if sort['column'] == "0" :
            if sort['order'] == "desc":
                results_ord = result_qry.order_by(Guestsession.starttime.desc())
            else:
                results_ord = result_qry.order_by(Guestsession.starttime.asc())
        elif sort['column'] == "1" :
            if sort['order'] == "desc":
                results_ord = result_qry.order_by(Guestsession.stoptime.desc())
            else:
                results_ord = result_qry.order_by(Guestsession.stoptime.asc())  
        elif sort['column'] == "2" :
            if sort['order'] == "desc":
                results_ord = result_qry.order_by(Guestsession.mac.desc())
            else:
                results_ord = result_qry.order_by(Guestsession.mac.asc()) 
        elif sort['column'] == "3" :
            if sort['order'] == "desc":
                results_ord = result_qry.order_by(Guestsession.data_used.desc())
            else:
                results_ord = result_qry.order_by(Guestsession.data_used.asc())                                 
        else:
            results_ord = result_qry.order_by(Guestsession.id.asc())  
        results = results_ord.offset(offset).limit(limit).all()
        return {'total':total,'results':results}    

    def to_table_row(self):
        site = self.site   
        stoptime = 'N/A'     
        starttime = arrow.get(self.starttime).to(site.timezone).format('DD-MM-YYYY HH:mm:ss')
        if self.stoptime:
            stoptime = arrow.get(self.stoptime).to(site.timezone).format('DD-MM-YYYY HH:mm:ss')
        #get data_used and convert to Mb
        dta = int(self.data_used) if self.data_used else 0
        data_used = str(math.ceil((dta/1024000.0)))

        return {'id':self.id,'stoptime':stoptime,'starttime':starttime,
                'mac':self.mac,'data_used':data_used,'phonenumber':self.device.get_phonenumber()
                }        
    def to_list(self):
        site = self.site
        starttime = arrow.get(self.starttime).to(site.timezone).format('DD-MM-YYYY HH:mm:ss')
        stoptime = 'N/A'
        if self.stoptime:
            stoptime = arrow.get(self.stoptime).to(site.timezone).format('DD-MM-YYYY HH:mm:ss')        
        #get data_used and convert to Mb
        dta = int(self.data_used) if self.data_used else 0
        data_used = str(math.ceil((dta/1024000.0)))
        list_to_clean = [ starttime,stoptime,self.mac,data_used,self.device.get_phonenumber()]
        return [x if x else '' for x in list_to_clean]

class Guesttrack(db.Model):
    ''' Class to track connection attempts, this is also used to track login process

    '''
    id          = db.Column(db.Integer, primary_key=True)
    track_id    = db.Column(db.String(40),index=True,unique=True)
    site_id     = db.Column(db.Integer, db.ForeignKey('wifisite.id'))
    session_id  = db.Column(db.Integer, db.ForeignKey('guestsession.id'))
    ap_mac      = db.Column(db.String(20),index=True)
    device_mac  = db.Column(db.String(20),index=True)
    timestamp   = db.Column(db.DateTime,default=datetime.datetime.utcnow,index=True)
    state       = db.Column(db.Integer,index=True)
    fb_liked    = db.Column(db.Integer,index=True,default=0)
    fb_posted   = db.Column(db.Integer,index=True,default=0)
    orig_url    = db.Column(db.String(200))
    demo        = db.Column(db.Integer,default=0,index=True)
    duration    = db.Column(db.Integer,default=60) #Duration authorized in minutes
    temp_login  = db.Column(db.Integer,default=0)

    def is_authorized(self):
        '''Return True if the guest_track is marked as authorized

        '''
        if self.state == GUESTRACK_SMS_AUTH and self.site.phone_login_en():
            return True
        elif self.state == GUESTRACK_EMAIL_AUTH  and self.site.email_login_en():
            return True
        elif self.state == GUESTRACK_VOUCHER_AUTH  and self.site.voucher_login_en():
            return True
        elif self.state == GUESTRACK_SOCIAL_AUTH  and self.site.fb_login_en():
            return True            
        elif self.state == GUESTRACK_PREAUTH:
            return True       
        else:
            return False

    def is_temp_authorized(self):
        ''' Return True if guest_track marked for is_temp_authorized

        '''
        if self.state == GUESTRACK_SOCIAL_PREAUTH:
            return True
        else:
            return False


class Facebookauth(db.Model):
    ''' Class to represent guest's Facebook connection, this is needed as one common APP is used for tracking guests in different sites.

    '''
    id          = db.Column(db.Integer, primary_key=True)
    profile_id  = db.Column(db.String(200), nullable=False,index=True)
    site_id     = db.Column(db.Integer, db.ForeignKey('wifisite.id'))    
    token       = db.Column(db.Text, nullable=False)
    state       = db.Column(db.Integer)
    guests      = db.relationship('Guest', backref='facebookauth',lazy='dynamic')
    
class Smsdata(db.Model):
    ''' Class to represent Device's SMS data

    '''
    id          = db.Column(db.Integer, primary_key=True)
    site_id     = db.Column(db.Integer, db.ForeignKey('wifisite.id'))    
    device_id    = db.Column(db.Integer, db.ForeignKey('device.id'))    
    phonenumber = db.Column(db.String(20),index=True)    
    authcode    = db.Column(db.String(20),index=True)    
    timestamp   = db.Column(db.DateTime,default=datetime.datetime.utcnow)
    status      = db.Column(db.Integer, index=True,default=SMS_DATA_NEW)
    send_try    = db.Column(db.Integer, index=True,default=0)