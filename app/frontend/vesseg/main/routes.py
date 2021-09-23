import os
import csv
from os.path import join
from pathlib import Path
import shutil
import datetime
import json
import click
from io import BytesIO
import requests
import zipfile
from functools import wraps
from flask import render_template, request, flash, redirect, url_for, current_app, send_file, jsonify, send_from_directory
from flask_login import current_user
from vesseg import db
from vesseg.main import bp
from vesseg.main.forms import ProjectForm, UploadForm, PreprocessForm, PredictForm, EvaluationForm, PredictionModelForm
from vesseg.models import Project, Image, PredictionModel, Mask, Task, User


# helper functions

def get_project_path(project_id):
    return Path(current_app.config['DATA_PATH'], 'projects', str(project_id))

def get_models_path():
    return Path(current_app.config['DATA_PATH'], 'models')

def get_data_path():
    return Path(current_app.config['DATA_PATH'])

def get_analysis_path(project_id):
    return Path(current_app.config['DATA_PATH'], 'projects', str(project_id), 'analysis')

def get_masks_path(project_id, predictionmodel_id):
    pm = PredictionModel.query.get(predictionmodel_id)
    pm_name = pm.name
    return Path(current_app.config['DATA_PATH'], 'projects', str(project_id), 'predicted', 'masks')


@bp.route('/')
def home():
    return render_template('main/home.html')


@bp.route('/project', methods=['GET', 'POST'])
def project():
    form = ProjectForm()
    if request.method == 'POST':
        if form.validate_on_submit():

            # Create project
            new_project = Project(project=form.project.data, user_id=current_user.id)
            db.session.add(new_project)
            db.session.commit()
            flash('project has been added')

            # Create folder structure for project on disk
            p_id = Project.query.filter_by(project=form.project.data, user_id=current_user.id).first().id
            folders = ['raw', 'preprocessed', 'predicted']
            [Path(get_project_path(p_id), f).mkdir(parents=True, exist_ok=True) for f in folders]

    projects = Project.query.filter_by(user_id=current_user.id).all()
    return render_template('main/project.html', form=form, projects=projects)


@bp.route('/project/delete', methods=['GET'])
def project_delete():
    p_id = request.args.get('project_id')

    # Remove folders and contents on disk
    remove_path = get_project_path(p_id)
    if remove_path.exists():
        shutil.rmtree(remove_path)

    # Remove database entries
    project = Project.query.filter_by(id=p_id).first()
    db.session.delete(project)
    db.session.commit()

    flash('project has been deleted')
    return redirect(url_for('main.project'))


@bp.route('/data', methods=['GET', 'POST'])
def data():
    form = UploadForm()
    form.project_id.choices = [(p.id, p.project) for p in Project.query.filter_by(user_id=current_user.id).all()]
    if request.method == 'POST':

        bio_img_formats = ['.vsi', '.ets'] 
        pil_img_formats = ['.png', '.jpg', '.jpeg', '.tif', '.tiff']     

        project_id = int(request.form['project_id'])
        src_path = Path(str(request.form['path']))
        suffix = str(src_path.suffix)
        stem_pretty = str(src_path.stem).replace('.', '_').replace(' ', '_')
        parent_pretty = str(src_path.parent).replace('.', '_').replace(' ', '_')

        # Save file on disk
        if suffix not in bio_img_formats+pil_img_formats:
            return "File format not supported", 400
        elif suffix in bio_img_formats:
            cat = 'bio'
        elif suffix in pil_img_formats:
            cat = 'pil'
        
        save_path = get_project_path(project_id) / 'raw' / cat / parent_pretty / (stem_pretty + suffix)
        save_path.parent.mkdir(exist_ok=True, parents=True)
        for f in request.files.getlist('file'):
            f.save(save_path)

        # Create database entry
        if not suffix == '.ets':
            if not Image.query.filter_by(project_id=project_id, image=stem_pretty).all():
                new_image = Image(project_id=project_id, image=stem_pretty, upload_file_type=suffix)
                db.session.add(new_image)
                db.session.commit()

    return render_template('main/data.html', form=form)


