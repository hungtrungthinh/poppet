from unifispot import celery
from celery.task.schedules import crontab
from celery.decorators import periodic_task
from celery.utils.log import get_task_logger
from flask import current_app
import time,arrow
from unifispot.base.utils.email import send_email
from unifispot.base.utils.helper import compare_versions
from unifispot.guest.models import Guest,Smsdata,Guestsession,Guesttrack
from unifispot.guest.newcontroller import Controller
from unifispot.client.models import Wifisite,Voucher
from unifispot.analytics.models import Sitestat
from unifispot.analytics.helpers import update_daily_stat
from unifispot.extensions import db
from unifispot.exports.helper import get_api_endpoint
from unifispot.const import API_END_POINT_NONE,CLIENT_REPORT_WEEKLY,CLIENT_REPORT_MONTHLY
from unifispot.superadmin.models import Account,Notification
from unifispot.const import GUESTRACK_VOUCHER_AUTH,GUESTRACK_SMS_AUTH,GUESTRACK_EMAIL_AUTH,GUESTRACK_PREAUTH,GUESTRACK_SOCIAL_AUTH
from unifispot.const import NOTIFI_ALL_USERS,NOTIFI_ALL_ADMIN,NOTIFI_ALL_CLIENTS,NOTIFI_ALL_SUPER,NOTIFI_ONCE
from flask_mail import Message,Attachment
from unifispot.extensions import mail
from unifispot.version import version

from sqlalchemy import and_,or_
from pymongo import MongoClient
import requests
import json
import math
from dateutil import tz


#task for handling API export after Guest has created
@celery.task(autoretry_on=Exception,max_retries=5)
def celery_export_api(guestid=None):
    guest = Guest.query.filter_by(id=guestid).first()
    if not guest:
        current_app.logger.error("Guest ID:%s is invalid"%guestid)
        return None
    wifisite = Wifisite.query.filter_by(id=guest.site_id).first()
    if not wifisite or wifisite.api_export == API_END_POINT_NONE :
        current_app.logger.error("Guest ID:%s has invalid site or API export is not configured"%guestid)   
        return None
    if guest.apisync==1:
        current_app.logger.error("Guest ID:%s has already synched"%guestid)   
        return None   
    if guest.demo==True:
        current_app.logger.debug("Guest ID:%s is a demo guest entry"%guestid)   
        return None              
    #get the endpoint and perform API export
    api_endpoint = get_api_endpoint(wifisite.api_export)
    current_app.logger.debug('Going to export guest ID:%s to API endpoint'%guest.id)
    if api_endpoint and api_endpoint(guest,wifisite):
        #API export was successful, mark entry as synched and put correct timestamp
        guest.apisync = True
        guest.synchedat = arrow.utcnow().datetime
        db.session.commit()

#task for handling SMS API
@celery.task(autoretry_on=Exception,max_retries=5)
def celery_send_sms(smsdataid=None):
    smsdata = Smsdata.query.filter_by(id=smsdataid).first()
    current_app.logger.debug("Going to send SMS to:%s with content :%s"%(smsdata.phonenumber,smsdata.authcode))  

    url = 'https://control.msg91.com/api/sendhttp.php'

    msg = "Your authcode is :%s"%smsdata.authcode

    data ={'authkey':current_app.config['SMS_AUTH_KEY'],
                'mobiles':smsdata.phonenumber,'message':msg,
                'sender':current_app.config['SMS_SENDER'],'route':'4','country':'91'}

    r = requests.get(url, params=data,verify=False)

    current_app.logger.debug("Received :%s when sending SMS to:%s with content :%s"%(r.text,smsdata.phonenumber,smsdata.authcode)) 

    r.raise_for_status()

