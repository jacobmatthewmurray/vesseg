from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import StringField, SubmitField, SelectField, MultipleFileField, BooleanField
from wtforms.validators import ValidationError, DataRequired
from ..models import Project, Image, Mask, PredictionModel


class ProjectForm(FlaskForm):

    project = StringField('project', validators=[DataRequired()])
    submit = SubmitField('create')

    def validate_project(self, project):
        existing_project = Project.query.filter_by(user_id=current_user.id)\
            .filter_by(project=project.data).first()
        if existing_project is not None:
            raise ValidationError('please use a different project name.')


class UploadForm(FlaskForm):

    project_id = SelectField('select project for which to upload files', validators=[DataRequired()], coerce=int)
    files = MultipleFileField('choose directory of files')
    submit = SubmitField('upload')


class PreprocessForm(FlaskForm):

    project_id = SelectField('select project for preprocessing', validators=[DataRequired()], coerce=int)
    preprocess = SelectField('select preprocess routine', validators=[DataRequired()], coerce=int)
    submit = SubmitField('preprocess')

    def validate_project_id(self, project_id):
        image_data = Image.query.filter_by(project_id=project_id.data).first()
        if image_data is None:
            raise ValidationError('selected project does not contain image data. please first upload images.')


class PredictForm(FlaskForm):

    project_id = SelectField('select project for prediction', validators=[DataRequired()], coerce=int)
    predictionmodel_id = SelectField('select prediction model', validators=[DataRequired()], coerce=int)
    submit = SubmitField('predict')


class EvaluationForm(FlaskForm):

    project_id = SelectField('select project for evaluation', validators=[DataRequired()], coerce=int)
    predictionmodel_id = SelectField('select prediction model', validators=[DataRequired()], coerce=int)
    submit = SubmitField('evaluate')


class PredictionModelForm(FlaskForm):

    name = StringField('model name', validators=[DataRequired()])
    container = StringField('container name', validators=[DataRequired()])
    model_path = StringField('path to model, relative to .../data/models', validators=[DataRequired()])
    additional_arguments = StringField('addtl arguments separated by a space')
    submit = SubmitField('add model')

    def validate_name(self, name):
        existing_name = PredictionModel.query.filter_by(name=name.data).first()
        if existing_name is not None:
            raise ValidationError('model exists, please use a different model name.')