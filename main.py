from flask import Flask, render_template, redirect, url_for, request, flash
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
import requests
import os


db = SQLAlchemy()
app = Flask(__name__)
########INSERT YOUR SECRET KEY########
app.config['SECRET_KEY'] = f'{os.urandom(12)}'
Bootstrap5(app)
engine = db.create_engine("sqlite:///fav_movies.db")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///fav_movies.db"
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)





class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log in')


class RegisterForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    submit = SubmitField('Register')


class EditForm(FlaskForm):
    rating = StringField('Rating')
    review = StringField('Review')
    submit = SubmitField('Change')


class AddForm(FlaskForm):
    title = StringField('Title', render_kw={"placeholder": "Enter movie title", "style": "text-align: center;"}, validators=[DataRequired()])
    submit = SubmitField('submit')


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, nullable=False)
    movie_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String, nullable=False)
    rating = db.Column(db.String, nullable=False)
    ranking = db.Column(db.Float, nullable=False)
    review = db.Column(db.String, nullable=False)
    img_url = db.Column(db.String, nullable=False)
    trailer_url = db.Column(db.String, nullable=False)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))


with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

@login_required
@app.route("/")
def home():
    if current_user.is_authenticated:
        movies = db.session.execute(db.select(Movie).where(Movie.owner_id == int(current_user.get_id())).order_by(Movie.rating.desc())).scalars().all()
        return render_template("index.html", movies=movies)
    else:
        return redirect('register')

@app.route('/register', methods=["GET", "POST"])
def register():
    forms = RegisterForm()
    if request.method == 'POST':
        if forms.validate_on_submit():
            result = db.session.execute(db.select(User).where(User.email == request.form.get('email')))
            user = result.scalar()
            if user:
                flash("This e-mail is already in our system, please log in")
                return redirect(url_for('login'))
            new_user = User(
                email=request.form.get('email'),
                password=generate_password_hash(password=request.form.get('password'), method='pbkdf2:sha256', salt_length=8),
                name=request.form.get('name')
            )
            db.session.add(new_user)
            try:
                db.session.commit()
                login_user(new_user)
                return redirect("index.html")
            except:
                login_user(new_user)
                return redirect("index.html")
    return render_template("register.html", forms=forms)


@app.route('/login', methods=["GET", "POST"])
def login():
    forms = LoginForm()
    if request.method == 'POST':
        if forms.validate_on_submit():
            try:
                email = request.form.get('email')
                password = request.form.get('password')
                user = db.session.execute(db.select(User).where(User.email == email)).scalar()
                if check_password_hash(user.password, password):
                    login_user(user)
                    return redirect("/")
            except AttributeError:
                return redirect("/")
    return render_template("login.html", forms=forms)

@login_required
@app.route('/logout')
def logout():
    logout_user()
    return render_template("index.html")

@login_required
@app.route('/edit', methods=["GET", "POST"])
def edit():
    forms = EditForm()
    if request.method == 'POST':
        with app.app_context():
            movie_to_update = db.session.execute(db.select(Movie).where(Movie.id == request.form.get('id'))).scalar()
            if request.form.get('rating'):
                movie_to_update.rating = f"My rating: {request.form.get('rating')}"
            if request.form.get('review'):
                movie_to_update.review = request.form.get('review')
            db.session.commit()
            return redirect("/")
    movie_id = request.args.get('id')
    movie_selected = db.get_or_404(Movie, movie_id)
    return render_template("edit.html", movie=movie_selected, forms=forms)

@login_required
@app.route('/delete')
def delete():
    movie_id = request.args.get('id')
    movie_selected = db.get_or_404(Movie, movie_id)
    if movie_selected:
        db.session.delete(movie_selected)
        db.session.commit()
    return redirect("/")


########INSERT YOUR TMDB BEARER TOKEN########

headers = {
    "accept": "application/json",
    "Authorization": f"Bearer {os.environ['bearer_token']}"
}


@login_required
@app.route('/add', methods=["GET", "POST"])
def add():
    forms = AddForm()
    if request.method == 'POST':
        if current_user.is_authenticated:
            if forms.title.validate(form=forms):
                with app.app_context():
                    url = f"https://api.themoviedb.org/3/search/movie?query={request.form.get('title')}&include_adult=false&language=en-US&page=1"
                    response = requests.get(url, headers=headers).json()
                    movie_data = response['results'][0]
                    movie_id = movie_data['id']
                    ########CHECK FOR DUPLICATES #################

                    potential_duplicates = db.session.execute(db.select(Movie).where(Movie.movie_id == movie_id)).scalars()
                    for title in potential_duplicates:
                        if title.movie_id == movie_id and title.owner_id == int(current_user.get_id()):
                            return redirect('/')

                ########INSERT YOUR TMDB API KEY TOKEN########
                trailer_key = requests.get(f'http://api.themoviedb.org/3/movie/557/videos', headers=headers).json()['results'][0]['key']
                new_movie = Movie(
                    movie_id = movie_id,
                    owner_id=current_user.get_id(),
                    title=movie_data['original_title'],
                    year=int(movie_data['release_date'][0:4]),
                    description=movie_data['overview'],
                    rating=str(f"TMDB: {movie_data['vote_average']}"),
                    ranking=movie_data['popularity'],
                    review="n/a",
                    img_url=f"https://image.tmdb.org/t/p/w500{movie_data['backdrop_path']}",
                    trailer_url=f"https://www.youtube.com/embed/{trailer_key}"
                )
                db.session.add(new_movie)
                db.session.commit()
                return redirect('/')
    return render_template("add.html", forms=forms)

@app.route('/description')
def description():
    movie_id = request.args.get('id')
    movie_selected = db.get_or_404(Movie, movie_id)
    return render_template("description.html", movie=movie_selected)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
