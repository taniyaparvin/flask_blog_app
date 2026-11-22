import os

from flask import Flask, abort, flash, redirect, render_template, request, url_for
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)

from models import Comment, Post, User, db

CATEGORIES = ["general", "python", "css", "javascript", "career"]

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-change-this-key")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///blog.db"

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


with app.app_context():
    db.create_all()


# ---------- Public pages ----------

@app.route("/")
def home():
    category = request.args.get("category")
    query = Post.query.order_by(Post.created_at.desc())
    if category:
        query = query.filter_by(category=category)
    posts = query.all()
    heading = f"Posts in {category}" if category else "Latest posts"
    return render_template(
        "home.html", posts=posts, categories=CATEGORIES, heading=heading
    )


@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def view_post(post_id):
    post = db.get_or_404(Post, post_id)

    if request.method == "POST":
        if not current_user.is_authenticated:
            return redirect(url_for("login"))
        text = request.form.get("text", "").strip()
        if text:
            db.session.add(Comment(text=text, post_id=post.id, user_id=current_user.id))
            db.session.commit()
        return redirect(url_for("view_post", post_id=post.id))

    comments = sorted(post.comments, key=lambda c: c.created_at)
    return render_template("post.html", post=post, comments=comments)


# ---------- Auth ----------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not username or not email or len(password) < 6:
            flash("Fill all fields. Password needs at least 6 characters.")
        elif User.query.filter((User.username == username) | (User.email == email)).first():
            flash("That username or email is already taken.")
        else:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash("Account created. You can log in now.")
            return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("home"))
        flash("Wrong email or password.")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


# ---------- Posts CRUD (logged-in users) ----------

@app.route("/create", methods=["GET", "POST"])
@login_required
def create_post():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        body = request.form.get("body", "").strip()
        category = request.form.get("category", "general")

        if not title or not body:
            flash("Title and body are required.")
        else:
            post = Post(title=title, body=body, category=category, user_id=current_user.id)
            db.session.add(post)
            db.session.commit()
            return redirect(url_for("view_post", post_id=post.id))

    return render_template("form.html", post=None, categories=CATEGORIES)


@app.route("/edit/<int:post_id>", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    post = db.get_or_404(Post, post_id)
    if post.user_id != current_user.id:
        abort(403)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        body = request.form.get("body", "").strip()
        if not title or not body:
            flash("Title and body are required.")
        else:
            post.title = title
            post.body = body
            post.category = request.form.get("category", "general")
            db.session.commit()
            return redirect(url_for("view_post", post_id=post.id))

    return render_template("form.html", post=post, categories=CATEGORIES)


@app.route("/delete/<int:post_id>", methods=["POST"])
@login_required
def delete_post(post_id):
    post = db.get_or_404(Post, post_id)
    if post.user_id != current_user.id:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash("Post deleted.")
    return redirect(url_for("my_posts"))


@app.route("/my-posts")
@login_required
def my_posts():
    posts = (
        Post.query.filter_by(user_id=current_user.id)
        .order_by(Post.created_at.desc())
        .all()
    )
    return render_template("home.html", posts=posts, categories=[], heading="My posts")


if __name__ == "__main__":
    app.run(debug=True)
