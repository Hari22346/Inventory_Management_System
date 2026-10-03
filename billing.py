from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from tkinter import font as tkfont
from employees import connect_database
import re, os, time, random

# QR support (optional, the app still works if it isn't installed)
try:
    import qrcode
    QR_OK = True
except Exception:
    QR_OK = False

FONT = 'times new roman'
BLUE = '#0f4d7d'
GREY = '#4d636d'

# ---- shop header printed on every bill (edit these) ----
SHOP_NAME = 'Rama Stock_App'
SHOP_PHONE_ADDR = 'Phone No. 6304634036, Nagari,517590'


def get_tax():
    """Read tax % saved from the Tax window (tax_table)."""
    cursor, connection = connect_database()
    if not cursor or not connection:
        return 0.0
    try:
        cursor.execute('use inventory_system')
        cursor.execute('CREATE TABLE IF NOT EXISTS tax_table (id INT PRIMARY KEY, tax DECIMAL(5,2))')
        cursor.execute('SELECT tax FROM tax_table WHERE id=1')
        row = cursor.fetchone()
        return float(row[0]) if row else 0.0
    except Exception:
        return 0.0
    finally:
        cursor.close()
        connection.close()


def load_products(treeview, name=''):
    """Columns: id, name, price, discount %, discounted price, quantity."""
    cursor, connection = connect_database()
    if not cursor or not connection:
        return
    try:
        cursor.execute('use inventory_system')
        base = ("SELECT id, name, price, discount, "
                "ROUND(price - (price * discount / 100), 2) AS discounted_price, quantity "
                "FROM product_data WHERE status='Active'")
        if name:
            cursor.execute(base + " AND name LIKE %s", (f'%{name}%',))
        else:
            cursor.execute(base)
        records = cursor.fetchall()
        if name and not records:
            messagebox.showerror('Error', 'No products found')
            return
        treeview.delete(*treeview.get_children())
        for r in records:
            treeview.insert('', END, values=r)
    except Exception as e:
        messagebox.showerror('Error', f'Error due to {e}')
    finally:
        cursor.close()
        connection.close()


def save_sale(cust_name, contact, items_text, amount, tax, net, cart):
    """Insert sale record (random unique 8-digit bill no) and reduce stock.
    Returns bill number or None."""
    cursor, connection = connect_database()
    if not cursor or not connection:
        return None
    try:
        cursor.execute('use inventory_system')
        cursor.execute('CREATE TABLE IF NOT EXISTS sales_data (bill_no INT AUTO_INCREMENT PRIMARY KEY, '
                       'customer_name VARCHAR(100), contact VARCHAR(30), bill_date VARCHAR(50), '
                       'items TEXT, bill_amount DECIMAL(10,2), tax DECIMAL(5,2), net_pay DECIMAL(10,2))')

        # random, unique 8-digit bill number
        bill_no = None
        for _ in range(20):
            candidate = random.randint(10000000, 99999999)
            cursor.execute('SELECT 1 FROM sales_data WHERE bill_no=%s', (candidate,))
            if not cursor.fetchone():
                bill_no = candidate
                break
        if bill_no is None:
            messagebox.showerror('Error', 'Could not generate a unique bill number, try again')
            return None

        cursor.execute('INSERT INTO sales_data (bill_no,customer_name,contact,bill_date,items,bill_amount,tax,net_pay) '
                       'VALUES(%s,%s,%s,%s,%s,%s,%s,%s)',
                       (bill_no, cust_name, contact, time.strftime('%d/%m/%Y %I:%M %p'),
                        items_text, amount, tax, net))
        cursor.execute('CREATE TABLE IF NOT EXISTS sale_items (id INT AUTO_INCREMENT PRIMARY KEY, bill_no INT, '
                       'sale_date VARCHAR(20), product_id INT, product_name VARCHAR(100), qty INT, '
                       'price DECIMAL(10,2), total DECIMAL(10,2))')
        for item in cart.values():
            cursor.execute('UPDATE product_data SET quantity=quantity-%s WHERE id=%s', (item['qty'], item['id']))
            cursor.execute('INSERT INTO sale_items (bill_no,sale_date,product_id,product_name,qty,price,total) '
                           'VALUES(%s,%s,%s,%s,%s,%s,%s)',
                           (bill_no, time.strftime('%d/%m/%Y'), item['id'], item['name'], item['qty'],
                            item['price'], round(item['price'] * item['qty'], 2)))
        connection.commit()
        return bill_no
    except Exception as e:
        messagebox.showerror('Error', f'Error due to {e}')
        return None
    finally:
        cursor.close()
        connection.close()


