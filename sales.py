from tkinter import *
from tkinter import ttk
from tkinter import messagebox, filedialog
from employees import connect_database
import os, re, csv

try:
    import qrcode
    from PIL import ImageTk
    QR_OK = True
except ImportError:
    QR_OK = False

try:
    import matplotlib
    matplotlib.use('TkAgg')
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator
    MPL_OK = True
except ImportError:
    MPL_OK = False

FONT = 'times new roman'
BLUE = '#0f4d7d'
BILL_DIR = 'bills'
DATE_DEFAULT = 'Select Date to View Sales'
SORT_DEFAULT = 'Select Sorting Option'
SORT_OPTIONS = {
    'Quantity Sold (High to Low)': 'qty DESC',
    'Quantity Sold (Low to High)': 'qty ASC',
    'Sales Amount (High to Low)': 'amount DESC',
    'Sales Amount (Low to High)': 'amount ASC',
    'Product Name (A-Z)': 'product_name ASC',
}


def ensure_table(cursor):
    cursor.execute('use inventory_system')
    cursor.execute('CREATE TABLE IF NOT EXISTS sale_items (id INT AUTO_INCREMENT PRIMARY KEY, bill_no INT, '
                   'sale_date VARCHAR(20), product_id INT, product_name VARCHAR(100), qty INT, '
                   'price DECIMAL(10,2), total DECIMAL(10,2))')


def fetch_dates():
    cursor, connection = connect_database()
    if not cursor or not connection:
        return []
    try:
        ensure_table(cursor)
        cursor.execute('SELECT sale_date FROM sale_items GROUP BY sale_date ORDER BY MAX(id) DESC')
        return [r[0] for r in cursor.fetchall()]
    except Exception as e:
        messagebox.showerror('Error', f'Error due to {e}')
        return []
    finally:
        cursor.close()
        connection.close()


def fetch_report(date=None, order='amount DESC'):
    cursor, connection = connect_database()
    if not cursor or not connection:
        return []
    try:
        ensure_table(cursor)
        where, args = '', ()
        if date:
            where, args = 'WHERE sale_date=%s', (date,)
        cursor.execute(f'SELECT product_name, SUM(qty) AS qty, SUM(total) AS amount FROM sale_items '
                       f'{where} GROUP BY product_name ORDER BY {order}', args)
        return cursor.fetchall()
    except Exception as e:
        messagebox.showerror('Error', f'Error due to {e}')
        return []
    finally:
        cursor.close()
        connection.close()


