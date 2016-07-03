from flask_wtf import Form
from flask_security import login_required,current_user
from wtforms import TextField, HiddenField,SelectField,FileField,BooleanField,PasswordField,TextAreaField,RadioField,SelectMultipleField,widgets,validators
from wtforms.validators import Required
from timezones import zones
from flask import current_app,flash
from facebook import  GraphAPI
from unifispot.const import AUTH_TYPE_BYPASS,AUTH_TYPE_SPLASH,AUTH_TYPE_EMAIL,AUTH_TYPE_VOUCHER,AUTH_TYPE_SOCIAL,AUTH_TYPE_SMS,API_END_POINT_NONE,API_END_POINT_MAIL_CHIMP
from unifispot.const import REDIRECT_ORIG_URL,REDIRECT_CUSTOM_URL,font_list,CLIENT_REPORT_NONE,CLIENT_REPORT_WEEKLY,CLIENT_REPORT_MONTHLY,ROLE_CLIENT


from .models import Sitefile,Wifisite,Landingpage,Client
from unifispot.models import User
from unifispot.admin.controller import Controller 
from unifispot.superadmin.models import Account

        
class WifiSiteForm(Form):
    name                = TextField('Name',validators = [Required()])   
    timezone            = SelectField('Site Timezone',choices=[])
    unifi_id            = SelectField('Select Unifi Site',choices=[])
    enablehtml          = HiddenField('Enable HTML Landing Page')
    auth_fb             = BooleanField('Enable FB Login',default=1)
    auth_email          = BooleanField('Enable Email Login',default=1)
    auth_phone          = BooleanField('Enable Phone Login',default=1)
    auth_voucher        = BooleanField('Enable Voucher Login',default=1)
    smsauth             = BooleanField('Enable SMS Auth',default=1)
    fb_page             = TextField('Fb Page URL')
    fb_page_id          = HiddenField('Fb Page ID')
    auth_fb_like        = BooleanField('Ask For Page Like',default=1)
    auth_fb_post        = BooleanField('Ask Guest For Checkin')
    redirect_method     = BooleanField('Redirect After Login',default=0)
    redirect_url        = TextField('Redirect Guest to URL',default='http://www.unifispot.com')
    fb_app_secret       = TextField('FB APP Secret')
    fb_appid            = TextField('FB APP ID')
    reports_list        = TextField('Additional Report Recipients')
    reports_type        = SelectField('Select Reports Frequency',coerce=int,choices=[],default=CLIENT_REPORT_WEEKLY)
    client_id           = SelectField('Select Client',coerce=int,choices=[],default=0)
    template            = SelectField('Choose Template',choices=[],default='template1')
    get_email           = BooleanField('Email',default=1)
    get_firstname       = BooleanField('First Name',default=1)
    get_lastname        = BooleanField('Last Name',default=1)
    get_dob             = BooleanField('DOB',default=1)
    get_extra1          = BooleanField('Extra1',default=1)    
    get_extra2          = BooleanField('Extra2',default=1)    
    api_export          = SelectField('Select API End Point',coerce=int,choices=[],default=API_END_POINT_NONE)
    api_auth_field1     = TextField('API Auth Field1',render_kw={"placeholder": "Server Prefix,something like us12"})
    api_auth_field2     = TextField('API Auth Field2',render_kw={"placeholder": "List ID"})
    api_auth_field3     = TextField('API Auth Field3',render_kw={"placeholder": "API Key"})
    daily_data_limit    = TextField('Session Data Limit(Mb)')
    monthly_data_limit  = TextField('Monthly Data Limit(Mb)')
    session_timelimit   = TextField('Session Timelimit(Mins)')
    enable_session_limit= BooleanField('Enable Session Limits')
    email_field         = TextField('Email Field')
    firstname_field     = TextField('Firstname Field')
    lastname_field      = TextField('Lastname Field')
    dob_field           = TextField('DOB Field')
    extra1_field        = TextField('Extra Field1')
    extra2_field        = TextField('Extra Field2')
    mandate_email       = BooleanField('Email',default=1)
    mandate_firstname   = BooleanField('First Name',default=1)
    mandate_lastname    = BooleanField('Last Name',default=1)
    mandate_dob         = BooleanField('DOB',default=1)
    mandate_extra1      = BooleanField('Extra1',default=1)    
    mandate_extra2      = BooleanField('Extra2',default=1)     
    newsletter          = BooleanField('Enable Newsletter Confirmation',default=0)     
    newsletter_mandate  = BooleanField('News Subscription mandatory',default=0)  
    newsletter_field    = TextField('Newsletter Subscription text')   


    def populate(self):        
        self.timezone.choices = [ (tz_name,tz_formated)for tz_offset, tz_name, tz_formated in zones.get_timezones() ]
        self.template.choices = [('template1','Template1'),('template2','Template2') ]
        self.reports_type.choices = [(CLIENT_REPORT_NONE,'No Reporting'),(CLIENT_REPORT_WEEKLY,'Weekly Reports'),(CLIENT_REPORT_MONTHLY,'Monthly Reports')]
        self.client_id.choices = []
        self.api_export.choices = [(API_END_POINT_NONE,'None'),(API_END_POINT_MAIL_CHIMP,'MailChimp')]
        self.unifi_id.choices = []

        for user in Client.query.filter_by(account_id=current_user.account_id).all():
            self.client_id.choices.append((user.id,user.displayname))

        if not current_app.config['NO_UNIFI']:
            account = Account().query.filter_by(id=current_user.account_id).first()
            settings = account.get_settings()
            try:
                c = Controller(settings['unifi_server'], settings['unifi_user'], settings['unifi_pass'],version='v4',site_id='default')
                for site in c.get_sites():
                    self.unifi_id.choices.append((site.get('name'),site.get('desc')))
            except:
                flash("Error connecting to Unifi Controller,please check Host/Credentials",'danger')
        else:
             self.unifi_id.choices = [('site1','SITE1'),('site2','SITE2'),('site3','SITE3')]

    def validate(self):
        rv = Form.validate(self)
        if not rv:
            return False
        #validate facebook credentials if FB auth is selected
        if self.auth_fb.data and AUTH_TYPE_SOCIAL:
            fb_appid = self.fb_appid.data or current_app.config['FB_APP_ID']   
            fb_app_secret = self.fb_app_secret.data or current_app.config['FB_APP_SECRET']
            try:
                access_token = GraphAPI().get_app_access_token(fb_appid,fb_app_secret)
            except:
                current_app.logger.exception('Exception while trying to get access_token with APP ID:%s Secret:%s'%(fb_appid,fb_app_secret))
                self.fb_app_secret.errors.append('Incorrect APP ID or secret configured')
                return False
            if ( self.auth_fb_like.data or self.auth_fb_post.data ) and self.fb_page.data == '':                
                self.fb_page.errors.append('Facebook Social action configured without Page URL')
                return False
            if  self.auth_fb_post.data and self.fb_page.data:
                try:
                    page = GraphAPI(access_token).get_object(self.fb_page.data,fields='location') 
                except: 
                    current_app.logger.exception('Exception while trying to get page:%s for location'%(self.fb_page.data))
                    self.fb_page.errors.append('Incorrect page URL specified')
                    return False
                if not page.get('location'):
                    self.fb_page.errors.append('Given FB Page does not supports checkin')
                    return False   
        if self.enable_session_limit.data:
            try:
                int(self.daily_data_limit.data)
            except:
                self.daily_data_limit.errors.append('Please enter valid value for Session Limit')
                return False                
            try:
                int(self.monthly_data_limit.data)
            except:
                self.monthly_data_limit.errors.append('Please enter valid value for Monthly Limit')
                return False                                       
            try:
                int(self.session_timelimit.data)
            except:
                self.session_timelimit.errors.append('Please enter valid value for Session time')
                return False                        
        return True





