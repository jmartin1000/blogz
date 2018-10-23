from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['DEBUG'] = True
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://user-name:user-pswd@localhost:8889/db_name'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://get-it-done:get-it-done@localhost:8889/get-it-done'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'P3ys&z73By3kGc'

class Blog(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.Text)
    # added this field to have to develop function to "delete" blog
    hidden = db.Column(db.Boolean)

    def __init__(self, title, body):
        self.title = title
        self.body = body
        self.hidden = False

@app.route('/blog')
def show_blogs():
    blogs = Blog.query.all()
    return render_template('blog-list.html', blogs=blogs)

@app.route("/newpost", methods=['GET', 'POST'])
def compose_blog():

    if request.method == 'POST':
        # pull info from form
        blog_title = request.form.get('title')
        content = request.form.get('blog_text')
        #verify fields are not empty before commiting to db
        if (not blog_title) or (blog_title.strip() == ''):
            flash("Blog need a title", 'error')
            return redirect('/newpost?blog_text='+content)
        elif (not content) or (content.strip() == ''):
            flash("What's a blog without content?", 'error')
            return redirect('/newpost?title='+blog_title)
        else:
            new_blog = Blog(blog_title, content)
            db.session.add(new_blog)
            db.session.commit()

            return redirect('/blog')

    #pull info from form when request is a GET
    blog_title = request.args.get('title')
    content = request.args.get('blog_text')
    blog_title = '' if blog_title is None else blog_title
    content = '' if content is None else content
    return render_template('add-blog.html', title=blog_title, blog_text=content)


if __name__ == "__main__":
    app.run()