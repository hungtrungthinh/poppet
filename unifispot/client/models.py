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


class Client(User):
    ''' Class to represent admin, each admin will be associated with a user of type admin

    '''
    id          = db.Column(db.Integer,db.ForeignKey('user.id'), primary_key=True)
    sites       = db.relationship('Wifisite', backref='client',lazy='dynamic')  
    __mapper_args__ = {'polymorphic_identity': 'client'}
    admin_id        = db.Column(db.Integer, db.ForeignKey('admin.id'))
    account_id      = db.Column(db.Integer, db.ForeignKey('account.id')) 

    #Search option with paging and sorting, uses LIKE on INDEXED fields 
    #and return num of total results  as well as number of rows controlled by paging
    def search_query(self,term,offset=0,limit=10,sort=None,modal_filters=None):
        if modal_filters:
            main_query = Client.query.filter_by(account_id=modal_filters['account_id'])
        else:
            main_query = Client.query
        if term:
            result_qry = main_query.filter(or_( Client.email.like('%'+term+'%'), Client.displayname.like('%'+term+'%')))
        else:
            result_qry = main_query
        result_qry = result_qry.distinct( )
        total = result_qry.count()
        if sort['column'] == "0" :
            if sort['order'] == "desc":
                results_ord = result_qry.order_by(User.email.desc())
            else:
                results_ord = result_qry.order_by(User.email.asc())
        else:
            results_ord = result_qry.order_by(User.id.asc())  
        results = results_ord.offset(offset).limit(limit).all()
        return {'total':total,'results':results}

    def to_table_row(self):
        return {'displayname':self.displayname,
                'email':self.email,
                'id':self.id,
                'account_id':self.account_id
                }

    def to_dict(self):
        return {'displayname':self.displayname,
                'email':self.email,
                'id':self.id,
                'account_id':self.account_id
                }
    def populate_from_form(self,form):
        self.email = form.email.data
        self.displayname = form.displayname.data
        if form.password.data:
            self.password = encrypt_password(form.password.data)

    def check_admin(self):        
        return False

    def get_user_type(self):  
        return ROLE_CLIENT

    def check_client(self):
        return True

    def get_admin_id(self):
        return NotImplemented




        
