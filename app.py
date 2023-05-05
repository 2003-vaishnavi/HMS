from flask import Flask, request, redirect, render_template, url_for, flash, session, send_file
from flask_mysqldb import MySQL
from flask_session import Session
from otp import genotp
from cmail import sendmail
from datetime import date
from datetime import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from tokenreset import token
import io
from io import BytesIO
import os
app = Flask(__name__)
app.secret_key = '*67@hjyjhk'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']='admin'
app.config['MYSQL_DB']='HMS'
Session(app)
mysql=MySQL(app)
@app.route('/')
def home():
    return render_template('home.html')
@app.route('/usignup', methods=['GET', 'POST'])
def UserSignup():
    if request.method == 'POST':
        user = request.form['username']
        email = request.form['email']
        password = request.form['Password']     
        otp=genotp()
        subject='Thanks for registering to the application'
        body=f'Use this otp to register {otp}'
        sendmail(email,subject,body)
        return render_template('otp.html',otp=otp,user=user,email=email,password=password)
    else:
        return render_template('signup.html') 
    return render_template('signup.html')
@app.route('/otp/<otp>/<user>/<email>/<password>',methods=['GET','POST'])
def otp(otp,user,email,password):
    if request.method=='POST':
        uotp=request.form['otp']
        if otp==uotp:
            cursor=mysql.connection.cursor()
            lst=[user,email,password]
            query='insert into admin values(%s,%s,%s)'
            cursor.execute(query,lst)
            mysql.connection.commit()
            cursor.close()
            flash('Details registered')
            return redirect(url_for('login'))
        else:
            flash('Wrong otp')
            return render_template('otp.html',otp=otp,user=user,email=email,password=password)
@app.route('/ulogin', methods=['GET','POST'])
def login():
    if session.get('user'):
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT COUNT(*) FROM admin WHERE email = %s AND password = %s', [email, password])
        count = cursor.fetchone()[0]
        if count == 0:
            flash('Invalid email id or password')
            return redirect(url_for('login'))
        else:
            session['user'] = email
            return redirect(url_for('dashboard'))
    return render_template('login.html')
@app.route('/forgetpassword',methods=['GET','POST'])
def forget():
    if request.method=='POST':
        email=request.form['email']
        cursor=mysql.connection.cursor()
        cursor.execute('select email from admin')
        data=cursor.fetchall()  
        if (email,) in data:
            cursor.execute('select email from admin where email=%s',[email])
            data=cursor.fetchone()[0]
            cursor.close()
            subject=f'Reset Password for {data}'
            body=f'Reset the passwword using- {request.host+url_for("createpassword",token=token(email,120))}'
            sendmail(email,subject,body)
            flash('Reset link sent to your mail')
            return redirect(url_for('login'))
        else:
            return 'Invalid user id'
    return render_template('forgot.html')
@app.route('/createpassword/<token>',methods=['GET','POST'])
def createpassword(token):
    try:
        s=Serializer(app.config['SECRET_KEY'])
        email=s.loads(token)['user']
        if request.method=='POST':
            npass=request.form['npassword']
            cpass=request.form['cpassword']
            if npass==cpass:
                cursor=mysql.connection.cursor()
                cursor.execute('update admin set password=%s where email=%s',[npass,email])
                mysql.connection.commit()
                return 'Password reset Successfull'
            else:
                return 'Password mismatch'
        return render_template('newpassword.html')
    except:
        return 'Link expired try again'
@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('home'))
    else:
        flash('already logged out!')
        return redirect(url_for('login'))
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')
@app.route('/details')  
def studentdetails():
    if session.get('user'):
        cursor=mysql.connection.cursor()
        cursor.execute('select * from students')
        data=cursor.fetchall()
        print(data)
        cursor.close()
        return render_template('studentdetails.html',data=data)
    else:
        return redirect(url_for('dashboard')) 
@app.route('/registration',methods=['GET','POST'])
def register():
    if request.method=='POST':
        sid=request.form['sid']
        sname=request.form['sname']
        section=request.form['section']
        roomno=request.form['roomno']
        cursor=mysql.connection.cursor()
        cursor.execute('insert into students(sid,sname,section,roomno) values(%s,%s,%s,%s)',[sid,sname,section,roomno])
        mysql.connection.commit()
        data=cursor.fetchall()
            #print(data)
        if (sid,) in data:
            flash('User already exists')
            return render_template('register.html')
            cursor.close()
        else:
            flash('Successfully registered')
            return render_template('dashboard.html')
    return render_template('register.html')
@app.route('/viewdetails/<sid>')
def viewdetails(sid):
    cursor=mysql.connection.cursor()
    cursor.execute('select * from students where sid=%s',[sid])
    data=cursor.fetchone()
    return render_template('detailsview.html',data=data)
@app.route('/updatedetails/<sid>',methods=['GET','POST'])
def updatedetails(sid):
    cursor=mysql.connection.cursor()
    cursor.execute('select * from students where sid=%s',[sid])
    data=cursor.fetchone()
    cursor.close()
    if request.method=='POST':
        sid=request.form['sid']
        sname=request.form['sname']
        section=request.form['section']
        roomno=request.form['roomno']
        cursor=mysql.connection.cursor()
        cursor.execute('update students set sid=%s,sname=%s,section=%s,roomno=%s where sid=%s',[sid,sname,section,roomno,sid])
        mysql.connection.commit()
        cursor.close()
        flash('Students updated successfully')
        return redirect(url_for('studentdetails'))
    return render_template('updatedetails.html',data=data)