def walk_directory_to_list(input_directory, val_fxn=lambda x: True):
    """Walks input directory to file list for bioformats reader. Takes a filepath validation function.
    """
    filelist = []

    if not os.path.isdir(input_directory):
        return filelist

    for root, dirs, files in os.walk(input_directory):
        for file in files:
            filepath = os.path.join(root, file)
            if val_fxn(filepath):
                filelist.append(filepath)
    return filelist


@bp.route('/predict', methods=['GET', 'POST'])
def predict():
    form = PredictForm()
    form.project_id.choices = [(p.id, p.project) for p in Project.query.filter_by(user_id=current_user.id).all()]
    form.predictionmodel_id.choices = [(m.id, m.name) for m in PredictionModel.query.filter_by().all()]
    if request.method == 'POST':
        if form.validate_on_submit():

            project_id = form.project_id.data
            tasks = []
            project_path = str(get_project_path(project_id))

            bio_img_formats = ['.vsi', '.ets'] 
            pil_img_formats = ['.png', '.jpg', '.jpeg', '.tif', '.tiff']     

            # Convert bio2png and pil2png 
            bio_path = Path(project_path, 'raw', 'bio')
            bio_files = walk_directory_to_list(bio_path, lambda x: Path(x).suffix in bio_img_formats)
            pil_path = Path(project_path, 'raw', 'pil')
            pil_files = walk_directory_to_list(pil_path, lambda x: Path(x).suffix in pil_img_formats)

            if not bio_files and not pil_files: 
                flash('No valid images added to project. Add images to project by going to the data section.', 'predict')
                return render_template('main/predict.html', form=form)
            if bio_files:
                tasks.append(('file_type_converter:latest', project_path, ['-i', '/data/raw/bio', '-o', '/data/preprocessed']))
            if pil_files:
                tasks.append(('processor:latest', project_path, ['-f', 'pil_to_png', '-i', '/data/raw/pil', '-o', '/data/preprocessed']))

            # Convert mode to plain RGB
            tasks.append(('processor:latest', project_path, ['-f', 'convert_mode', '-i', '/data/preprocessed', '-o', '/data/preprocessed']))

            # Resize to (512,512)
            tasks.append(('processor:latest', project_path, ['-f', 'resize', '-i', '/data/preprocessed', '-o', '/data/preprocessed']))

            # # Predict
            predictionmodel_id = form.predictionmodel_id.data
            pm = PredictionModel.query.get(predictionmodel_id)
            name = pm.name.replace(' ', '_').replace('.','_')
            container = pm.container
            data_path = str(get_data_path())
            model_path = os.path.join('/data/models', pm.model_path)
            prepro_path = os.path.join('/data/projects', str(project_id), 'preprocessed')
            pred_mask_path = os.path.join('/data/projects', str(project_id), 'predicted', name, 'masks')
            pred_olay_path = os.path.join('/data/projects', str(project_id), 'predicted', name, 'olays')
            additional_arguments = pm.additional_arguments.strip().split(' ') if pm.additional_arguments else []
            additional_arguments = [str(ag) for ag in additional_arguments]


            Path(project_path, 'predicted', name, 'masks').mkdir(parents=True, exist_ok=True)
            tasks.append((container, data_path, ['-i', prepro_path, '-o', pred_mask_path, '-m', model_path] + additional_arguments))

            # Add post-processing
            tasks.append(('processor:latest', project_path, ['-f', 'create_overlay', '-i', '/data/preprocessed', '-o', '/data/predicted/' + name + '/olays' ]))

            # Add analysis
            kwarg_str = '{"predictionmodel_name": "' + name +'"}'
            tasks.append(('processor:latest', project_path, ['-f', 'analyzer', '-i', '/data', '-o', '', '-k', kwarg_str]))
            
            # Add tasks
            task_ids = add_tasks(tasks, current_user.id, project_id)
            flash('Prediction tasks have been added to queue.', 'predict')
            task_ids = [{'task_id': task_id} for task_id in task_ids]
            return render_template('main/predict.html', form=form, tasks=task_ids)
    return render_template('main/predict.html', form=form)


