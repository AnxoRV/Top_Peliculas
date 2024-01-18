from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)

#VARIABLES
Lista_Pelis = []
#Url para la busqueda en TMDB
URL_TMDB = "https://api.themoviedb.org/3/search/movie?include_adult=false&language=en-US&page=1"
URL_PARA_IMAGEN = "https://www.themoviedb.org/t/p/w1280/"
API_KEY_TMDB = "dd70b3d1ce2c61064be1c6436f8d9e94"

#Creamos la base de datos
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///peliculas.db"
# crear la extension
db = SQLAlchemy()
# inicializar la app con la extension
db.init_app(app)

#CREAR LA TABLA Pelicula
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)

with app.app_context():
    db.create_all()

#Creo dos entradas por código

# new_movie = Movie(
#     title="BladeRunner",
#     year=2002,
#     description="La historia de un cazador de replicantes en un futuro distopico",
#     rating=9.0,
#     ranking=10,
#     review="Un clasico de la ciencia ficcion",
#     img_url="https://www.themoviedb.org/t/p/w600_and_h900_bestv2/k7tpmwwSqwJ6l1f1FqDMnM7x5c2.jpg"
# )
# segunda_pelicula = Movie(
#     title="Avatar The Way of Water",
#     year=2022,
#     description="Set more than a decade after the events of the first film, learn the story of the Sully family (Jake, Neytiri, and their kids), the trouble that follows them, the lengths they go to keep each other safe, the battles they fight to stay alive, and the tragedies they endure.",
#     rating=7.3,
#     ranking=9,
#     review="I liked the water.",
#     img_url="https://image.tmdb.org/t/p/w500/t6HIqrRAclMCA60NsSmeqe9RmNV.jpg"
# )


# with app.app_context():
#     db.session.add(new_movie)
#     db.session.add(segunda_pelicula)
#     db.session.commit()

#CREAMOS EL FLASK FORM PARA EDITAR
class RateMovieForm(FlaskForm):
    rating = StringField("Tu puntuacion de 1 a 10 aqui")
    review = StringField("Tu comentario aqui...")
    submit = SubmitField("Listo")
#CREAMOS EL FLASK FORM PARA AÑADIR PELICULAS
class AddMovieForm(FlaskForm):
    title = StringField("Introduce el titulo")
    submit = SubmitField("Buscar en TMDB")



@app.route("/")
def home():
    consulta = db.session.execute(db.Select(Movie).order_by(Movie.rating))
    
    #Convertimos el resultado de la consulta en una lista de Python
    Lista_Pelis = consulta.scalars().all()
    
    #Recorremos la lista de pelis, que ya esta ordenada por ranking y le asignamos ranking en secuencia al recorrela
    
    for i in range(len(Lista_Pelis)):
        
        Lista_Pelis[i].ranking = len(Lista_Pelis) - i
        db.session.commit()

    return render_template("index.html", pelis = Lista_Pelis)






#Añadimos la funcionalidad para editar una pelicula
@app.route("/edit", methods=["GET", "POST"])
def edit_movie():
    formulario = RateMovieForm()
    movie_id = request.args.get("id")
    peli_a_editar = db.get_or_404(Movie, movie_id)
    #Si hace click en actualizar/submit en el formulario entra en el if
    if formulario.validate_on_submit():
        peli_a_editar.rating = float(formulario.rating.data)
        peli_a_editar.review = formulario.review.data
        db.session.commit()
        return redirect(url_for('home'))
#si no se está editando aún llega aqui y renderiza la pagina para editar, pasandole la peli a editar y el formulario
    return render_template("edit.html", peli = peli_a_editar, form = formulario)





#Eliminar una pelicula
@app.route("/delete", methods=["GET"])
def delete_movie():
    movie_id = request.args.get("id")
    peli_a_eliminar = db.get_or_404(Movie, movie_id)
    db.session.delete(peli_a_eliminar)
    db.session.commit()
    return redirect(url_for("home"))


app.route("/find", methods=["POST"])
def find_movie():
    #Aqui llega el id de la pelicula que el usuario ha seleccionado entre los resultados de la busqueda, desde select.html
    movie_api_id = request.args.get("id")
    print("Este es el ID: ")
    print(movie_api_id)
    # Si hay un movie_api_id hacemos una nueva llamada a la API para conseguir los detalles de la pelicula
    #es un request especial que se hace con el url añadiendo una barra y el id de la pelicula
    if movie_api_id:
        movie_api_url = f"{URL_TMDB}/{movie_api_id}"
        response = requests.get(movie_api_url, params={"api_key":API_KEY_TMDB, "language": "es_ES"})
        datos = response.json()
        #Damos de alta la pelicula en nuestra base de datos
        nueva_peli = Movie(
            title=datos["title"],
            year=datos["release_date"].split("-")[0],
            #Componemos la URL con la base y el poster_path que nos devuelve la API
            img_url=f"{URL_PARA_IMAGEN}{datos['poster_path']}",
            description=datos["overview"]
        )
        db.session.add(nueva_peli)
        db.session.commit()
        return redirect(url_for("home"))
    


#Añadir una pelicula
@app.route("/add", methods=["GET", "POST"])
def add_movie():
    #API KEY de TMDB: "dd70b3d1ce2c61064be1c6436f8d9e94"
    formulario = AddMovieForm()
    
    if formulario.validate_on_submit():
        print("Buscando...")
        titulo_pelicula = formulario.title.data
        #Buscar en TMDB por titulo accediendo a la API y el modulo request
        response = requests.get(URL_TMDB, params={"api_key":API_KEY_TMDB, "query":titulo_pelicula })
        datos_resultado = response.json()["results"]
        #print(datos_resultado)
        #renderizamos select.html con los resultados posibles para que el usuario elija
        return render_template("select.html", options = datos_resultado)

    #Si no entra en el if, es que no ha hecho aún submit en el formulario asi que lo renderizamos
    return render_template("add.html", form=formulario)



    

if __name__ == '__main__':
    app.run(debug=True)
