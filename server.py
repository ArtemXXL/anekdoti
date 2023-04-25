import os
from werkzeug.utils import secure_filename
from flask import Flask, flash, url_for
from flask import render_template, redirect
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, EmailField, TextAreaField, FileField,\
    validators
from wtforms.validators import DataRequired
from flask import session, request
from data.db_session import *
from data.__all_models import *
from pyperclip import *
import requests
import html
import datetime
import json

ALLOWED_EXTENSIONS = {'png'}

global_init("db/log.db")
app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


def get_from_anekdotbar(n):
    """получение анекдотов с сайта Anekdotbar.ru"""
    r = requests.get("https://anekdotbar.ru/")
    data = []
    for i in html.unescape(r.text).split('div class="tecst">')[1:n + 1:]:
        txt = i.split('<div class="wrrating">')[0]
        data.append(txt.strip().split("<br>"))
    return data


def get_from_anekdoty_ru(n):
    """получение анекдотов с сайта Анекдоты.ру"""
    r = requests.get("https://anekdoty.ru/")
    dat = []
    for i in html.unescape(r.text).split('<ul class="item-list">')[1].split("<li id="):
        if len(i.split('<p>')) >= 2:
            text = i.split('<p>')[1].split('</p>')[0]
            data = text.split('<a')
            text_without_a = "".join(data[0].split(">"))
            for i in data[1::]:
                text_without_a += "".join("".join(i.split(">")[1::]).split('</a'))
            lines = text_without_a.split("<br")
            dat.append(lines)
    return dat[:n:]


class AddJokeForm(FlaskForm):
    #форма добавления анекдота
    text = TextAreaField('Анекдот', validators=[DataRequired()])
    submit = SubmitField('Добавить')


