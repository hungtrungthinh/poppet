#! flask/bin/python
from os.path import abspath

from flask import current_app
from flask_script import Manager
from flask_assets import ManageAssets
from flask_migrate import Migrate, MigrateCommand

from unifispot import create_app
from unifispot.extensions import db
from unifispot.const import AUTH_TYPE_ALL


app = create_app(mode='development')
manager = Manager(app)
manager.add_command('assets', ManageAssets())
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)


#app.run(host='0.0.0.0',debug = True)
@manager.command
def init_data():
    with app.app_context():
        from  sqlalchemy.exc import OperationalError    
        from flask_security.utils import encrypt_password
        from unifispot.models import User  
        from unifispot.superadmin.models import Account
        from unifispot.admin.models import Admin       
        try:
            account = Account.query.filter_by(id=1).first()
        except :
            app.logger.debug( "No Account table Entry found,could be running migration ")
        else:
            if not account:
                #create default admin user
                enc_pass        = encrypt_password('password')
                account         = Account()
                db.session.add(account)
                admin_user = Admin(email='admin@admin.com',password=enc_pass,displayname= "Admin User",active=1)
                admin_user.account = account
                db.session.add(admin_user)
                db.session.commit()

@manager.command
def demo_init():
    with app.app_context():
        from  sqlalchemy.exc import OperationalError    
        from flask_security.utils import encrypt_password
        from unifispot.models import User  
        from unifispot.superadmin.models import Account
        from unifispot.admin.models import Admin       
        from unifispot.client.models import Client,Wifisite,Landingpage 
        from unifispot.guest.models import Guest
        import arrow
        from random import randint 
        from unifispot.analytics.models import Sitestat  
        from unifispot.base.utils.helper import get_random_integers 
        from faker import Factory
        fake = Factory.create()

        try:
            account = Account.query.filter_by(id=1).first()
        except :
            app.logger.debug( "No Account table Entry found,could be running migration ")
        else:
            if not account:
                #create default admin user
                enc_pass        = encrypt_password('password')
                account         = Account()
                db.session.add(account)
                admin_user  = Admin(email='admin@admin.com',password=enc_pass,displayname= "Admin User1",active=1)
                admin_user2 = Admin(email='admin2@admin.com',password=enc_pass,displayname= "Admin User2",active=1)
                admin_user3 = Admin(email='admin3@admin.com',password=enc_pass,displayname= "Admin User3",active=1)
                admin_user.account = account
                admin_user2.account = account
                admin_user3.account = account
                db.session.add(admin_user)
                db.session.add(admin_user2)
                db.session.add(admin_user3)
                client_user1      = Client(email='client1@admin.com',password=enc_pass,displayname= "client1",active=1)
                db.session.add(client_user1)
                client_user1.account = account
                site1           = Wifisite(name='Client1 Site1',unifi_id='site1',auth_fb_like=1,timezone="Europe/Copenhagen",
                                        auth_method= AUTH_TYPE_ALL,smsauth=1)    
                db.session.add(site1)
                site1.account   = account
                site1.client    = client_user1
                landing1        = Landingpage()   
                landing1.site           = site1
                site1.landingpages.append(landing1) 
                db.session.add(landing1)
                db.session.commit()    
                site1.default_landing = landing1.id                  
                db.session.commit()
                site2           = Wifisite(name='Client1 Site2',unifi_id='site1',auth_fb_like=1,timezone="Europe/Copenhagen",
                                        auth_method= AUTH_TYPE_ALL,smsauth=1)    
                db.session.add(site2)
                site2.account   = account
                site2.client    = client_user1
                landing2        = Landingpage()   
                landing2.site           = site2
                site1.landingpages.append(landing2) 
                db.session.add(landing2)
                db.session.commit()    
                site1.default_landing = landing2.id                  
                db.session.commit()
                ##-----------------------Stats for site1
                now = arrow.now()
                month_start = now.floor('month')
                days        = (now.ceil('month') - month_start).days
                for i in range(days):
                    day_key = month_start.replace(days=i).floor('day').naive
                    daystat = Sitestat(site_id=site1.id,date=day_key)
                    num_visits             = randint(10,50)
                    num_logins             = randint(5,num_visits)
                    num_newlogins          = randint(5,num_logins) 
                    logins                 = get_random_integers(4,num_logins)
                    daystat.num_visits     = num_visits
                    daystat.num_likes      = randint(1,10)
                    daystat.num_checkins   = randint(1,10)
                    daystat.num_newlogins  = num_newlogins
                    daystat.num_repeats    = num_logins - num_newlogins
                    daystat.num_emails     = logins[0]
                    daystat.num_fb         = logins[1]
                    daystat.num_vouchers   = logins[2]
                    daystat.num_phones     = logins[3]
                    db.session.add(daystat)
                db.session.commit()                
                ##-----------------------Stats for site2
                for i in range(days):
                    day_key = month_start.replace(days=i).floor('day').naive
                    daystat = Sitestat(site_id=site2.id,date=day_key)
                    num_visits             = randint(10,50)
                    num_logins             = randint(5,num_visits)
                    num_newlogins          = randint(5,num_logins) 
                    logins                 = get_random_integers(4,num_logins)
                    daystat.num_visits     = num_visits
                    daystat.num_likes      = randint(1,10)
                    daystat.num_checkins   = randint(1,10)
                    daystat.num_newlogins  = num_newlogins
                    daystat.num_repeats    = num_logins - num_newlogins
                    daystat.num_emails     = logins[0]
                    daystat.num_fb         = logins[1]
                    daystat.num_vouchers   = logins[2]
                    daystat.num_phones     = logins[3]
                    db.session.add(daystat)
                db.session.commit()     
                ##------------------guests for site1
                for i in range(100):
                    db.session.add(Guest(firstname=fake.first_name(),lastname=fake.last_name(),email=fake.email()))
                db.session.commit()