def billing_form(window, x=0):
    global back_image
    window.update_idletasks()
    W = window.winfo_width()
    if W < 900:                 # window not drawn yet -> fallback
        W = 1350
    H = 567
    sales_frame = Frame(window, width=W, height=H, bg='white')
    sales_frame.place(x=x, y=100)

    # ---- column widths: equal 10px gaps, middle a bit wider ----
    PAD = 10
    avail = W - 4 * PAD
    lw = int(avail * 0.31)      # left
    rw = int(avail * 0.32)      # right
    mw = avail - lw - rw        # middle (largest)
    lx = PAD
    mx = lx + lw + PAD
    rx = mx + mw + PAD          # right frame ends exactly at W - PAD

    cart = {}
    selected = {}
    tax_percent = get_tax()
    last_bill = {'text': '', 'path': '', 'qr': None}

    # ---------------- helpers ----------------
    def refresh_cart():
        cart_tree.delete(*cart_tree.get_children())
        amount = 0
        for it in cart.values():
            cart_tree.insert('', END, values=(it['id'], it['name'], it['price'], it['qty']))
            amount += it['price'] * it['qty']
        tax_amt = amount * tax_percent / 100
        net = amount + tax_amt
        cart_label.config(text=f'My Cart   Total Products: {len(cart)}')
        bill_amount_label.config(text=f'Bill Amount (₹)\n{amount:.2f}')
        net_pay_label.config(text=f'Net Pay (₹)\n{net:.2f}')
        return amount, tax_amt, net

    def clear_product_fields():
        selected.clear()
        name_var.set('')
        price_var.set('')
        qty_entry.delete(0, END)
        stock_label.config(text='In Stock: 0')
        product_tree.selection_remove(product_tree.selection())

    def select_product(event):
        sel = product_tree.selection()
        if not sel:
            return
        v = product_tree.item(sel[0])['values']
        if not v:
            return
        # v = id, name, price, discount %, discounted price, stock
        pid, name = v[0], v[1]
        mrp, discount, disc_price, stock = float(v[2]), float(v[3]), float(v[4]), int(v[5])
        selected.update(id=pid, name=name, mrp=mrp, discount=discount,
                        price=round(disc_price, 2), stock=stock)
        name_var.set(name)
        price_var.set(selected['price'])
        qty_entry.delete(0, END)
        qty_entry.insert(0, 1)
        stock_label.config(text=f'In Stock: {stock}')

    def select_cart_item(event):
        sel = cart_tree.selection()
        if not sel:
            return
        v = cart_tree.item(sel[0])['values']
        it = cart.get(int(v[0]))
        if not it:
            return
        selected.update(id=it['id'], name=it['name'], mrp=it['mrp'], discount=it['discount'],
                        price=it['price'], stock=it['stock'])
        name_var.set(it['name'])
        price_var.set(it['price'])
        qty_entry.delete(0, END)
        qty_entry.insert(0, it['qty'])
        stock_label.config(text=f"In Stock: {it['stock']}")

    def add_update_cart():
        if not selected:
            messagebox.showerror('Error', 'Select a product first')
            return
        q = qty_entry.get().strip()
        if not q.isdigit():
            messagebox.showerror('Error', 'Enter a valid quantity')
            return
        q = int(q)
        if q == 0:
            if selected['id'] in cart:
                if messagebox.askyesno('Confirm', 'Remove this product from cart?'):
                    del cart[selected['id']]
            else:
                messagebox.showerror('Error', 'Quantity must be at least 1')
                return
        elif q > selected['stock']:
            messagebox.showerror('Error', f"Only {selected['stock']} in stock")
            return
        else:
            cart[selected['id']] = dict(id=selected['id'], name=selected['name'],
                                        mrp=selected['mrp'], discount=selected['discount'],
                                        price=selected['price'], qty=q, stock=selected['stock'])
        refresh_cart()
        clear_product_fields()

    def make_qr(bill_no, cust_name, contact, items_text, net):
        """Create QR image for the bill. Returns (PhotoImage, path) or (None, None)."""
        if not QR_OK:
            return None, None
        try:
            data = (f'Bill No: {bill_no}\nDate: {time.strftime("%d/%m/%Y %I:%M %p")}\n'
                    f'Name: {cust_name}\nContact: {contact}\n'
                    f'Items: {items_text[:150]}\nNet Pay: Rs {net:.2f}')
            qr = qrcode.QRCode(box_size=3, border=2)
            qr.add_data(data)
            qr.make(fit=True)
            img = qr.make_image(fill_color='black', back_color='white')
            qr_path = os.path.join('bills', f'{bill_no}_qr.png')
            img.save(qr_path)
            return PhotoImage(file=qr_path), qr_path
        except Exception:
            return None, None

    def build_plain_bill(bill_no, cust_name, contact, date_str, amount, total_disc, tax_amt, net):
        """Fixed-width version saved to the .txt file (used for printing)."""
        w = 66
        L = [SHOP_NAME.center(w), SHOP_PHONE_ADDR.center(w), '=' * w,
             f'Customer Name: {cust_name}', f'Phone no: {contact}',
             f'Bill no: {bill_no}    Date: {date_str}', '=' * w,
             f'{"Name":<16}{"Qty":>4}{"Price":>10}{"Discount":>18}{"Final Price":>14}', '=' * w]
        for i in cart.values():
            d_amt = (i['mrp'] - i['price']) * i['qty']
            disc_txt = f"{i['discount']}%={d_amt:.1f}"
            L.append(f"{i['name'][:15]:<16}{i['qty']:>4}{i['mrp']:>10.1f}{disc_txt:>18}"
                     f"{i['price'] * i['qty']:>14.1f}")
        L += ['=' * w,
              f'{"Bill Amount":<30}{amount:>10.1f}',
              f'{"Total Discount":<30}{total_disc:>10.1f}',
              f'{"Tax":<30}{tax_amt:>10.1f}',
              f'{"Net Pay":<30}{net:>10.1f}', '=' * w]
        return '\n'.join(L)

    def show_bill_in_widget(bill_no, cust_name, contact, date_str, amount, total_disc,
                            tax_amt, net, photo):
        """Render the bill in the right-hand text area (reference layout)."""
        width_px = max(rw - 40, 300)
        # tab stops for the columns: Qty | Price | Discount | Final Price
        tabs = (str(int(width_px * 0.27)), str(int(width_px * 0.37)),
                str(int(width_px * 0.55)), str(int(width_px * 0.80)))
        bill_text.config(state=NORMAL, tabs=tabs)
        bill_text.delete(1.0, END)
        f = tkfont.Font(font=bill_text.cget('font'))
        sep = '=' * max(10, int(width_px / max(f.measure('='), 1)))

        bill_text.insert(END, f'{SHOP_NAME}\n', 'center')
        bill_text.insert(END, f'{SHOP_PHONE_ADDR}\n', 'center')
        bill_text.insert(END, sep + '\n')
        bill_text.insert(END, f'Customer Name: {cust_name}\n')
        bill_text.insert(END, f'Phone no: {contact}\n')
        bill_text.insert(END, f'Bill no: {bill_no}\t\t\tDate: {date_str}\n')
        bill_text.insert(END, sep + '\n')
        bill_text.insert(END, 'Name\tQty\tPrice\tDiscount\tFinal Price\n')
        bill_text.insert(END, sep + '\n\n')
        for i in cart.values():
            d_amt = (i['mrp'] - i['price']) * i['qty']
            bill_text.insert(END, f"{i['name'][:14]}\t{i['qty']}\t₹{i['mrp']:.1f}\t"
                                  f"{i['discount']}%={d_amt:.1f}\t₹{i['price'] * i['qty']:.1f}\n")
        bill_text.insert(END, sep + '\n')
        bill_text.insert(END, f'Bill Amount\t\t₹{amount:.1f}\n')
        bill_text.insert(END, f'Total Discount\t\t₹{total_disc:.1f}\n')
        bill_text.insert(END, f'Tax\t\t₹{tax_amt:.1f}\n')
        bill_text.insert(END, f'Net Pay\t\t₹{net:.1f}\n')
        bill_text.insert(END, sep + '\n\n')

        if photo:
            bill_text.insert(END, 'Scan for bill details\n', 'center')
            start = bill_text.index('end-1c linestart')
            bill_text.image_create(END, image=photo)
            bill_text.insert(END, '\n')
            bill_text.tag_add('center', start, 'end-1c')
        elif not QR_OK:
            bill_text.insert(END, '(QR not shown: run  pip install qrcode[pil])\n', 'center')
        bill_text.insert(END, '\nThank you, visit again!\n', 'center')
        bill_text.config(state=DISABLED)

    def generate_bill():
        if not cust_name_entry.get().strip() or not cust_contact_entry.get().strip():
            messagebox.showerror('Error', 'Customer details are required')
            return
        if not cart:
            messagebox.showerror('Error', 'Cart is empty')
            return
        amount, tax_amt, net = refresh_cart()
        total_disc = sum((i['mrp'] - i['price']) * i['qty'] for i in cart.values())
        cust_name = cust_name_entry.get().strip()
        contact = cust_contact_entry.get().strip()
        items_text = ', '.join(f"{i['name']} x{i['qty']}" for i in cart.values())

        bill_no = save_sale(cust_name, contact, items_text, amount, tax_percent, net, cart)
        if bill_no is None:
            return
        date_str = time.strftime('%d/%m/%Y')

        os.makedirs('bills', exist_ok=True)
        last_bill['text'] = build_plain_bill(bill_no, cust_name, contact, date_str,
                                             amount, total_disc, tax_amt, net)
        last_bill['path'] = os.path.join('bills', f'{bill_no}.txt')
        with open(last_bill['path'], 'w', encoding='utf-8') as f:
            f.write(last_bill['text'])

        # QR code
        photo, _ = make_qr(bill_no, cust_name, contact, items_text, net)
        last_bill['qr'] = photo          # keep reference so Tk doesn't discard the image

        show_bill_in_widget(bill_no, cust_name, contact, date_str, amount, total_disc,
                            tax_amt, net, photo)

        cart.clear()
        refresh_cart()
        clear_product_fields()
        load_products(product_tree)
        messagebox.showinfo('Success', f'Bill {bill_no} generated')

    def print_bill():
        if not last_bill['text']:
            messagebox.showerror('Error', 'Generate a bill first')
            return
        path = last_bill['path']
        try:
            os.startfile(path, 'print')       # Windows
        except Exception:
            messagebox.showinfo('Saved', f'Bill saved to {path}')

    def clear_all():
        cart.clear()
        refresh_cart()
        clear_product_fields()
        cust_name_entry.delete(0, END)
        cust_contact_entry.delete(0, END)
        bill_text.config(state=NORMAL)
        bill_text.delete(1.0, END)
        bill_text.config(state=DISABLED)
        last_bill['text'] = ''
        last_bill['qr'] = None
        calc_var.set('')
        search_entry.delete(0, END)
        load_products(product_tree)

    # ---------------- calculator ----------------
    calc_var = StringVar()

    def calc_press(ch):
        calc_var.set(calc_var.get() + ch)

    def calc_ans():
        expr = calc_var.get()
        if not re.fullmatch(r'[0-9+\-*/. ()]+', expr or 'x'):
            return
        try:
            res = eval(expr)
            res = int(res) if float(res).is_integer() else round(res, 4)
            calc_var.set(str(res))
        except Exception:
            calc_var.set('Error')

    # ================= LEFT : All Products =================
    left = Frame(sales_frame, bg='white', bd=1, relief=RIDGE)
    left.place(x=lx, y=5, width=lw, height=555)
    Label(left, text='All Products', font=(FONT, 15, 'bold'), bg=BLUE, fg='white').pack(fill=X)

    sf = Frame(left, bg='white')
    sf.pack(pady=8)
    Label(sf, text='Product Name', font=('arial', 11, 'bold'), bg='white').grid(row=0, column=0, padx=5)
    search_entry = Entry(sf, font=(FONT, 12), bg='lightyellow', width=14)
    search_entry.grid(row=0, column=1)
    Button(sf, text='Search', font=(FONT, 12, 'bold'), bg=BLUE, fg='white', width=8, cursor='hand2',
           command=lambda: load_products(product_tree, search_entry.get().strip())).grid(row=1, column=0, pady=8)
    Button(sf, text='Show All', font=(FONT, 12, 'bold'), bg=BLUE, fg='white', width=8, cursor='hand2',
           command=lambda: (search_entry.delete(0, END), load_products(product_tree))).grid(row=1, column=1)

    pf = Frame(left)
    pf.pack(fill=BOTH, expand=1, padx=5, pady=(0, 5))
    py = Scrollbar(pf, orient=VERTICAL)
    px = Scrollbar(pf, orient=HORIZONTAL)
    product_tree = ttk.Treeview(pf, columns=('id', 'name', 'price', 'discount', 'disc_price', 'qty'),
                                show='headings', yscrollcommand=py.set, xscrollcommand=px.set)
    py.pack(side=RIGHT, fill=Y)
    px.pack(side=BOTTOM, fill=X)
    py.config(command=product_tree.yview)
    px.config(command=product_tree.xview)
    product_tree.pack(fill=BOTH, expand=1)
    for col, text, w in (('id', 'ID', 30), ('name', 'Name', 95), ('price', 'Price', 55),
                         ('discount', 'Discount (%)', 80), ('disc_price', 'Discounted Price', 105),
                         ('qty', 'Qty', 40)):
        product_tree.heading(col, text=text)
        product_tree.column(col, width=w)
    product_tree.bind('<ButtonRelease-1>', select_product)

    # ================= MIDDLE =================
    mid = Frame(sales_frame, bg='white')
    mid.place(x=mx, y=5, width=mw, height=555)

    cust_frame = Frame(mid, bg='white', bd=1, relief=RIDGE)
    cust_frame.place(x=0, y=0, width=mw, height=75)
    Label(cust_frame, text='Customer Details', font=(FONT, 15, 'bold'), bg=BLUE, fg='white').pack(fill=X)
    Label(cust_frame, text='Name', font=('arial', 11, 'bold'), bg='white').place(x=10, y=40)
    cust_name_entry = Entry(cust_frame, font=(FONT, 12), bg='lightyellow', width=13)
    cust_name_entry.place(x=60, y=40)
    Label(cust_frame, text='Contact No.', font=('arial', 11, 'bold'), bg='white').place(x=mw // 2 + 5, y=40)
    cust_contact_entry = Entry(cust_frame, font=(FONT, 12), bg='lightyellow', width=11)
    cust_contact_entry.place(x=mw // 2 + 105, y=40)

    # calculator (left half) + cart (right half)
    cw = (mw - 5) // 2
    calc = Frame(mid, bg='white', bd=1, relief=RIDGE)
    calc.place(x=0, y=85, width=cw, height=300)
    Label(calc, text='Calculator', font=('arial', 13, 'bold'), bg='white').pack()
    Entry(calc, textvariable=calc_var, font=('arial', 14, 'bold'), justify=RIGHT, bd=2,
          relief=GROOVE).pack(fill=X, padx=3)
    kb = Frame(calc, bg='white')
    kb.pack()
    keys = [('7', '8', '9', '+'), ('4', '5', '6', '-'), ('1', '2', '3', '*'), ('Ans', 'Clear', '0', '/')]
    for r, row in enumerate(keys):
        for c, k in enumerate(row):
            if k == 'Ans':
                cmd = calc_ans
            elif k == 'Clear':
                cmd = lambda: calc_var.set('')
            else:
                cmd = lambda k=k: calc_press(k)
            Button(kb, text=k, font=('arial', 11, 'bold'), width=5, height=2, bd=1,
                   cursor='hand2', command=cmd).grid(row=r, column=c)

    cart_frame = Frame(mid, bg='white', bd=1, relief=RIDGE)
    cart_frame.place(x=cw + 5, y=85, width=mw - cw - 5, height=300)
    cart_label = Label(cart_frame, text='My Cart   Total Products: 0', font=('arial', 10, 'bold'), bg='white')
    cart_label.pack()
    cy = Scrollbar(cart_frame, orient=VERTICAL)
    cx = Scrollbar(cart_frame, orient=HORIZONTAL)
    cart_tree = ttk.Treeview(cart_frame, columns=('id', 'name', 'price', 'qty'), show='headings',
                             yscrollcommand=cy.set, xscrollcommand=cx.set)
    cy.pack(side=RIGHT, fill=Y)
    cx.pack(side=BOTTOM, fill=X)
    cy.config(command=cart_tree.yview)
    cx.config(command=cart_tree.xview)
    cart_tree.pack(fill=BOTH, expand=1)
    for col, text, w in (('id', 'ID', 30), ('name', 'Name', 90), ('price', 'Price', 60), ('qty', 'Qty', 40)):
        cart_tree.heading(col, text=text)
        cart_tree.column(col, width=w)
    cart_tree.bind('<ButtonRelease-1>', select_cart_item)

    # product entry
    prod = Frame(mid, bg='white', bd=1, relief=RIDGE)
    prod.place(x=0, y=395, width=mw, height=160)
    name_var, price_var = StringVar(), StringVar()
    c2, c3 = mw // 3 + 15, 2 * mw // 3 + 5
    Label(prod, text='Product Name', font=('arial', 11, 'bold'), bg='white').place(x=10, y=15)
    Label(prod, text='Price', font=('arial', 11, 'bold'), bg='white').place(x=c2, y=15)
    Label(prod, text='Quantity', font=('arial', 11, 'bold'), bg='white').place(x=c3, y=15)
    Entry(prod, textvariable=name_var, font=(FONT, 12), state='readonly', width=13).place(x=10, y=45)
    Entry(prod, textvariable=price_var, font=(FONT, 12), state='readonly', width=11).place(x=c2, y=45)
    qty_entry = Entry(prod, font=(FONT, 12), bg='lightyellow', width=11)
    qty_entry.place(x=c3, y=45)
    stock_label = Label(prod, text='In Stock: 0', font=('arial', 11, 'bold'), bg='white')
    stock_label.place(x=20, y=108)
    Button(prod, text='Clear', font=(FONT, 12, 'bold'), bg=BLUE, fg='white', width=9, cursor='hand2',
           command=clear_product_fields).place(x=mw - 290, y=103)
    Button(prod, text='Add/Update Cart', font=(FONT, 12, 'bold'), bg=BLUE, fg='white', width=14, cursor='hand2',
           command=add_update_cart).place(x=mw - 170, y=103)

    # ================= RIGHT : Billing =================
    right = Frame(sales_frame, bg='white', bd=1, relief=RIDGE)
    right.place(x=rx, y=5, width=rw, height=555)
    Label(right, text='Customer Billing Area', font=(FONT, 15, 'bold'), bg=BLUE, fg='white').pack(fill=X)
    bf = Frame(right)
    bf.place(x=0, y=32, width=rw - 2, height=400)
    by = Scrollbar(bf, orient=VERTICAL)
    bill_text = Text(bf, bg='lightyellow', font=(FONT, 10), yscrollcommand=by.set, state=DISABLED,
                     wrap=NONE, padx=8, pady=6)
    bill_text.tag_configure('center', justify='center')
    by.pack(side=RIGHT, fill=Y)
    by.config(command=bill_text.yview)
    bill_text.pack(fill=BOTH, expand=1)

    bw = (rw - 2 - 20) // 3
    lbl = dict(font=('arial', 10, 'bold'), bg=GREY, fg='white')
    bill_amount_label = Label(right, text='Bill Amount (₹)\n0', **lbl)
    bill_amount_label.place(x=5, y=442, width=bw, height=52)
    Label(right, text=f'Tax\n{tax_percent}%', **lbl).place(x=10 + bw, y=442, width=bw, height=52)
    net_pay_label = Label(right, text='Net Pay (₹)\n0', **lbl)
    net_pay_label.place(x=15 + 2 * bw, y=442, width=bw, height=52)

    btn = dict(font=(FONT, 12, 'bold'), bg=BLUE, fg='white', cursor='hand2')
    Button(right, text='Generate Bill', command=generate_bill, **btn).place(x=5, y=500, width=bw, height=48)
    Button(right, text='Print', command=print_bill, **btn).place(x=10 + bw, y=500, width=bw, height=48)
    Button(right, text='Clear All', command=clear_all, **btn).place(x=15 + 2 * bw, y=500, width=bw, height=48)

    back_image = PhotoImage(file='back-arrow.png')
    Button(sales_frame, image=back_image, bd=0, cursor='hand2', bg='white',
           command=sales_frame.place_forget).place(x=1050, y=-2, width=0, height=0)

    load_products(product_tree)
    return sales_frame