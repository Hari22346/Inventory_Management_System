from tkinter import *
from tkinter import ttk
from tkinter import messagebox
import re
import os
import time
import traceback
from employees import connect_database
from dashboard import open_dashboard, open_employee_billing

FONT = 'times new roman'
BLUE = '#4a90e2'
GREY = '#d3d3d3'

# Default administrator (created automatically if no admin exists)
DEFAULT_ADMIN_ID = 545454
DEFAULT_ADMIN_PASSWORD = '@Hari6304'


ADMIN_IMAGES = ['inventory.png', 'checklist.png', 'back-arrow.png', 'folder-management.png',
                'man.png', 'supplier.png', 'categorization.png', 'package.png', 'increase.png', 'tax.png',
                'logout.png', 'staff.png', 'total_suppliers.png', 'market-segment.png', 'products.png',
                'trend.png']
EMPLOYEE_IMAGES = ['inventory.png', 'back-arrow.png']


def missing_images(files):
    return [f for f in files if not os.path.exists(f)]


def show_error(title, text):
    r = Tk()
    r.withdraw()
    messagebox.showerror(title, text)
    r.destroy()


def load_image(file):
    try:
        return PhotoImage(file=file)
    except TclError:
        return None


# ------------------------------------------------------------------ database setup
def prepare_database():
    """Create the database + every table and the default admin account (runs on every start)."""
    cursor, connection = connect_database()
    if not cursor or not connection:
        return False
    try:
        cursor.execute('CREATE DATABASE IF NOT EXISTS inventory_system')
        cursor.execute('USE inventory_system')
        cursor.execute('CREATE TABLE IF NOT EXISTS employee_data (empid INT PRIMARY KEY, name VARCHAR(100), '
                       'email VARCHAR(100), gender VARCHAR(50), dob VARCHAR(30), contact VARCHAR(30), '
                       'employment_type VARCHAR(50), education VARCHAR(50), work_shift VARCHAR(50), '
                       'address VARCHAR(100), doj VARCHAR(50), salary VARCHAR(50), usertype VARCHAR(50), '
                       'password VARCHAR(50))')
        cursor.execute('CREATE TABLE IF NOT EXISTS supplier_data (invoice INT PRIMARY KEY, name VARCHAR(100), '
                       'contact VARCHAR(15), description TEXT)')
        cursor.execute('CREATE TABLE IF NOT EXISTS category_data (id INT PRIMARY KEY, name VARCHAR(100), '
                       'description TEXT)')
        cursor.execute('CREATE TABLE IF NOT EXISTS product_data (id INT AUTO_INCREMENT PRIMARY KEY, '
                       'category VARCHAR(100), supplier VARCHAR(100), name VARCHAR(100), price DECIMAL(10,2), '
                       'discount INT, discounted_price DECIMAL(10,2), quantity INT, status VARCHAR(50))')
        cursor.execute('CREATE TABLE IF NOT EXISTS sales_data (bill_no INT AUTO_INCREMENT PRIMARY KEY, '
                       'customer_name VARCHAR(100), contact VARCHAR(30), bill_date VARCHAR(50), items TEXT, '
                       'bill_amount DECIMAL(10,2), tax DECIMAL(5,2), net_pay DECIMAL(10,2))')
        cursor.execute('CREATE TABLE IF NOT EXISTS sale_items (id INT AUTO_INCREMENT PRIMARY KEY, bill_no INT, '
                       'sale_date VARCHAR(20), product_id INT, product_name VARCHAR(100), qty INT, '
                       'price DECIMAL(10,2), total DECIMAL(10,2))')
        cursor.execute('CREATE TABLE IF NOT EXISTS tax_table (id INT PRIMARY KEY, tax DECIMAL(5,2))')

        cursor.execute('SELECT empid FROM employee_data WHERE empid=%s', (DEFAULT_ADMIN_ID,))
        if not cursor.fetchone():
            today = time.strftime('%d/%m/%Y')
            cursor.execute('INSERT INTO employee_data VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                           (DEFAULT_ADMIN_ID, 'Admin', 'admin@example.com', 'Male', '01/01/2000', '0000000000',
                            'Full Time', 'B.Tech', 'Morning', 'Head Office', today, '0', 'Admin',
                            DEFAULT_ADMIN_PASSWORD))
        connection.commit()
        return True
    except Exception as e:
        messagebox.showerror('Error', f'Error due to {e}')
        return False
    finally:
        cursor.close()
        connection.close()


