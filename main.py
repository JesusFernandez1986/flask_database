from flask import Flask, render_template, request, redirect, url_for, make_response
from models import User, db
import random
import hashlib
import uuid

app = Flask(__name__)
db.create_all()

wrong_guess = []

@app.route("/login", methods=["POST"])
def login():
    name = request.form.get("user-name")        #cogemos del formulario el nombre y el email y los guardamos en las variables name y email
    email = request.form.get("user-email")
    secret_number = random.randint(1, 30)       #generamos un numero aleatorio y lo guardamos en secret_number
    password = request.form.get("user-password")

    hashed_password = hashlib.sha256(password.encode()).hexdigest()     #encriptamos el password


    user = db.query(User).filter_by(email=email).first()    #comprobamos si ese usuario existe en nuestra base de datos, filtrando por el email

    if not user:                                #si no hay un usuario registrado, creamos una instancia nueva para ese usuario y la guardamos en la bsae de datos
        user = User(name=name, email=email, secret_number=secret_number, password=hashed_password,)
        db.add(user)
        db.commit()

    if hashed_password != user.password:
        return "WRONG PASSWORD! Go back and try again."
    elif hashed_password == user.password:             #si el password introducido es igual al de la base de datos generamos un numero de sesion y lo guardamos en la BD
        session_token = str(uuid.uuid4())
        user.session_token = session_token
        db.add(user)
        db.commit()

    response = make_response(redirect(url_for('index')))
    response.set_cookie("session_token", session_token, httponly=True, samesite='Strict')       #guardamos el token de sesions en una cookie llamada session_token
    return response

@app.route('/', methods=["GET", "POST"])
def index():
    if request.method == "GET":
        data = {}
        session_token = request.cookies.get("session_token")                        #guardamos el valor de la cookie session token en la variable session_token

        if session_token:
            user = db.query(User).filter_by(session_token=session_token).first()  #si tenemos una session token, miramos y comparamos en la base de datos
        else:                                                                       #si no creamos una instancia user vacia
            user = None

        data.update({'user': user})
        return render_template("index.html", data=data)


    elif request.method == "POST":
        guess = request.form.get('guess', False)
        email_address = request.cookies.get("email")
        user = db.query(User).filter_by(email=email_address).first()

        try:                    # compara si el valor introducido es un entero y si no lo es devuelve un error
            guess = int(guess)
        except Exception:
            data = {'result': False,
                    "user": user,
                    "error": 2}
            response = make_response(render_template("index.html", data=data))
            return response

        if guess > 30 or guess < 1:    #comprueba que ademas de ser un entero sea un valor comprendido entre 1 y 30, si no devuelve un error
            data = {'result': False,
                    "user": user,
                    "error": 1}
            response = make_response(render_template("index.html", data=data))
            return response

        if guess == int(user.secret_number):    # Si ha acertado:
            new_secret = random.randint(1, 30)
            user.secret_number = new_secret
            db.add(user)
            db.commit()
            new_wrong = wrong_guess.copy()
            data = {'result': True,
                    "wrong_guess": new_wrong,
                    "user": user}
            wrong_guess.clear()
            response = make_response(render_template("index.html", data=data))
            return response
        else:                              # Si no hemos acertado damos una pista para que pueda acertar
            if int(user.secret_number) < guess:
                data = {'result': False, # Diferentes lineas para mas orden y solo un diccionario con datos
                        'hint': "Demasiado grande, prueba algo mas pequeño",
                        'user': user}
            else:
                data = {'result': False,
                        'hint': "Demasiado pequeño, prueba algo mas grande",
                        'user': user}
            response = make_response(render_template("index.html", data=data))
            wrong_guess.append(guess)
        return response # Devolvemos  un response por pantalla,mostrando un mensaje segun si ha acertado o si ha puesto un numero mayor o menor
    return render_template("index.html")


if __name__ == '__main__':
    app.run(debug=True)