class SignUpForm(FlaskForm):
    # форма регистрации
    login = StringField('Имя пользователя', validators=[DataRequired()])
    email = EmailField('Электронная почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    second_password = PasswordField('Повторите пароль', validators=[DataRequired()])
    submit = SubmitField('Регистрация')


class SignInForm(FlaskForm):
    # форма входа
    login = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Вход')


class AccauntForm(FlaskForm):
    # форма выхода
    submit = SubmitField('Выход')


def func_of_joke(key, db_sess, name, checks):
    """обработка событий с кнопок на анекдотах"""
    if "del" in key and checks["delete"]:
        if request.form.get(key):
            dat = key.split("del")
            id = int(dat[1])
            joke = db_sess.query(Joke).filter(Joke.id == id).first()
            db_sess.delete(joke)
            db_sess.commit()
    if "copy" in key and checks["copy"]:
        if request.form.get(key):
            dat = key.split("copy")
            id = int(dat[1])
            joke = db_sess.query(Joke).filter(Joke.id == id).first()
            txt = str(joke.content)
            txt = '\n'.join(txt.split('|'))
            copy(txt)
    if "up" in key and checks["up"]:
        if request.form.get(key):
            user = db_sess.query(User).filter(User.name == name).first()
            votes = json.loads(user.vote)
            dat = key.split("up")
            id = int(dat[1])
            joke = db_sess.query(Joke).filter(Joke.id == id).first()
            if str(id) in votes.keys():
                if votes[str(id)] == -1:
                    joke.range += 2
            else:
                joke.range += 1
            votes[str(id)] = 1
            user.vote = json.dumps(votes)
            db_sess.commit()
            during_id = "joke" + str(id)
            return redirect(f"index#{during_id}")
    if "down" in key and checks["down"]:
        if request.form.get(key):
            user = db_sess.query(User).filter(User.name == name).first()
            votes = json.loads(user.vote)
            dat = key.split("down")
            id = int(dat[1])
            joke = db_sess.query(Joke).filter(Joke.id == id).first()
            if str(id) in votes.keys():
                if votes[str(id)] == 1:
                    joke.range -= 2
            else:
                joke.range -= 1
            votes[str(id)] = -1
            user.vote = json.dumps(votes)
            db_sess.commit()
            during_id = "joke" + str(id)
            return redirect(f"index#{during_id}")


def allowed_file(filename):
    """ Функция проверки расширения файла """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/add-joke', methods=['GET', 'POST'])
def add_joke():
    name = session.get('name', '')
    # поиск
    search_joke = request.args.get('search_joke', default='', type=str)
    if search_joke != '':
        return redirect(f'../search/{search_joke}')
    # добавление формы
    form = AddJokeForm()
    authorized = session.get('authorized', False)
    db_sess = create_session()
    user = db_sess.query(User).filter(User.name == name).first()
    if form.validate_on_submit():
        joke = Joke()
        joke.content = "|".join(form.text.data.split("\n"))
        joke.user_id = user.id
        joke.range = 0
        db_sess.add(joke)
        db_sess.commit()
        return redirect('../accaunt')
    return render_template('add_task.html', title='Добавить Анекдот', authorized=authorized, name=name, form=form)


@app.route('/sign-in', methods=['GET', 'POST'])
def sign_in():
    name = session.get('name', '')
    form = SignInForm()
    authorized = session.get('authorized', False)
    # поиск
    search_joke = request.args.get('search_joke', default='', type=str)
    if search_joke != '':
        return redirect(f'../search/{search_joke}')
    error = ""
    if form.validate_on_submit():
        db_sess = create_session()
        user = db_sess.query(User).filter(User.name == form.login.data).first()
        if user:
            if str(form.password.data) == str(user.password):
                session['authorized'] = True
                session['name'] = form.login.data
                session['email'] = user.email
                session['is_photo'] = user.is_photo
                return redirect('../accaunt')
            else:
                error = "Введён не правильный пароль"
        else:
            error = "Пользователя с таким именем не сущестует"
    return render_template('sign_in.html', title='Вход', authorized=authorized, name=name, form=form, error_sign_in=error)


@app.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    form = SignUpForm()
    authorized = session.get('authorized', False)
    # поиск
    search_joke = request.args.get('search_joke', default='', type=str)
    if search_joke != '':
        return redirect(f'../search/{search_joke}')
    name = session.get('name', '')
    error = ""
    if form.validate_on_submit():
        if form.password.data == form.second_password.data:
            db_sess = create_session()
            user = db_sess.query(User).filter(User.name == form.login.data).first()
            if user:
                error = "Пользаватель с таким именем уже существует"
            else:
                user = User()
                user.name = form.login.data
                user.email = form.email.data
                user.password = form.password.data
                user.vote = "{}"
                db_sess.add(user)
                db_sess.commit()
                session['authorized'] = True
                session['is_photo'] = False
                session['name'] = form.login.data
                session['email'] = form.email.data
                session['password'] = form.password.data
                return redirect('../accaunt')
        else:
            error = "Пароли не совпадают"
    return render_template('sign_up.html', title='Регистрация', authorized=authorized, name=name, form=form,
                           error_sign_up=error)


@app.route('/accaunt', methods=['GET', 'POST'])
def accaunt():
    # Страница аккаунта
    db_sess = create_session()
    search_joke = request.args.get('search_joke', default='', type=str)
    # кнопки на анекдотах
    during_checks = dict()
    during_checks["copy"] = True
    during_checks["delete"] = True
    during_checks["down"] = False
    during_checks["up"] = False
    name = session.get('name', '')
    if request.method == 'POST':
        d = request.form.to_dict()
        for i in d.keys():
            func_of_joke(i, db_sess, name, during_checks)
    is_photo = session.get('is_photo', False)
    user = db_sess.query(User).filter(User.name == name).first()
    form = AccauntForm()
    if search_joke != '':
        return redirect(f'../search/{search_joke}')
    if request.method == 'POST':
        if form.validate_on_submit():
            session['authorized'] = False
            session['name'] = ''
            session['email'] = ''
            session['password'] = ''
            session['is_photo'] = False
            return redirect('../index')
        d = request.form.to_dict()
        # обработка аватарки
        if 'file' not in request.files:
            flash('Не могу прочитать файл')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('Нет выбранного файла')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            session["is_photo"] = True
            user.is_photo = True
            db_sess.commit()
            file.save(f"static/uploads/{user.id}.png")
        for i in d.keys():
            func_of_joke(i, db_sess, name, during_checks)

    authorized = session.get('authorized', False)
    email = session.get('email', '')
    id = user.id
    role = user.role
    data = []
    jokes = db_sess.query(Joke).filter(Joke.user_id == user.id).all()
    for i in jokes:
        dat = dict()
        dat["content"] = i.content.split("|")
        dat["user"] = db_sess.query(User).filter(User.id == i.user_id).first().name
        dat["date"] = i.date.strftime('%m.%d.%Y')
        dat["id"] = i.id
        dat["user_id"] = i.user_id
        dat["range"] = i.range
        data.append(dat)
    return render_template('accaunt.html', title='Аккаунт', authorized=authorized, name=name, email=email,
                           form=form, jokes=data, id=id, checks=during_checks, role=role, is_photo=user.is_photo)


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    # Главная страница
    joke_by_anekdoty_ru = get_from_anekdoty_ru(1)[0]
    joke_by_anekdotbar = get_from_anekdotbar(1)[0]
    db_sess = create_session()
    name = session.get('name', '')
    authorized = session.get('authorized', False)
    # кнопки на анекдотах
    during_checks = dict()
    user = db_sess.query(User).filter(User.name == name).first()
    during_checks["copy"] = True
    during_checks["delete"] = False
    if user:
        if user.role == "admin" or user.role == "king":
            during_checks["delete"] = True
    if not authorized:
        during_checks["down"] = False
        during_checks["up"] = False
    else:
        during_checks["down"] = True
        during_checks["up"] = True
    if request.method == 'POST':
        d = request.form.to_dict()
        for i in d.keys():
            func_of_joke(i, db_sess, name, during_checks)
    # поиск
    search_joke = request.args.get('search_joke', default='', type=str)
    if search_joke != '':
        return redirect(f'../search/{search_joke}')
    data = []
    jokes = db_sess.query(Joke).all()
    for i in jokes:
        dat = dict()
        dat["content"] = i.content.split("|")
        dat["user"] = db_sess.query(User).filter(User.id == i.user_id).first().name
        dat["date"] = i.date.strftime('%m.%d.%Y')
        dat["id"] = i.id
        dat["range"] = i.range
        dat["user_id"] = i.user_id
        data.append(dat)
    return render_template('index.html', title="Главная страница", authorized=authorized, name=name,
                           jokes=data, checks=during_checks, anekdoty_ru=joke_by_anekdoty_ru,
                           anekdotbar=joke_by_anekdotbar)


@app.route('/search/<text>', methods=['GET', 'POST'])
def search(text):
    # Страница поиска
    db_sess = create_session()
    name = session.get('name', '')
    authorized = session.get('authorized', False)
    # кнопки на анекдотах
    during_checks = dict()
    user = db_sess.query(User).filter(User.name == name).first()
    during_checks["copy"] = True
    during_checks["delete"] = False
    if user:
        if user.role == "admin":
            during_checks["delete"] = True
    if not authorized:
        during_checks["down"] = False
        during_checks["up"] = False
    else:
        during_checks["down"] = True
        during_checks["up"] = True
    if request.method == 'POST':
        d = request.form.to_dict()
        for i in d.keys():
            func_of_joke(i, db_sess, name, during_checks)
    # поиск
    search_joke = request.args.get('search_joke', default='', type=str)
    if search_joke != '':
        return redirect(f'../search/{search_joke}')
    name = session.get('name', '')
    data = []
    jokes = db_sess.query(Joke).all()
    for i in jokes:
        if text in i.content:
            dat = dict()
            dat["content"] = i.content.split("|")
            dat["user"] = db_sess.query(User).filter(User.id == i.user_id).first().name
            dat["date"] = i.date.strftime('%m.%d.%Y')
            dat["id"] = i.id
            dat["user_id"] = i.user_id
            dat["range"] = i.range
            data.append(dat)
    return render_template('search.html', title="Поиск", authorized=authorized, name=name, tag=[],
                           jokes=data, search_text=text, checks=during_checks)


@app.route('/top', methods=['GET', 'POST'])
def top():
    # Топ анекдотов
    db_sess = create_session()
    name = session.get('name', '')
    authorized = session.get('authorized', False)
    # кнопки на анекдотах
    during_checks = dict()
    user = db_sess.query(User).filter(User.name == name).first()
    during_checks["copy"] = True
    during_checks["delete"] = False
    if user:
        if user.role == "admin" or user.role == "king":
            during_checks["delete"] = True
    if not authorized:
        during_checks["down"] = False
        during_checks["up"] = False
    else:
        during_checks["down"] = True
        during_checks["up"] = True
    if request.method == 'POST':
        d = request.form.to_dict()
        for i in d.keys():
            func_of_joke(i, db_sess, name, during_checks)
    # поиск
    search_joke = request.args.get('search_joke', default='', type=str)
    if search_joke != '':
        return redirect(f'../search/{search_joke}')
    data = []
    jokes = db_sess.query(Joke).all()
    for i in jokes:
        dat = dict()
        dat["content"] = i.content.split("|")
        dat["user"] = db_sess.query(User).filter(User.id == i.user_id).first().name
        dat["date"] = i.date.strftime('%m.%d.%Y')
        dat["id"] = i.id
        dat["range"] = i.range
        dat["user_id"] = i.user_id
        data.append(dat)
    data.sort(key=lambda x: x["range"], reverse=True)
    return render_template('top.html', title="Топ", authorized=authorized, name=name, tag=[],
                           jokes=data, checks=during_checks)


@app.route('/anekdoty_ru', methods=['GET', 'POST'])
def anekdoty_ru():
    # Страница с анекдотами с сайта анекдоты.ру
    name = session.get('name', '')
    authorized = session.get('authorized', False)
    # поиск
    search_joke = request.args.get('search_joke', default='', type=str)
    if search_joke != '':
        return redirect(f'../search/{search_joke}')
    data = []
    jokes = get_from_anekdoty_ru(10)
    data.sort(key=lambda x: x["range"], reverse=True)
    return render_template('anekdoty_ru.html', title="Анекдоты.ру", authorized=authorized, name=name, tag=[],
                           jokes=jokes)


@app.route('/anekdotbar', methods=['GET', 'POST'])
def anekdotbar():
    # Страница с анекдотами с сайта анекдотбар.ру
    name = session.get('name', '')
    authorized = session.get('authorized', False)
    # поиск
    search_joke = request.args.get('search_joke', default='', type=str)
    if search_joke != '':
        return redirect(f'../search/{search_joke}')
    jokes = get_from_anekdotbar(10)
    return render_template('anekdotbar.html', title="Anekdotbar.ru", authorized=authorized, name=name, jokes=jokes)


@app.route('/accaunts/<accaunt_id>', methods=['GET', 'POST'])
def accaunts(accaunt_id):
    # Страницы аккаунтов пользователей
    db_sess = create_session()
    search_joke = request.args.get('search_joke', default='', type=str)
    authorized = session.get('authorized', False)
    name = session.get('name', "")
    user = db_sess.query(User).filter(User.id == accaunt_id).first()
    during_checks = dict()
    during_checks["copy"] = True
    during_checks["delete"] = False
    during_checks["down"] = True
    during_checks["up"] = True
    if user:
        if user.role == "admin" or user.role == "king":
            during_checks["delete"] = True
    if not authorized:
        during_checks["down"] = False
        during_checks["up"] = False
    else:
        during_checks["down"] = True
        during_checks["up"] = True
    if search_joke != '':
        return redirect(f'../search/{search_joke}')

    user_params = None
    data = []
    if user:
        user_params = dict()
        user_params["name"] = user.name
        user_params["email"] = user.email
        user_params["id"] = user.id
        user_params["role"] = user.role
        user_params["is_photo"] = user.is_photo
        jokes = db_sess.query(Joke).filter(Joke.user_id == user.id).all()
        for i in jokes:
            dat = dict()
            dat["content"] = i.content.split("|")
            dat["user"] = db_sess.query(User).filter(User.id == i.user_id).first().name
            dat["date"] = i.date.strftime('%m.%d.%Y')
            dat["id"] = i.id
            dat["user_id"] = i.user_id
            dat["range"] = i.range
            data.append(dat)
    return render_template('accaunts.html', title='Аккаунт', authorized=authorized, name=name, user=user_params,
                           jokes=data, id=id, checks=during_checks)


if __name__ == '__main__':
    app.run(port=5000, host='127.0.0.1')