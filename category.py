from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from employees import connect_database


def select_data(id_entry,category_name_entry,description_text,treeview):
    index=treeview.selection()
    content=treeview.item(index)
    actual_content=content['values']
    id_entry.delete(0,END)
    category_name_entry.delete(0,END)
    description_text.delete(1.0,END)
    
    id_entry.insert(0,actual_content[0])
    category_name_entry.insert(0,actual_content[1])
    description_text.insert(1.0,actual_content[2])


def update_supplier(id,name,description,treeview):
    index=treeview.selection()
    if not index:
        messagebox.showerror('Error','No row is selected')
        return
    try:
        cursor,connection=connect_database()
        if not cursor or not connection:
            return
        cursor.execute('use inventory_system')
        cursor.execute('SELECT * from category_data WHERE id=%s',id)
        current_data=cursor.fetchone()
        current_data=current_data[1:]
        print(current_data)
        
        new_data=(name,description)
        print(new_data)
        
        if current_data==new_data:
            messagebox.showinfo('Info','No changes detected')
            return
        
        cursor.execute('UPDATE category_data SET name=%s,description=%s WHERE id=%s',(name,description,id))
        connection.commit()
        messagebox.showinfo('Info','Data is updated')
        treeview_data(treeview)
    except Exception as e:
            messagebox.showerror('Erro',f'Error due to {e}')
    finally:
        cursor.close()
        connection.close()


def delete_category(treeview):
    index=treeview.selection()
    content=treeview.item(index)
    row=content['values']
    id=row[0]
    if not index:
        messagebox.showerror('Error','No row is selected')
        return
    try:
        cursor,connection=connect_database()
        if not cursor or not connection:
            return
        cursor.execute('use inventory_system')
        cursor.execute('DELETE FROM category_data WHERE id=%s',id)
        connection.commit()
        treeview_data(treeview)
        messagebox.showinfo('Info','Record is deleted')
    except Exception as e:
        messagebox.showerror('Erro',f'Error due to {e}')
    finally:
        cursor.close()
        connection.close()
    


def clear(id_entry,category_name_entry,description_text):
    id_entry.delete(0,END)
    category_name_entry.delete(0,END)
    description_text.delete(1.0,END)
    
    
def treeview_data(treeview):
    cursor,connection=connect_database()
    if not cursor or not connection:
        return
    try:
        cursor.execute('use inventory_system')
        cursor.execute('Select * from category_data')
        records=cursor.fetchall()
        treeview.delete(*treeview.get_children())
        for record in records:
            treeview.insert('',END,values=record)
    except Exception as e:
            messagebox.showerror('Error',f'Error due to {e}')
    finally:
        cursor.close()
        connection.close()
        


def add_category(id,name,description,treeview):
    if id=='' or name=='' or description=='':
        messagebox.showerror('Error','All fields are required')
    else:
        cursor,connection=connect_database()
        if not cursor or not connection:
            return
        try:
            cursor.execute('use inventory_system')
            cursor.execute('CREATE TABLE IF NOT EXISTS category_data (id INT PRIMARY KEY, name VARCHAR(100),'
                                    'description TEXT)')
            cursor.execute('SELECT * from category_data WHERE id=%s',id)
            if cursor.fetchone():
                messagebox.showerror('Error','Id already exists')
                return
            cursor.execute('INSERT INTO category_data VALUES(%s,%s,%s)',(id,name,description))
            connection.commit()
            messagebox.showinfo('Info','Data is inserted')
            treeview_data(treeview)
        except Exception as e:
                messagebox.showerror('Erro',f'Error due to {e}')
        finally:
            cursor.close()
            connection.close()
    

