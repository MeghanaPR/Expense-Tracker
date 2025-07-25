import sqlite3
import tkinter as tk
from tkinter import *
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk  # Import PIL modules
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Function to register a new user
def register():
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')
    cursor.execute('''
        INSERT INTO users (username, password) VALUES (?, ?)
    ''', (username_entry.get(), password_entry.get()))
    conn.commit()
    conn.close()
    messagebox.showinfo("Registration", "Registration successful")

# Function to login an existing user
def login():
    global current_user_id
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id FROM users WHERE username=? AND password=?
    ''', (username_entry.get(), password_entry.get()))
    user = cursor.fetchone()
    conn.close()
    clear_fields()
    if user:
        current_user_id = user[0]
        login_register_frame.pack_forget()
        expense_frame.pack(pady=20)
    else:
        messagebox.showerror("Login", "Invalid username or password")

# Function to add an expense
def add_expense(user_id):
    # Check if all required fields are filled out
    if not date_entry.get() or not description_entry.get() or not payee_entry.get() or not mode_of_payment_combobox.get() or not amount_entry.get():
        messagebox.showerror("Error", "All fields must be filled out.")
        return
    
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            date TEXT,
            description TEXT,
            payee TEXT,
            mode_of_payment TEXT,
            amount REAL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    cursor.execute('''
        INSERT INTO expenses (user_id, date, description, payee, mode_of_payment, amount)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, date_entry.get(), description_entry.get(), payee_entry.get(), mode_of_payment_combobox.get(), amount_entry.get()))
    conn.commit()
    conn.close()
    clear_fields()
    messagebox.showinfo("Expense Added", "Expense added successfully")
    view_expenses(user_id)

# Function to update expense
def update_expense(user_id):
    try:
        selected_item = expenses_list.selection()[0]  # Get selected item
        values = expenses_list.item(selected_item, 'values')  # Get the expense values

        # Extract the id of the selected expense from the database
        conn = sqlite3.connect('expenses.db')
        c = conn.cursor()
        c.execute('''
            SELECT id FROM expenses WHERE user_id=? AND date=? AND description=? AND payee=? AND mode_of_payment=? AND amount=?
        ''', (user_id, values[0], values[1], values[2], values[3], values[4]))
        expense_id = c.fetchone()[0]

        # Update the selected expense in the database
        c.execute('''
            UPDATE expenses
            SET date=?, description=?, payee=?, mode_of_payment=?, amount=?
            WHERE id=?
        ''', (date_entry.get(), description_entry.get(), payee_entry.get(), mode_of_payment_combobox.get(), amount_entry.get(), expense_id))
        conn.commit()
        conn.close()
        messagebox.showinfo("Expense Updated", "Expense updated successfully")
        view_expenses(user_id)  # Refresh the list after updating an expense

    except IndexError:
        messagebox.showerror("Error", "Please select an expense to update.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to update expense: {e}")

# Function to remove expense
def remove_expense(user_id):
    try:
        selected_item = expenses_list.selection()[0]  # Get selected item
        values = expenses_list.item(selected_item, 'values')  # Get the expense values
        
        conn = sqlite3.connect('expenses.db')
        c = conn.cursor()
        c.execute('''
            DELETE FROM expenses
            WHERE date=? AND description=? AND payee=? AND mode_of_payment=? AND amount=? AND user_id=?
        ''', (*values, user_id))
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", "Expense removed successfully.")
        view_expenses(user_id)  # Refresh the list after removing an expense
    except Exception as e:
        messagebox.showerror("Error", f"Failed to remove expense: {e}")

# Function to view expenses
def view_expenses(user_id):
    create_treeview()  # Create the Treeview
    try:
        conn = sqlite3.connect('expenses.db')
        c = conn.cursor()
        c.execute('SELECT date, description, payee, mode_of_payment, amount FROM expenses WHERE user_id=?', (user_id,))
        rows = c.fetchall()
        conn.close()

        # Update the treeview contents
        for item in expenses_list.get_children():
            expenses_list.delete(item)
        for row in rows:
            expenses_list.insert("", "end", values=row)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to view expenses: {e}")

# Function to select an expense from the Treeview
def select_expense(event):
    try:
        selected_item = expenses_list.selection()[0]
        values = expenses_list.item(selected_item, 'values')
        
        date_entry.delete(0, 'end')
        date_entry.insert('end', values[0])
        
        description_entry.delete(0, 'end')
        description_entry.insert('end', values[1])
        
        payee_entry.delete(0, 'end')
        payee_entry.insert('end', values[2])
        
        mode_of_payment_combobox.set(values[3])
        
        amount_entry.delete(0, 'end')
        amount_entry.insert('end', values[4])
    except IndexError:
        pass

