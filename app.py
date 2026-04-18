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

# using is_member_active
def get_all_members(active_only=False):
    cursor = db.cursor(dictionary=True)
    if active_only:
        cursor.execute("""
            SELECT * FROM member
            WHERE is_member_active(member_id) = TRUE
        """)
    else:
        cursor.execute("SELECT * FROM member")
    result = cursor.fetchall()
    cursor.close()
    return result


@app.route('/')
def home():
    return render_template('index.html', name="Gym Management System")


@app.route('/members')
def members():
    active_only = request.args.get('active_only') == '1'
    all_members = get_all_members(active_only=active_only)
    return render_template('members.html', name="Members Table", all_members_rows=all_members, active_only=active_only)


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

# utilizing active_membership view
def get_member_page_data(member_id):
    cursor = db.cursor(dictionary=True)
 
    # Core membership rows from the view
    cursor.execute("""
        SELECT
            member_id,
            name,
            email,
            membership_name,
            start_date,
            end_date
        FROM active_memberships
        WHERE member_id = %s
    """, (member_id,))
    rows = cursor.fetchall()
 
    if not rows:
        cursor.close()
        return None
 
    # Extra fields not in the view
    cursor.execute("""
        SELECT m.phone, m.status, m.member_id, ms.price
        FROM member m
        JOIN member_membership mm ON m.member_id = mm.member_id
        JOIN memberships ms ON mm.membership_id = ms.membership_id
        WHERE m.member_id = %s
          AND (mm.end_date IS NULL OR mm.end_date >= CURDATE())
    """, (member_id,))
    extras = {row['member_id']: row for row in cursor.fetchall()}
    cursor.close()
 
    # Merge extras into each view row
    for row in rows:
        extra = extras.get(row['member_id'], {})
        row['phone']  = extra.get('phone')
        row['status'] = extra.get('status')
        row['price']  = extra.get('price')
 
    return rows


@app.route('/member_page/<int:member_id>')
def member_page(member_id):
    rows = get_member_page_data(member_id)

    if not rows:
        return "Member not found <a href='/members'>Go back</a>"
    
    #Get total payments for this member
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT get_total_payments(%s) AS total_paid", (member_id,))
    total_paid = cursor.fetchone()['total_paid']
    cursor.close()

    return render_template('member_page.html', member_data=rows, total_paid=total_paid)


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