class Wifisite(db.Model):
    ''' Class to represent wifi sites. Each client can have multiple sites


    '''
    id                  = db.Column(db.Integer, primary_key=True)
    client_id           = db.Column(db.Integer, db.ForeignKey('client.id'))
    admin_id            = db.Column(db.Integer, db.ForeignKey('admin.id'))
    account_id          = db.Column(db.Integer, db.ForeignKey('account.id'))     
    name                = db.Column(db.String(255),index=True,default="defaultsite")  
    default_landing     = db.Column(db.Integer)
    landingpages        = db.relationship('Landingpage', backref='site',lazy='dynamic')
    guests              = db.relationship('Guest', backref='site',lazy='dynamic')
    unifi_id            = db.Column(db.String(50),index=True,default="default")
    devices             = db.relationship('Device', backref='site',lazy='dynamic')    
    sessions            = db.relationship('Guestsession', backref='site',lazy='dynamic')    
    guesttracks         = db.relationship('Guesttrack', backref='site',lazy='dynamic')    
    sitefiles           = db.relationship('Sitefile', backref='site',lazy='dynamic')    
    facebookauths       = db.relationship('Facebookauth', backref='site',lazy='dynamic')    
    vouchers            = db.relationship('Voucher', backref='site',lazy='dynamic')    
    sitestats           = db.relationship('Sitestat', backref='site',lazy='dynamic')    
    voucherdesign       = db.relationship('Voucherdesign', backref='site',lazy='dynamic')    
    template            = db.Column(db.String(50),default='template1')    
    emailformfields     = db.Column(db.Integer,default=(FORM_FIELD_LASTNAME+FORM_FIELD_FIRSTNAME))    
    auth_method         = db.Column(db.Integer,default=AUTH_TYPE_ALL)
    auth_fb_like        = db.Column(db.Integer,default=FACEBOOK_LIKE_OFF)
    auth_fb_post        = db.Column(db.Integer,default=FACEBOOK_POST_OFF)
    redirect_method     = db.Column(db.Integer,default=REDIRECT_ORIG_URL)
    reports_type        = db.Column(db.Integer,default=CLIENT_REPORT_WEEKLY)
    reports_list        = db.Column(db.String(400))
    enable_redirect     = db.Column(db.Boolean())
    redirect_url        = db.Column(db.String(200),default='http://www.unifispot.com')
    fb_appid            = db.Column(db.String(200))
    fb_app_secret       = db.Column(db.String(200))
    fb_page             = db.Column(db.Text,default='https://www.facebook.com/Unifispot-1652553388349756')
    timezone            = db.Column(db.String(20),default='UTC')
    api_export          = db.Column(db.Integer,default=API_END_POINT_NONE)
    api_auth_field1     = db.Column(db.String(200))
    api_auth_field2     = db.Column(db.String(200))
    api_auth_field3     = db.Column(db.String(200))
    daily_data_limit    = db.Column(db.String(10))
    monthly_data_limit  = db.Column(db.String(10),default=1000)
    session_timelimit   = db.Column(db.Integer,default=60)    
    enable_session_limit= db.Column(db.Boolean())
    smsauth             = db.Column(db.Boolean())
    email_field         = db.Column(db.String(20),default='Email ID')
    firstname_field     = db.Column(db.String(20),default='Firstname')
    lastname_field      = db.Column(db.String(20),default='Lastname')
    dob_field           = db.Column(db.String(20),default='DOB')
    extra1_field        = db.Column(db.String(20),default='Extra1')
    extra2_field        = db.Column(db.String(20),default='Extra2')
    mandatoryfields     = db.Column(db.Integer,default=(MANDATE_FIELD_FIRSTNAME + MANDATE_FIELD_LASTNAME))
    newsletter          = db.Column(db.Boolean(),default=0,index=True)
    newsletter_field    = db.Column(db.String(50),default='I agree to subscribe to the news letter') 
    newsletter_mandate  = db.Column(db.Boolean(),default=0,index=True) 




    def populate_from_form(self,form):
        self.name               = form.name.data
        self.unifi_id           = form.unifi_id.data
        self.template           = form.template.data
        self.enablehtml	        = form.enablehtml.data
        self.auth_method	    = (form.auth_fb.data and AUTH_TYPE_SOCIAL) + (form.auth_phone.data and AUTH_TYPE_SMS) + (form.auth_voucher.data and AUTH_TYPE_VOUCHER)+ (form.auth_email.data and AUTH_TYPE_EMAIL)
        self.auth_fb_like	    = form.auth_fb_like.data
        self.auth_fb_post       = form.auth_fb_post.data
        self.daily_data_limit   = form.daily_data_limit.data or 0
        self.enable_session_limit= form.enable_session_limit.data
        self.monthly_data_limit = form.monthly_data_limit.data or 0
        self.session_timelimit  = form.session_timelimit.data or 0
        self.smsauth            = form.smsauth.data
        self.email_field        = form.email_field.data
        self.firstname_field    = form.firstname_field.data
        self.lastname_field     = form.lastname_field.data
        self.dob_field          = form.dob_field.data
        self.extra1_field       = form.extra1_field.data
        self.extra2_field       = form.extra2_field.data
        if self.account.en_advertisement:
            self.redirect_method	= form.redirect_method.data
            self.redirect_url       = form.redirect_url.data
        self.newsletter         = form.newsletter.data
        self.newsletter_field   = form.newsletter_field.data
        self.newsletter_mandate = form.newsletter_mandate.data
        self.fb_page            = form.fb_page.data
        self.timezone           = form.timezone.data
        if self.account.en_fbauth_change:        
            self.fb_appid           = form.fb_appid.data
            self.fb_app_secret      = form.fb_app_secret.data
        if self.account.en_reporting:
            self.reports_type       = form.reports_type.data
            self.reports_list	    = form.reports_list.data
        self.emailformfields    = (form.get_lastname.data and FORM_FIELD_LASTNAME)  + (form.get_firstname.data and FORM_FIELD_FIRSTNAME) + \
                (form.get_dob.data and FORM_FIELD_DOB) + (form.get_extra1.data and FORM_FIELD_EXTRA1 ) + \
                (form.get_extra2.data and FORM_FIELD_EXTRA2) + (form.get_email.data and FORM_FIELD_EMAIL)
        self.mandatoryfields    = (form.mandate_lastname.data and MANDATE_FIELD_LASTNAME)  + (form.mandate_email.data and MANDATE_FIELD_EMAIL)  +\
                                (form.mandate_firstname.data and MANDATE_FIELD_FIRSTNAME) + \
                                (form.mandate_dob.data and MANDATE_FIELD_DOB) + (form.mandate_extra1.data and MANDATE_FIELD_EXTRA1 ) + \
                                (form.mandate_extra2.data and MANDATE_FIELD_EXTRA2)                
        if self.account.en_api_export:
            self.api_export         = form.api_export.data
            self.api_auth_field1    = form.api_auth_field1.data
            self.api_auth_field2    = form.api_auth_field2.data
            self.api_auth_field3    = form.api_auth_field3.data

    def fb_login_en(self):
        return (self.auth_method & AUTH_TYPE_SOCIAL)

    def phone_login_en(self):
        return (self.auth_method & AUTH_TYPE_SMS)

    def voucher_login_en(self):
        return (self.auth_method & AUTH_TYPE_VOUCHER)

    def email_login_en(self):
        return (self.auth_method & AUTH_TYPE_EMAIL)        

    def to_dict(self):
        reports_type = None
        reports_list = None
        fb_appid = None
        fb_app_secret= None
        redirect_method = None
        redirect_url = None
        api_export = None
        api_auth_field1 = None
        api_auth_field2 = None
        api_auth_field3 = None
        emailformfields = self.emailformfields if self.emailformfields else 0
        mandatoryfields = self.mandatoryfields if self.mandatoryfields else 0
        if self.account.en_reporting:
            reports_type = self.reports_type
            reports_list = self.reports_list
        if self.account.en_fbauth_change:
            fb_appid = self.fb_appid
            fb_app_secret = self.fb_app_secret
        if self.account.en_advertisement:
            redirect_method = self.redirect_method
            redirect_url = self.redirect_url
        if self.account.en_api_export:
            api_export = self.api_export
            api_auth_field1 = self.api_auth_field1
            api_auth_field2 = self.api_auth_field2
            api_auth_field3 = self.api_auth_field3
        return dict_normalise_values({ 'name':self.name,'unifi_id':self.unifi_id, 'id':self.id, \
                'template':self.template,
                'get_email': (emailformfields &FORM_FIELD_EMAIL),\
                'get_lastname': (emailformfields &FORM_FIELD_LASTNAME),\
                'get_firstname': (emailformfields &FORM_FIELD_FIRSTNAME),\
                'get_dob': (emailformfields &FORM_FIELD_DOB),\
                'get_extra1': (emailformfields &FORM_FIELD_EXTRA1),\
                'get_extra2': (emailformfields &FORM_FIELD_EXTRA2),\
                'mandate_email': (mandatoryfields &MANDATE_FIELD_EMAIL),\
                'mandate_lastname': (mandatoryfields &MANDATE_FIELD_LASTNAME),\
                'mandate_firstname': (mandatoryfields &MANDATE_FIELD_FIRSTNAME),\
                'mandate_dob': (mandatoryfields &MANDATE_FIELD_DOB),\
                'mandate_extra1': (mandatoryfields &MANDATE_FIELD_EXTRA1),\
                'mandate_extra2': (mandatoryfields &MANDATE_FIELD_EXTRA2),\
                'auth_fb':(self.auth_method &AUTH_TYPE_SOCIAL),'auth_email':(self.auth_method &AUTH_TYPE_EMAIL),\
                'auth_phone':(self.auth_method &AUTH_TYPE_SMS),'auth_voucher':(self.auth_method &AUTH_TYPE_VOUCHER),\
                'default_landing':self.default_landing,'reports_type':reports_type, \
                'fb_page':self.fb_page,'auth_fb_like':self.auth_fb_like,'auth_fb_post':self.auth_fb_post,\
                'fb_appid':fb_appid,'fb_app_secret':fb_app_secret,
                'redirect_method':redirect_method,'redirect_url':redirect_url,'timezone':self.timezone,\
                'emailformfields':emailformfields,'reports_list':reports_list,'client_id':self.client.id,\
                'api_export':api_export,'api_auth_field1':api_auth_field1,'api_auth_field2':api_auth_field2,\
                'api_auth_field3':api_auth_field3,'monthly_data_limit':self.monthly_data_limit,\
                'daily_data_limit':self.daily_data_limit,\
                'smsauth':self.smsauth,'email_field':self.email_field,'firstname_field':self.firstname_field,\
                'lastname_field':self.lastname_field,'dob_field':self.dob_field,'extra1_field':self.extra1_field,\
                'extra2_field':self.extra2_field,'newsletter':self.newsletter,\
                'newsletter_field':self.newsletter_field,'newsletter_mandate':self.newsletter_mandate,
                'session_timelimit':self.session_timelimit,'enable_session_limit':self.enable_session_limit})



    #Search option with paging and sorting, uses LIKE on INDEXED fields 
    #and return num of total results  as well as number of rows controlled by paging
    def search_query(self,term,offset=0,limit=10,sort=None,modal_filters=None):        
        main_query = Wifisite.query.filter_by()
        if term:
            result_qry = main_query
        else:
            result_qry = main_query
        result_qry = result_qry.distinct( )
        total = result_qry.count()
        if sort['column'] == "0" :
            if sort['order'] == "desc":
                results_ord = result_qry.order_by(Wifisite.name.desc())
            else:
                results_ord = result_qry.order_by(Wifisite.name.asc())
        else:
            results_ord = result_qry.order_by(Landingpage.id.asc()) 
        results = results_ord.offset(offset).limit(limit).all()
        return {'total':total,'results':results}       
 

