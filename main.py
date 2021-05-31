from flask import Blueprint, render_template,request, flash,redirect,url_for
from __init__ import create_app, db
from flask_login import login_required, current_user
import json
import requests
from models import Dictionary, UserWords
import random
main = Blueprint('main', __name__)

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

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/profile')
@login_required
def profile():
    userwords = UserWords.query.filter_by(
        user_name=current_user.user_name).all()
    for userword in userwords:
        calculate_power(userword.word)
    return render_template('profile.html', name=current_user.user_name,userwords = userwords)

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

@main.route('/profile/<int:word_id>')
@login_required
def word(word_id):
    userword = get_userword(word_id)
    increment_search_count(userword.word)
    calculate_power(userword.word)
    definition = get_definition(word_id)
    return render_template('word.html', userword=userword, definition = definition)

@main.route('/profile/<int:word_id>/delete', methods=('POST',))
@login_required
def delete(word_id):
    userword = UserWords.query.filter_by(id=word_id).first()
    db.session.delete(userword)
    db.session.commit()
    flash('"{}" was successfully deleted from your dictionary!'.format(userword.word))
    return redirect(url_for('main.profile'))

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

app = create_app()
if __name__ == '__main__':
    db.create_all(app=create_app())
    app.run(debug=True) # run the flask app on debug mode