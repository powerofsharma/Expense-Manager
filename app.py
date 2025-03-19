import os
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Google Sheets setup
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Load Google Sheets credentials from environment variable
cred_json = json.loads(os.getenv("GOOGLE_SHEETS_CREDENTIALS"))  # Load from environment variable
creds = ServiceAccountCredentials.from_json_keyfile_dict(cred_json, SCOPE)
client = gspread.authorize(creds)

# Open Google Sheet
SHEET_ID = "1abbEg-kBh3DsC5eFcdPN8HezKdZEzwAJZ3GeuioMJMc"  # Updated with your Google Sheet ID
sheet = client.open_by_key(SHEET_ID)
expenses_sheet = sheet.worksheet("Expenses")
budget_sheet = sheet.worksheet("Budget")


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        username = request.form.get("username")
        return redirect(url_for("dashboard", username=username))
    return render_template("index.html")


@app.route("/dashboard/<username>", methods=["GET", "POST"])
def dashboard(username):
    expenses_data = expenses_sheet.get_all_records()
    budget_data = budget_sheet.get_all_records()

    user_expenses = [e for e in expenses_data if e["Username"] == username]
    user_budget = next((b for b in budget_data if b["Username"] == username), {"Monthly_Budget": 0})

    total_expense = sum(float(e["Amount"]) for e in user_expenses if e["Type"] == "Expense")
    total_income = sum(float(e["Amount"]) for e in user_expenses if e["Type"] == "Income")
    monthly_budget = float(user_budget.get("Monthly_Budget", 0))
    balance = monthly_budget - total_expense

    return render_template(
        "dashboard.html",
        username=username,
        expenses=user_expenses,
        total_expense=total_expense,
        total_income=total_income,
        monthly_budget=monthly_budget,
        balance=balance
    )


@app.route("/add_transaction/<username>", methods=["POST"])
def add_transaction(username):
    date = request.form.get("date")
    amount = request.form.get("amount")
    category = request.form.get("category")
    description = request.form.get("description")
    trans_type = request.form.get("type")

    expenses_sheet.append_row([date, amount, category, description, trans_type, username])
    return redirect(url_for("dashboard", username=username))


@app.route("/set_budget/<username>", methods=["POST"])
def set_budget(username):
    budget = request.form.get("budget")
    budget_data = budget_sheet.get_all_records()

    user_budget_row = next((i + 2 for i, b in enumerate(budget_data) if b["Username"] == username), None)

    if user_budget_row:
        budget_sheet.update_cell(user_budget_row, 2, budget)  # Update existing budget
    else:
        budget_sheet.append_row([username, budget])  # Add new budget entry

    return redirect(url_for("dashboard", username=username))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=10000)