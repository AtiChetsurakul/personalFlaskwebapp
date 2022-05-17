from flask import Flask,render_template, redirect, url_for, flash,request,send_from_directory
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import *
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from functools import wraps
import pyperclip3 as pyclip
import datetime as dt

# TODO move this to os.env
PASSWORD_STR = os.environ.get('adminpassw','pw')

uri = os.getenv("DATABASE_URL","sqlite:///portf.db")  # or other relevant config var
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
    
app = Flask(__name__)
app.config['SECRET_KEY'] =os.environ.get('secretkey','apple_nohash')
app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['sheet'] = 'static/files'
app.config['sheetpath'] = os.environ.get('SHEETPATH_CV','cv.csv')

db = SQLAlchemy(app)
Bootstrap(app)
login_manager = LoginManager()
login_manager.init_app(app)

ckeditor = CKEditor(app)



'if does not want to use os.env the use these'
"""
PASSWORD_STR = 'pw'
app.config['SECRET_KEY'] ='apple_hash'
"""

'''
database build and config create user and post table into the db file then check if admin are create yet ?
'''

class User(db.Model,UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False,unique=True)
    password = db.Column(db.String(500),nullable=False)
    email = db.Column(db.String(250), nullable=False)

class FolioPost(db.Model):
    __tablename__ = "port_posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    img_url = db.Column(db.String(1000), nullable=False)
    body = db.Column(db.Text,nullable = False)
    category = db.Column(db.String(1),nullable=False)



db.create_all()


'''
automatic_createadmin
if some database flop and then reactivate again the admin which will be only one ID on this webapp will alway be accessible

'''
tocheck = User.query.filter_by(username = 'admin').first()
if not tocheck:
    admin_user = User(username = 'admin',password = generate_password_hash(PASSWORD_STR, method='pbkdf2:sha256', salt_length=8),email = 'none')
    db.session.add(admin_user)
    db.session.commit()


'''
create decorator method
'''

'to given only username match with "admin" only to be able to do the task'
def admin_only(func):
    @wraps(func)
    def inner(*args,**kwargs):
        fal = 'Unauthorize permission',400
        if not current_user :
            return fal
        id = current_user.get_id()
        return func(*args,**kwargs) if (User.query.get(id).username == 'admin') else fal
    return inner


'''
All route for the web app here in this section
'''

@app.route("/")
def hello_world():
    return render_template('index.html')

@app.route('/login',methods = ['GET','POST'])
def to_login():
    form = LoginForm()

    if request.method == 'POST':
        if not form.validate_on_submit():
            return render_template('login.html',form = form)
        tocheck = User.query.filter_by(username = request.form.get('username')).first()
        if not tocheck:
            return 'Non correct',400
        if check_password_hash(tocheck.password,request.form.get('password')):
            login_user(tocheck)
            return redirect(url_for('hello_world'))
    
    return render_template('login.html',form = form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('hello_world'))


@app.route('/cpost',methods = ['GET','POST'])
@login_required
@admin_only
def crpost():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = FolioPost(title=form.title.data,subtitle = form.subtitle.data,date = str(dt.date.today().strftime("%B %d, %Y")),
        img_url = form.img_url.data,body = form.body.data,category = form.category.data)
        '''
        to post body -> using {{body | safe}}
        '''
        if not new_post:
            return 'Bad post',400
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('hello_world'))
    return render_template('testpost.html',form= form)

@app.route('/portfolio')
def show_pf():
    proj = FolioPost.query.all()
    return render_template('portfolio.html',proj = proj)


@app.route('/porj/<int:id>')
def show_each_pj(id):
    pj = FolioPost.query.get(id)
    return render_template('showport.html',pj=pj)


@app.route("/delete/<int:post_id>")
@login_required
@admin_only
def delete_post(post_id):
    post_to_delete = FolioPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('show_pf'))

@app.route("/edit-post/<int:post_id>",methods=['GET','POST'])
@login_required
@admin_only
def edit_post(post_id):
    post = FolioPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        body=post.body,
        category = post.category
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.category = edit_form.category.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_each_pj", id=post.id))

    return render_template("testpost.html", form=edit_form)


'''
route for developer config 
'''

@app.route('/onlyadmin')
@login_required
@admin_only
def test_onlyadmin():
    return 'yay'


@app.route('/download')
def download_cv():
    return send_from_directory(app.config['sheet'],path=app.config['sheetpath'],as_attachment= True)


" framework or api require method "



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))








"app run method"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5050,debug=True)