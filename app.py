from flask import Flask, render_template, request, jsonify, redirect
import mysql.connector
from flask_cors import CORS
from dotenv import load_dotenv
import os
from mysql.connector import Error

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



def get_all_members():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM member")
    result = cursor.fetchall()
    cursor.close()
    return result


@app.route('/')
def home():
    return render_template('index.html', name="Gym Management System")


@app.route('/members')
def members():
    all_members = get_all_members()
    return render_template('members.html', name="Members Table", all_members_rows=all_members)


@app.route('/add_member', methods=['GET','POST'])
def add_member():
    cursor = db.cursor(dictionary=True)
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')

        query = "INSERT INTO member(name, email, phone) VALUES (%s, %s, %s)"
        cursor.execute(query, (name, email,phone))
        db.commit()

    
        member_id = cursor.lastrowid
        cursor.close()
        return f"Member added successfuly! <a href='/assign_membership/{member_id}'>Assign Membership</a>"
    cursor.close()
    return render_template('add_member.html', name='Add Member')


@app.route('/edit_member/<int:member_id>', methods=['GET', 'POST'])
def edit_member(member_id):
    cursor = db.cursor(dictionary=True)
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
        cursor.close()
        return redirect('/members')
    
    cursor.execute("SELECT * FROM member WHERE member_id = %s", (member_id,))
    member = cursor.fetchone()
    cursor.close()
    return render_template('edit_member.html', name='Edit Member', member=member)


@app.route('/delete_member/<int:member_id>')
def delete_member(member_id):
    cursor = db.cursor(dictionary=True)
    try:
        # delete payments related to member
        cursor.execute("""
            DELETE FROM payments WHERE member_id = %s
        """, (member_id,))

        # delete class enrollments
        cursor.execute("""
            DELETE FROM class_enrollment WHERE member_id = %s
        """, (member_id,))

        # DELETE memberships
        cursor.execute("""
            DELETE FROM member_membership WHERE member_id = %s
        """, (member_id,))

        # delete member
        cursor.execute("DELETE FROM member WHERE member_id = %s", (member_id,))
        db.commit()
    except Exception as e:
        cursor.close()
        return f"Cannot delete member. <a href='/members'>Go Back</a>"
    cursor.close()
    return redirect('/members')

@app.route('/member_page/<int:member_id>')
def member_page(member_id):
    cursor = db.cursor(dictionary=True)
    query = """
    SELECT
        m.name,
        m.phone,
        m.email,
        m.status,
        m.member_id,
        ms.membership_name,
        ms.price,
        mm.start_date,
        mm.end_date
    FROM member m 
    JOIN member_membership mm ON m.member_id = mm.member_id
    JOIN memberships ms ON mm.membership_id = ms.membership_id
    WHERE m.member_id = %s;
    """

    cursor.execute(query, (member_id,))
    rows = cursor.fetchall()
    cursor.close()
    if rows:
        return render_template('member_page.html', member_data=rows)
    
    return "Member not found <a href='/members'>Go back</a>"
    

@app.route('/assign_membership/<int:member_id>', methods=['GET', 'POST'])
def assign_membership(member_id):
    cursor = db.cursor(dictionary=True)
    if request.method == 'POST':
        membership_id = request.form.get('membership_id')
        start_date = request.form.get('start_date')
        
        try:
            # checking for active membership
            check_query = """
            SELECT COUNT(*) AS count
            FROM member_membership
            WHERE member_id = %s
            AND (end_date IS NULL OR end_date >= CURDATE())
            """
            cursor.execute(check_query, (member_id,))
            result = cursor.fetchone()

            if result['count'] > 0:
                # auto ending old membership
                cursor.execute("""
                UPDATE member_membership
                SET end_date = CURDATE()
                WHERE member_id = %s
                AND (end_date IS NULL OR end_date >= CURDATE())
                """, (member_id,))

            cursor.execute("SELECT duration_months FROM memberships WHERE membership_id = %s", (membership_id,))
            duration = cursor.fetchone()['duration_months']
            query = """
            INSERT INTO member_membership (member_id, membership_id, start_date, end_date)
            VALUES (%s, %s, %s, DATE_ADD(%s, INTERVAL %s MONTH))
            """
            cursor.execute(query, (member_id, membership_id, start_date, start_date, duration))
            db.commit()
        except Error as e:
            cursor.close()
            return f"Error: {str(e)} <a href='/members'>Go back</a>"
        cursor.close()
        return redirect('/members')
        
    cursor.execute("SELECT * FROM memberships")
    memberships = cursor.fetchall()
    cursor.close()
    return render_template('assign_membership.html', name='Assign Membership', member_id=member_id, memberships=memberships)


