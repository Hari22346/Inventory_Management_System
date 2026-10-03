from tkinter import *
from tkinter import messagebox
from employees import employee_form, connect_database
from supplier import supplier_form
from category import category_form
from product import product_form
from sales import sales_form
from billing import billing_form, get_tax
import time

FONT = 'times new roman'


def build_header(window, name, on_logout):
    """Title bar, logout button and live welcome/date/time bar (shared by both windows)."""
    window.title_image = PhotoImage(file='inventory.png')
    Label(window, image=window.title_image, compound=LEFT, text='Inventory Management System',
          font=(FONT, 40, 'bold'), bg='#010c48', fg='white', anchor='w', padx=20).place(x=0, y=0, relwidth=1)
    Button(window, text='Logout', font=(FONT, 20, 'bold'), fg='#010c48', cursor='hand2',
           command=on_logout).place(x=1100, y=10)
    subtitle = Label(window, font=(FONT, 15), bg='#4d636d', fg='white')
    subtitle.place(x=0, y=70, relwidth=1)

    def tick():
        subtitle.config(text=f'Welcome {name}\t\t\t\t\t\t\t\t {time.strftime("%I:%M:%S %p on %A, %B %d, %Y")}')
        subtitle.after(1000, tick)
    tick()


def new_window(title):
    window = Tk()
    window.title(title)
    window.geometry('1270x668+0+0')
    window.resizable(0, 0)
    window.config(bg='white')
    return window


# ------------------------------------------------------------------ Tax window
def tax_window(parent):
    def save_text():
        try:
            tax = float(tax_count.get())
            if not 0 <= tax <= 100:
                raise ValueError
        except ValueError:
            messagebox.showerror('Error', 'Enter a tax between 0 and 100', parent=tax_root)
            return
        cursor, connection = connect_database()
        if not cursor or not connection:
            return
        try:
            cursor.execute('use inventory_system')
            cursor.execute('CREATE TABLE IF NOT EXISTS tax_table (id INT PRIMARY KEY, tax DECIMAL(5,2))')
            cursor.execute('INSERT INTO tax_table (id,tax) VALUES(1,%s) ON DUPLICATE KEY UPDATE tax=%s', (tax, tax))
            connection.commit()
            messagebox.showinfo('Success', f'Tax is set to {tax}% and saved successfully', parent=tax_root)
        except Exception as e:
            messagebox.showerror('Error', f'Error due to {e}', parent=tax_root)
        finally:
            cursor.close()
            connection.close()

    tax_root = Toplevel(parent)
    tax_root.title('Tax Window')
    tax_root.geometry('300x200')
    tax_root.grab_set()
    Label(tax_root, text='Enter Tax Percentage(%)', font=('arial', 12)).pack()
    tax_count = Spinbox(tax_root, from_=0, to=100, increment=0.5, font=('arial', 12))
    tax_count.pack(pady=10)
    tax_count.delete(0, END)
    tax_count.insert(0, get_tax())          # show the currently saved tax
    Button(tax_root, text='Save', font=('arial', 20, 'bold'), bg='#4d636d', fg='white', width=10,
           command=save_text).pack(pady=20)


# ------------------------------------------------------------------ Admin dashboard
def open_dashboard(empid, name):
    """Admin window. Returns True if the user pressed Logout, False if the window was closed."""
    window = new_window('Dashboard')
    state = {'logout': False, 'frame': None}

    def logout():
        if messagebox.askyesno('Logout', 'Do you want to logout?'):
            state['logout'] = True
            window.destroy()

    def exit_app():
        if messagebox.askyesno('Exit', 'Do you want to exit?'):
            window.destroy()

    def show_form(form_function):
        if state['frame']:
            state['frame'].destroy()
        state['frame'] = form_function(window)

    build_header(window, name, logout)

    leftFrame = Frame(window, bg='white')
    leftFrame.place(x=0, y=102, width=180, height=555)
    logoImage = PhotoImage(file='checklist.png')
    Label(leftFrame, image=logoImage).pack(fill=X)
    Label(leftFrame, text='Menu', font=(FONT, 20), bg='#009688').pack(fill=X)

    menu = [('man.png', ' Employee', lambda: show_form(employee_form)),
            ('supplier.png', ' Supplier', lambda: show_form(supplier_form)),
            ('categorization.png', ' Category', lambda: show_form(category_form)),
            ('package.png', ' Product', lambda: show_form(product_form)),
            ('increase.png', ' Sales', lambda: show_form(sales_form)),
            ('tax.png', ' Tax', lambda: tax_window(window)),
            ('logout.png', ' Exit', exit_app)]
    icons = []
    for file, text, command in menu:
        icon = PhotoImage(file=file)
        icons.append(icon)
        Button(leftFrame, image=icon, compound=LEFT, text=text, font=(FONT, 20, 'bold'), anchor='w',
               padx=10, command=command).pack(fill=X)

    # summary cards: (title, icon, colour, x, y, table)
    cards = [('Total Employees', 'staff.png', '#2C3E50', 400, 125, 'employee_data'),
             ('Total Suppliers', 'total_suppliers.png', '#8E44AD', 800, 125, 'supplier_data'),
             ('Total Categories', 'market-segment.png', '#27AE60', 400, 310, 'category_data'),
             ('Total Products', 'products.png', '#2C3E50', 800, 310, 'product_data'),
             ('Total Sales', 'trend.png', '#E74C3C', 600, 496, 'sales_data')]
    count_labels = {}
    for title, file, color, x, y, table in cards:
        frame = Frame(window, bg=color, bd=3, relief=RIDGE)
        frame.place(x=x, y=y, height=170, width=200)
        icon = PhotoImage(file=file)
        icons.append(icon)
        Label(frame, image=icon, bg=color).pack(pady=10)
        Label(frame, text=title, bg=color, fg='white', font=(FONT, 15, 'bold')).pack()
        count_labels[table] = Label(frame, text='0', bg=color, fg='white', font=(FONT, 30, 'bold'))
        count_labels[table].pack()

    def update_counts():
        cursor, connection = connect_database()
        if cursor and connection:
            try:
                cursor.execute('use inventory_system')
                for table, label in count_labels.items():
                    try:
                        cursor.execute(f'SELECT COUNT(*) FROM {table}')
                        label.config(text=cursor.fetchone()[0])
                    except Exception:
                        label.config(text=0)      # table not created yet
            finally:
                cursor.close()
                connection.close()
        window.after(5000, update_counts)

    update_counts()
    window.mainloop()
    return state['logout']


# ------------------------------------------------------------------ Employee window (billing only)
def open_employee_billing(empid, name):
    """Employee window with only the billing page. Returns True if Logout was pressed."""
    window = new_window('Billing')
    state = {'logout': False}

    def logout():
        if messagebox.askyesno('Logout', 'Do you want to logout?'):
            state['logout'] = True
            window.destroy()

    build_header(window, name, logout)
    billing_form(window, x=0)
    window.mainloop()
    return state['logout']