class LandingFilesForm(Form):
    logofile        = FileField('Logo File')
    bgfile          = FileField('Background Image')
    tosfile         = FileField('Select T&C pdf')

class SimpleLandingPageForm(Form):
    pagebgcolor1     = TextField('Page Background Color')
    gridbgcolor     = TextField('Grid Background Color')
    textcolor       = TextField('Text Color')
    textfont        = SelectField('Select Font',coerce=int,default=2)
    def populate(self):
        #Font options
        fonts = [(idx,font) for idx,font in enumerate(font_list)]
        self.textfont.choices = fonts

class LandingPageForm(Form):
    site_id         = HiddenField('Site ID')
    logofile        = HiddenField('Header File')  
    bgfile          = HiddenField('Background Image')
    pagebgcolor     = TextField('Page Background Color')    
    bgcolor         = TextField('Header Background Color')
    headerlink      = TextField('Header Link')
    basefont        = SelectField('Header Base Font',coerce=int,default=2)
    topbgcolor      = TextField('Top Background Color')
    toptextcolor    = TextField('Top Text Color')
    topfont         = SelectField('Top Font',coerce=int,default=2)
    toptextcont     = TextAreaField('Top Content')
    middlebgcolor   = TextField('Middle Background Color')
    middletextcolor = TextField('Middle Text Color')
    middlefont      = SelectField('Bottom Base Font',coerce=int,default=2)
    bottombgcolor   = TextField('Bottom Background Color') 
    bottomtextcolor = TextField('Bottom Text Color')
    bottomfont      = SelectField('Base Font',coerce=int,default=2)
    footerbgcolor   = TextField('Footer Background Color')
    footertextcolor = TextField('Text Color')
    footerfont      = SelectField('Base Font',coerce=int,default=2)
    footertextcont  = TextAreaField('Footer Content')
    btnbgcolor      = TextField('Button Color')
    btntxtcolor     = TextField('Button Text Color')
    btnlinecolor    = TextField('Button Border Color')
    tosfile         = HiddenField('Select T&C pdf')
    copytextcont    = TextAreaField('Copyright Text')
    

    def populate(self,siteid):
        #Font options
        fonts = [(idx,font) for idx,font in enumerate(font_list)]
        self.basefont.choices = fonts
        self.topfont.choices = fonts
        self.middlefont.choices = fonts
        self.bottomfont.choices = fonts
        self.footerfont.choices = fonts
        self.site_id.data = siteid




