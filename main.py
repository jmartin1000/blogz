from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import desc

app = Flask(__name__)
app.config['DEBUG'] = True
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://user-name:user-pswd@localhost:8889/db_name'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:blogz@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'Gs3k&zc3y73PBy'


class Blog(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.Text)
    pub_date = db.Column(db.DateTime)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    hidden = db.Column(db.Boolean)

    def __init__(self, title, body, pub_date, owner):
        self.title = title
        self.body = body
        self.pub_date = datetime.utcnow()
        self.owner_id = owner
        self.hidden = False
    
    def __repr__(self):
        return '<Blog %r>' % self.title

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def __repr__(self):
        return '<User %r>' %self.username

@app.before_request
def require_login():
    allowed_routes = ['login', 'signup']
    if request.endpoint not in allowed_routes and "username" not in session:
        return redirect('/login')

@app.route('/')
def index():
    return render_template('index.html', header_title='Home')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        verify = request.form.get('verify')
        # validate user name
        if len(username) < 3:
            flash('Valid username must be at least 3 characters')
            return redirect('/signup')
        elif not is_distinct(username):
            flash(username + ' already in use')
            return redirect('/signup')
        # validate password
        elif not password:
            flash('Oops! Did you forget to enter a password?')
            return redirect('/signup')
        elif password != verify:
            flash('The passwords do not match')
            return redirect('/signup')
        # all is well - create user and open session
        else:
            user = User(username=username, password=password)
            db.session.add(user)
            db.session.commit()
            session['username'] = user.username
            return redirect('/newpost')
    else:
        return render_template('signup.html', header_title='Register with Blogz!')

def is_distinct(string):
    existing_user = User.query.filter_by(username=string).first()
    if not existing_user:
        return True
    else:
        return False

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session['username'] = username
            return redirect('/newpost')
        elif not user:
            flash(user + ' is not a registered username')
            return redirect('/login')
        elif password != user.password:
            flash('invalid password')
            return redirect('/login')
    return render_template('login.html', header_title='Log into Blogz!')

@app.route('/logout')
def logout():
    del session['username']
    return redirect("/blog")

@app.route('/blog')
def show_blogs():
    # need this if statement to deal with two diff get posts 
    # the first is the case when we want the blog list to load
    # the sedond is when we want to view a page with only one  specified blog
    if len(request.args) == 0:
        blogs = Blog.query.filter_by(hidden=False).order_by(desc(Blog.pub_date)).all()
        return render_template('blog-list.html', blogs=blogs, header_title="Blogs")
    else:
        blog_id = request.args.get('id')
        blog = Blog.query.get(blog_id)
        header_title = blog.title
        curr_user = User.query.filter_by(username=session['username']).first()
        return render_template('blog-page.html', blog=blog, header_title=header_title, curr_user=curr_user)


@app.route("/newpost", methods=['GET', 'POST'])
def compose_blog():
    # add this line after esatablishing sessions, to identify owner
    #owner = User.query.filter_by(email=session['email']).first()

    if request.method == 'POST':
        print("/newpost POST method initiated")
        # pull info from form
        blog_title = request.form.get('title')
        content = request.form.get('blog_text')
        date = request.form.get('date')
        #verify fields are not empty before commiting to db
        if (not blog_title) or (blog_title.strip() == ''):
            flash("Blogs need a title, silly!", 'error')
            return redirect('/newpost?blog_text='+content+'&blog_date='+date)
        elif (not content) or (content.strip() == ''):
            flash("What's a blog without content?", 'error')
            return redirect('/newpost?title='+ blog_title +'&blog_date=' + date)
        else:
            owner = User.query.filter_by(username=session['username']).first()
            print('ALERT!!! new post blog title = ', blog_title, "owner id = ", owner.id)
            new_blog = Blog(blog_title, content, date, owner.id)
            db.session.add(new_blog)
            db.session.commit()
            view = Blog.query.filter_by(title=blog_title).first()
            blog_id = str(view.id)
            print('ALERT!!! new post blog id = ', blog_id)
            print("BLOG ID of new post =", blog_id)
            return redirect('/blog?id=' + blog_id + 'header_title=' + blog_title)

    #pull info from form when request is a GET
    blog_title = request.args.get('title')
    content = request.args.get('blog_text')
    blog_date = request.args.get('blog_date')
    blog_title = '' if blog_title is None else blog_title
    content = '' if content is None else content
    blog_date = datetime.utcnow() if blog_date is None else blog_date
    return render_template('add-blog.html', header_title='Add a Blog Entry',title=blog_title, blog_text=content, blog_date=blog_date)

# opens a template that allows user to edit blog
@app.route('/edit-blog', methods=['POST'])
def edit_blog():

    blog_id = int(request.form.get('blog-id'))
    blog = Blog.query.get(blog_id)
    print("blog.pub_date = ",blog.pub_date)
    blog_date = str(blog.pub_date)
    print("blog_date = ",blog_date)

    return render_template('edit-blog.html', blog=blog, blog_date=blog_date, header_title="Edit Blog Entry")

# does the work of updating the entry in the database
@app.route('/update-blog', methods=['POST'])
def update_blog():

    blog_id = int(request.form.get('blog-id'))
    new_title = request.form.get('title')
    new_body = request.form.get('blog_text')
    new_date = request.form.get('date')
    blog = Blog.query.get(blog_id)
    blog.title = new_title
    blog.body = new_body
    #blog.pub_date = new_date
    blog.pub_date = datetime.utcnow() if new_date is None else new_date
    db.session.add(blog)
    db.session.commit()
    print("blog.pub_date = ", blog.pub_date)
    
    return redirect('/blog?id='+str(blog_id))

# asks the user to verify that they want to delete an entry
@app.route('/delete-blog', methods=['POST'])
def delete_blog():

    blog_id = int(request.form.get('blog-id'))
    blog = Blog.query.get(blog_id)

    return render_template('verify-delete.html', blog=blog, header_title="Are you sure you want to delete?")

# updates the entry to "hide" the blog entry
@app.route('/complete-delete', methods=['POST'])
def complete_delete():

    blog_id = int(request.form.get('blog-id'))
    blog = Blog.query.get(blog_id)
    blog.hidden = True
    db.session.add(blog)
    db.session.commit()

    return redirect("/blog")



if __name__ == "__main__":
    app.run()