# Function to summarize expenses
def summarize_expenses(user_id):
    try:
        conn = sqlite3.connect('expenses.db')
        c = conn.cursor()
        c.execute('SELECT mode_of_payment, SUM(amount) FROM expenses WHERE user_id=? GROUP BY mode_of_payment', (user_id,))
        rows = c.fetchall()
        conn.close()
        
        summary = "Summary of Expenses by Mode of Payment:\n"
        for row in rows:
            summary += f"{row[0]}: {row[1]}\n"
        
        messagebox.showinfo("Expense Summary", summary)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to summarize expenses: {e}")

def visualize_expenses(user_id):
    try:
        conn = sqlite3.connect('expenses.db')
        c = conn.cursor()
        c.execute('SELECT description, SUM(amount) FROM expenses WHERE user_id=? GROUP BY description ORDER BY SUM(amount) DESC', (user_id,))
        rows = c.fetchall()
        conn.close()

        if not rows:
            messagebox.showinfo("No Data", "No expenses found to visualize.")
            return

        descriptions = [row[0] for row in rows]
        amounts = [row[1] for row in rows]

        # Create a new window for the graph
        graph_window = Toplevel()
        graph_window.title("Expense Visualization by Description")

        fig, ax = plt.subplots()
        ax.bar(descriptions, amounts, color='b')
        ax.set_title('Expenses by Description')
        ax.set_xlabel('Description')
        ax.set_ylabel('Amount')
        ax.grid(True)
        ax.tick_params(axis='x', rotation=45)  # Rotate x-axis labels for better readability

        canvas = FigureCanvasTkAgg(fig, master=graph_window)
        canvas.get_tk_widget().pack(fill='both', expand=True)
        canvas.draw()

        # Optional: Add a button to close the graph window
        close_button = Button(graph_window, text="Close", command=graph_window.destroy)
        close_button.pack()

    except Exception as e:
        messagebox.showerror("Error", f"Failed to visualize expenses: {e}")

# Function to export expenses to PDF
def export_to_pdf(user_id):
    try:
        conn = sqlite3.connect('expenses.db')
        c = conn.cursor()
        c.execute('SELECT * FROM expenses WHERE user_id=?', (user_id,))
        rows = c.fetchall()
        conn.close()

        if not rows:
            messagebox.showinfo("No Data", "No expenses found to export.")
            return

        # Generate PDF
        pdf_filename = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if pdf_filename:
            c = canvas.Canvas(pdf_filename, pagesize=letter)
            y_start = 750  # Starting y position for the table
            line_height = 20  # Height of each line (for table)

            # PDF Title
            c.setFont("Helvetica-Bold", 16)
            c.drawCentredString(300, y_start, "Expense Report")
            c.setFont("Helvetica", 12)
            c.drawCentredString(300, y_start - 20, f"User ID: {user_id}")

            # PDF Table headers
            table_headers = ["Date", "Description", "Payee", "Mode of Payment", "Amount"]
            y_start -= 40
            for i, header in enumerate(table_headers):
                c.drawString(50 + i * 100, y_start, header)
            y_start -= line_height

            # PDF Table data
            for row in rows:
                for i, value in enumerate(row[2:]):  # Skip id and user_id fields
                    c.drawString(50 + i * 100, y_start, str(value))
                y_start -= line_height
                if y_start < 50:
                    c.showPage()
                    y_start = 750

            c.save()
            messagebox.showinfo("Export Successful", f"Expenses exported to {pdf_filename} successfully.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to export expenses: {e}")

# Function to export expenses to Excel
def export_to_excel(user_id):
    try:
        conn = sqlite3.connect('expenses.db')
        c = conn.cursor()
        c.execute('SELECT * FROM expenses WHERE user_id=?', (user_id,))
        rows = c.fetchall()
        conn.close()

        if not rows:
            messagebox.showinfo("No Data", "No expenses found to export.")
            return

        # Generate Excel file
        excel_filename = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if excel_filename:
            df = pd.DataFrame(rows, columns=["ID", "User ID", "Date", "Description", "Payee", "Mode of Payment", "Amount"])
            df.to_excel(excel_filename, index=False)
            messagebox.showinfo("Export to Excel", f"Expenses exported successfully to {excel_filename}")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to export expenses to Excel: {e}")