class SiteFileForm(Form):
    file_label = TextField('File Label')

    def populate(self):
        pass 


class VoucherForm(Form):  
    duration        = TextField("Duration",validators = [Required()])
    notes           = TextField("Note")
    number          = TextField("Create",validators = [Required()])
    bytes_t         = TextField("Total Data in Mb",validators = [Required()])
    duration_t      = SelectField("Select",coerce=int,choices=[(1,'Hours'),(2,'Days'),(3,'Months')] )  
    num_devices     = TextField("Devices Allowed")  
    speed_dl        = TextField("Download Speed")
    speed_ul        = TextField("Upload Speed")
    def populate(self):
        pass

class VoucherDesignForm(Form):
    site_id         = HiddenField('Site ID')
    logofile        = HiddenField('Header File')   
    bgcolor         = TextField('Background Color')
    txtcolor        = TextField('Text Color')
    bordercolor     = TextField('Border Color')
    showlogo        = BooleanField('Show Logo',default=1)     
    shownotes       = BooleanField('Show Notes',default=1)
    showqr          = BooleanField('Show QRcode',default=1)
    showduration    = BooleanField('Show Duration',default=1)
    showdata        = BooleanField('Show Data Limit',default=1)
    showspeed       = BooleanField('Show Speed Limit',default=1)
    def populate(self):
        pass    

class VoucherFilesForm(Form):
    logofile        = FileField('Logo File')
    def populate(self):
        pass    
