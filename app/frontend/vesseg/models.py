import datetime
from . import db
from . import login_manager
import redis
import rq
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


class User(UserMixin, db.Model):

    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    email = db.Column(db.Text, nullable=True)
    password_hash = db.Column(db.String(200), nullable=False)
    admin = db.Column(db.Boolean, nullable=False, default=False)
    last_login = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    created_on = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    projects = db.relationship('Project', backref='user', cascade='save-update, merge, delete, delete-orphan')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        db.session.commit()


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


class Project(UserMixin, db.Model):

    __tablename__ = 'project'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    project = db.Column(db.String(64), nullable=False)
    created_on = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    images = db.relationship('Image', backref='project', cascade='save-update, merge, delete, delete-orphan')

        
    def __repr__(self):
        return '<Project {}>'.format(self.project)


class Image(UserMixin, db.Model):

    __tablename__ = 'image'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    image = db.Column(db.String, nullable=False)
    upload_file_type = db.Column(db.String)
    original_width = db.Column(db.Integer)
    original_height = db.Column(db.Integer)
    resized_width = db.Column(db.Integer)
    resized_height = db.Column(db.Integer)
    x_length = db.Column(db.Float)
    y_length = db.Column(db.Float)
    x_length_unit = db.Column(db.String)
    y_length_unit = db.Column(db.String)
    preprocessed = db.Column(db.Boolean, default=False)
    created_on = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    masks = db.relationship('Mask', backref='image_mask', cascade='save-update, merge, delete, delete-orphan')

    def __repr__(self):
        return '<Image {}>'.format(self.image)


class PredictionModel(UserMixin, db.Model):

    __tablename__ = 'predictionmodel'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    container = db.Column(db.String(64), unique=False, nullable=False)
    model_path = db.Column(db.String(64), nullable=False)
    additional_arguments = db.Column(db.String(128), nullable=True)
    created_on = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    masks = db.relationship('Mask', backref='prediction_mask', cascade='save-update, merge, delete, delete-orphan')

    def __repr__(self):
        return '<PredictionModel {}>'.format(self.name)


class Mask(UserMixin, db.Model):

    __tablename__ = 'mask'

    id = db.Column(db.Integer, primary_key=True)
    mask = db.Column(db.String(128), nullable=False)
    image_id = db.Column(db.Integer, db.ForeignKey('image.id'), nullable=False)
    predictionmodel_id = db.Column(db.Integer, db.ForeignKey('predictionmodel.id'), nullable=False)
    background_pixels = db.Column(db.Integer)
    plaque_pixels = db.Column(db.Integer)
    lumen_pixels = db.Column(db.Integer)
    evaluation = db.Column(db.Integer)
    evaluated_on = db.Column(db.DateTime, nullable=True, default=datetime.datetime.utcnow)
    created_on = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)

    def __repr__(self):
        return '<Mask {}>'.format(self.mask)


class Task(db.Model):

    __tablename__ = 'task'

    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String(128), index=True)
    task_queue = db.Column(db.String(128), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    created_on = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    completed = db.Column(db.Boolean, nullable=False, default=False)

    def get_rq_job(self):
        try:
            rq_job = rq.job.Job.fetch(self.id, connection=current_app.redis)
        except Exception:
            return None
        return rq_job

    def get_progress(self):
        job = self.get_rq_job()
        registry = rq.registry.StartedJobRegistry(queue=current_app.task_queue)
        status = job.meta.get('status', 0) if job is not None else 1
        if status == 1:
            self.completed = True
            db.session.commit()
        status_percent = round(status*100,0)
        return status_percent
    
    