@bp.route('/evaluate', methods=['GET', 'POST'])
def evaluate():
    form = EvaluationForm()
    form.project_id.choices = [(p.id, p.project) for p in Project.query.filter_by(user_id=current_user.id).all()]
    form.predictionmodel_id.choices = [(m.id, m.name) for m in PredictionModel.query.filter_by().all()]
    if request.method == 'POST':
        if form.validate_on_submit():
            project_id = form.project_id.data
            project_name = Project.query.get(project_id).project
            predictionmodel_id = form.predictionmodel_id.data
            predictionmodel_name = PredictionModel.query.get(predictionmodel_id).name

            # Update database and make evaluation list

            masks = walk_directory_to_list(join(get_project_path(project_id), 'predicted', predictionmodel_name, 'masks'), lambda x: x.endswith('.png'))

            if not masks:
                flash('No predictions found for the selected project model combination.')
                return redirect(url_for('main.evaluate'))

            evaluation = []

            for m in masks:
                mask_name = str(Path(m).stem)
                project_id = int(project_id)
                predictionmodel_id = int(predictionmodel_id)
                image_id = Image.query.filter_by(project_id=project_id, image=mask_name).first().id
                mask = Mask.query.filter_by(image_id=image_id, predictionmodel_id=predictionmodel_id).first()
                if not mask:
                    db.session.add(Mask(mask=mask_name, image_id=image_id, predictionmodel_id=predictionmodel_id))
                    db.session.commit()
                    mask = Mask.query.filter_by(image_id=image_id, predictionmodel_id=predictionmodel_id).first()
                mask_id = mask.id 
                mask_evaluation = mask.evaluation
                mask_evaluation_on = mask.evaluated_on
                mask_path = m.replace('/masks/', '/olays/')
                image_path = join(get_project_path(project_id), 'preprocessed', str(Path(m).name))

                evaluation.append({
                    'mask_id': mask_id,
                    'mask_path': mask_path, 
                    'current_evaluation': mask_evaluation,
                    'current_evaluation_on': mask_evaluation_on,
                    'image_path': image_path
                })
                

            return render_template('main/evaluation.html',
                                   evaluation=evaluation,
                                   predictionmodel_name=predictionmodel_name,
                                   project_name=project_name)
    return render_template('main/evaluate.html', form=form)


@bp.route('/data/image/<path:path>')
def get_image(path):
    filename = Path('/', path).name
    directory = Path('/', path).parent
    return send_from_directory(directory, filename, as_attachment=True)


@bp.route('/data/evaluation', methods=['POST'])
def set_evaluation():

    mask_id = int(request.form['mask_id'])
    evaluation = int(request.form['new_evaluation'])
    evaluated_on = datetime.datetime.utcnow()

    mask = Mask.query.get(mask_id)
    mask.evaluation = evaluation
    mask.evaluated_on = evaluated_on
    db.session.commit()

    return json.dumps({'success': True, 'evaluation': evaluation, 'evaluated_on': str(evaluated_on)}), 200, \
           {'ContentType': 'application/json'}


