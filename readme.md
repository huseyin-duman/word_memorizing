# Word Memorazing App

Word Memorazing is a web app to create personal dictionary and practice your saved word. It is developed in python by using Flask. 

You need to signup to use app. When you login to app you will see your saved words in your profile page with your power about the word. If you are new in app then your dictionary will be empty. To add words to your dictionary you can search some word and add them to your personal dictionary. If you add at least 10 words to your dictionary you can start to practice. 

In your profile you can click on a word to see details about the word. It includes definition of the word, search appearance, practice appearance and practice point. In this page user can remove the word from personal dictionary.

When you search a word in your personal dictionary you will get +1 for search appearance. Similar to that practice appearance gets +1 when a word appeared in practice. Practice point gets +1 if you answerd correctly to the word in practice. However, practice point gets -2 if you select the wrong answer about the question. Also other 2 options will get -1 for practice point.

You can just start to practice with username as guest and password 12345. Number one to ten are in the dictionary for this profile. Or you can create a new profile to yourself and start adding words to your personal dictionary.

## Environment Setup and Initialization:

To setup environment install required packages to virtual environment. Navigate to the project folder on cmd and install
requirements.

```bash
py -m venv env
.\env\Scripts\activate
pip install -r requirements.txt
```
If you do not want to use guest account with already words in dictionary clear databese by deleting db.sqlite from your folder.

To start word memorizing app.

```bash
python main.py
```

To reach web interface of meeting organizer type http://127.0.0.1:5000 to your browser and start using app.

## Close Look to Some Parts of Code:
There are 4 .py folder in the project. 

__init__.py contains some initializations about database and Flask.

models.py is for tabels of database. There are three tables in the app. User for signup and authentication. It contains user_name and password. Dictionary is a general dictionary for the words which are searched by any user. This table allows us to send less request to api by sending definition to any user if they search a word which is already searched by any user. The last table UserWords contains user specific information like saved words and their corresponding points and counts such as power and search count.