class Landingpage(db.Model):
    ''' Class to represent landing page design

    '''
    id              = db.Column(db.Integer, primary_key=True)
    site_id         = db.Column(db.Integer, db.ForeignKey('wifisite.id'))
    logofile        = db.Column(db.String(200),default='/static/img/logo.png')
    bgfile          = db.Column(db.String(200),default='/static/img/bg.jpg')
    pagebgcolor     = db.Column(db.String(10),default='#ffffff')
    bgcolor         = db.Column(db.String(10),default='#ffffff')
    headerlink      = db.Column(db.String(200))
    basefont        = db.Column(db.Integer,default=2)
    topbgcolor      = db.Column(db.String(10),default='#ffffff')
    toptextcolor    = db.Column(db.String(10))
    topfont         = db.Column(db.Integer,default=2)
    toptextcont     = db.Column(db.String(2000),default='Please Sign In for WiFi')
    middlebgcolor   = db.Column(db.String(10),default='#ffffff')
    middletextcolor = db.Column(db.String(10))
    middlefont      = db.Column(db.Integer,default=2)
    bottombgcolor   = db.Column(db.String(10),default='#ffffff')
    bottomtextcolor = db.Column(db.String(10))
    bottomfont      = db.Column(db.Integer,default=2)
    bottomtextcont  = db.Column(db.String(2000))
    footerbgcolor   = db.Column(db.String(10),default='#ffffff')
    footertextcolor = db.Column(db.String(10))
    footerfont      = db.Column(db.Integer,default=2)
    footertextcont  = db.Column(db.String(2000))
    btnbgcolor      = db.Column(db.String(10))
    btntxtcolor     = db.Column(db.String(10))
    btnlinecolor    = db.Column(db.String(10),default='#000000')
    tosfile         = db.Column(db.String(200),default='/static/img/tos.pdf')
    copytextcont    = db.Column(db.String(2000))


    def populate_from_form(self,form):
        self.site_id        = form.site_id.data
        self.logofile       = form.logofile.data
        self.bgfile         = form.bgfile.data
        self.pagebgcolor    = form.pagebgcolor.data
        self.bgcolor        = form.bgcolor.data
        self.headerlink     = form.headerlink.data
        self.basefont       = form.basefont.data
        self.topbgcolor     = form.topbgcolor.data
        self.toptextcolor   = form.toptextcolor.data
        self.topfont        = form.topfont.data
        self.toptextcont    = form.toptextcont.data
        self.middlebgcolor  = form.middlebgcolor.data
        self.middletextcolor= form.middletextcolor.data
        self.middlefont     = form.middlefont.data
        self.bottombgcolor  = form.bottombgcolor.data
        self.bottomtextcolor= form.bottomtextcolor.data
        self.bottomfont     = form.bottomfont.data
        self.footerbgcolor  = form.footerbgcolor.data
        self.footertextcolor= form.footertextcolor.data
        self.footerfont     = form.footerfont.data
        self.footertextcont = form.footertextcont.data
        self.btnbgcolor     = form.btnbgcolor.data
        self.btntxtcolor    = form.btntxtcolor.data
        self.btnlinecolor   = form.btnlinecolor.data
        self.tosfile        = form.tosfile.data
        self.copytextcont   = form.copytextcont   .data


    #Search option with paging and sorting, uses LIKE on INDEXED fields 
    #and return num of total results  as well as number of rows controlled by paging
    def search_query(self,term,offset=0,limit=10,sort=None,modal_filters=None):        
        main_query = Landingpage.query.filter(and_(Landingpage.site_id==modal_filters['siteid'],Landingpage.demo==False))
        if term:
            result_qry = main_query
        else:
            result_qry = main_query
        result_qry = result_qry.distinct( )
        total = result_qry.count()
        if sort['column'] == "0" :
            if sort['order'] == "desc":
                results_ord = result_qry.order_by(Landingpage.name.desc())
            else:
                results_ord = result_qry.order_by(Landingpage.name.asc())
        else:
            results_ord = result_qry.order_by(Landingpage.id.asc()) 
        results = results_ord.offset(offset).limit(limit).all()
        return {'total':total,'results':results}

    def to_table_row(self):
        return {'name':self.name,
            'site_id':self.site_id,
            'id':self.id
        }
    def to_dict(self):
        return dict_normalise_values({
            'id':self.id,
            'site_id':self.site_id,
            'logofile':self.logofile,
            'bgfile':self.bgfile,
            'pagebgcolor':self.pagebgcolor,
            'bgcolor':self.bgcolor ,
            'headerlink':self.headerlink,
            'basefont':self.basefont,
            'topbgcolor':self.topbgcolor,
            'toptextcolor':self.toptextcolor ,
            'topfont':self.topfont,
            'toptextcont':self.toptextcont ,
            'middlebgcolor':self.middlebgcolor ,
            'middletextcolor':self.middletextcolor,
            'middlefont':self.middlefont,
            'bottombgcolor':self.bottombgcolor ,
            'bottomtextcolor':self.bottomtextcolor,
            'bottomfont':self.bottomfont,
            'footerbgcolor':self.footerbgcolor,
            'footertextcolor':self.footertextcolor ,
            'footerfont':self.footerfont,
            'footertextcont':self.footertextcont ,
            'btnbgcolor':self.btnbgcolor,
            'btntxtcolor':self.btntxtcolor  ,
            'btnlinecolor':self.btnlinecolor,
            'tosfile':self.tosfile,
            'copytextcont':self.copytextcont  
        })