def sales_form(window):
    global back_image
    sales_frame = Frame(window, width=1090, height=567, bg='white')
    sales_frame.place(x=180, y=100)

    Label(sales_frame, text='Customer Bill and Sales Analysis', font=(FONT, 16, 'bold'),
          bg=BLUE, fg='white').place(x=0, y=0, relwidth=1)
    back_image = PhotoImage(file='back-arrow.png')
    Button(sales_frame, image=back_image, bd=0, cursor='hand2', bg='white',
           command=sales_frame.place_forget).place(x=10, y=30)

    qr_ref = {}   # keep reference so Tkinter does not garbage-collect the QR image
    graph = {'fig': None}   # keeps the currently open sales graph window

    # ---------------- bill list / bill area ----------------
    def load_bill_list():
        listbox.delete(0, END)
        if not os.path.isdir(BILL_DIR):
            return
        files = [f for f in os.listdir(BILL_DIR) if f.endswith('.txt')]
        files.sort(key=lambda f: int(f[:-4]) if f[:-4].isdigit() else 0)
        for f in files:
            listbox.insert(END, f)

    def show_bill(event=None):
        sel = listbox.curselection()
        if not sel:
            return
        name = listbox.get(sel[0])
        try:
            with open(os.path.join(BILL_DIR, name), encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            messagebox.showerror('Error', f'Cannot open bill: {e}')
            return
        bill_text.config(state=NORMAL)
        bill_text.delete(1.0, END)
        bill_text.insert(END, content + '\n\n')
        net = re.search(r'Net Pay\s+([\d.]+)', content)
        summary = f'Invoice: {name[:-4]} | Net Pay: Rs {net.group(1) if net else "-"}'
        if QR_OK:
            img = qrcode.make(summary).get_image().resize((130, 130))
            qr_ref['img'] = ImageTk.PhotoImage(img)
            bill_text.image_create(END, image=qr_ref['img'])
            bill_text.insert(END, '\n')
            bill_text.insert(END, 'Scan the QR code for the invoice summary.', 'center')
        else:
            bill_text.insert(END, '(Install "qrcode" and "pillow" to show the QR code)', 'center')
        bill_text.tag_add('center', 'end-3l', END)
        bill_text.config(state=DISABLED)

    def search_bill():
        no = invoice_entry.get().strip()
        if no == '':
            messagebox.showerror('Error', 'Please enter invoice No.')
            return
        names = listbox.get(0, END)
        if f'{no}.txt' not in names:
            messagebox.showerror('Error', 'No bill found')
            return
        idx = names.index(f'{no}.txt')
        listbox.selection_clear(0, END)
        listbox.selection_set(idx)
        listbox.see(idx)
        show_bill()

    # ---------------- graph ----------------
    def graph_is_open():
        fig = graph['fig']
        return fig is not None and plt.fignum_exists(fig.number)

    def close_graph():
        if MPL_OK and graph_is_open():
            plt.close(graph['fig'])
        graph['fig'] = None

    def draw_graph(rows, date):
        """Draw (or redraw) the bar chart: product name vs total quantity sold."""
        if not MPL_OK:
            messagebox.showerror('Error', 'Install matplotlib to view the graph:\n\npip install matplotlib')
            return
        if not rows:
            close_graph()
            return
        try:
            names = [str(r[0]) for r in rows]
            qtys = [int(r[1]) for r in rows]

            if graph_is_open():
                fig = graph['fig']
                fig.clf()
            else:
                fig = plt.figure(figsize=(10, 5.5))
                graph['fig'] = fig
            ax = fig.add_subplot(111)

            bars = ax.bar(names, qtys, color='blue')
            for bar, q in zip(bars, qtys):          # quantity label on top of each bar
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), str(q),
                        ha='center', va='bottom', fontsize=9)

            title = 'Sales Report' + (f' - {date}' if date else ' - All Dates')
            ax.set_title(title)
            ax.set_xlabel('Product Name')
            ax.set_ylabel('Total Quantity Sold')
            ax.yaxis.set_major_locator(MaxNLocator(integer=True))
            ax.set_ylim(0, max(qtys) * 1.12)
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
            fig.tight_layout()
            fig.canvas.draw_idle()
            plt.show(block=False)
            try:
                fig.canvas.manager.window.lift()    # bring graph window to the front
            except Exception:
                pass
        except Exception as e:
            messagebox.showerror('Error', f'Cannot draw graph: {e}')

    # ---------------- analysis ----------------
    def load_report():
        """Fill the table using the selected date / sort option. Returns (rows, date)."""
        date = date_combobox.get()
        date = None if date in (DATE_DEFAULT, 'All') else date
        order = SORT_OPTIONS.get(sort_combobox.get(), 'amount DESC')
        rows = fetch_report(date, order)
        treeview.delete(*treeview.get_children())
        total = 0
        for name, qty, amount in rows:
            treeview.insert('', END, values=(name, int(qty), f'{float(amount):.2f}'))
            total += float(amount)
        total_label.config(text=f'Total Sales Amount: ₹ {total:.2f}')
        return rows, date

    def on_filter_change(event=None):
        """Date / sort changed: refresh table, and refresh the graph if it is already open."""
        rows, date = load_report()
        if MPL_OK and graph_is_open():
            draw_graph(rows, date)

    def show_report():
        """Show Report button: refresh table and open the sales graph."""
        rows, date = load_report()
        if not rows:
            close_graph()
            messagebox.showinfo('No Data', 'No sales found for the selected date.')
            return
        draw_graph(rows, date)

    def export_report():
        rows = [treeview.item(i)['values'] for i in treeview.get_children()]
        if not rows:
            messagebox.showerror('Error', 'No data to export. Click Show Report first')
            return
        path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV file', '*.csv')],
                                            initialfile='sales_report.csv')
        if not path:
            return
        try:
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                w = csv.writer(f)
                w.writerow(['Product Name', 'Quantity Sold', 'Total Sales Amount (Rs)'])
                w.writerows(rows)
                w.writerow([])
                w.writerow(['', 'Total', total_label.cget('text').split('₹')[1].strip()])
            messagebox.showinfo('Success', 'Report exported successfully')
        except Exception as e:
            messagebox.showerror('Error', f'Error due to {e}')

    def reset():
        invoice_entry.delete(0, END)
        date_combobox.config(values=['All'] + fetch_dates())
        date_combobox.set(DATE_DEFAULT)
        sort_combobox.set(SORT_DEFAULT)
        bill_text.config(state=NORMAL)
        bill_text.delete(1.0, END)
        bill_text.config(state=DISABLED)
        load_bill_list()
        close_graph()
        load_report()

    # ---------------- left: bill list ----------------
    lf = Frame(sales_frame, bg='white')
    lf.place(x=20, y=100, width=175, height=330)
    ly = Scrollbar(lf, orient=VERTICAL)
    listbox = Listbox(lf, font=(FONT, 12), yscrollcommand=ly.set, activestyle='none')
    ly.pack(side=RIGHT, fill=Y)
    ly.config(command=listbox.yview)
    listbox.pack(fill=BOTH, expand=1)
    listbox.bind('<ButtonRelease-1>', show_bill)

    # ---------------- middle: invoice search + bill area ----------------
    Label(sales_frame, text='Invoice No.', font=(FONT, 12, 'bold'), bg='white').place(x=215, y=55)
    invoice_entry = Entry(sales_frame, font=(FONT, 12), bg='lightyellow', width=11)
    invoice_entry.place(x=300, y=55)
    Button(sales_frame, text='Search Bill', font=(FONT, 11, 'bold'), bg=BLUE, fg='white', cursor='hand2',
           width=10, command=search_bill).place(x=410, y=51)

    bf = Frame(sales_frame, bd=2, relief=RIDGE)
    bf.place(x=215, y=100, width=345, height=330)
    Label(bf, text='Customer Bill Area', font=(FONT, 13, 'bold'), bg=BLUE, fg='white').pack(fill=X)
    by = Scrollbar(bf, orient=VERTICAL)
    bill_text = Text(bf, font=('courier new', 9), bg='white', yscrollcommand=by.set, state=DISABLED, wrap=NONE)
    by.pack(side=RIGHT, fill=Y)
    by.config(command=bill_text.yview)
    bill_text.pack(fill=BOTH, expand=1)
    bill_text.tag_configure('center', justify='center')

    # ---------------- right: analysis ----------------
    date_combobox = ttk.Combobox(sales_frame, font=(FONT, 12), width=28, state='readonly')
    date_combobox.set(DATE_DEFAULT)
    date_combobox.place(x=600, y=60)
    date_combobox.bind('<<ComboboxSelected>>', on_filter_change)

    sort_combobox = ttk.Combobox(sales_frame, font=(FONT, 12), width=28, state='readonly',
                                 values=list(SORT_OPTIONS))
    sort_combobox.set(SORT_DEFAULT)
    sort_combobox.place(x=600, y=100)
    sort_combobox.bind('<<ComboboxSelected>>', on_filter_change)

    total_label = Label(sales_frame, text='Total Sales Amount: ₹ 0.00', font=(FONT, 13, 'bold'), bg='white')
    total_label.place(x=600, y=140)

    tf = Frame(sales_frame)
    tf.place(x=600, y=175, width=470, height=255)
    ty = Scrollbar(tf, orient=VERTICAL)
    tx = Scrollbar(tf, orient=HORIZONTAL)
    treeview = ttk.Treeview(tf, columns=('product', 'qty', 'amount'), show='headings',
                            yscrollcommand=ty.set, xscrollcommand=tx.set)
    ty.pack(side=RIGHT, fill=Y)
    tx.pack(side=BOTTOM, fill=X)
    ty.config(command=treeview.yview)
    tx.config(command=treeview.xview)
    treeview.pack(fill=BOTH, expand=1)
    treeview.heading('product', text='Product Name')
    treeview.heading('qty', text='Quantity Sold')
    treeview.heading('amount', text='Total Sales Amount (₹)')
    treeview.column('product', width=190)
    treeview.column('qty', width=100, anchor='center')
    treeview.column('amount', width=150, anchor='e')

    # ---------------- bottom buttons ----------------
    bb = Frame(sales_frame, bg='white')
    bb.place(x=420, y=480)
    btn = dict(font=(FONT, 12, 'bold'), bg=BLUE, fg='white', width=11, cursor='hand2')
    Button(bb, text='Export', command=export_report, **btn).grid(row=0, column=0, padx=15)
    Button(bb, text='Show Report', command=show_report, **btn).grid(row=0, column=1, padx=15)
    Button(bb, text='Reset', command=reset, **btn).grid(row=0, column=2, padx=15)

    sales_frame.bind('<Destroy>', lambda e: close_graph() if e.widget is sales_frame else None)

    reset()
    return sales_frame