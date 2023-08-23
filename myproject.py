# from flask import Flask
# app = Flask(__name__)

# @app.route("/")
# def hello():
#     return "<h1 style='color:blue'>Hello Tere!</h1>"

# if __name__ == "__main__":
#     app.run(host='0.0.0.0')
from flask import Flask, request, jsonify, render_template, redirect
# from flask_restful import Api, Resource
import datetime
import psycopg2, hashlib, uuid

#connect to the dbs
con = psycopg2.connect(
    host ="localhost",
    database = "mydb",
    user = "postgres",
    password = "labris"
    )
cur = con.cursor()
app = Flask(__name__)
# api = Api(app)

@app.route('/')

def index():
    cur.close()
    return render_template("home.html")

@app.route("/user/list",methods = ["GET"])

def users():
    cur = con.cursor()
    cur.execute("SELECT username from users")
    rows = cur.fetchall()
    con.commit()
    cur.close()
    return jsonify(rows)

@app.route("/onlineusers")

def onlineusers():
    cur = con.cursor()

    cur.execute("SELECT username from onlineusers")
    rows = cur.fetchall()
    con.commit()
    cur.close()

    return jsonify(rows)

@app.route("/user/create", methods = ["GET","POST"])

def create():
    cur = con.cursor()
    if request.method == "GET":
        cur.close()
        return render_template("create.html")
    if request.method == "POST":
        print(request.form)
        new_username = request.form["username"]
        new_firstname = request.form["firstname"]
        new_middlename = request.form["middlename"]
        new_lastname = request.form["lastname"]
        new_birthdate = request.form["birthdate"]
        new_email = request.form["email"]
        new_password = request.form["password"]
        if len(new_password) <8:
            msg = "Please Check The Password Requirements And Try Again."
            return render_template("create.html",msg=msg)
        isu = False
        isl = False
        isn = False
        for i in new_password:
            if i.isupper():
                isu = True
            if i.islower():
                isl = True
            if i.isdigit():
                isn = True
            if isu and isl and isn:
                break
        if not (isu and isl and isn):
            msg = "Please Check The Password Requirements And Try Again."
            cur.close()
            return render_template("create.html",msg=msg)
        new_salt = uuid.uuid4().hex
        hashed_password = hashlib.sha256(new_password.encode("utf-8")+new_salt.encode("utf-8")).hexdigest()
        cur.execute(f"SELECT username FROM users WHERE username = '{new_username}'")
        usrnm = cur.fetchall()
        if usrnm:
            msg = "This Username Is Taken!"
            cur.close()
            return render_template("create.html",msg=msg)
        cur.execute(f"SELECT email FROM users WHERE email = '{new_email}'")
        eml = cur.fetchall()
        if eml:
            msg ="This E-mail Is Taken!"
            cur.close()
            return render_template("create.html",msg =msg)
        cur.execute(f"INSERT into users (username, firstname, middlename, lastname, birthdate, email, password, salt) VALUES ('{new_username}', '{new_firstname}', '{new_middlename}','{new_lastname}', '{new_birthdate}', '{new_email}', '{hashed_password}', '{new_salt}')")
        cur.execute(f"INSERT into onlineusers (username, ipaddress, logindatetime) VALUES ('{new_username}', '{request.remote_addr}', '{datetime.datetime.now()}') ")
        cur.execute(f"INSERT INTO Activities (username, ipaddress, activity, datetime) VALUES ('{new_username}', '{request.remote_addr}', 'login', '{datetime.datetime.now()}') ")
        con.commit()
        cur.close()
        return redirect(f"/{new_username}")
    

@app.route("/login", methods =["GET", "POST"])

def login():
    cur = con.cursor()
    if request.method == "GET":
        return render_template("login.html")
    else:
        login_username = request.form["username"]
        login_password = request.form["password"]
        cur.execute(f"SELECT username from onlineusers where username = '{login_username}'")
        usernames = cur.fetchall()
        if not usernames == []:
            if bool(usernames[0]):
                msg = "This User Has Already Logged In."
                cur.close()
                return render_template("login.html",msg=msg)
        cur.execute(f"SELECT password, salt FROM users WHERE username = '{login_username}'")
        loginusr = cur.fetchall()
        if not loginusr:
            cur.close()
            msg = "Wrong username or password."
            return render_template("login.html",msg=msg)
        hashed_p = hashlib.sha256(login_password.encode("utf-8")+loginusr[0][1].encode("utf-8")).hexdigest() 
        if loginusr[0][0] == hashed_p:
            cur.execute(f"UPDATE users SET online = true, logindatetime = '{datetime.datetime.now()}' WHERE username = '{login_username}'")
            cur.execute(f"INSERT into onlineusers (username, ipaddress, logindatetime) VALUES ('{login_username}', '{request.remote_addr}', '{datetime.datetime.now()}') ")
            cur.execute(f"INSERT INTO Activities (username, ipaddress, activity, datetime) VALUES ('{login_username}', '{request.remote_addr}', 'login', '{datetime.datetime.now()}') ")
            con.commit()
            cur.close()
            return redirect(f"/{login_username}")
        else:
            cur.close()
            msg = "Wrong username or password."
            return render_template("login.html",msg =msg)
        
        return render_template("login.html")

@app.route("/<username>")

def welcome(username):
    return render_template("hello.html", username=username)

@app.route("/<username>/logout", methods = ["GET", "POST"])