#entry to store the details of uploaded files
class Sitefile(db.Model):
    ''' Class to represent Files, each entry will point to a file stored in the HD

    '''
    id              = db.Column(db.Integer, primary_key=True)   
    site_id         = db.Column(db.Integer, db.ForeignKey('wifisite.id'))
    file_location   = db.Column(db.String(255))
    file_type       =  db.Column(db.Integer)
    file_thumb_location = db.Column(db.String(255))
    file_label      = db.Column(db.String(255))

    def to_dict(self):
        return { 'file_location':self.file_location,
                    'id':self.id,'file_type':self.file_type,
                    'file_thumb_location':self.file_thumb_location,
                    'file_label':self.file_label}

    def populate_from_form(self,form):
        self.file_label     = form.file_label.data

    def update_ownership(self,request):
        siteid =  request.view_args.get('siteid')
        self.site_id = siteid

    def get_file_path(self,fileid):
        if fileid == 0:
            return '/static/img/default_file.png'
        file_path = Sitefile.query.filter_by(id=fileid).first()
        return file_path

vouchers_devices = db.Table('vouchers_devices',
    db.Column('voucher_id', db.Integer(), db.ForeignKey('voucher.id')),
    db.Column('device_id', db.Integer(), db.ForeignKey('device.id')))