@bp.route('/download/<int:project_id>')
def download_project(project_id):

    analysis_path = get_analysis_path(project_id)

    images = db.session.query(Image).filter_by(project_id=project_id).all()
    image_ids = [i.id for i in images]
    eval_data = db.session.query(Mask, PredictionModel)\
        .join(PredictionModel, Mask.predictionmodel_id == PredictionModel.id)\
        .filter(Mask.image_id.in_(image_ids))\
        .all()
    
    eval_info = []
    
    for row in eval_data:
        
        eval_info.append({
            'image': row.Mask.mask,
            'predictionmodel_name': row.PredictionModel.name, 
            'evaluation': row.Mask.evaluation
        })

    column_headers = ['image', 'predictionmodel_name', 'evaluation']
    file_name = 'evaluation_analysis.csv'

    with open(join(analysis_path, file_name), 'w') as f:
        dict_writer = csv.DictWriter(f, column_headers)
        dict_writer.writeheader()
        dict_writer.writerows(eval_info)
    
    analysis_files = walk_directory_to_list(analysis_path)

    memory_zip_file = BytesIO()
    with zipfile.ZipFile(memory_zip_file, 'w') as zf:
        for a in analysis_files:
            zf.write(a, Path(a).name)
    memory_zip_file.seek(0)
    return send_file(memory_zip_file, attachment_filename='analysis.zip', as_attachment=True)


@bp.route('/tasks', methods=['GET', 'POST'])
def tasks():
    tasks = Task.query.filter(Task.user_id == current_user.id, Task.completed != True).all()
    return render_template('main/tasks.html', tasks=tasks)


@bp.route('/tasks/status', methods=['GET'])
def _tasks_status():
    task_id = request.args.get('task_id')
    task = Task.query.get(task_id)
    progress = task.get_progress()
    return json.dumps({'task_id': task_id, 'progress': progress})


def add_tasks(tasks, user_id, project_id):

    task_ids = []
    kwargs = {'job_timeout': '12h'}
    for i, task in enumerate(tasks):
        if i>0:
            kwargs['depends_on'] = task_ids[i-1]

        rq_job = current_app.task_queue.enqueue('docker_launcher.docker_launcher', args=task, **kwargs)
        task_ids.append(rq_job.get_id())
        db_task = Task(id=task_ids[-1], name=task[0], user_id=user_id, project_id=project_id, task_queue=current_app.task_queue.name)
        db.session.add(db_task)
        db.session.commit()
    
    return task_ids


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not User.query.get(current_user.id).admin:
            return "Admin status required.", 401
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/admin', methods=['GET'])
@admin_required
def admin():
    return render_template('main/admin.html')
    # return render_template('main/admin.html')


@bp.route('/admin/projects', methods=['GET', 'POST'])
@admin_required
def admin_projects():
    projects = db.session.query(User, Project).join(User, Project.user_id == User.id).all()
    return render_template('main/admin_projects.html', projects=projects)


@bp.route('/admin/projects/delete', methods=['GET', 'POST'])
@admin_required
def admin_projects_delete():
    p_id = request.args.get('project_id')

    # Remove folders and contents on disk
    remove_path = get_project_path(p_id)
    if remove_path.exists():
        shutil.rmtree(remove_path)

    # Remove database entries
    project = Project.query.filter_by(id=p_id).first()
    db.session.delete(project)
    db.session.commit()

    return redirect(url_for('main.admin_projects'))


@bp.route('/admin/models', methods=['GET', 'POST'])
@admin_required
def admin_models():
    form = PredictionModelForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            pm = PredictionModel(
                name=form.name.data, 
                container=form.container.data, 
                model_path=form.model_path.data, 
                additional_arguments=form.additional_arguments.data
                )
            db.session.add(pm)
            db.session.commit()
            return redirect(url_for('main.admin_models'))
    pms = PredictionModel.query.all()
    return render_template('main/admin_models.html', form=form, pms=pms)


@bp.route('/admin/models/delete', methods=['GET'])
@admin_required
def admin_models_delete():
    pm_id = request.args.get('pm_id')
    pm = PredictionModel.query.get(pm_id)
    db.session.delete(pm)
    db.session.commit()
    return redirect(url_for('main.admin_models'))


@bp.route('/download/<filename>', methods=['GET', 'POST'])
def download(filename):
    model_download_path = os.path.join(get_models_path(), 'download')
    return send_from_directory(model_download_path, filename, as_attachment=True)    

