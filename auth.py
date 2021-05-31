from flask import Blueprint, render_template, redirect, url_for, request,flash
from werkzeug.security import generate_password_hash, check_password_hash
from models import User
from __init__ import create_app, db
from flask_login import login_user, logout_user, login_required

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        user_name = request.form.get('user_name')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        user = User.query.filter_by(user_name=user_name).first()

        # check if the user actually exists
        # take the user-supplied password, hash it, and compare it to the hashed password in the database
        if not user or not check_password_hash(user.password, password):
            flash('Please check your login details and try again.')
        else:
           # if the above check passes, then we know the user has the right credentials
            login_user(user, remember=remember)
            return redirect(url_for('main.profile'))

    return render_template('login.html')

@auth.route('/signup', methods=('GET', 'POST'))
def signup():
    if request.method == 'POST':
        user_name = request.form.get('user_name')
        password = request.form.get('password')
        password_again = request.form.get('password_again')

        user = User.query.filter_by(
            user_name=user_name).first()  # if this returns a user, then the email already exists in database

        if user:  # if a user is found, we want to redirect back to signup page so user can try again
            flash("This user name is already exists. Please enter a new user name")
        elif password !=password_again:
            flash("two passwords are not same please reenter password.")
        else:
            # create a new user with the form data. Hash the password so the plaintext version isn't saved.
            new_user = User(user_name=user_name, password=generate_password_hash(password, method='sha256'))

            # add the new user to the database
            db.session.add(new_user)
            db.session.commit()

            return redirect(url_for('auth.login'))


    return render_template('signup.html')


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))