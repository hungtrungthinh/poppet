from flask_wtf import Form
from wtforms import TextField, HiddenField,BooleanField,TextAreaField
from wtforms.validators import Required,DataRequired,Email

from unifispot.const import *

class FacebookTrackForm(Form):

    authlike = HiddenField("Auth Like")
    authpost = HiddenField("Auth Post")

def generate_emailform(wifisite):
    class F(Form):
        pass
    setattr(F, 'email', TextField('%s*'%wifisite.email_field,validators = [DataRequired(),Email()]))
    if wifisite.emailformfields &  FORM_FIELD_FIRSTNAME :
        if wifisite.mandatoryfields & MANDATE_FIELD_FIRSTNAME:
            setattr(F, 'firstname', TextField('%s*'%wifisite.firstname_field,validators = [Required()])) 
        else:
            setattr(F, 'firstname', TextField(wifisite.firstname_field)) 

    if wifisite.emailformfields &  FORM_FIELD_LASTNAME :
        if wifisite.mandatoryfields & MANDATE_FIELD_LASTNAME:
            setattr(F, 'lastname', TextField('%s*'%wifisite.lastname_field,validators = [Required()])) 
        else:
            setattr(F, 'lastname', TextField(wifisite.lastname_field)) 
    if wifisite.emailformfields &  FORM_FIELD_DOB :
        if wifisite.mandatoryfields & MANDATE_FIELD_DOB:
            setattr(F, 'dob', TextField('%s*'%wifisite.dob_field,validators = [Required()]))     
        else:
            setattr(F, 'dob', TextField(wifisite.dob_field))     

    if wifisite.emailformfields &  FORM_FIELD_EXTRA1 :
        if wifisite.mandatoryfields & MANDATE_FIELD_EXTRA1:
            setattr(F, 'extra1', TextField('%s*'%wifisite.extra1_field,validators = [Required()]))                            
        else:
            setattr(F, 'extra1', TextField(wifisite.extra1_field))                            

    if wifisite.emailformfields &  FORM_FIELD_EXTRA2 :
        if wifisite.mandatoryfields & MANDATE_FIELD_EXTRA2:
            setattr(F, 'extra2', TextField('%s*'%wifisite.extra2_field,validators = [Required()]))                            
        else:
            setattr(F, 'extra2', TextField(wifisite.extra2_field))    
    if wifisite.newsletter:
        setattr(F, 'newsletter', BooleanField('Newsletter')) 

    return F()

def generate_voucherform(wifisite):
    class F(Form):
        pass
    setattr(F, 'voucher', TextField('Voucher*',validators = [DataRequired()]))  
    if wifisite.emailformfields &  FORM_FIELD_EMAIL :
        if wifisite.mandatoryfields & MANDATE_FIELD_EMAIL:
            setattr(F, 'email', TextField('%s*'%wifisite.email_field,validators = [Required()])) 
        else:
            setattr(F, 'email', TextField(wifisite.email_field)) 

    if wifisite.emailformfields &  FORM_FIELD_FIRSTNAME :
        if wifisite.mandatoryfields & MANDATE_FIELD_FIRSTNAME:
            setattr(F, 'firstname', TextField('%s*'%wifisite.firstname_field,validators = [Required()])) 
        else:
            setattr(F, 'firstname', TextField(wifisite.firstname_field)) 

    if wifisite.emailformfields &  FORM_FIELD_LASTNAME :
        if wifisite.mandatoryfields & MANDATE_FIELD_LASTNAME:
            setattr(F, 'lastname', TextField('%s*'%wifisite.lastname_field,validators = [Required()])) 
        else:
            setattr(F, 'lastname', TextField(wifisite.lastname_field)) 
    if wifisite.emailformfields &  FORM_FIELD_DOB :
        if wifisite.mandatoryfields & MANDATE_FIELD_DOB:
            setattr(F, 'dob', TextField('%s*'%wifisite.dob_field,validators = [Required()]))     
        else:
            setattr(F, 'dob', TextField(wifisite.dob_field))     

    if wifisite.emailformfields &  FORM_FIELD_EXTRA1 :
        if wifisite.mandatoryfields & MANDATE_FIELD_EXTRA1:
            setattr(F, 'extra1', TextField('%s*'%wifisite.extra1_field,validators = [Required()]))                            
        else:
            setattr(F, 'extra1', TextField(wifisite.extra1_field))                            

    if wifisite.emailformfields &  FORM_FIELD_EXTRA2 :
        if wifisite.mandatoryfields & MANDATE_FIELD_EXTRA2:
            setattr(F, 'extra2', TextField('%s*'%wifisite.extra2_field,validators = [Required()]))                            
        else:
            setattr(F, 'extra2', TextField(wifisite.extra2_field))    
    if wifisite.newsletter:
        setattr(F, 'newsletter', BooleanField('Newsletter')) 
    return F()

def generate_smsform(wifisite):
    class F(Form):
        pass
    setattr(F, 'phonenumber', TextField('Phone Number',validators = [Required()])) 
    if wifisite.emailformfields &  FORM_FIELD_FIRSTNAME :
         setattr(F, 'firstname', TextField('First Name',validators = [Required()])) 
    if wifisite.emailformfields &  FORM_FIELD_LASTNAME :
         setattr(F, 'lastname', TextField('Last Name',validators = [Required()])) 
    if wifisite.emailformfields &  FORM_FIELD_EMAIL :
         setattr(F, 'email', TextField('Email ID',validators = [DataRequired(),Email()]))
    return F()

class PhonenumberForm(Form):
    phonenumber = TextField('Phone Number',validators = [Required()])
    authcode    = TextField('Auth Code',validators = [Required()])


class CheckinForm(Form):
    message = TextAreaField('Optional Message')