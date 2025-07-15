from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SelectField, TextAreaField, IntegerField, FileField, FieldList, FormField, Form
from wtforms.validators import DataRequired, Optional
from flask_wtf.file import FileAllowed

class IdentificationForm(Form):
    nin_number = StringField('NIN Number', validators=[DataRequired()])
    passport_number = StringField('Passport Number', validators=[DataRequired()])
    primary_phone = StringField('Primary Phone', validators=[DataRequired()])
    secondary_phone = StringField('Secondary Phone', validators=[Optional()])
    photo = FileField('Photo', validators=[Optional(), FileAllowed(['jpg','png'])])
    nin_doc = FileField('NIN Document', validators=[Optional(), FileAllowed(['pdf','jpg','png'])])

class FamilyMemberForm(Form):
    name = StringField('Name', validators=[DataRequired()])
    alive = SelectField('Alive?', choices=[('yes','Yes'),('no','No')])
    nin = StringField('NIN', validators=[Optional()])
    contact = StringField('Contact', validators=[Optional()])
    address = StringField('Address', validators=[Optional()])

class AcademicForm(Form):
    level = StringField('Level', validators=[DataRequired()])
    institution = StringField('Institution', validators=[DataRequired()])
    award = StringField('Award', validators=[Optional()])
    year = IntegerField('Year', validators=[Optional()])

class WorkForm(Form):
    company = StringField('Company', validators=[DataRequired()])
    title = StringField('Title', validators=[DataRequired()])
    start_date = DateField('Start Date', validators=[Optional()])
    end_date = DateField('End Date', validators=[Optional()])
    responsibilities = TextAreaField('Responsibilities', validators=[Optional()])

class ReferralForm(Form):
    referral_source = StringField('Referral Source', validators=[Optional()])
    referral_person = StringField('Referral Person', validators=[Optional()])

class ClientForm(FlaskForm):
    # Step 1: Personal Info
    full_name = StringField('Full Name', validators=[DataRequired()])
    date_of_birth = DateField('Date of Birth', validators=[DataRequired()])
    marital_status = SelectField('Marital Status', choices=[('single','Single'),('married','Married')])
    religion = StringField('Religion', validators=[Optional()])
    tribe = StringField('Tribe', validators=[Optional()])
    district_of_origin = StringField('District of Origin', validators=[DataRequired()])
    number_of_children = IntegerField('Number of Children', validators=[Optional()])
    occupation = StringField('Occupation', validators=[DataRequired()])
    medical_history = TextAreaField('Medical History', validators=[Optional()])
    # Step 2: Identification
    identification = FormField(IdentificationForm)
    # Step 3: Family Info
    father = FormField(FamilyMemberForm, label="Father")
    mother = FormField(FamilyMemberForm, label="Mother")
    # Step 4: Next of Kin
    nok_name = StringField('Next of Kin Name', validators=[DataRequired()])
    nok_relationship = StringField('Relationship', validators=[DataRequired()])
    nok_contact = StringField('Contact', validators=[DataRequired()])
    nok_address = StringField('Address', validators=[DataRequired()])
    # Step 5: Academic History
    academics = FieldList(FormField(AcademicForm), min_entries=1, max_entries=5)
    # Step 6: Work Experience
    work_exps = FieldList(FormField(WorkForm), min_entries=0, max_entries=5)
    # Step 7: Referral Info
    referral = FormField(ReferralForm)
    submit = StringField('Submit')