@app.route('/deactivate_member/<int:member_id>')
def deactivate_member(member_id):
    cursor = db.cursor(dictionary=True)
    # end active membership
    cursor.execute("""
        UPDATE member_membership SET end_date = CURDATE()
        WHERE member_id = %s 
        AND (end_date IS NULL OR end_date >= CURDATE())
    """, (member_id,))

    # set member to inactive
    cursor.execute("""
    UPDATE member
    SET status = 'Inactive'
    WHERE member_id = %s
    """, (member_id,))
    
    db.commit()
    cursor.close()
    return redirect('/members')


@app.route('/activate_member/<int:member_id>')
def activate_member(member_id):
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        UPDATE member
        SET status = 'Active'
        WHERE member_id = %s
    """, (member_id,))
    
    db.commit()
    cursor.close()
    return redirect(f'/assign_membership/{member_id}')


"""
Memberships table
"""

def get_memberships():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM memberships")
    result = cursor.fetchall()
    cursor.close()
    return result

@app.route('/memberships')
def memberships():
    memberships = get_memberships()
    return render_template('memberships.html', name='Memberships', rows=memberships)


@app.route('/add_membership', methods=['GET', 'POST'])
def add_membership():
    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        membership_name = request.form.get('membership_name')
        price = request.form.get('price')
        duration_months = request.form.get('duration_months')

        try:
            query = """
                INSERT INTO memberships (membership_name, price, duration_months)
                VALUES (%s, %s, %s)
            """
            cursor.execute(query, (membership_name, price, duration_months))
            db.commit()
            cursor.close()
            return redirect('/memberships')
        except Error as e:
            db.rollback()
            cursor.close()
            return f"Error adding membership: {str(e)} <a href='/add_membership'>Go back</a>"

    cursor.close()
    return render_template('add_membership.html', name='Add Membership')

@app.route('/edit_membership/<int:membership_id>', methods=['GET', 'POST'])
def edit_membership(membership_id):
    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        membership_name = request.form.get('membership_name')
        price = request.form.get('price')
        duration_months = request.form.get('duration_months')

        try:
            query = """
                UPDATE memberships SET membership_name = %s, price = %s, duration_months = %s
                WHERE membership_id = %s
            """
            cursor.execute(query, (membership_name, price, duration_months, membership_id))

            db.commit()
            cursor.close()
            return redirect('/memberships')
        except Error as e:
            db.rollback()
            cursor.close()
            return f"Error updating membership: {str(e)} <a href='/edit_membership/{membership_id}'>Go back</a>"
    cursor.execute("SELECT * FROM memberships WHERE membership_id = %s", (membership_id,))
    membership = cursor.fetchone()
    cursor.close()

    if not membership:
        return "Membership not found. <a href='/memberships'>Go back</a>"
    
    return render_template('edit_membership.html', name='Edit Membership', membership=membership)


@app.route('/membership_page/<int:membership_id>')
def membership_page(membership_id):
    cursor = db.cursor(dictionary=True)

    query = """
    SELECT
        ms.membership_id,
        ms.membership_name,
        ms.price,
        ms.duration_months,
        m.member_id,
        m.name,
        m.email,
        m.phone,
        mm.start_date,
        mm.end_date
    FROM memberships ms
    JOIN member_membership mm ON ms.membership_id = mm.membership_id
    JOIN member m ON mm.member_id = m.member_id
    WHERE ms.membership_id = %s;
    """

    cursor.execute(query, (membership_id,))
    rows = cursor.fetchall()
    cursor.close()

    if rows:
        return render_template('membership_page.html', rows=rows)

    # membership exists but has no enrolled members
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM memberships WHERE membership_id = %s", (membership_id,))
    membership = cursor.fetchone()
    cursor.close()

    if membership:
        return render_template('membership_page.html', rows=[], membership=membership)

    return "Membership not found. <a href='/memberships'>Go back</a>"

"""
staff table

"""

def get_staff():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM staff")
    result = cursor.fetchall()
    cursor.close()
    return result

@app.route('/staff')
def staff():
    all_staff = get_staff()
    return render_template('staff.html', name="Members Table", rows=all_staff)


@app.route('/add_staff', methods=['GET', 'POST'])
def add_staff():
    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone_number')
        email = request.form.get('email')
        hire_date = request.form.get('hire_date')
        salary = request.form.get('salary')
        role = request.form.get('role')

        query = """
            INSERT INTO staff (name, phone_number, email, hire_date, salary, role)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (name, phone, email, hire_date, salary, role))
        db.commit()

        cursor.close()
        return redirect('/staff')
    cursor.close()
    return render_template('add_staff.html')
        

if __name__=="__main__":
    app.run(host="0.0.0.0", debug=True)