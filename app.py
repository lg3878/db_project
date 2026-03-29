from flask import Flask, render_template, request, jsonify, redirect
import mysql.connector
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")

app = Flask(__name__)
CORS(app)

db = mysql.connector.connect(
    host="localhost",
    user=DB_USERNAME,
    password=DB_PASSWORD,
    database="mydb"
)

cursor = db.cursor(dictionary=True)

def get_active_members():
    
    cursor.execute("SELECT * FROM active_memberships") # utilizing one of the views created for the project
    result = cursor.fetchall()
    print(result)
    return result

def get_all_members():
    cursor.execute("SELECT * FROM member")
    result = cursor.fetchall()
    return result

@app.route('/')
def home():
    return render_template('index.html', name="Gym Management System")


#READ
@app.route('/members')
def members():
    all_members = get_all_members()
    active_members = get_active_members()
    return render_template('members.html', name="Members Table", all_members_rows=all_members, active_members_rows=active_members)


#CREATE
@app.route('/add_member', methods=['GET','POST'])
def add_member():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')

        query = "INSERT INTO member(name, email, phone) VALUES (%s, %s, %s)"
        cursor.execute(query, (name, email,phone))
        db.commit()

        return "Member added successfuly! <a href='/members'>Go back</a>"
    return render_template('add_member.html', name='Add Member')


#UPDATE
@app.route('/edit_member/<int:member_id>', methods=['GET', 'POST'])
def edit_member(member_id):
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        
        query = """
                UPDATE member
                SET name = %s, email = %s, phone = %s
                WHERE member_id = %s
                """
        cursor.execute(query, (name, email,phone, member_id))
        db.commit()
        return redirect('/members')
    
    cursor.execute("SELECT * FROM member WHERE member_id = %s", (member_id,))
    member = cursor.fetchone()
    return render_template('edit_member.html', name='Edit Member', member=member)


#DELETE
@app.route('/delete_member/<int:member_id>')
def delete_member(member_id):

    try:
        cursor.execute("DELETE FROM member WHERE member_id = %s", (member_id,))
        db.commit()
    except Exception as e:
        return f"Error deleting mmeber: {str(e)} <a href='mmembers'>Go Back</a>"
    
    return redirect('/members')



if __name__=="__main__":
    app.run(host="0.0.0.0", debug=True)
    cursor.close()