# ------------------------------------------------------------------ registration window
def open_register(root, empid_entry):
    reg = Toplevel(root)
    reg.title('Register')
    reg.geometry('430x600+400+40')
    reg.resizable(0, 0)
    reg.config(bg='white')
    reg.grab_set()

    Label(reg, text='Register New User', font=(FONT, 22, 'bold'), bg=BLUE, fg='white').pack(fill=X)

    form = Frame(reg, bg='white')
    form.pack(pady=15)

    def add_label(text, row):
        Label(form, text=text, font=(FONT, 13, 'bold'), bg='white').grid(row=row, column=0, sticky='w',
                                                                         padx=10, pady=8)

    add_label('Employee Id', 0)
    id_e = Entry(form, font=(FONT, 13), bg='lightyellow', width=20)
    id_e.grid(row=0, column=1)

    add_label('Name', 1)
    name_e = Entry(form, font=(FONT, 13), bg='lightyellow', width=20)
    name_e.grid(row=1, column=1)

    add_label('Email', 2)
    email_e = Entry(form, font=(FONT, 13), bg='lightyellow', width=20)
    email_e.grid(row=2, column=1)

    add_label('Contact', 3)
    contact_e = Entry(form, font=(FONT, 13), bg='lightyellow', width=20)
    contact_e.grid(row=3, column=1)

    add_label('Gender', 4)
    gender_c = ttk.Combobox(form, values=('Male', 'Female'), font=(FONT, 12), width=18, state='readonly')
    gender_c.set('Select Gender')
    gender_c.grid(row=4, column=1)

    add_label('User Type', 5)
    type_c = ttk.Combobox(form, values=('Employee', 'Admin'), font=(FONT, 12), width=18, state='readonly')
    type_c.set('Employee')
    type_c.grid(row=5, column=1)

    add_label('Password', 6)
    pass_e = Entry(form, font=(FONT, 13), bg='lightyellow', width=20, show='*')
    pass_e.grid(row=6, column=1)

    add_label('Confirm Password', 7)
    confirm_e = Entry(form, font=(FONT, 13), bg='lightyellow', width=20, show='*')
    confirm_e.grid(row=7, column=1)

    add_label('Admin Password*', 8)
    admin_e = Entry(form, font=(FONT, 13), bg='lightyellow', width=20, show='*')
    admin_e.grid(row=8, column=1)
    Label(reg, text='*Needed only when registering a new Admin (enter an existing admin\'s password)',
          font=(FONT, 9), bg='white', fg='grey', wraplength=400).pack()

    def register():
        empid = id_e.get().strip()
        name = name_e.get().strip()
        email = email_e.get().strip()
        contact = contact_e.get().strip()
        gender = gender_c.get()
        usertype = type_c.get()
        password = pass_e.get().strip()
        confirm = confirm_e.get().strip()
        admin_pass = admin_e.get().strip()

        if '' in (empid, name, email, contact, password, confirm) or gender == 'Select Gender':
            messagebox.showerror('Error', 'All fields are required', parent=reg)
            return
        if not empid.isdigit():
            messagebox.showerror('Error', 'Employee Id must be a number', parent=reg)
            return
        if not re.fullmatch(r'[\w.+-]+@[\w-]+\.[\w.-]+', email):
            messagebox.showerror('Error', 'Enter a valid email address', parent=reg)
            return
        if not (contact.isdigit() and len(contact) == 10):
            messagebox.showerror('Error', 'Contact must be a 10 digit number', parent=reg)
            return
        if password != confirm:
            messagebox.showerror('Error', 'Passwords do not match', parent=reg)
            return
        if len(password) > 50:
            messagebox.showerror('Error', 'Password is too long (max 50 characters)', parent=reg)
            return

        cursor, connection = connect_database()
        if not cursor or not connection:
            return
        try:
            cursor.execute('USE inventory_system')
            if usertype == 'Admin':
                cursor.execute("SELECT empid FROM employee_data WHERE usertype='Admin' AND password=%s",
                               (admin_pass,))
                if not admin_pass or not cursor.fetchone():
                    messagebox.showerror('Error', 'Admin password is wrong. Only an existing admin can '
                                                  'authorise a new admin.', parent=reg)
                    return
            cursor.execute('SELECT empid FROM employee_data WHERE empid=%s', (empid,))
            if cursor.fetchone():
                messagebox.showerror('Error', 'Employee Id already exists', parent=reg)
                return
            today = time.strftime('%d/%m/%Y')
            cursor.execute('INSERT INTO employee_data VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                           (empid, name, email, gender, today, contact, 'Full Time', 'B.Tech', 'Morning',
                            'N/A', today, '0', usertype, password))
            connection.commit()
        except Exception as e:
            messagebox.showerror('Error', f'Error due to {e}', parent=reg)
            return
        finally:
            cursor.close()
            connection.close()

        messagebox.showinfo('Success', 'Registration successful. Please login now.', parent=reg)
        empid_entry.delete(0, END)
        empid_entry.insert(0, empid)
        reg.destroy()

    Button(reg, text='Register', font=(FONT, 15, 'bold'), bg=BLUE, fg='white', activebackground=BLUE,
           activeforeground='white', cursor='hand2', width=16, command=register).pack(pady=10)
    Button(reg, text='Back to Login', font=(FONT, 11), bd=0, fg=BLUE, bg='white', cursor='hand2',
           command=reg.destroy).pack()
    id_e.focus_set()