auth.py is for methods about authentication. First import relevant libraries.
```python
from flask import Blueprint, render_template, redirect, url_for, request,flash
from werkzeug.security import generate_password_hash, check_password_hash
from models import User
from __init__ import create_app, db
from flask_login import login_user, logout_user, login_required
```
sign up method asks user name and password for the user. It asks password two time to ensure user entered password correct. Also sign up method checks if the user name is already exists. In both controls if there is unexpected condition flashes relevant warning. Method saves hashed password for security.
```python
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
```
Login method checks user name and password to login user.
```python
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
```
logut method logs out the current user.
```python
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))
```
main.py contains method which are related with user actions.First import relevant libraries.
```python
from flask import Blueprint, render_template,request, flash,redirect,url_for
from __init__ import create_app, db
from flask_login import login_required, current_user
import json
import requests
from models import Dictionary, UserWords
import random
```
There are several methods to update points of relevant column in UserWords table.
Also there are 2 additional methods to get userword and definitin from relevant tables with id.
```python
@login_required
def update_practice_point(word,value):
    userword = UserWords.query.filter_by(
        word=word, user_name=current_user.user_name).first()
    userword.practice_point = userword.practice_point + value
    db.session.commit()

@login_required
def increment_appearance_count(word):
    userword = UserWords.query.filter_by(
        word=word, user_name=current_user.user_name).first()
    userword.appearance_count = userword.appearance_count + 1
    db.session.commit()

@login_required
def increment_search_count(word):
    userword = UserWords.query.filter_by(
        word=word, user_name=current_user.user_name).first()
    userword.search_count = userword.search_count + 1
    db.session.commit()

@login_required
def calculate_power(word):
    userword = UserWords.query.filter_by(word = word,
        user_name=current_user.user_name).first()
    power = userword.search_count+userword.appearance_count+userword.practice_point
    userword.power = power
    db.session.commit()

@login_required
def get_userword(word_id):
    userword = UserWords.query.filter_by(id=word_id,).first()
    return userword

@login_required
def get_definition(word_id):
    userword = UserWords.query.filter_by(id=word_id, ).first()
    definition = Dictionary.query.filter_by(word=userword.word).first().definition
    return definition
```    
profile method gets user words from database and sends them to profile.html to create profile page.
```python
@main.route('/profile')
@login_required
def profile():
    userwords = UserWords.query.filter_by(
        user_name=current_user.user_name).all()
    for userword in userwords:
        calculate_power(userword.word)
    return render_template('profile.html', name=current_user.user_name,userwords = userwords)
```
search method asks word to user and gets definition from database or api.If it gets definition from api it also saves the meaning and the word to Dictionary api to use it in future searchs.
```python
@main.route('/search', methods=('GET', 'POST'))
@login_required
def search():
    if request.method == 'POST':
        word = request.form.get('word')

        # check if the word contains only letters
        if not word.isalpha():
           flash('Please enter word only contains letters')
        else:
            dictWord = Dictionary.query.filter_by(
                word=word).count()
            if dictWord!=0:
                return redirect(url_for('main.result',word=word))
            else:
                url = "https://wordsapiv1.p.rapidapi.com/words/"+word+"/definitions"
                headers = {"X-RapidAPI-Host": "wordsapiv1.p.rapidapi.com",
                           "X-RapidAPI-Key":"2575265f2emsh3253ad0fe6112e7p10d5c6jsna3da56f0eeba"}
                res = requests.request("GET", url,headers=headers)
                definition = json.loads(res.text)["definitions"][0]["definition"]
                new_word= Dictionary(word=word, definition=definition)
                db.session.add(new_word)
                db.session.commit()
                return redirect(url_for('main.result', word=word))
    return render_template('search.html')
```
result method represents the definition of the word to user. It also adds to word users personal dictionary if user wants. Also this method increments the search count of the word if the word is already in personal dictionary of the user.
```python
@main.route('/result/<word>', methods=('GET', 'POST'))
@login_required
def result(word):
    counts = UserWords.query.filter_by(
        word=word, user_name=current_user.user_name).count()

    if counts != 0 and request.method == 'GET':
        increment_search_count(word)

    if request.method == 'POST':
        if counts!=0:
            flash(word+" is already in your dictionary")
            return redirect(url_for('main.profile'))
        else:
            new_user_word = UserWords(word=word,
                                      user_name=current_user.user_name,
                                      search_count=1,
                                      appearance_count=0,
                                      practice_point=0,
                                      power = 1)
            db.session.add(new_user_word)
            db.session.commit()
            flash(word + " added to your dictionary")
            return redirect(url_for('main.profile'))

    dictWord = Dictionary.query.filter_by(
        word=word).first()
    definition = dictWord.definition
    return render_template('result.html',word=word,definition=definition)
```
wrod method represents the details of the selected userword to user. It also increments search count because it shows the definition to user one more time.
```python
@main.route('/profile/<int:word_id>')
@login_required
def word(word_id):
    userword = get_userword(word_id)
    increment_search_count(userword.word)
    calculate_power(userword.word)
    definition = get_definition(word_id)
    return render_template('word.html', userword=userword, definition = definition)
```
delete method allows user to remove a word from personal dictionary.
```python
@main.route('/profile/<int:word_id>/delete', methods=('POST',))
@login_required
def delete(word_id):
    userword = UserWords.query.filter_by(id=word_id).first()
    db.session.delete(userword)
    db.session.commit()
    flash('"{}" was successfully deleted from your dictionary!'.format(userword.word))
    return redirect(url_for('main.profile'))
```
Practice method shows a random definition from userwords and three option with one correct to user. Also it increments the practice appearance of words in options.
```python
@main.route('/practice')
@login_required
def practice():
    count = UserWords.query.filter_by(user_name=current_user.user_name).count()
    if count < 10:
        flash('To practice you need to have at least 10 word in your dictionary.')
        return redirect(url_for('main.search'))
    else:
        userwords = UserWords.query.filter_by(user_name=current_user.user_name).all()
        word_numbers = random.sample(range(0, count - 1), 3)
        answer = random.randint(0, 2)
        definition = get_definition(userwords[word_numbers[answer]].id)
        words = [userwords[word_numbers[0]].word,
                 userwords[word_numbers[1]].word,
                 userwords[word_numbers[2]].word]
        #increment the appearance count of the words which will be in practice
        for i in range(3):
            increment_appearance_count(userwords[word_numbers[i]].word)

        return render_template('practice.html', words=words, definition=definition,
                               answer=userwords[word_numbers[answer]].word)
```
practice result checks the user's answer with the correct word and shows the result to the user as true or false. Also it updates the practice point of the words according to correctness of answer.
```python
@main.route('/<words>/<answer>', methods=('POST',))
@login_required
def practice_result(words,answer):
    submitted_answer = request.form['answer']
    if answer == submitted_answer:
        update_practice_point(answer,1)
        return render_template('practice_result.html', result ="True")
    else:
        words = words.replace("[","")
        words = words.replace("]","")
        words = words.replace("'", "")
        words = words.replace(",", "")
        words = words.split(" ")
        for word in words:
            if word == answer:
                update_practice_point(word, -2)
            update_practice_point(word, -1)
        return render_template('practice_result.html', result="False")
```
Finally main.py creates app and run it on local server.
```python
app = create_app()
if __name__ == '__main__':
    db.create_all(app=create_app())
    app.run(debug=True) # run the flask app on debug mode
```