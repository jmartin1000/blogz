from flask import Flask, request, redirect, render_template, session, flash
#from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import desc, asc
from app import app, db
from models import User, Blog
from hashutils import make_pw_hash, make_salt, check_pw_hash

app.secret_key = 'Gs3k&zc3y73PBy'

@app.before_request
def require_login():
    allowed_routes = ['login', 'signup', 'index', 'show_blogs']
    if request.endpoint not in allowed_routes and "username" not in session:
        return redirect('/login')

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    #blogs = Blog.query.filter_by(hidden=False).order_by(desc(Blog.pub_date)).all()
    users = User.query.order_by(asc(User.username)).paginate(page=page, per_page=5)
    return render_template('index.html', header_title='Blogz', users=users)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        verify = request.form.get('verify')
        # validate user name
        if len(username) < 3:
            flash('Valid username must be at least 3 characters', 'error')
            return redirect('/signup')
        elif not is_distinct(username):
            flash(username + ' already in use', 'error')
            return redirect('/signup')
        # validate password
        elif not password:
            flash('Oops! Did you forget to enter a password?', 'error')
            return redirect('/signup')
        elif password != verify:
            flash('The passwords do not match', 'error')
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
        if user and check_pw_hash(password, user.pw_hash):
            session['username'] = username
            return redirect('/newpost')
        elif not user:
            flash(user + ' is not a registered username', 'error')
            return redirect('/login')
        elif not check_pw_hash(password, user.pw_hash):
            flash('invalid password', 'error')
            return redirect('/login')
    return render_template('login.html', header_title='Log into Blogz!')

@app.route('/logout')
def logout():
    del session['username']
    return redirect("/blog")  

@app.route('/blog')
def show_blogs():
    print('!!!!!! ARGS: page=', request.args.get('page'), 'user=', request.args.get('user'), 'blog id=', request.args.get('id'))
    # need this if statement to deal with two diff get posts 
    # the first is the case when we want the blog list to load
    # the sedond is when we want to view a page with only one  specified blog
    if (request.args.get('user') == None or request.args.get('user') == '') and (request.args.get('id') == None or request.args.get('id') == ''):
        print('!!!!! CASE 1')
        page = request.args.get('page', 1, type=int)
        blogs = Blog.query.filter_by(hidden=False).order_by(desc(Blog.pub_date)).paginate(page=page, per_page=5)
        return render_template('blog-list.html', blogs=blogs, header_title="Blogs")
    elif request.args.get('id') != None:
        print('!!!!! CASE 2')
        blog_id = request.args.get('id')
        blog = Blog.query.get(blog_id)
        header_title = blog.title
        if 'username' in session:
            curr_user = User.query.filter_by(username=session['username']).first()
            return render_template('blog-page.html', blog=blog, header_title=header_title, curr_user=curr_user)
        else:
            return render_template('blog-page.html', blog=blog, header_title=header_title)
    elif request.args.get('user') != None:
        print('!!!!! CASE 3')
        page = request.args.get('page', 1, type=int)
        user_id = request.args.get('user')
        user = User.query.get(user_id)
        header_title = 'Blogs by ' + user.username
        blogs = Blog.query.filter_by(owner_id=user.id, hidden=False).order_by(desc(Blog.pub_date)).paginate(page=page, per_page=5)
        if 'username' in session:
            curr_user = User.query.filter_by(username=session['username']).first()
            return render_template('blog-list.html', blogs=blogs, owner_id=user.id, header_title=header_title, curr_user=curr_user)
        else:
            return render_template('blog-list.html', blogs=blogs, owner_id=user_id, header_title=header_title)


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
            new_blog = Blog(blog_title, content, date, owner.id)
            db.session.add(new_blog)
            db.session.commit()
            view = Blog.query.filter_by(title=blog_title).first()
            blog_id = str(view.id)
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
    blog_date = str(blog.pub_date)

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
    blog.pub_date = datetime.utcnow() if new_date is None else new_date
    db.session.add(blog)
    db.session.commit()
    
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