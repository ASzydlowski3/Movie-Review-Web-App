from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os

db = SQLAlchemy()

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)
engine = db.create_engine("sqlite:///fav_movies.db")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///fav_movies.db"
db.init_app(app)



class EditForm(FlaskForm):
    rating = StringField('Rating')
    review = StringField('Review')
    submit = SubmitField('Change')

class AddForm(FlaskForm):
    title = StringField('Title', render_kw={"placeholder": "Enter movie title", "style": "text-align: center;"}, validators=[DataRequired()])
    submit = SubmitField('submit')

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String, nullable=False)
    rating = db.Column(db.String, nullable=False)
    ranking = db.Column(db.Float, nullable=False)
    review = db.Column(db.String, nullable=False)
    img_url = db.Column(db.String, nullable=False)
    trailer_url = db.Column(db.String, nullable=False)


with app.app_context():
    db.create_all()

@app.route("/")
def home():
    movies = db.session.execute(db.select(Movie).order_by(Movie.rating.desc())).scalars().all()
    return render_template("index.html", movies=movies)

@app.route('/edit', methods=["GET", "POST"])
def edit():
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
    return render_template("edit.html", movie=movie_selected, forms=EditForm())

@app.route('/delete')
def delete():
    movie_id = request.args.get('id')
    movie_selected = db.get_or_404(Movie, movie_id)
    db.session.delete(movie_selected)
    db.session.commit()
    return redirect("/")


########INSERT YOUR TMDB BEARER TOKEN########

headers = {
    "accept": "application/json",
    "Authorization": os.environ['bearer_token']
}



@app.route('/add', methods=["GET", "POST"])
def add():
    addform = AddForm()
    if request.method == 'POST':
        if addform.title.validate(form=addform):
            with app.app_context():
                url = f"https://api.themoviedb.org/3/search/movie?query={request.form.get('title')}&include_adult=false&language=en-US&page=1"
                response = requests.get(url, headers=headers).json()
                movie_data = response['results'][0]
                movie_id = movie_data['id']
                ########INSERT YOUR TMDB API KEY TOKEN########
                trailer_key = requests.get(f'http://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={os.environ["api_key"]}').json()['results'][0]['key']
                new_movie = Movie(
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
                try:
                    db.session.commit()
                except:
                    return redirect('/')
                return redirect('/')
    return render_template("add.html", form=addform)

@app.route('/description')
def description():
    movie_id = request.args.get('id')
    movie_selected = db.get_or_404(Movie, movie_id)
    return render_template("description.html", movie=movie_selected)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