@app.route('/delete_membership/<int:membership_id>')
def delete_membership(membership_id):
    cursor = db.cursor(dictionary=True)
    try:
        # get all member_membership_ids for this tier
        cursor.execute("""
            SELECT member_membership_id FROM member_membership
            WHERE membership_id = %s
        """, (membership_id,))
        mm_ids = [row['member_membership_id'] for row in cursor.fetchall()]

        if mm_ids:
            format_strings = ','.join(['%s'] * len(mm_ids))

            # delete payments tied to those membership records
            cursor.execute(f"""
                DELETE FROM payments
                WHERE member_membership_id IN ({format_strings})
            """, mm_ids)

            # delete member_membership records
            cursor.execute(f"""
                DELETE FROM member_membership
                WHERE member_membership_id IN ({format_strings})
            """, mm_ids)

        # delete the membership tier itself
        cursor.execute("DELETE FROM memberships WHERE membership_id = %s", (membership_id,))
        db.commit()
    except Error as e:
        db.rollback()
        cursor.close()
        return f"Error deleting membership: {str(e)} <a href='/memberships'>Go back</a>"

    cursor.close()
    return redirect('/memberships')


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
    return render_template('staff.html', name="Staff Table", rows=all_staff)


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
        is_trainer = request.form.get('is_trainer')  # 'on' if checked, None if not
        certification = request.form.get('certification')

        try:
            cursor.execute("""
                INSERT INTO staff (name, phone_number, email, hire_date, salary, role)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (name, phone, email, hire_date, salary, role))

            staff_id = cursor.lastrowid

            if is_trainer:
                cursor.execute("""
                    INSERT INTO trainers (staff_id, certification)
                    VALUES (%s, %s)
                """, (staff_id, certification or None))

            db.commit()
            cursor.close()
            return redirect('/staff')
        except Error as e:
            db.rollback()
            cursor.close()
            return f"Error adding staff: {str(e)} <a href='/add_staff'>Go back</a>"

    cursor.close()
    return render_template('add_staff.html')

        
@app.route('/staff_page/<int:staff_id>')
def staff_page(staff_id):
    cursor = db.cursor(dictionary=True)

    query = """
    SELECT
        s.staff_id,
        s.name,
        s.email,
        s.phone_number,
        s.role,
        s.salary,
        s.hire_date,
        s.status,
        s.last_day,
        c.class_id,
        ct.class_name,
        c.scheduled_time,
        c.duration_minutes,
        c.capacity
    FROM staff s
    LEFT JOIN trainers t ON s.staff_id = t.staff_id
    LEFT JOIN classes c ON t.staff_id = c.trainers_staff_id
    LEFT JOIN class_type ct ON c.class_type_id = ct.class_type_id
    WHERE s.staff_id = %s;
    """

    cursor.execute(query, (staff_id,))
    rows = cursor.fetchall()
    cursor.close()

    if not rows:
        return "Staff member not found. <a href='/staff'>Go back</a>"

    return render_template('staff_page.html', rows=rows)


@app.route('/edit_staff/<int:staff_id>', methods=['GET', 'POST'])
def edit_staff(staff_id):
    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone_number')
        email = request.form.get('email')
        salary = request.form.get('salary')
        role = request.form.get('role')
        is_trainer = request.form.get('is_trainer')  # 'on' if checked, None if not
        certification = request.form.get('certification') or None

        try:
            # update core staff fields
            cursor.execute("""
                UPDATE staff SET name = %s, phone_number = %s, email = %s, salary = %s, role = %s
                WHERE staff_id = %s
            """, (name, phone, email, salary, role, staff_id))

            # check if already a trainer
            cursor.execute("SELECT staff_id FROM trainers WHERE staff_id = %s", (staff_id,))
            already_trainer = cursor.fetchone()

            if is_trainer and already_trainer:
                # update certification
                cursor.execute("""
                    UPDATE trainers SET certification = %s WHERE staff_id = %s
                """, (certification, staff_id))
            elif is_trainer and not already_trainer:
                # promote to trainer
                cursor.execute("""
                    INSERT INTO trainers (staff_id, certification) VALUES (%s, %s)
                """, (staff_id, certification))
            elif not is_trainer and already_trainer:
                # demote: remove trainer record (and their classes)
                cursor.execute("SELECT class_id FROM classes WHERE trainers_staff_id = %s", (staff_id,))
                class_ids = [row['class_id'] for row in cursor.fetchall()]

                if class_ids:
                    fmt = ','.join(['%s'] * len(class_ids))
                    cursor.execute(f"DELETE FROM class_enrollment WHERE class_id IN ({fmt})", class_ids)
                    cursor.execute(f"DELETE FROM classes WHERE class_id IN ({fmt})", class_ids)

                cursor.execute("DELETE FROM trainers WHERE staff_id = %s", (staff_id,))

            db.commit()
            cursor.close()
            return redirect(f'/staff_page/{staff_id}')
        except Error as e:
            db.rollback()
            cursor.close()
            return f"Error updating staff: {str(e)} <a href='/edit_staff/{staff_id}'>Go back</a>"

    # GET: fetch staff + check if trainer
    cursor.execute("SELECT * FROM staff WHERE staff_id = %s", (staff_id,))
    staff_member = cursor.fetchone()

    cursor.execute("SELECT certification FROM trainers WHERE staff_id = %s", (staff_id,))
    trainer = cursor.fetchone()
    cursor.close()

    if not staff_member:
        return "Staff member not found. <a href='/staff'>Go back</a>"

    return render_template('edit_staff.html', name='Edit Staff', staff=staff_member, trainer=trainer)

@app.route('/deactivate_staff/<int:staff_id>')
def deactivate_staff(staff_id):
    cursor = db.cursor(dictionary=True)
    try:
        last_day = request.args.get('last_day')
        query = """
            UPDATE staff
            SET status = 'Inactive', last_day = %s
            WHERE staff_id = %s
        """
        cursor.execute(query, (last_day, staff_id))
        db.commit()
    except Error as e:
        db.rollback()
        cursor.close()
        return f"Error deactivating staff: {str(e)} <a href='/staff'>Go back</a>"

    cursor.close()
    return redirect('/staff')


@app.route('/activate_staff/<int:staff_id>')
def activate_staff(staff_id):
    cursor = db.cursor(dictionary=True)
    try:
        query = """
            UPDATE staff
            SET status = 'Active', last_day = NULL
            WHERE staff_id = %s
        """
        cursor.execute(query, (staff_id,))
        db.commit()
    except Error as e:
        db.rollback()
        cursor.close()
        return f"Error activating staff: {str(e)} <a href='/staff'>Go back</a>"

    cursor.close()
    return redirect('/staff')


@app.route('/delete_staff/<int:staff_id>')
def delete_staff(staff_id):
    cursor = db.cursor(dictionary=True)
    try:
        # delete maintenance records assigned to this staff member
        cursor.execute("""
            DELETE FROM maintenance WHERE staff_id = %s
        """, (staff_id,))

        # check if staff member is a trainer
        cursor.execute("""
            SELECT staff_id FROM trainers WHERE staff_id = %s
        """, (staff_id,))
        is_trainer = cursor.fetchone()

        if is_trainer:
            # get class_ids for this trainer
            cursor.execute("""
                SELECT class_id FROM classes WHERE trainers_staff_id = %s
            """, (staff_id,))
            class_ids = [row['class_id'] for row in cursor.fetchall()]

            if class_ids:
                format_strings = ','.join(['%s'] * len(class_ids))

                # delete class enrollments for those classes
                cursor.execute(f"""
                    DELETE FROM class_enrollment
                    WHERE class_id IN ({format_strings})
                """, class_ids)

                # delete the classes themselves
                cursor.execute(f"""
                    DELETE FROM classes
                    WHERE class_id IN ({format_strings})
                """, class_ids)

            # delete trainer record
            cursor.execute("""
                DELETE FROM trainers WHERE staff_id = %s
            """, (staff_id,))

        # delete staff member
        cursor.execute("DELETE FROM staff WHERE staff_id = %s", (staff_id,))
        db.commit()
    except Error as e:
        db.rollback()
        cursor.close()
        return f"Error deleting staff member: {str(e)} <a href='/staff'>Go back</a>"

    cursor.close()
    return redirect('/staff')



"""
Trainer table
Create is done in staff functions above

"""


def get_trainers():
    cursor = db.cursor(dictionary=True)
    query = """
        SELECT
            s.staff_id,
            s.name,
            s.email,
            s.phone_number,
            s.role,
            s.salary,
            s.hire_date,
            s.status,
            t.certification
        FROM trainers t
        JOIN staff s ON t.staff_id = s.staff_id;
    """
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    return result


@app.route('/trainers')
def trainers():
    all_trainers = get_trainers()
    return render_template('trainers.html', name="Trainers Table", rows=all_trainers)


"""
Classes table
"""

def get_classes():
    cursor = db.cursor(dictionary=True)
    query = """
        SELECT
            c.class_id,
            ct.class_name,
            ct.difficulty_level,
            c.scheduled_time,
            c.duration_minutes,
            c.capacity,
            s.name AS trainer_name,
            s.staff_id AS trainer_staff_id,
            (SELECT COUNT(*) FROM class_enrollment ce WHERE ce.class_id = c.class_id) AS enrolled_count,
            (c.capacity - (SELECT COUNT(*) FROM class_enrollment ce WHERE ce.class_id = c.class_id)) AS spots_remaining
        FROM classes c
        JOIN class_type ct ON c.class_type_id = ct.class_type_id
        JOIN trainers t ON c.trainers_staff_id = t.staff_id
        JOIN staff s ON t.staff_id = s.staff_id
        ORDER BY c.scheduled_time
    """
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    return result


@app.route('/classes')
def classes():
    all_classes = get_classes()
    return render_template('classes.html', name='Classes', rows=all_classes)

@app.route('/add_class', methods=['GET', 'POST'])
def add_class():
    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        class_type_id = request.form.get('class_type_id')
        trainer_id = request.form.get('trainer_id')
        scheduled_time = request.form.get('scheduled_time')
        duration_minutes = request.form.get('duration_minutes')
        capacity = request.form.get('capacity')

        try:
            cursor.execute("""
                INSERT INTO classes (class_type_id, trainers_staff_id, scheduled_time, duration_minutes, capacity)
                VALUES (%s, %s, %s, %s, %s)
            """, (class_type_id, trainer_id, scheduled_time, duration_minutes, capacity))
            db.commit()
            cursor.close()
            return redirect('/classes')
        except Error as e:
            db.rollback()
            cursor.close()
            return f"Error adding class: {str(e)} <a href='/add_class'>Go back</a>"

    # populate dropdowns
    cursor.execute("SELECT * FROM class_type")
    class_types = cursor.fetchall()

    cursor.execute("""
        SELECT t.staff_id, s.name
        FROM trainers t
        JOIN staff s ON t.staff_id = s.staff_id
        WHERE s.status = 'Active'
    """)
    trainers = cursor.fetchall()
    cursor.close()

    return render_template('add_class.html', name='Add Class', class_types=class_types, trainers=trainers)


@app.route('/class_page/<int:class_id>')
def class_page(class_id):
    cursor = db.cursor(dictionary=True)
    query = """
        SELECT
            c.class_id,
            ct.class_name,
            ct.difficulty_level,
            c.scheduled_time,
            c.duration_minutes,
            c.capacity,
            c.trainers_staff_id AS trainer_staff_id,
            s.name AS trainer_name,
            m.member_id,
            m.name AS member_name,
            m.email,
            ce.attendance_status,
            ce.signup_date
        FROM classes c
        JOIN class_type ct ON c.class_type_id = ct.class_type_id
        JOIN staff s ON c.trainers_staff_id = s.staff_id
        LEFT JOIN class_enrollment ce ON c.class_id = ce.class_id
        LEFT JOIN member m ON ce.member_id = m.member_id
        WHERE c.class_id = %s
    """
    cursor.execute(query, (class_id,))
    rows = cursor.fetchall()
 
    if not rows:
        cursor.close()
        return "Class not found. <a href='/classes'>Go back</a>"
 
    # Call DB function for available spots
    cursor.execute("SELECT get_available_spots(%s) AS available_spots", (class_id,))
    available_spots = cursor.fetchone()['available_spots']
    cursor.close()
 
    return render_template('class_page.html', rows=rows, available_spots=available_spots)


@app.route('/edit_class/<int:class_id>', methods=['GET', 'POST'])
def edit_class(class_id):
    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        class_type_id = request.form.get('class_type_id')
        trainer_id = request.form.get('trainer_id')
        scheduled_time = request.form.get('scheduled_time')
        duration_minutes = request.form.get('duration_minutes')
        capacity = request.form.get('capacity')

        try:
            cursor.execute("""
                UPDATE classes
                SET class_type_id = %s, trainers_staff_id = %s,
                    scheduled_time = %s, duration_minutes = %s, capacity = %s
                WHERE class_id = %s
            """, (class_type_id, trainer_id, scheduled_time, duration_minutes, capacity, class_id))
            db.commit()
            cursor.close()
            return redirect(f'/class_page/{class_id}')
        except Error as e:
            db.rollback()
            cursor.close()
            return f"Error updating class: {str(e)} <a href='/edit_class/{class_id}'>Go back</a>"

    # GET: fetch class + populate dropdowns
    cursor.execute("SELECT * FROM classes WHERE class_id = %s", (class_id,))
    class_row = cursor.fetchone()

    if not class_row:
        cursor.close()
        return "Class not found. <a href='/classes'>Go back</a>"

    cursor.execute("SELECT * FROM class_type")
    class_types = cursor.fetchall()

    cursor.execute("""
        SELECT t.staff_id, s.name
        FROM trainers t
        JOIN staff s ON t.staff_id = s.staff_id
        WHERE s.status = 'Active'
    """)
    trainers = cursor.fetchall()
    cursor.close()

    return render_template('edit_class.html', name='Edit Class',
                           class_row=class_row, class_types=class_types, trainers=trainers)


@app.route('/delete_class/<int:class_id>')
def delete_class(class_id):
    cursor = db.cursor(dictionary=True)
    try:
        # delete payments tied to class enrollments
        cursor.execute("""
            DELETE FROM payments WHERE class_enrollment_id IN (
                SELECT class_enrollment_id FROM class_enrollment WHERE class_id = %s
            )
        """, (class_id,))

        # delete enrollments
        cursor.execute("DELETE FROM class_enrollment WHERE class_id = %s", (class_id,))

        # delete class
        cursor.execute("DELETE FROM classes WHERE class_id = %s", (class_id,))
        db.commit()
    except Error as e:
        db.rollback()
        cursor.close()
        return f"Error deleting class: {str(e)} <a href='/classes'>Go back</a>"

    cursor.close()
    return redirect('/classes')


"""

Class Type table

"""

def get_class_types():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM class_type")
    result = cursor.fetchall()
    cursor.close()
    return result


@app.route('/class_types')
def class_types():
    all_class_types = get_class_types()
    return render_template('class_types.html', name='Class Types', rows=all_class_types)


@app.route('/add_class_type', methods=['GET', 'POST'])
def add_class_type():
    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        class_name = request.form.get('class_name')
        difficulty_level = request.form.get('difficulty_level')

        try:
            cursor.execute("""
                INSERT INTO class_type (class_name, difficulty_level)
                VALUES (%s, %s)
            """, (class_name, difficulty_level))
            db.commit()
            cursor.close()
            return redirect('/class_types')
        except Error as e:
            db.rollback()
            cursor.close()
            return f"Error adding class type: {str(e)} <a href='/add_class_type'>Go back</a>"

    cursor.close()
    return render_template('add_class_type.html', name='Add Class Type')


"""
Equipment
"""


def get_equipment():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM equipment ORDER BY equipment_name")
    result = cursor.fetchall()
    cursor.close()
    return result


@app.route('/equipment')
def equipment():
    all_equipment = get_equipment()
    return render_template('equipment.html', name='Equipment', rows=all_equipment)


@app.route('/add_equipment', methods=['GET', 'POST'])
def add_equipment():
    cursor = db.cursor(dictionary=True)
 
    if request.method == 'POST':
        equipment_name = request.form.get('equipment_name')
        purchase_date = request.form.get('purchase_date')
 
        try:
            cursor.execute("""
                INSERT INTO equipment (equipment_name, purchase_date)
                VALUES (%s, %s)
            """, (equipment_name, purchase_date))
            db.commit()
            cursor.close()
            return redirect('/equipment')
        except Error as e:
            db.rollback()
            cursor.close()
            return f"Error adding equipment: {str(e)} <a href='/add_equipment'>Go back</a>"
 
    cursor.close()
    return render_template('add_equipment.html', name='Add Equipment')
 
 
@app.route('/edit_equipment/<int:equipment_id>', methods=['GET', 'POST'])
def edit_equipment(equipment_id):
    cursor = db.cursor(dictionary=True)
 
    if request.method == 'POST':
        equipment_name = request.form.get('equipment_name')
        purchase_date = request.form.get('purchase_date')
 
        try:
            cursor.execute("""
                UPDATE equipment
                SET equipment_name = %s, purchase_date = %s
                WHERE equipment_id = %s
            """, (equipment_name, purchase_date, equipment_id))
            db.commit()
            cursor.close()
            return redirect('/equipment')
        except Error as e:
            db.rollback()
            cursor.close()
            return f"Error updating equipment: {str(e)} <a href='/edit_equipment/{equipment_id}'>Go back</a>"
 
    cursor.execute("SELECT * FROM equipment WHERE equipment_id = %s", (equipment_id,))
    item = cursor.fetchone()
    cursor.close()
 
    if not item:
        return "Equipment not found. <a href='/equipment'>Go back</a>"
 
    return render_template('edit_equipment.html', name='Edit Equipment', item=item)
 
 
@app.route('/equipment_page/<int:equipment_id>')
def equipment_page(equipment_id):
    cursor = db.cursor(dictionary=True)
 
    # Fetch equipment details along with its maintenance history
    query = """
        SELECT
            e.equipment_id,
            e.equipment_name,
            e.purchase_date,
            m.maintenance_id,
            m.maintenance_date,
            s.staff_id,
            s.name AS staff_name,
            s.role AS staff_role
        FROM equipment e
        LEFT JOIN maintenance m ON e.equipment_id = m.equipment_id
        LEFT JOIN staff s ON m.staff_id = s.staff_id
        WHERE e.equipment_id = %s
        ORDER BY m.maintenance_date DESC
    """
    cursor.execute(query, (equipment_id,))
    rows = cursor.fetchall()
    cursor.close()
 
    if not rows:
        return "Equipment not found. <a href='/equipment'>Go back</a>"
 
    return render_template('equipment_page.html', rows=rows)
 
 
@app.route('/delete_equipment/<int:equipment_id>')
def delete_equipment(equipment_id):
    cursor = db.cursor(dictionary=True)
    try:
        # Delete maintenance records first (FK dependency)
        cursor.execute("DELETE FROM maintenance WHERE equipment_id = %s", (equipment_id,))
 
        # Delete equipment
        cursor.execute("DELETE FROM equipment WHERE equipment_id = %s", (equipment_id,))
        db.commit()
    except Error as e:
        db.rollback()
        cursor.close()
        return f"Error deleting equipment: {str(e)} <a href='/equipment'>Go back</a>"
 
    cursor.close()
    return redirect('/equipment')


"""
Payments
"""

PAYMENT_METHODS = ['card', 'cash', 'bank transfer', 'check', 'online'] # for drop down menu rather than a freeform text field
 
 
def get_all_payments():
    cursor = db.cursor(dictionary=True)
    # Uses the View: member_payment_details 
    cursor.execute("""
        SELECT *
        FROM member_payment_details
        ORDER BY payment_date DESC
    """)
    result = cursor.fetchall()
    cursor.close()
    return result



@app.route('/payments')
def payments():
    all_payments = get_all_payments()
    # Collect unique members for filter dropdown
    members_seen = {}
    for p in all_payments:
        members_seen[p['member_id']] = p['member_name']
    return render_template(
        'payments.html',
        name='Payments',
        rows=all_payments,
        members=members_seen,
        payment_statuses=['pending', 'completed', 'failed', 'refunded'],
        payment_types=['membership', 'class']
    )


@app.route('/add_payment', methods=['GET', 'POST'])
def add_payment():
    cursor = db.cursor(dictionary=True)
 
    if request.method == 'POST':
        member_id = request.form.get('member_id')
        payment_type = request.form.get('payment_type')
        payment_method = request.form.get('payment_method')
        amount = request.form.get('amount')
        payment_date = request.form.get('payment_date')
        status = request.form.get('status')
        member_membership_id = request.form.get('member_membership_id') or None
        class_enrollment_id = request.form.get('class_enrollment_id') or None
 
        # Enforce the check constraint in Python too
        if payment_type == 'membership' and not member_membership_id:
            cursor.close()
            return "Error: membership payment requires a membership selection. <a href='/add_payment'>Go back</a>"
        if payment_type == 'class' and not class_enrollment_id:
            cursor.close()
            return "Error: class payment requires a class enrollment selection. <a href='/add_payment'>Go back</a>"
 
        try:
            cursor.execute("""
                INSERT INTO payments
                    (member_id, amount, payment_date, payment_method, status,
                     payment_type, member_membership_id, class_enrollment_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (member_id, amount, payment_date, payment_method, status,
                  payment_type, member_membership_id, class_enrollment_id))
            db.commit()
            cursor.close()
            return redirect('/payments')
        except Error as e:
            db.rollback()
            cursor.close()
            return f"Error adding payment: {str(e)} <a href='/add_payment'>Go back</a>"
 
    # GET: just load the member list; memberships/classes are fetched via AJAX
    cursor.execute("SELECT member_id, name FROM member ORDER BY name")
    members = cursor.fetchall()
    cursor.close()
 
    return render_template(
        'add_payment.html',
        name='Add Payment',
        members=members,
        payment_methods=PAYMENT_METHODS,
        payment_statuses=['pending', 'completed', 'failed', 'refunded']
    )


@app.route('/get_member_payment_targets/<int:member_id>')
def get_member_payment_targets(member_id):
    """AJAX endpoint: returns active memberships and class enrollments for a member."""
    cursor = db.cursor(dictionary=True)
 
    cursor.execute("""
        SELECT mm.member_membership_id, ms.membership_name, mm.start_date, mm.end_date
        FROM member_membership mm
        JOIN memberships ms ON mm.membership_id = ms.membership_id
        WHERE mm.member_id = %s
          AND (mm.end_date IS NULL OR mm.end_date >= CURDATE())
        ORDER BY mm.start_date DESC
    """, (member_id,))
    memberships = cursor.fetchall()
 
    cursor.execute("""
        SELECT ce.class_enrollment_id, ct.class_name, c.scheduled_time, ce.attendance_status
        FROM class_enrollment ce
        JOIN classes c ON ce.class_id = c.class_id
        JOIN class_type ct ON c.class_type_id = ct.class_type_id
        WHERE ce.member_id = %s
        ORDER BY c.scheduled_time DESC
    """, (member_id,))
    enrollments = cursor.fetchall()
 
    cursor.close()
 
    # Convert dates/datetimes to strings for JSON serialisation
    for m in memberships:
        m['start_date'] = str(m['start_date'])
        m['end_date'] = str(m['end_date']) if m['end_date'] else None
    for e in enrollments:
        e['scheduled_time'] = str(e['scheduled_time'])
 
    return jsonify({'memberships': memberships, 'enrollments': enrollments})
 
 
@app.route('/edit_payment/<int:payment_id>', methods=['GET', 'POST'])
def edit_payment(payment_id):
    cursor = db.cursor(dictionary=True)
 
    if request.method == 'POST':
        payment_method = request.form.get('payment_method')
        amount = request.form.get('amount')
        payment_date = request.form.get('payment_date')
        status = request.form.get('status')
 
        try:
            # Only allow editing non-structural fields; payment_type and
            # the membership/class link are immutable after creation.
            cursor.execute("""
                UPDATE payments
                SET amount = %s, payment_date = %s, payment_method = %s, status = %s
                WHERE payment_id = %s
            """, (amount, payment_date, payment_method, status, payment_id))
            db.commit()
            cursor.close()
            return redirect('/payments')
        except Error as e:
            db.rollback()
            cursor.close()
            return f"Error updating payment: {str(e)} <a href='/edit_payment/{payment_id}'>Go back</a>"
 
    cursor.execute("SELECT * FROM payments WHERE payment_id = %s", (payment_id,))
    payment = cursor.fetchone()
    cursor.close()
 
    if not payment:
        return "Payment not found. <a href='/payments'>Go back</a>"
 
    return render_template(
        'edit_payment.html',
        name='Edit Payment',
        payment=payment,
        payment_methods=PAYMENT_METHODS,
        payment_statuses=['pending', 'completed', 'failed', 'refunded']
    )
 
 
@app.route('/delete_payment/<int:payment_id>')
def delete_payment(payment_id):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("DELETE FROM payments WHERE payment_id = %s", (payment_id,))
        db.commit()
    except Error as e:
        db.rollback()
        cursor.close()
        return f"Error deleting payment: {str(e)} <a href='/payments'>Go back</a>"
 
    cursor.close()
    return redirect('/payments')

#calling the add_membership_payment function
@app.route('/record_membership_payment/<int:member_id>', methods=['GET', 'POST'])
def record_membership_payment(member_id):
    cursor = db.cursor(dictionary=True)
 
    if request.method == 'POST':
        membership_id = request.form.get('membership_id')
        amount = request.form.get('amount')
 
        try:
            cursor.callproc('add_membership_payment', [member_id, membership_id, amount])
            db.commit()
            cursor.close()
            return redirect(f'/member_page/{member_id}')
        except Error as e:
            db.rollback()
            cursor.close()
            return f"Error recording payment: {str(e)} <a href='/record_membership_payment/{member_id}'>Go back</a>"
 
    # GET: fetch active membership(s) for this member to populate the form
    cursor.execute("""
        SELECT mm.member_membership_id, mm.membership_id, ms.membership_name, ms.price
        FROM member_membership mm
        JOIN memberships ms ON mm.membership_id = ms.membership_id
        WHERE mm.member_id = %s
          AND (mm.end_date IS NULL OR mm.end_date >= CURDATE())
    """, (member_id,))
    active_memberships = cursor.fetchall()
 
    cursor.execute("SELECT name FROM member WHERE member_id = %s", (member_id,))
    member = cursor.fetchone()
    cursor.close()
 
    if not active_memberships:
        return f"No active membership found for this member. <a href='/member_page/{member_id}'>Go back</a>"
 
    return render_template(
        'record_membership_payment.html',
        member_id=member_id,
        member=member,
        active_memberships=active_memberships
    )


"""
Maintenance
"""

def get_all_maintenance():
    cursor = db.cursor(dictionary=True)
    query = """
        SELECT
            m.maintenance_id,
            m.maintenance_date,
            e.equipment_id,
            e.equipment_name,
            s.staff_id,
            s.name AS staff_name,
            s.role AS staff_role
        FROM maintenance m
        JOIN equipment e ON m.equipment_id = e.equipment_id
        JOIN staff s ON m.staff_id = s.staff_id
        ORDER BY m.maintenance_date DESC
    """
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    return result
 
 
@app.route('/maintenance')
def maintenance():
    all_maintenance = get_all_maintenance()
    # Build unique equipment and staff lists for filter dropdowns
    equipment_seen = {}
    staff_seen = {}
    for row in all_maintenance:
        equipment_seen[row['equipment_id']] = row['equipment_name']
        staff_seen[row['staff_id']] = row['staff_name']
    return render_template(
        'maintenance.html',
        name='Maintenance',
        rows=all_maintenance,
        equipment_map=equipment_seen,
        staff_map=staff_seen
    )
 
 
@app.route('/add_maintenance', methods=['GET', 'POST'])
@app.route('/add_maintenance/<int:equipment_id>', methods=['GET', 'POST'])
def add_maintenance(equipment_id=None):
    cursor = db.cursor(dictionary=True)
 
    if request.method == 'POST':
        eq_id = request.form.get('equipment_id')
        staff_id = request.form.get('staff_id')
        maintenance_date = request.form.get('maintenance_date')
 
        try:
            cursor.execute("""
                INSERT INTO maintenance (equipment_id, staff_id, maintenance_date)
                VALUES (%s, %s, %s)
            """, (eq_id, staff_id, maintenance_date))
            db.commit()
            cursor.close()
            # Return to equipment page if we came from there, otherwise maintenance list
            came_from = request.form.get('came_from')
            if came_from == 'equipment_page':
                return redirect(f'/equipment_page/{eq_id}')
            return redirect('/maintenance')
        except Error as e:
            db.rollback()
            cursor.close()
            return f"Error logging maintenance: {str(e)} <a href='/add_maintenance'>Go back</a>"
 
    cursor.execute("SELECT equipment_id, equipment_name FROM equipment ORDER BY equipment_name")
    all_equipment = cursor.fetchall()
 
    cursor.execute("""
        SELECT staff_id, name, role FROM staff
        WHERE status = 'Active'
        ORDER BY name
    """)
    all_staff = cursor.fetchall()
    cursor.close()
 
    return render_template(
        'add_maintenance.html',
        name='Log Maintenance',
        all_equipment=all_equipment,
        all_staff=all_staff,
        preselected_equipment_id=equipment_id
    )


"""
Class Enrollment Route

"""

@app.route('/enroll', methods=['GET', 'POST'])
@app.route('/enroll/class/<int:class_id>', methods=['GET', 'POST'])
@app.route('/enroll/member/<int:member_id>', methods=['GET', 'POST'])
def enroll(class_id=None, member_id=None):
    cursor = db.cursor(dictionary=True)
 
    if request.method == 'POST':
        enroll_class_id  = request.form.get('class_id')
        enroll_member_id = request.form.get('member_id')
        came_from        = request.form.get('came_from', 'class')
 
        try:
            cursor.callproc('enroll_member_in_class', [enroll_member_id, enroll_class_id])
            db.commit()
        except Error as e:
            db.rollback()
            cursor.close()
            # Surface the stored procedure's SIGNAL messages cleanly
            return render_template(
                'enroll_error.html',
                error=str(e),
                class_id=enroll_class_id,
                member_id=enroll_member_id,
                came_from=came_from
            )
 
        # Fetch confirmation details
        cursor.execute("""
            SELECT
                m.member_id,
                m.name AS member_name,
                m.email,
                c.class_id,
                ct.class_name,
                c.scheduled_time,
                c.duration_minutes,
                s.name AS trainer_name
            FROM member m
            JOIN class_enrollment ce ON m.member_id = ce.member_id
            JOIN classes c ON ce.class_id = c.class_id
            JOIN class_type ct ON c.class_type_id = ct.class_type_id
            JOIN staff s ON c.trainers_staff_id = s.staff_id
            WHERE m.member_id = %s AND c.class_id = %s
        """, (enroll_member_id, enroll_class_id))
        enrollment = cursor.fetchone()
        cursor.close()
 
        return render_template(
            'enroll_confirmation.html',
            enrollment=enrollment,
            came_from=came_from
        )
 
    # --- GET: build form ---
 
    # Pre-load member if coming from member page
    preselected_member = None
    if member_id:
        cursor.execute("SELECT member_id, name FROM member WHERE member_id = %s", (member_id,))
        preselected_member = cursor.fetchone()
 
    # Pre-load class if coming from class page
    preselected_class = None
    if class_id:
        cursor.execute("""
            SELECT c.class_id, ct.class_name, c.scheduled_time, c.capacity,
                   (SELECT COUNT(*) FROM class_enrollment WHERE class_id = c.class_id) AS enrolled
            FROM classes c
            JOIN class_type ct ON c.class_type_id = ct.class_type_id
            WHERE c.class_id = %s
        """, (class_id,))
        preselected_class = cursor.fetchone()
 
    # Member dropdown (only needed when no member pre-selected)
    all_members = []
    if not member_id:
        cursor.execute("""
            SELECT member_id, name FROM member
            WHERE status = 'Active'
            ORDER BY name
        """)
        all_members = cursor.fetchall()
 
    # Class dropdown (only needed when no class pre-selected)
    all_classes = []
    if not class_id:
        cursor.execute("""
            SELECT
                c.class_id,
                ct.class_name,
                c.scheduled_time,
                c.capacity,
                (SELECT COUNT(*) FROM class_enrollment ce WHERE ce.class_id = c.class_id) AS enrolled
            FROM classes c
            JOIN class_type ct ON c.class_type_id = ct.class_type_id
            HAVING (c.capacity - enrolled) > 0
            ORDER BY c.scheduled_time
        """)
        all_classes = cursor.fetchall()
 
    cursor.close()
 
    came_from = 'class' if class_id else 'member'
 
    return render_template(
        'enroll.html',
        name='Enroll Member',
        preselected_member=preselected_member,
        preselected_class=preselected_class,
        all_members=all_members,
        all_classes=all_classes,
        came_from=came_from
    )

if __name__=="__main__":
    app.run(host="0.0.0.0", debug=True)