from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flaskext.mysql import MySQL
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import quoted_name, text
from sqlalchemy import Column, Integer, String, Date, func, text, cast, desc, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from flask_bcrypt import Bcrypt
from datetime import datetime
import os
from pathlib import Path
import glob
import mysql.connector as mysql

# import MySQLdb.cursors

myconn = mysql.connect(host='localhost', database='PhotoShare', user='root', password='123456789')

if myconn.is_connected():
    print("Connection established..")

cursor = myconn.cursor()

app = Flask(__name__, template_folder='Templates', static_folder='albums')
# app.secret_key = 'your_secret_key_here'
# bcrypt = Bcrypt(app)
#
# app.config['MYSQL_HOST'] = 'localhost:3306'
# app.config['MYSQL_USER'] = 'root'
# app.config['MYSQL_PASSWORD'] = '123456789'
# app.config['MYSQL_DB'] = 'PhotoShare'
#
# mysql = MySQL(app)
# print(mysql)
app.secret_key = '123!@#123'
global_email = ''


@app.route('/')
def main():
    cursor.execute(
        'SELECT u.first_name, u.last_name,  COUNT(DISTINCT p.photo_id) + COUNT(DISTINCT c.comment_id) as contribution FROM users u LEFT JOIN albums a ON u.user_id = a.user_id LEFT JOIN photos p ON a.album_id = p.album_id LEFT JOIN comments c ON p.photo_id = c.photo_id GROUP BY u.user_id ORDER BY contribution DESC LIMIT 10;')
    # Fetch one record and return result
    top_users = cursor.fetchall()
    print('top_users', top_users)

    return render_template('index.html', top_users=top_users)
    return render_template('index.html')


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        # Create variables for easy access
        email = request.form['email']
        password = request.form['password']
        # Check if account exists using MySQL
        # cursor = mysql.cursor()
        cursor.execute('SELECT * FROM users WHERE email = %s AND password = %s', (email, password))
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            # session['loggedin'] = True
            print(account[0])
            session['user_id'] = int(account[0])
            # Redirect to home page
            global_email = email
            return redirect(url_for('Myprofile'))
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
            print('Incorrect')
    return render_template('index.html', msg='')


@app.route('/myProfile')
def Myprofile():
    user_id = session.get('user_id')
    # print('user id = ',user_id)
    cursor.execute('SELECT * FROM Albums WHERE user_id = %s;',(user_id,))
    # Fetch one record and return result
    albums = cursor.fetchall()
    len_of_albums = len(albums)
    cursor.execute(
        'SELECT u.first_name, u.last_name, u.email FROM friends f JOIN users u ON f.friend_id = u.user_id WHERE f.user_id = %s;',(user_id,))
    # Fetch one record and return result
    friends = cursor.fetchall()
    cursor.execute('SELECT friend_id FROM friends WHERE user_id= %s',(user_id, ))
    friend_id = cursor.fetchall()[0][0]
    cursor.execute('SELECT u.first_name, u.last_name, u.email FROM friends f JOIN users u ON f.user_id = u.user_id WHERE f.friend_id = 1;')
    friend3 = cursor.fetchall()
    cursor.execute('SELECT f.friend_id, COUNT(*) as mutual_friends FROM friends f WHERE f.user_id IN ( SELECT f2.friend_id FROM friends f2 WHERE f2.user_id = %s ) AND f.friend_id NOT IN ( SELECT f3.friend_id FROM friends f3 WHERE f3.user_id = %s ) GROUP BY f.friend_id ORDER BY mutual_friends;',(friend_id, user_id))
    friends1 = cursor.fetchall()
    return render_template('MyProfile.html', albums=albums, friends=friends, len_of_albums=len_of_albums, friends1=friends1, friend3=friend3)


@app.route('/search')
def search():
    return render_template('Signup.html')


@app.route('/popular')
def popular():
    return render_template('Signup.html')

@app.route('/add_friend', methods=['GET', 'POST'])
def add_friend():
    if request.method == 'POST':
        user_id = session.get('user_id')
        friend_email = request.form['friend_email']
        cursor.execute('SELECT user_id FROM users WHERE email = %s',(friend_email, ))
        print('SELECT user_id FROM users WHERE email = %s',(friend_email, ))
        friend_id = cursor.fetchall()[0][0]
        today_date = datetime.today().strftime('%Y-%m-%d')
        query = "INSERT INTO friends (friend_id,user_id, date_of_friendship) VALUES (%s, %s, %s)"
        print(friend_id, user_id, today_date)
        values = (friend_id, user_id, today_date)
        cursor.execute(query, values)
        myconn.commit()

    return redirect(url_for('Myprofile'))


@app.route('/signUp', methods=['GET', 'POST'])
def signUp():
    if request.method == 'POST':
        # Get the form data
        #user_id = 1  # increment from previous user bitch
        cursor.execute('SELECT max(user_id) FROM Users;')
        max_user_id = cursor.fetchone()
        user_id = int(max_user_id[0]) + 1
        email = request.form['email']
        first_name = request.form['firstName']
        last_name = request.form['lastName']
        password = request.form['password']
        gender = request.form['gender']
        date_of_birth = request.form['dateOfBirth']
        hometown = request.form['hometown']

        # Insert the user's information into the database
        query = "INSERT INTO users (user_id,email, first_name, last_name, password, gender, date_of_birth, hometown) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        values = (user_id, email, first_name, last_name, password, gender, date_of_birth, hometown)
        cursor.execute(query, values)
        myconn.commit()

        # Redirect to the login page
        flash('You have successfully registered')
        return redirect(url_for('Myprofile'))

    # If the request method is GET, render the registration page
    return render_template('Signup.html')

@app.route('/addalbum', methods=['GET', 'POST'])
def addalbum():
    if request.method == 'POST':
        # Get the form data
        #user_id = 1  # increment from previous user bitch
        cursor.execute('SELECT max(album_id) FROM albums;')
        max_album_id = cursor.fetchone()
        album_id = int(max_album_id[0]) + 1
        album_name = request.form['album_name']
        cursor.execute('SELECT max(photo_id) FROM photos;')
        max_photo_id = cursor.fetchone()
        photo_id = int(max_photo_id[0]) + 1
        photodata = request.form['photo']
        caption = request.form['caption']
        tag_name = request.form['tags']



        # Insert the user's information into the database
        query = "INSERT INTO users (user_id,email, first_name, last_name, password, gender, date_of_birth, hometown) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        values = (album_id, album_name, first_name, last_name, password, gender, date_of_birth, hometown)
        cursor.execute(query, values)
        myconn.commit()

        # Redirect to the login page
        flash('You have successfully registered')
        return redirect(url_for('Myprofile'))

    # If the request method is GET, render the registration page
    return render_template('Signup.html')

@app.route('/photofeed')
def photofeed():
    return render_template('Photofeed.html')


if __name__ == '__main__':
    app.run(debug=True, port=5001)

if __name__ == '__main__':
    app.run(debug=True)
