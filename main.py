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
    hidden = db.Column(db.Boolean)

    def __init__(self, title, body):
        self.title = title
        self.body = body
        self.hidden = False

@app.route('/blog')
def show_blogs():
    # need this if statement to deal with two diff get posts 
    # the first is the case when we want the blog list to load
    # the sedond is when we want to view a page with only one  specified blog
    if len(request.args) == 0:
        blogs = Blog.query.filter_by(hidden=False).all()
        return render_template('blog-list.html', blogs=blogs)
    else:
        blog_id = request.args.get('id')
        blog = Blog.query.get(blog_id)
        return render_template('blog-page.html', blog=blog)


@app.route("/newpost", methods=['GET', 'POST'])
def compose_blog():

    if request.method == 'POST':
        # pull info from form
        blog_title = request.form.get('title')
        content = request.form.get('blog_text')
        #verify fields are not empty before commiting to db
        if (not blog_title) or (blog_title.strip() == ''):
            flash("Blogs need a title, silly!", 'error')
            return redirect('/newpost?blog_text='+content)
        elif (not content) or (content.strip() == ''):
            flash("What's a blog without content?", 'error')
            return redirect('/newpost?title='+blog_title)
        else:
            new_blog = Blog(blog_title, content)
            db.session.add(new_blog)
            db.session.commit()
            view = Blog.query.filter_by(title=blog_title).first()
            blog_id = str(view.id)
            return redirect('/blog?id=' + blog_id)

    #pull info from form when request is a GET
    blog_title = request.args.get('title')
    content = request.args.get('blog_text')
    blog_title = '' if blog_title is None else blog_title
    content = '' if content is None else content
    return render_template('add-blog.html', title=blog_title, blog_text=content)

# opens a template that allows user to edit blog
@app.route('/edit-blog', methods=['POST'])
def edit_blog():

    blog_id = int(request.form.get('blog-id'))
    blog = Blog.query.get(blog_id)

    return render_template('edit-blog.html', blog=blog)

# does the work of updating the entry in the database
@app.route('/update-blog', methods=['POST'])
def update_blog():

    blog_id = int(request.form.get('blog-id'))
    new_title = request.form.get('title')
    new_body = request.form.get('blog_text')
    blog = Blog.query.get(blog_id)
    blog.title = new_title
    blog.body = new_body
    db.session.add(blog)
    db.session.commit()
    
    return redirect('/blog?id='+str(blog_id))

# asks the user to verify that they want to delete an entry
@app.route('/delete-blog', methods=['POST'])
def delete_blog():

    blog_id = int(request.form.get('blog-id'))
    blog = Blog.query.get(blog_id)

    return render_template('verify-delete.html', blog=blog)

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