@periodic_task(run_every=(crontab(minute="*/5")))
def celery_session_monitor(*args, **kwargs):
    current_app.logger.info('-----------Running celery_session_monitor-----------------------')
    sites = Wifisite.query.all()
    for site in sites:
        if site.enable_session_limit or site.voucher_login_en() :
            current_app.logger.info('celery_session_monitor processing Site:%s'%site.name)       
            account = Account().query.filter_by(id=site.account_id).first()
            settings = account.get_settings()
            try:
                c =  Controller(settings['unifi_server'], settings['unifi_user'], settings['unifi_pass'],'8443','v4',site.unifi_id)       
                #get all STAs
                stas = c.get_clients()
                for sta in stas:
                    if sta.get('is_guest') and sta.get('authorized'):
                        rx_bytes = int(sta.get('rx_bytes'))
                        tx_bytes = int(sta.get('tx_bytes'))
                        total_data = rx_bytes + tx_bytes 
                        data_mb    = int(math.ceil((total_data/1024000.0)))
                        
                        mac = sta.get('mac')
                        guest_session = Guestsession.query.filter_by(site_id=site.id,mac=mac).first()
                        if not guest_session:
                            current_app.logger.debug('MAC:%s in site:%s have no session'%(mac,site.name))
                            continue
                        current_app.logger.debug('MAC:%s in site:%s seems to have used \
                                data:%s Mb'%(mac,site.name,data_mb))                         
                        if guest_session.state == GUESTRACK_VOUCHER_AUTH:
                            #if voucher authorized check for balance data in voucher
                            current_app.logger.debug('MAC:%s in site:%s seems to have authorized via Voucher '%(mac,site.name))
                            voucher = Voucher.query.filter_by(site_id=site.id,device_id=guest_session.device_id).first()
                            if not voucher:
                                current_app.logger.error('MAC:%s in site:%s no_voucher found '%(mac,site.name))
                                continue
                            if voucher.bytes_t and data_mb > voucher.data_available():
                                current_app.logger.debug('MAC:%s in site:%s seems to have exceeded voucher:%s limit \
                                    hence disconnecting'%(mac,site.name,voucher.id))   
                        #if not voucher authorized check if device exceeded session limit if session limit is enabled
                        else:
                            if site.enable_session_limit and data_mb > int(site.daily_data_limit) :
                                current_app.logger.debug('MAC:%s in site:%s seems to have exceeded data \
                                    hence disconnecting'%(mac,site.name)) 
                                c.unauthorize_guest(mac)   
            except:
                current_app.logger.exception('Exception while monitoring site:%s'%site.name)                


@periodic_task(run_every=(crontab(minute="*/5")))
def celery_session_history(*args, **kwargs):
    current_app.logger.info('-----------Running celery_session_history-----------------------')
    client = MongoClient('localhost', 27117)
    mongodb = client['ace']
    guests = mongodb['guest']
    sites  = mongodb['site']

    #get all sites in mongodb and try to map to an equivalent wifisite
    site_dict = {}
    for site in sites.find():
        wifisite = Wifisite.query.filter_by(unifi_id=site['name']).first()
        site_id = None
        if wifisite:
            site_id = wifisite.id    

        site_dict[str(site['_id'])] = site_id

    #get all sessions
    utcwindow = arrow.utcnow().replace(minutes=-10).timestamp

    current_app.logger.debug('Checking guest sessions')

    for guest in guests.find({'end':{'$gt':utcwindow}}):
        start = arrow.get(guest.get('start')).humanize()
        end   = arrow.get(guest.get('end')).humanize()
        tx_bytes = guest.get('tx_bytes',0)
        rx_bytes = guest.get('rx_bytes',0)
        obj_id = str(guest['_id'])
        mac = guest['mac']
        current_app.logger.debug('MAC:%s Start:%s End:%s  Site:%s TX:%s RX:%s'%(mac,start,end,site_dict.get(guest['site_id']),tx_bytes,rx_bytes))
        #check if the guest belongs to a known wifisite
        site_id = site_dict.get(guest['site_id'])
        if site_id:            
            guestsession = Guestsession.query.filter_by(obj_id=obj_id,site_id=site_id).first()
            #if this session was logged before
            if guestsession:
                duration              = guest.get('duration')
                if duration:
                    guestsession.duration = int(duration/60.0)
                guestsession.stoptime = arrow.get(guest.get('end')).naive
                guestsession.data_used = (tx_bytes + rx_bytes)
                db.session.commit()
                current_app.logger.debug('Updated Guestsession:%s for MAC:%s in SiteID:%s Starttime:%s to:%s'%(guestsession.id,mac,site_id,start,obj_id))
            else:
                #find all recent sessions of this MAC
                session_start = arrow.get(guest.get('start')).replace(minutes=-1).naive
                guestsession = Guestsession.query.filter(and_(Guestsession.site_id==site_id,Guestsession.mac==mac,Guestsession.starttime >=session_start)).first()
                if not guestsession:
                    current_app.logger.error('No session found for MAC:%s in SiteID:%s Starttime:%s'%(mac,site_id,start))
                guestsession.stoptime = arrow.get(guest.get('end')).naive
                guestsession.data_used = (tx_bytes + rx_bytes)
                guestsession.obj_id = obj_id
                db.session.commit()
                current_app.logger.debug('Connected Guestsession:%s for MAC:%s in SiteID:%s Starttime:%s to :%s'%(guestsession.id,mac,site_id,start,obj_id))