@manager.command
def defaul_customfields():
    with app.app_context():
        from unifispot.client.models import Client,Wifisite,Landingpage 
        from unifispot.const import MANDATE_FIELD_FIRSTNAME,MANDATE_FIELD_LASTNAME
        sites = Wifisite.query.all()        
        for site in sites:
            site.email_field         = 'Email ID'
            site.firstname_field     = 'Firstname'
            site.lastname_field      = 'Lastname'
            site.dob_field           = 'DOB'
            site.extra1_field        = 'Extra1'
            site.extra2_field        = 'Extra2'
            site.mandatoryfields     = MANDATE_FIELD_FIRSTNAME + MANDATE_FIELD_LASTNAME
            db.session.commit()

@manager.command
def defaul_sessiontime():
    with app.app_context():
        from unifispot.client.models import Client,Wifisite,Landingpage 
        from unifispot.const import MANDATE_FIELD_FIRSTNAME,MANDATE_FIELD_LASTNAME
        sites = Wifisite.query.all()        
        for site in sites:
            site.session_timelimit         = 60
            db.session.commit()     

@manager.command
def fb_ips():
    with app.app_context():
        from unifispot.superadmin.models import Account 
        from unifispot.guest.newcontroller import Controller       
        account = Account().query.first()
        settings = account.get_settings() 
        site_id = 'ieu6ek9y'
        site_code = '572a12afe4b078cda06e7e41'
        portal_ip = '139.59.192.71'
        portal_subnet = '139.59.192.71/32'
        portal_hostname = 'urbanespot.com'
        c =  Controller(settings['unifi_server'], settings['unifi_user'], settings['unifi_pass'],'8443','v4',site_id)             
        c.set_guest_access(site_id,site_code,portal_ip,portal_subnet,portal_hostname)

@manager.command
def enable_sms_preauth():
    with app.app_context():
        from unifispot.superadmin.models import Account 
        from unifispot.guest.newcontroller import Controller       
        account = Account().query.first()
        account.en_sms_preauth = 1
        db.session.commit()

@manager.command
def test_email_report():
    with app.app_context():
        from unifispot.tasks import generate_report,celery_weekly_report,celery_monthly_report
        import arrow
        today     = arrow.now()
        start_of_week = today.replace(days=-today.weekday()).floor('day')
        end_of_week = today.replace(days=7-today.weekday()).ceil('day')        
        celery_monthly_report()

@manager.command
def update_notifications():
    with app.app_context():
        from unifispot.tasks import celery_get_notification
        celery_get_notification()

@manager.command
def test_update_daily_stat():
    with app.app_context():
        import arrow
        from unifispot.client.models import Wifisite
        from dateutil import tz
        from unifispot.analytics.helpers import update_daily_stat
        today     = arrow.now()
        start_of_month = today.floor('month')
        diff = (today - start_of_month).days
        sites = Wifisite.query.all()
        for site in sites:  
            for i in range(diff):
                daydate = today.replace(days=-i)
                update_daily_stat(site.id,daydate)

@manager.command
def rebuild_daily_stat():
    with app.app_context():
        import arrow
        from unifispot.client.models import Wifisite
        from unifispot.analytics.models import Sitestat
        from dateutil import tz
        from unifispot.analytics.helpers import update_daily_stat
        today     = arrow.now()
        start_of_month = today.floor('month')
        diff = (today - start_of_month).days
        sites = Wifisite.query.all()
        app.logger.info('----------rebuilding daily stats------')
        for site in sites: 
            tzinfo = tz.gettz(site.timezone) 
            sitestats = Sitestat.query.filter_by(site_id=site.id).all()
            for stats in sitestats:
                daydate = arrow.get(stats.date,tzinfo=tzinfo)
                update_daily_stat(site.id,daydate)

@manager.command
def reset_admin():
    with app.app_context():
        from unifispot.models import User
        from flask_security.utils import encrypt_password
        admin = User.query.filter_by(id=1).first()
        enc_pass        = encrypt_password('password')
        admin.password = enc_pass
        db.session.commit()


@manager.command
def migrate_vouchers():
    with app.app_context():
        from unifispot.client.models import Voucher,Wifisite,Voucherdesign
        from unifispot.guest.models import Device
        for voucher in Voucher.query.all():
            if voucher.device_id:
                device = Device.query.filter_by(id=voucher.device_id).first()
                voucher.devices.append(device)
                voucher.device_id = None 
                voucher.num_devices = 1
                device.voucher_id = voucher.id
                db.session.commit()
        for site in Wifisite.query.all():
            if not Voucherdesign.query.filter_by(site_id=site.id).first():
                design = Voucherdesign()
                design.site = site
                db.session.add(design)
                db.session.commit()


manager.run()