#Store vouchers
class  Voucher(db.Model):
    id              = db.Column(db.Integer, primary_key=True)
    batchid         = db.Column(db.String(40),index=True)
    voucher         = db.Column(db.String(20),index=True)
    notes           = db.Column(db.String(50),index=True)
    duration_t      = db.Column(db.BigInteger(),default=3600)
    bytes_t         = db.Column(db.BigInteger(),default=1000)
    speed_dl        = db.Column(db.BigInteger(),default=256)
    speed_ul        = db.Column(db.BigInteger(),default=256)
    used            = db.Column(db.Boolean(),default=False,index=True)
    num_devices     = db.Column(db.Integer,default=1,index=True)
    site_id         = db.Column(db.Integer, db.ForeignKey('wifisite.id'))
    duration        = db.Column(db.String(20),index=True,default='1 Hours')
    used_at         = db.Column(db.DateTime,index=True)   #used time in UTC,filled once voucher is used
    device_id       = db.Column(db.Integer, db.ForeignKey('device.id'))
    sessions        = db.relationship('Guestsession', backref='voucher',lazy='dynamic') #to track sessions
    devices         = db.relationship("Device",secondary=vouchers_devices,backref="vouchers")

    def populate_from_form(self,form):
        self.notes      = form.notes.data
        self.bytes_t    = form.bytes_t.data
        self.num_devices= form.num_devices.data
        self.speed_ul   = form.speed_ul.data
        self.speed_dl   = form.speed_dl.data
        #set duration accordingly
        if form.duration_t.data == 1:
            self.duration    = form.duration.data + ' Hours'
            self.duration_t  = int(form.duration.data) * 60 * 60
        elif form.duration_t.data == 2:
            self.duration    = form.duration.data + ' Days'
            self.duration_t  = int(form.duration.data) * 60 * 60 * 24
        elif form.duration_t.data == 3:
            self.duration    = form.duration.data + ' Months'   
            self.duration_t  = int(form.duration.data) * 60 * 60 * 24 * 30  


    def to_dict(self):

        return {'site':self.site.name,'duration':self.duration,
                'status':'<span class="label label-danger">Used</span>' if self.used else '<span class="label label-success">Initializing</span>',
                'voucher':self.voucher,'note':self.notes,'bytes_t':self.bytes_t,'num_devices':self.num_devices,
                'id':self.id
                }                 



    #Search option with paging and sorting, uses LIKE on INDEXED fields 
    #and return num of total results  as well as number of rows controlled by paging
    def search_query(self,term,offset=0,limit=10,sort=None,modal_filters=None):
        main_query = Voucher.query.filter_by(site_id=modal_filters['siteid'])
        if term:
            result_qry = main_query.outerjoin(Voucher.site).filter(or_( Wifisite.name.like('%'+term+'%'), Voucher.voucher.like('%'+term+'%'), Voucher.notes.like('%'+term+'%')))
        else:
            result_qry = main_query
        result_qry = result_qry.distinct( )
        total = result_qry.count()
        if sort['column'] == "0" :
            if sort['order'] == "desc":
                results_ord = result_qry.order_by(Wifisite.name.desc())
            else:
                results_ord = result_qry.order_by(Wifisite.name.asc())
        elif sort['column'] == "1" :
            if sort['order'] == "desc":
                results_ord = result_qry.order_by(Voucher.voucher.desc())
            else:
                results_ord = result_qry.order_by(Voucher.voucher.desc())
        elif sort['column'] == "2" :
            if sort['order'] == "desc":
                results_ord = result_qry.order_by(Voucher.duration.desc())
            else:
                results_ord = result_qry.order_by(Voucher.duration.desc())          
        elif sort['column'] == "3" :
            if sort['order'] == "desc":
                results_ord = result_qry.order_by(Voucher.used.desc())
            else:
                results_ord = result_qry.order_by(Voucher.used.desc())        
        elif sort['column'] == "4" :
            if sort['order'] == "desc":
                results_ord = result_qry.order_by(Voucher.notes.desc())
            else:
                results_ord = result_qry.order_by(Voucher.notes.desc())    
        else:
            results_ord = result_qry.order_by(Voucher.id.asc())  
        results = results_ord.offset(offset).limit(limit).all()
        return {'total':total,'results':results}

    def to_table_row(self):

        duration = '%s:%sMb '%(self.duration,self.bytes_t)

        return {'site':self.site.name,'duration':duration,
                'status':'<span class="label label-danger">Used</span>' if self.used else '<span class="label label-primary">Available</span>',
                'voucher':self.voucher,'note':self.notes,'num_devices':self.num_devices ,'used':self.used,
                'id':self.id
                }

    def check_validity(self):
        #first check if voucher is already used and

        #first check if voucher's expiry time is over
        now = arrow.utcnow().timestamp 
        expiry = arrow.get(self.used_at).timestamp + self.duration_t
        if now >= expiry:
            return False

        #check if data limit us expired
        if self.bytes_t:
            data_consumed = 0
            for session in self.sessions:
                data_consumed += int(session.data_used)

            data_mb = int(math.ceil((data_consumed/1024000.0)))

            if data_mb > self.bytes_t:
                return False

        return True

    def time_available(self):
        '''Retuns remaining time in a voucher in minutes

        '''
        now = arrow.utcnow().timestamp 
        expiry = arrow.get(self.used_at).timestamp + self.duration_t
        return int((expiry - now )/60)

    def data_available(self):
        '''Retuns remaining data in a voucher in Mb

        '''
        if self.bytes_t:
            data_consumed = 0
            for session in self.sessions:
                data_consumed += int(session.data_used)    

            data_mb = int(math.ceil((data_consumed/1024000.0)))
            return self.bytes_t - data_mb
        else:
            return 0

    def uses_available(self):
        '''Retuns number of uses available in this voucher

        '''
        free = int(self.num_devices) - len(self.devices)
        return free