def category_form(window):
    global back_image,logo
    category_frame=Frame(window,width=1090,height=567,bg='white')
    category_frame.place(x=180,y=100)
    
    heading_label=Label(category_frame,text='Manage Category Details',font=('times new roman',16,'bold'),bg='#0f4d7d',fg='white')
    heading_label.place(x=0,y=0,relwidth=1)
    
    back_image=PhotoImage(file='back-arrow.png')
    back_button=Button(category_frame,image=back_image,bd=0,cursor='hand2',bg='white',
                           command=lambda: category_frame.place_forget())
    back_button.place(x=10,y=30)
    
    logo=PhotoImage(file='folder-management.png')
    label=Label(category_frame,image=logo,bg='white')
    label.place(x=30,y=100)
    
    details_frame=Frame(category_frame,bg='white')
    details_frame.place(x=500,y=60)
    
    id_label=Label(details_frame,text='ID',font=('times new roman',14,'bold'),bg='white')
    id_label.grid(row=0,column=0,padx=20,sticky='w')
    id_entry=Entry(details_frame,font=('times new roman',14,'bold'),bd=2)
    id_entry.grid(row=0,column=1,sticky='w')
    
    category_name_label=Label(details_frame,text='Category Name',font=('times new roman',14,'bold'),bg='white')
    category_name_label.grid(row=1,column=0,padx=20,sticky='w')
    category_name_entry=Entry(details_frame,font=('times new roman',14,'bold'),bd=2)
    category_name_entry.grid(row=1,column=1,pady=20,sticky='w')
    
    description_label=Label(details_frame,text='Description',font=('times new roman',14,'bold'),bg='white')
    description_label.grid(row=2,column=0,padx=20,sticky='nw')
    description_text=Text(details_frame,width=45,height=7,bd=2)
    description_text.grid(row=2,column=1)
    
    button_frame=Frame(category_frame,bg='white')
    button_frame.place(x=630,y=280)
    
    add_button=Button(button_frame,text='Save',font=('times new roman',14),width=8,cursor='hand2',
                                     fg='white',bg='#0f4d7d',command=lambda:add_category(id_entry.get(),category_name_entry.get(),description_text.get(1.0,END).strip(),treeview))
    add_button.grid(row=0,column=0,padx=20)
    
    update_button=Button(button_frame,text='Update',font=('times new roman',14),width=8,cursor='hand2',
                                         fg='white',bg='#0f4d7d',command=lambda:update_supplier(id_entry.get(),category_name_entry.get(),
                                                                                         description_text.get(1.0,END).strip(),treeview))
    update_button.grid(row=0,column=1)
    
    delete_button=Button(button_frame,text='Delete',font=('times new roman',14),width=8,cursor='hand2',
                                         fg='white',bg='#0f4d7d',command=lambda:delete_category(treeview))
    delete_button.grid(row=0,column=2,padx=20)
    
    clear_button=Button(button_frame,text='Clear',font=('times new roman',14),width=8,cursor='hand2',
                                             fg='white',bg='#0f4d7d',command=lambda:clear(id_entry,category_name_entry,description_text))
    clear_button.grid(row=0,column=3)
    
    
    treeview_frame=Frame(category_frame,bg='lightyellow')
    treeview_frame.place(x=530,y=340,height=200,width=550)
    
    scrolly=Scrollbar(treeview_frame,orient=VERTICAL)
    scrollx=Scrollbar(treeview_frame,orient=HORIZONTAL)
        
    treeview=ttk.Treeview(treeview_frame,columns=('id','name','description'),show='headings',
                              yscrollcommand=scrolly.set,xscrollcommand=scrollx.set)
    scrolly.pack(side=RIGHT,fill=Y)
    scrollx.pack(side=BOTTOM,fill=X)
    scrollx.config(command=treeview.xview)
    scrolly.config(command=treeview.yview)
    treeview.pack(fill=BOTH,expand=1)
    treeview.heading('id',text='ID')
    treeview.heading('name',text='Category Name')
    treeview.heading('description',text='Description')
    
    treeview.column('id',width=80)
    treeview.column('name',width=160)
    treeview.column('description',width=300)
    treeview_data(treeview)
    
    treeview.bind('<ButtonRelease-1>',lambda event: select_data(id_entry,category_name_entry,description_text,treeview))
    
    return category_frame