@app.route('/deletedetails/<sid>')
def deletedetails(sid):
        cursor=mysql.connection.cursor()
        cursor.execute('delete from students where sid=%s',[sid])
        mysql.connection.commit()
        cursor.close()
        flash('Students deleted successfully')
        return redirect(url_for('studentdetails'))
@app.route('/studentrecord')
def studentrecord():
    if session.get('user'):
        cursor=mysql.connection.cursor()
        cursor.execute('select * from std_records')
        data=cursor.fetchall()
        print(data)
        cursor.close()
        return render_template('studentrecord.html',data=data)
    else:
        return redirect(url_for('dashboard'))
@app.route('/addstudents',methods=['GET','POST'])
def addstudents():
    if session.get('user'):
        if request.method=='POST':
            date=request.form['date']
            id=request.form['id']
            sid=request.form['sid']
            sname=request.form['sname']
            Section=request.form['Section']
            Roomno=request.form['Roomno']
            stu_checkin=request.form['stu_checkin']
            stu_checkout=request.form['stu_checkout']
            cursor=mysql.connection.cursor()
            cursor.execute('insert into std_records(id,sid,sname,Section,Roomno,stu_checkin,stu_checkout) values(%s,%s,%s,%s,%s,%s,%s)',[id,sid,sname,Section,Roomno,stu_checkin,stu_checkout])
            mysql.connection.commit()
            cursor.close()
            flash(f'student added successful')
            return redirect(url_for('studentrecord'))
        return render_template('Studentrecord.html')
    else:
        return redirect(url_for('addstudents'))
        #return render_template('addstudent.html')
@app.route('/checkin',methods=['GET','POST'])
def checkin():
    details=None
    cursor=mysql.connection.cursor()
    cursor.execute('SELECT * from students')
    data=cursor.fetchall()
    data1=request.args.get('sname') if request.args.get('sname') else 'empty'
    print(data1)
    cursor.execute('SELECT * from students where sid=%s',[data1])
    details=cursor.fetchone()
    cursor.execute('SELECT date,id,sid,sname,section,Roomno,stu_checkout,stu_checkin from std_records')
    std_records=cursor.fetchall()
    cursor.close()
    if request.method=='POST':
        sid=request.form['sid']
        sname=request.form['name']
        section=request.form['section']
        Roomno=request.form['roomno']
        cursor=mysql.connection.cursor()
        today=date.today()
        day=today.day
        month=today.month
        year=today.year
        today_date=datetime.strptime(f'{year}-{month}-{day}','%Y-%m-%d')
        date_today=datetime.strftime(today_date,'%Y-%m-%d')
        cursor.execute('select count(*) from std_records where sid=%s ',[sid])
        count=int(cursor.fetchone()[0])
        if sid=="":
            flash('Select The student Id first')
        elif count>=1:
            flash('The student already gone outside')
        else:
            cursor=mysql.connection.cursor()
            cursor.execute('insert into std_records(date,sid,sname,Section,Roomno) values(%s,%s,%s,%s,%s)',[date_today,sid,sname,section,Roomno])
            mysql.connection.commit()
            cursor.execute('SELECT date,id,sid,sname,Section,Roomno,stu_checkout,stu_checkin from std_records')
            std_records=cursor.fetchall()
            cursor.close()
    return render_template('Check in-page.html',data1=data1,data=data,details=details,std_records=std_records)
@app.route('/checkoutupdate/<date>/<id1>')
def checkoutupdate(date,id1):
    cursor=mysql.connection.cursor()
    cursor.execute('update std_records set stu_checkout=current_timestamp() where  id=%s and date=%s ',[id1,date])
    mysql.connection.commit()
    return redirect(url_for('checkin'))
@app.route('/checkinupdate/<date>/<id1>')
def checkinupdate(id1,date):
    cursor=mysql.connection.cursor()
    cursor.execute('update std_records set stu_checkin=current_timestamp() where  id=%s and date=%s ',[id1,date])
    mysql.connection.commit()
    return redirect(url_for('checkin'))
@app.route('/checkoutvisitor/<id1>')
def checkoutvisitor(id1):
    cursor=mysql.connection.cursor()
    cursor.execute('update visitor set checkout=current_timestamp() where vid=%s',[id1])
    mysql.connection.commit()
    return redirect(url_for('visitor'))
@app.route('/checkinvisitor/<id1>')
def checkinvisitor(id1):
    cursor=mysql.connection.cursor()
    cursor.execute('update visitor set checkin=current_timestamp() where vid=%s',[id1])
    mysql.connection.commit()
    return redirect(url_for('visitor'))
@app.route('/visitor',methods=['GET','POST'])
def visitor():
    cursor=mysql.connection.cursor()
    cursor.execute('SELECT * from students')
    data=cursor.fetchall()
    cursor.execute('Select * from visitor')
    details=cursor.fetchall()
    cursor.close()
    if request.method=="POST":
        id1=request.form['sid']
        name=request.form['visitorname']
        mobile=request.form['visitormobile']
        cursor=mysql.connection.cursor()
        cursor.execute('INSERT INTO visitor(sid,name,mobilenumber) values(%s,%s,%s)',[id1,name,mobile])
        cursor.execute('Select * from visitor')
        details=cursor.fetchall()
        mysql.connection.commit()
    return render_template('VisitorsCheckin.html',data=data,details=details)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
