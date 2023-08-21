from flask import Flask, render_template, redirect, url_for, request, flash
from flask_bootstrap import Bootstrap5
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, LoginManager, login_required, current_user, logout_user
import requests
import os
from forms import *
from dbmodels import *
import random
import string

app = Flask(__name__)
########INSERT YOUR SECRET KEY########
app.config['SECRET_KEY'] = ''.join(random.choices(string.ascii_lowercase, k=12))
Bootstrap5(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///fav_movies.db"
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)


with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

####################### FRONT END ROUTES ##############################

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
                name=request.form.get('name'),
                apikey = ''.join(random.choices(string.ascii_lowercase, k=30))
            )
            db.session.add(new_user)
            try:
                db.session.commit()
                login_user(new_user)
                return redirect("/")
            except:
                login_user(new_user)
                return redirect("/")
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
                    try:
                        movie_data = response['results'][0]
                        movie_id = movie_data['id']
                    except IndexError:
                        flash("Movie not found, try again")
                        return redirect(url_for('add'))
                    ########CHECK FOR DUPLICATES #################

                    potential_duplicates = db.session.execute(db.select(Movie).where(Movie.movie_id == movie_id)).scalars()
                    for title in potential_duplicates:
                        if title.movie_id == movie_id and title.owner_id == int(current_user.get_id()):
                            return redirect('/')

                try:
                    trailer_key = requests.get(f'http://api.themoviedb.org/3/movie/{movie_id}/videos', headers=headers).json()['results'][0]['key']
                except IndexError:
                    trailer_key = False
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


@app.context_processor
def inject_api_key():
    try:
        apikey = db.session.execute(db.select(User).where(User.id == int(current_user.get_id()))).scalar().apikey
        return dict(current_api=apikey)
    except TypeError:
        return dict(current_api='empty')

####################### API ROUTES ##############################


def authorization(apikey):
    user = db.session.execute(db.select(User).where(User.apikey == apikey)).scalar()
    if user:
        return user.id
    return False

@app.route('/api/movies', methods=["GET"])
def movies_api():
    requesting_user_id = authorization(request.headers.get('apikey'))
    if requesting_user_id:
        movies = db.session.execute(db.select(Movie).where(Movie.owner_id == requesting_user_id).order_by(
            Movie.rating.desc())).scalars().all()
        response = []
        for movie in movies:
            response.append({
                'id' : movie.id,
                'movie_id': movie.movie_id,
                'owner_id': movie.owner_id,
                'title': movie.title,
                'year': movie.year,
                'description': movie.description,
                'rating': movie.rating,
                'ranking': movie.ranking,
                'review': movie.review,
                'img_url': movie.img_url,
                'trailer_url': movie.trailer_url
            })
        return response
    return {'response': 'invalid data provided'}


@app.route('/api/register', methods=["POST"])
def register_api():
    check_if_exists = db.session.execute(db.select(User).where(User.email == request.headers.get('email'))).scalar()
    if not check_if_exists:
        new_user = User(
            email=request.headers.get('email'),
            password=generate_password_hash(password=request.headers.get('password'), method='pbkdf2:sha256',
                                            salt_length=8),
            name=request.headers.get('name'),
            apikey=''.join(random.choices(string.ascii_lowercase, k=30))
        )
        db.session.add(new_user)
        db.session.commit()
        return {'result': 'Successfully registered new user',
                'apikey': new_user.apikey}
    else:
        return {'response': 'invalid data provided'}


@app.route('/api/add', methods=["POST"])
def add_api():
    requesting_user_id = authorization(request.headers.get('apikey'))
    if requesting_user_id:
        with app.app_context():
            url = f"https://api.themoviedb.org/3/search/movie?query={request.args.get('title')}&include_adult=false&language=en-US&page=1"
            response = requests.get(url, headers=headers).json()
            try:
                movie_data = response['results'][0]
                movie_id = movie_data['id']
            except IndexError:
                return {'result': 'Movie not found'}

            ########CHECK FOR DUPLICATES #################

            potential_duplicates = db.session.execute(
                db.select(Movie).where(Movie.movie_id == movie_id)).scalars()
            for title in potential_duplicates:
                if title.movie_id == movie_id and title.owner_id == requesting_user_id:
                    return {'result': 'movie already added'}

            try:
                trailer_key = \
                requests.get(f'http://api.themoviedb.org/3/movie/{movie_id}/videos', headers=headers).json()['results'][
                    0]['key']
            except IndexError:
                trailer_key = False
            new_movie = Movie(
                movie_id=movie_id,
                owner_id=requesting_user_id,
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
            return {'result': f'{new_movie.title} successfully added'}

@app.route('/api/edit', methods=["POST"])
def edit_api():
    requesting_user_id = authorization(request.headers.get('apikey'))
    if requesting_user_id:
        with app.app_context():
            movie_to_update = db.session.execute(db.select(Movie).where(Movie.id == request.args.get('id'))).scalar()
            if requesting_user_id == movie_to_update.owner_id:
                if request.args.get('rating'):
                    movie_to_update.rating = f"My rating: {request.args.get('rating')}"
                if request.args.get('review'):
                    movie_to_update.review = request.args.get('review')
                db.session.commit()
                return {'result': f'Successfully edited {movie_to_update.title}'}
    return {'response': 'invalid data provided'}


@app.route('/api/delete', methods=["DELETE"])
def delete_api():
    requesting_user_id = authorization(request.headers.get('apikey'))
    if requesting_user_id:
        with app.app_context():
            movie_to_delete = db.session.execute(db.select(Movie).where(Movie.id == request.args.get('id'))).scalar()
            if movie_to_delete:
                if requesting_user_id == movie_to_delete.owner_id:
                    title = movie_to_delete.title
                    db.session.delete(movie_to_delete)
                    db.session.commit()
                    return {'result': f'Successfully deleted {title}'}
    return {'response': 'invalid data provided'}


if __name__ == '__main__':
    app.run(host='0.0.0.0')