#task for update analytics
@periodic_task(run_every=crontab(hour=0, minute=30, day_of_week=1))
def celery_weekly_report(*args, **kwargs):
    current_app.logger.info('-----------Running celery_weekly_report-----------------------')
    sites = Wifisite.query.all()
    for site in sites:
        if site.reports_type == CLIENT_REPORT_WEEKLY:
            tzinfo = tz.gettz(site.timezone)
            day     = arrow.now(tzinfo).replace(days=-2) #calculate past week
            start_of_week = day.floor('week')
            end_of_week = day.ceil('week')
            generate_report(site.id,start_of_week,end_of_week)

@periodic_task(run_every=crontab(hour=0, minute=30, day_of_month=1))           
def celery_monthly_report(*args, **kwargs):
    current_app.logger.info('-----------Running celery_monthly_report-----------------------')
    sites = Wifisite.query.all()
    for site in sites:
        if site.reports_type == CLIENT_REPORT_MONTHLY:
            tzinfo = tz.gettz(site.timezone)
            day     = arrow.now(tzinfo).replace(days=-2)
            start_of_month = day.floor('month')
            end_of_month = day.ceil('month')
            generate_report(site.id,start_of_month,end_of_month)

@periodic_task(run_every=(crontab(minute=0,hour="*/1")))
def celery_update_stat(*args, **kwargs):
    current_app.logger.info('-----------Running celery_update_stat-----------------------')
    sites = Wifisite.query.all()
    for site in sites:
        tzinfo = tz.gettz(site.timezone)
        now    = arrow.now(tzinfo)
        #process today's status for this site
        update_daily_stat(site.id,now)
        if now.hour < 2:
            #process yesterday's stats as well
            yesterday = now.replace(days=-1)
            update_daily_stat(site.id,yesterday)


@periodic_task(run_every=(crontab(minute=0,hour="*/1")))
def celery_get_notification(*args, **kwargs):
    '''Connect to https://notify.unifispot.com/notify.json and get notifications

    '''
    current_app.logger.info('-----------Running celery_get_notification-----------------------')
    accounts = Account.query.all()
    response = requests.get('http://notify.unifispot.com/notify.json')
    response.raise_for_status()
    data = response.json()
    for notify in data.get('notifications'):
        if not  Notification.check_notify_added(notify.get('notifi_id')):
            #check if version id specified
            if  notify.get('version') and compare_versions(notify.get('version'),version) != 0:
                break
            elif notify.get('min_version') and compare_versions(notify.get('min_version'),version) == 1:
                break
            elif notify.get('max_version') and compare_versions(notify.get('max_version'),version) == -1:
                break
            for account in accounts:
                db.session.add(Notification(content=notify['content'],notifi_type=notify['notifi_type'],
                            notifi_id=notify['notifi_id'],user_id=0,account_id=account.id))
    db.session.commit()           
    return 1




def generate_report(siteid,startday,endday):
    '''Create and send report for given site during the specified periodic_task


    '''
    site = Wifisite.query.filter_by(id=siteid).first()
    start_date = startday.format('DD-MM-YYYY')
    end_date   = endday.format('DD-MM-YYYY')
    current_app.logger.debug('Going to process report for :%s from :%s to :%s'%(site.name,start_date,end_date))    
    #get all entries within given period
    entries = Guest.query.filter(and_(Guest.site_id==siteid,Guest.demo ==0, 
                    Guest.created_at >= startday,Guest.created_at <= endday)).all()

    csvList = '\n'.join(','.join(row.to_list()) for row in entries)  


    filename = "Report_%s_to_%s.csv"%(start_date,end_date)  
    attachment = Attachment(filename=filename,content_type='txt/plain',data=csvList)
    msg = Message("Wifi usage report for the period :%s to :%s"%(start_date,end_date),
                    sender=current_app.config['REPORT_EMAIL_SENDER'],
                    recipients=[site.client.email,site.reports_list],attachments =[attachment],bcc=current_app.config['ADMINS'])

    msg.body  = "Dear %s,\n\n"\
            "\tPlease find the wifi usage report for the period of starting from:%s to %s \n"\
            "\nRegards\n"\
            "Admin"%(site.name,start_date,end_date)
    mail.send(msg)