def userlogout(username):
    cur = con.cursor()
    if request.method == "GET":
        cur.close()
        return render_template("userlogout.html")
    else:
        cur.execute(f"UPDATE users SET online = false, logindatetime = NULL WHERE username = '{username}'")
        cur.execute(f"DELETE FROM onlineusers WHERE username = '{username}'")
        cur.execute(f"INSERT INTO Activities (username, ipaddress, activity, datetime) VALUES ('{username}', '{request.remote_addr}', 'logout', '{datetime.datetime.now()}') ")
        con.commit()
        cur.close()
        return redirect("/")
        

@app.route("/logout", methods = ["GET", "POST"])

def logout():
    cur = con.cursor()
    if request.method == "GET":
        cur.close()
        return render_template("logout.html")
    else:
        cur = con.cursor()
        login_username = request.form["username"]
        login_password = request.form["password"]
        cur.execute(f"SELECT password, salt FROM users WHERE username = '{login_username}'")
        loginusr = cur.fetchall()
        cur.execute(f"SELECT username from onlineusers where username = '{login_username}'")
        onlineusr = cur.fetchall()
        if not onlineusr:
            return "This User Has Already Logged Out."
        hashed_p = hashlib.sha256(login_password.encode("utf-8") + loginusr[0][1].encode("utf-8")).hexdigest()
        if loginusr[0][0] == hashed_p:
            cur.execute(f"UPDATE users SET online = false, logindatetime = NULL WHERE username = '{login_username}'")
            cur.execute(f"DELETE FROM onlineusers WHERE username = '{login_username}'")
            cur.execute(f"INSERT INTO Activities (username, ipaddress, activity, datetime) VALUES ('{login_username}', '{request.remote_addr}', 'logout', '{datetime.datetime.now()}') ")
        con.commit()
        cur.close()
        return redirect("/")

@app.route("/user/delete/<id>", methods = ["GET","POST"])
def delete(id):
    cur = con.cursor()
    if request.method == "GET":
        cur.close()
        return render_template("delete.html")
    else:
        login_password = request.form["password"]
        cur.execute(f"SELECT password, salt FROM users WHERE username = '{id}'")
        loginusr = cur.fetchall()
        hashed_p = hashlib.sha256(login_password.encode("utf-8") + loginusr[0][1].encode("utf-8")).hexdigest()
        if loginusr[0][0] == hashed_p:
            cur.execute(f"DELETE FROM users WHERE username = '{id}'")
        con.commit()
        cur.close()
        return render_template("home.html")

@app.route("/user/update/<id>",methods=["GET", "POST"])

def update(id):
    cur = con.cursor()
    if request.method == "GET":
        cur.close()
        return render_template("loginupdate.html")
    else:
        login_password = request.form["password"]
        cur.execute(f"SELECT password, salt FROM users WHERE username = '{id}'")
        loginusr = cur.fetchall()
        hashed_p = hashlib.sha256(login_password.encode("utf-8") + loginusr[0][1].encode("utf-8")).hexdigest()
        con.commit()
        if loginusr[0][0] == hashed_p:
            cur.close()
            return redirect(f"/user/updateuser/'{id}'")
        else:
            return "Wrong Password. Please Try again."

@app.route("/user/updateuser/<username>", methods = ["GET", "POST"])

def updateuser(username):
    cur = con.cursor()
    if request.method == "GET":
        cur.close()
        return render_template("update.html")
    else:
        updated_username = request.form["username"]
        updated_firstname = request.form["firstname"]
        updated_middlename = request.form["middlename"]
        updated_lastname = request.form["lastname"]
        updated_birthdate = request.form["birthdate"]
        updated_email = request.form["email"]
        updated_password = request.form["password"]
        cur.execute(f"SELECT firstname, middlename, lastname, birthdate, email, password, salt FROM users WHERE username = '{username}'")
        info = cur.fetchall()[0]
        if not updated_username:
            updated_username = username
        else:
            cur.execute(f"SELECT username FROM users WHERE username = '{updated_username}'")
            usrnm = cur.fetchall()
            if usrnm:
                msg = "This Username is Taken"
                return render_template("update.html",msg =msg)
        if len(updated_password) <8:
            msg = "Please Check The Password Requirements And Try Again."
            return render_template("update.html",msg=msg)
        isu = False
        isl = False
        isn = False
        for i in updated_password:
            if i.isupper():
                isu = True
            if i.islower():
                isl = True
            if i.isdigit():
                isn = True
            if isu and isl and isn:
                break
        if not (isu and isl and isn):
            msg = "Please Check The Password Requirements And Try Again."
            return render_template("update.html",msg=msg)
        if not updated_firstname:
            updated_firstname = info[0]
        if not updated_middlename:
            updated_middlename = info[1]
        if not updated_lastname:
            updated_lastname = info[2]
        if not updated_birthdate:
            updated_birthdate = info[3]
        if not updated_email:
            updated_email = info[4]
        if not updated_password:
            hashedp = info[5]
            new_salt = info[6]
        else:
            new_salt = uuid.uuid4().hex
            hashedp = hashlib.sha256(updated_password.encode("utf-8") + new_salt.encode("utf-8")).hexdigest()        
        cur.execute(f"UPDATE users SET username = '{updated_username}', firstname = '{updated_firstname}', middlename = '{updated_middlename}', lastname = '{updated_lastname}', birthdate = '{updated_birthdate}', email = '{updated_email}', password = '{hashedp}', salt = '{new_salt}' WHERE username = '{username}'")
        con.commit()
        return redirect(f"/{username}")

if __name__ == "__main__":
    app.run(host ="0.0.0.0")