# ------------------------------------------------------------------ login window
def run_login():
    """Shows the login window. Returns (empid, name, usertype) or None if closed."""
    result = {}
    root = Tk()
    root.title('Login')
    root.geometry('800x500+250+80')
    root.resizable(0, 0)
    root.config(bg='white')

    Label(root, text='Inventory Management System', font=(FONT, 36), bg=BLUE, fg='white').place(x=0, y=0, relwidth=1)

    banner = load_image('login.png')
    if banner:
        Label(root, image=banner, bg='white').place(x=30, y=140)

    box = Frame(root, bg=GREY)
    box.place(x=500, y=80, width=260, height=390)

    avatar = load_image('boy.png')
    if avatar:
        Label(box, image=avatar, bg=GREY).place(x=65, y=10)
    Label(box, text='Employee Id', font=(FONT, 14, 'bold'), bg=GREY).place(x=15, y=170)
    empid_entry = Entry(box, font=(FONT, 13), width=20, bd=0)
    empid_entry.place(x=15, y=200)
    Label(box, text='Password', font=(FONT, 14, 'bold'), bg=GREY).place(x=15, y=235)
    password_entry = Entry(box, font=(FONT, 13), width=17, bd=0, show='*')
    password_entry.place(x=15, y=265)

    view_icon, hide_icon = load_image('view.png'), load_image('hide.png')

    def set_eye(visible):
        password_entry.config(show='' if visible else '*')
        if view_icon and hide_icon:
            eye_button.config(image=view_icon if visible else hide_icon)
        else:
            eye_button.config(text='Hide' if visible else 'Show')

    eye_button = Button(box, bd=0, bg=GREY, activebackground=GREY, cursor='hand2',
                        command=lambda: set_eye(password_entry.cget('show') == '*'))
    eye_button.place(x=200, y=262)
    set_eye(False)

    def forgot():
        messagebox.showinfo('Forgot Password', 'Please contact the administrator to reset your password.')

    forgot_label = Label(box, text='Forgot Password?', font=(FONT, 10), bg=GREY, fg=BLUE, cursor='hand2')
    forgot_label.place(x=15, y=295)
    forgot_label.bind('<Button-1>', lambda e: forgot())

    register_label = Label(box, text='New user? Register', font=(FONT, 10, 'bold'), bg=GREY, fg=BLUE,
                           cursor='hand2')
    register_label.place(x=135, y=295)
    register_label.bind('<Button-1>', lambda e: open_register(root, empid_entry))

    def login(event=None):
        empid, password = empid_entry.get().strip(), password_entry.get().strip()
        if empid == '' or password == '':
            messagebox.showerror('Error', 'All fields are required')
            return
        if not empid.isdigit():
            messagebox.showerror('Error', 'Employee Id must be a number')
            return
        cursor, connection = connect_database()
        if not cursor or not connection:
            return
        try:
            cursor.execute('USE inventory_system')
            cursor.execute('SELECT name, usertype FROM employee_data WHERE empid=%s AND password=%s',
                           (empid, password))
            row = cursor.fetchone()
        except Exception as e:
            messagebox.showerror('Error', f'Error due to {e}')
            return
        finally:
            cursor.close()
            connection.close()
        if not row:
            messagebox.showerror('Error', 'Invalid Employee Id or Password')
            return
        result['user'] = (int(empid), row[0], row[1])
        root.destroy()

    Button(box, text='Login', font=(FONT, 15, 'bold'), bg=BLUE, fg='white', activebackground=BLUE,
           activeforeground='white', cursor='hand2', width=16, command=login).place(x=15, y=335)
    root.bind('<Return>', login)

    root.update()
    prepare_database()
    empid_entry.focus_set()
    root.mainloop()
    return result.get('user')


if __name__ == '__main__':
    while True:
        user = run_login()
        if not user:
            break
        empid, name, usertype = user
        is_admin = usertype.strip().lower() == 'admin'
        missing = missing_images(ADMIN_IMAGES if is_admin else EMPLOYEE_IMAGES)
        if missing:
            show_error('Missing image files',
                       'Put these files in the same folder as main.py:\n\n' + '\n'.join(missing))
            break
        try:
            if is_admin:
                logged_out = open_dashboard(empid, name)         # Admin -> dashboard + all pages
            else:
                logged_out = open_employee_billing(empid, name)  # Employee -> billing page only
        except Exception:
            err = traceback.format_exc()
            print(err)
            show_error('Error opening page', err[-900:])
            break
        if not logged_out:
            break