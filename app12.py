from flask import Flask, render_template, request,url_for,session,flash,redirect
import mysql.connector
import smtplib
from flask_session import Session
from key import secret_key,salt
from itsdangerous import URLSafeTimedSerializer
from stoken import token
from cmail import sendmail
app = Flask(__name__)
app.secret_key=secret_key
app.config['SESSION_TYPE']='filesystem'
# MySQL database configuration
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="admin",
    database="pnm"
)

# Create a cursor object to interact with the database
cursor = mydb.cursor()

@app.route('/')
def index():
    # Retrieve feedback data from the database
   
   
    return render_template('title.html')

@app.route('/login',methods=['GET','POST'])
def login():
    if session.get('user'):
        return redirect(url_for('home'))
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from users where username=%s and password=%s',[username,password])
        count=cursor.fetchone()[0]
        if count==1:
            session['user']=username
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password')
            return render_template('login.html')
    return render_template('login.html')
@app.route('/registration',methods=['GET','POST'])
def registration():
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        email=request.form['email']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*)  from users where username=%s',[username])
        count=cursor.fetchone()[0]
        cursor.execute('select count(*)  from users where email=%s',[email])
        count1=cursor.fetchone()[0]
        cursor.close()
        if count==1:
            flash('username is already in use')
            return render_template('register.html')
        elif count1==1:
            flash('Email already in use')
            return render_template('registration.html')
        data={'username':username,'password':password,'email':email}
        subject='Email Confirmation'
        body=f"Thanks for signing up\n\n follow this link  further steps-{url_for('confirm',token=token(data),_external=True)}"
        sendmail(to=email,subject=subject,body=body)
        flash('Confirmation link sent to mail')
        return redirect(url_for('login'))
    return render_template('register.html')
@app.route('/confirm/<token>')
def confirm(token):
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        data=serializer.loads(token,salt=salt,max_age=180)
    except Exception as e:
        #print(e)
        return 'Link Expired register again'
    else:
        cursor=mydb.cursor(buffered=True)
        username=data['username']
        cursor.execute('select count(*) from users where username=%s',[username])
        count=cursor.fetchone()[0]
        if count==1:
            cursor.close()
            flash('you already registered')
            return redirect(url_for('login'))
        else:
            cursor.execute('insert into users values(%s,%s,%s)',[data['username'],data['password'],data['email']])
            mydb.commit()
            cursor.close()
            flash('Details registered!')
            return redirect(url_for('login'))

@app.route('/homepage')
def home():
    if session.get('user'):
        return render_template('homepage.html')
    else:
        return redirect(url_for('login'))
@app.route('/submit', methods=['POST'])
def submit():
    # Retrieve form data
    project_name = request.form['project_name']
    rating = request.form['rating']
    comments = request.form['comments']

    # Insert feedback data into the database
    cussor=mydb.cursor()
    cursor.execute("INSERT INTO feedback (project_name, rating, comments) VALUES (%s, %s, %s)", (project_name, rating, comments))
    mydb.commit()
    return redirect(url_for('view'))

@app.route('/view')
def view():
    if session.get('user'):
        username=session.get('user')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select project_name,rating,comments from feedback')
        data=cursor.fetchall()      
        cursor.close()
        return render_template('index.html',data=data)
    else:
        return redirect(url_for('login'))
    return "Thank you for your feedback"
   
    
app.run(debug=True,use_reloader=True)