class Voucherdesign(db.Model):
    ''' Class to represent Voucher design

    '''
    id              = db.Column(db.Integer, primary_key=True)
    site_id         = db.Column(db.Integer, db.ForeignKey('wifisite.id'))
    logofile        = db.Column(db.String(200),default='/static/img/logo.png')
    showlogo        = db.Column(db.Integer,default=1)
    shownotes       = db.Column(db.Integer,default=1)
    showqr          = db.Column(db.Integer,default=1)
    showduration    = db.Column(db.Integer,default=1)
    showdata        = db.Column(db.Integer,default=1)
    showspeed       = db.Column(db.Integer,default=1)
    bgcolor         = db.Column(db.String(10),default='#ffffff')
    txtcolor        = db.Column(db.String(10),default='#000000')
    bordercolor     = db.Column(db.String(10),default='#000000')



    def to_dict(self):
        return {'site_id':self.site_id,
                'logofile':self.logofile,'showlogo':self.showlogo,'shownotes':self.shownotes,'showqr':self.showqr,
                'showduration':self.showduration,'showdata':self.showdata,'showspeed':self.showspeed,
                'bgcolor':self.bgcolor,'txtcolor':self.txtcolor,'bordercolor':self.bordercolor,
                'id':self.id
                }   

    def populate_from_form(self,form):
        self.logofile       = form.logofile.data                
        self.showlogo       = form.showlogo.data                
        self.shownotes      = form.shownotes.data                
        self.showqr         = form.showqr.data                
        self.showduration   = form.showduration.data                
        self.showdata       = form.showdata.data                
        self.showspeed      = form.showspeed.data                
        self.bgcolor        = form.bgcolor.data                
        self.txtcolor       = form.txtcolor.data                
        self.bordercolor    = form.bordercolor.data                