# 🏪 Inventory Management & Billing System

A desktop-based **Inventory Management & Billing System** developed using **Python, Tkinter, and MySQL**. The application helps manage products, categories, suppliers, employees, inventory, billing, taxes, and sales reports through a user-friendly graphical interface.

## 📌 Overview

This project provides a centralized system for handling day-to-day inventory and sales operations.

### Core capabilities

- Role-based **Admin and Employee login**
- Employee, supplier, category, and product management
- Inventory and stock tracking
- Product discount calculation
- Customer billing and invoice generation
- Tax configuration
- Automatic stock updates after sales
- Sales analysis and visualization
- CSV report export
- QR-code support for invoices

---

## ✨ Features

### 🔐 Authentication

- Employee ID and password login
- Admin and Employee roles
- User registration
- Admin authorization for Admin registration
- Password confirmation and input validation
- Logout functionality

### 📊 Admin Dashboard

The dashboard provides an overview of the inventory system with live counts for:

- Employees
- Suppliers
- Categories
- Products
- Sales

Administrators can access all management modules from a single interface.

### 📦 Inventory Management

Manage products with information such as:

- Product ID
- Category
- Supplier
- Product name
- Price
- Discount
- Discounted price
- Quantity
- Stock status

Products can be added, updated, deleted, searched, and filtered.

### 🚚 Supplier & Category Management

Manage supplier and category information using standard CRUD operations:

- Create
- Read
- Update
- Delete
- Search
- Clear form data

### 🧾 Billing

The billing module provides a simple point-of-sale workflow:

1. Search available products
2. Select product and quantity
3. Add items to cart
4. Calculate totals
5. Apply tax
6. Generate invoice
7. Save billing information
8. Update inventory stock

### 💰 Tax Management

Administrators can configure the tax percentage used during billing. The configured value is stored in MySQL and automatically applied to new bills.

### 📈 Sales Reports

The sales module provides:

- Invoice search
- Date-based filtering
- Sales sorting
- Total sales calculation
- Product-wise sales analysis
- Sales visualization
- CSV report export

### 📱 QR Code

The billing system supports QR-code generation for invoice information.

---

## 🛠️ Tech Stack

| Technology | Usage |
|---|---|
| **Python** | Application logic |
| **Tkinter** | Desktop GUI |
| **MySQL** | Database |
| **PyMySQL** | MySQL connectivity |
| **tkcalendar** | Date selection |
| **Matplotlib** | Sales visualization |
| **QRCode** | Invoice QR generation |
| **Pillow** | Image/QR handling |
| **CSV** | Report export |

---

## 🏗️ System Architecture

                         ┌───────────────┐
                         │     Login     │
                         └───────┬───────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                 Admin                    Employee
                    │                         │
                    ▼                         ▼
             Admin Dashboard              Billing
                    │                         │
       ┌────────────┼────────────┐            │
       ▼            ▼            ▼            ▼
   Employees    Suppliers    Categories    Products
                                  │            │
                                  └─────┬──────┘
                                        ▼
                                  Inventory
                                        │
                                        ▼
                                     Billing
                                        │
                                        ▼
                                   Sales Data
                                        │
                              ┌─────────┴─────────┐
                              ▼                   ▼
                           Reports             Graphs
                              │
                              ▼
                         CSV Export
```

---

## 🗄️ Database

The application uses a MySQL database named:

```
inventory_system
```

### Main Tables

```
inventory_system
│
├── employee_data
├── supplier_data
├── category_data
├── product_data
├── sales_data
├── sale_items
└── tax_table
```

The application initializes the required database tables when the system starts.

---

## 📁 Project Structure

```text
Inventory-Management-System/
│
├── main.py
├── dashboard.py
├── employees.py
├── supplier.py
├── category.py
├── product.py
├── sales.py
├── billing.py
│
├── bills/
│
├── inventory.png
├── checklist.png
├── back-arrow.png
├── folder-management.png
├── man.png
├── supplier.png
├── categorization.png
├── package.png
├── increase.png
├── tax.png
├── logout.png
├── staff.png
├── total_suppliers.png
├── market-segment.png
├── products.png
├── trend.png
│
└── README.md

---

## ⚙️ Requirements

- Python 3.9+
- MySQL Server
- Git

### Python Dependencies

pip install pymysql tkcalendar matplotlib qrcode pillow

---

## 🔄 Application Workflow

```text
Login
  │
  ├── Admin
  │     │
  │     ├── Employee Management
  │     ├── Supplier Management
  │     ├── Category Management
  │     ├── Product Management
  │     ├── Tax Configuration
  │     └── Sales Reports
  │
  └── Employee
        │
        └── Billing
              │
              ├── Product Selection
              ├── Cart
              ├── Tax Calculation
              ├── Invoice
              └── Stock Update

---

## 👥 User Roles

| Module               | Admin | Employee |

| Login                |   ✅  |   ✅   |
| Registration         |   ✅  |   ✅   |
| Employee Management  |   ✅  |   ❌   |
| Supplier Management  |   ✅  |   ❌   |
| Category Management  |   ✅  |   ❌   |
| Product Management   |   ✅  |   ❌   |
| Tax Configuration    |   ✅  |   ❌   |
| Billing              |   ✅  |   ✅   |
| Sales Reports        |   ✅  |   ❌   |
| Logout               |   ✅  |   ✅   |

---

## 🔮 Future Enhancements

- Secure password hashing
- Environment-based database configuration
- Low-stock notifications
- Barcode scanning
- PDF invoice generation
- Email invoice delivery
- Advanced sales analytics
- Power BI integration
- More granular user permissions
- Modern responsive UI

---

## 🔒 Security

**Do not upload real database credentials or passwords to GitHub.**

Use environment variables for sensitive configuration:

import os

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

Add sensitive files such as `.env` to `.gitignore`.

---

## 👨‍💻 Author

**R Hari Prasanth**

Electronics and Communication Engineering Graduate

- LinkedIn: www.linkedin.com/in/r-hari-prasanth-54369a376
- GitHub:   https://github.com/Hari22346

---

## ⭐ Project

If you find this project useful, consider giving the repository a **star ⭐**.

---

## 📄 License

This project is created for **educational and portfolio purposes**.