def search_expenses(user_id):
    search_query = search_entry.get()
    if not search_query:
        messagebox.showerror("Error", "Please enter a search query.")
        return

    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('''
        SELECT date, description, payee, mode_of_payment, amount
        FROM expenses
        WHERE user_id=? AND (date LIKE? OR description LIKE? OR payee LIKE? OR mode_of_payment LIKE?)
    ''', (user_id, f"%{search_query}%", f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"))
    rows = c.fetchall()
    conn.close()

    expenses_list.delete(*expenses_list.get_children())  # Clear the Treeview
    for row in rows:
        expenses_list.insert("", "end", values=row)  # Insert the search results

# Function to clear the input fields
def clear_fields():
    date_entry.delete(0, 'end')
    description_entry.delete(0, 'end')
    payee_entry.delete(0, 'end')
    mode_of_payment_combobox.set('')
    amount_entry.delete(0, 'end')

# Function to logout
def logout():
    global current_user_id
    current_user_id = None
    expense_frame.pack_forget()
    login_register_frame.pack(pady=20)

def resize_background(event=None):
    if 'background_image' in globals():
        image = Image.open("bg.jpeg")
        image = image.resize((root.winfo_width(), root.winfo_height()), Image.LANCZOS)
        bg_image = ImageTk.PhotoImage(image)
        background_label.config(image=bg_image)
        background_label.image = bg_image

# Initialize the main window
root = Tk()
root.title("Expense Tracker")
root.geometry("800x600")

background_label = Label(root)
background_label.place(x=0, y=0, relwidth=1, relheight=1)
background_image = Image.open("bg.jpeg")
background_image = background_image.resize((root.winfo_width(), root.winfo_height()),Image.LANCZOS)
background_photo = ImageTk.PhotoImage(background_image)
background_label.config(image=background_photo)
background_label.image = background_photo

root.bind("<Configure>", resize_background)

# Set custom colors
background_color = "antique white"
entry_background_color = "wheat1"
button_background_color = "salmon"
button_foreground_color = "#050505"
treeview_background_color = "pale turquoise"
treeview_foreground_color = "RoyalBlue1"

root.configure(bg=background_color)

# Frame for login and registration
login_register_frame = Frame(root)
login_register_frame.pack(pady=20)

welcome_label = Label(login_register_frame, text="Expense Tracker", 
                      bg=background_color, 
                      font=("Times New Roman", 30, "bold italic"),  # Change font style to bold
                      fg="DarkGoldenrod4")  # Change font color to a specific color
welcome_label.grid(row=0, column=0, columnspan=2, padx=20, pady=20)

username_label = Label(login_register_frame, text="Username:", bg=background_color, font=("Arial", 13))
username_label.grid(row=1, column=0, padx=20, pady=20)
username_entry = Entry(login_register_frame, bg=entry_background_color)
username_entry.grid(row=1, column=1, padx=20, pady=20)

password_label = Label(login_register_frame, text="Password:", bg=background_color, font=("Arial", 13))
password_label.grid(row=2, column=0, padx=20, pady=20)
password_entry = Entry(login_register_frame, show='*', bg=entry_background_color)
password_entry.grid(row=2, column=1, padx=20, pady=20)

register_button = Button(login_register_frame, text="Register", command=register, bg=button_background_color, fg=button_foreground_color, font=("Arial", 13))
register_button.grid(row=3, column=0, padx=10, pady=10)

login_button = Button(login_register_frame, text="Login", command=login, bg=button_background_color, fg=button_foreground_color, font=("Arial", 13))
login_button.grid(row=3, column=1, padx=10, pady=10)

# Frame for adding expenses
expense_frame = Frame(root, bg=background_color)

date_label = Label(expense_frame, text="Date:", bg=background_color)
date_label.grid(row=0, column=0, padx=10, pady=10)
date_entry = Entry(expense_frame, bg=entry_background_color)
date_entry.grid(row=0, column=1, padx=10, pady=10)

logout_button = Button(expense_frame, text="Logout", command=logout, bg=button_background_color, fg=button_foreground_color)
logout_button.grid(row=0, column=40)

description_label = Label(expense_frame, text="Description:", bg=background_color)
description_label.grid(row=1, column=0, padx=10, pady=10)
description_entry = Entry(expense_frame, bg=entry_background_color)
description_entry.grid(row=1, column=1, padx=10, pady=10)

payee_label = Label(expense_frame, text="Payee:", bg=background_color)
payee_label.grid(row=2, column=0, padx=10, pady=10)
payee_entry = Entry(expense_frame, bg=entry_background_color)
payee_entry.grid(row=2, column=1, padx=10, pady=10)

mode_of_payment_label = Label(expense_frame, text="Mode of Payment:", bg=background_color)
mode_of_payment_label.grid(row=3, column=0, padx=10, pady=10)
mode_of_payment_combobox = ttk.Combobox(expense_frame, values=["GPay", "Cash", "Net Banking", "PhonePe", "Debit Card", "Others"])
mode_of_payment_combobox.grid(row=3, column=1, padx=10, pady=10)

amount_label = Label(expense_frame, text="Amount:", bg=background_color)
amount_label.grid(row=4, column=0, padx=10, pady=10)
amount_entry = Entry(expense_frame, bg=entry_background_color)
amount_entry.grid(row=4, column=1, padx=10, pady=10)

add_expense_button = Button(expense_frame, text="Add Expense", command=lambda: add_expense(current_user_id), bg=button_background_color, fg=button_foreground_color)
add_expense_button.grid(row=5, column=0, padx=10, pady=10)

update_expense_button = Button(expense_frame, text="Update Expense", command=lambda: update_expense(current_user_id), bg=button_background_color, fg=button_foreground_color)
update_expense_button.grid(row=5, column=1, padx=10, pady=10)

remove_expense_button = Button(expense_frame, text="Remove Expense", command=lambda: remove_expense(current_user_id), bg=button_background_color, fg=button_foreground_color)
remove_expense_button.grid(row=5, column=2, padx=10, pady=10)

view_expenses_button = Button(expense_frame, text="View Expenses", command=lambda: view_expenses(current_user_id), bg=button_background_color, fg=button_foreground_color)
view_expenses_button.grid(row=5, column=3, padx=10, pady=10)

summarize_expenses_button = Button(expense_frame, text="Summarize Expenses", command=lambda: summarize_expenses(current_user_id), bg=button_background_color, fg=button_foreground_color)
summarize_expenses_button.grid(row=6, column=0, padx=10, pady=10)

visualize_expenses_button = Button(expense_frame, text="Visualize Expenses", command=lambda: visualize_expenses(current_user_id), bg=button_background_color, fg=button_foreground_color)
visualize_expenses_button.grid(row=6, column=1, padx=10, pady=10)

export_to_pdf_button = Button(expense_frame, text="Export to PDF", command=lambda: export_to_pdf(current_user_id), bg=button_background_color, fg=button_foreground_color)
export_to_pdf_button.grid(row=6, column=2, padx=10, pady=10)

import_from_excel_button = Button(expense_frame, text="Export to Excel", command=lambda: export_to_excel(current_user_id), bg=button_background_color, fg=button_foreground_color)
import_from_excel_button.grid(row=6, column=3, padx=10, pady=10)

search_label = Label(expense_frame, text="Search:", bg=background_color)
search_label.grid(row=7, column=0, padx=10, pady=10)
search_entry = Entry(expense_frame, bg=entry_background_color)
search_entry.grid(row=7, column=1, padx=10, pady=10)
search_button = Button(expense_frame, text="Search", command=lambda: search_expenses(current_user_id), bg=button_background_color, fg=button_foreground_color)
search_button.grid(row=7, column=2, padx=10, pady=10)

def create_treeview():
    global expenses_list
    columns = ("Date", "Description", "Payee", "Mode of Payment", "Amount")
    expenses_list = ttk.Treeview(expense_frame, columns=columns, show="headings", selectmode="browse")

    for col in columns:
        expenses_list.heading(col, text=col)
        expenses_list.column(col, width=150)

    # Create and configure the scrollbar
    expenses_scrollbar = Scrollbar(expense_frame, orient="vertical")
    expenses_scrollbar.grid(row=9, column=3, sticky="ns")
    expenses_list.config(yscrollcommand=expenses_scrollbar.set)
    expenses_scrollbar.config(command=expenses_list.yview)

    # Add Treeview to the grid layout
    expenses_list.grid(row=9, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

    # Ensure the grid column and row weights are set so the Treeview can expand
    expense_frame.grid_rowconfigure(9, weight=1)
    expense_frame.grid_columnconfigure(0, weight=1)
    expense_frame.grid_columnconfigure(1, weight=1)
    expense_frame.grid_columnconfigure(2, weight=1)

    expenses_list.bind('<<TreeviewSelect>>', select_expense)

    # Only create the Treeview once
    if not hasattr(create_treeview, 'created'):
        create_treeview.created = True
    else:
        # If the Treeview already exists, just update its contents
        for item in expenses_list.get_children():
            expenses_list.delete(item)

# Apply styles
style = ttk.Style()
style.configure("Treeview", background=treeview_background_color, foreground=treeview_foreground_color, rowheight=25, fieldbackground=treeview_background_color)
style.configure("Treeview.Heading", font=("Helvetica", 10, "bold"))

root.mainloop()
