import gspread
import json
import os
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# 🔹 Google Sheets API Setup
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# 🔹 Load Credentials from Environment Variable
creds_json = os.getenv("GOOGLE_CREDENTIALS")
if creds_json:
    creds_dict = json.loads(creds_json)  # Convert JSON string to dictionary
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
    client = gspread.authorize(creds)
else:
    raise Exception("GOOGLE_CREDENTIALS environment variable not set")

# 🔹 Open Google Sheet
SHEET_ID = "1abbEg-kBh3DsC5eFcdPN8HezKdZEzwAJZ3GeuioMJMc"
sheet = client.open_by_key(SHEET_ID)
expenses_sheet = sheet.worksheet("Expenses")
budget_sheet = sheet.worksheet("Budget")


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        username = request.form.get("username")
        return redirect(url_for("dashboard", username=username))
    return render_template("index.html")


@app.route("/dashboard/<username>")
def dashboard(username):
    expenses_data = expenses_sheet.get_all_records()
    budget_data = budget_sheet.get_all_records()

    user_expenses = [e for e in expenses_data if e["Username"] == username]
    user_budget = next((b for b in budget_data if b["Username"] == username), {"Monthly_Budget": 0})

    total_expense = sum(float(e["Amount"]) for e in user_expenses if e["Type"].lower() == "expense")
    monthly_budget = float(user_budget.get("Monthly_Budget", 0))
    balance = monthly_budget - total_expense

    return render_template("dashboard.html", username=username, total_expense=total_expense,
                           monthly_budget=monthly_budget, balance=balance)


@app.route("/add_transaction/<username>", methods=["GET", "POST"])
def add_transaction(username):
    if request.method == "POST":
        date = request.form.get("date")
        amount = request.form.get("amount")
        category = request.form.get("category")
        description = request.form.get("description")
        trans_type = request.form.get("type")

        expenses_sheet.append_row([date, amount, category, description, trans_type, username])
        return redirect(url_for("transactions", username=username))

    return render_template("add_transaction.html", username=username)


@app.route("/reports/<username>")
def reports(username):
    expenses_data = expenses_sheet.get_all_records()
    user_expenses = [e for e in expenses_data if e["Username"] == username]

    categories = []
    amounts = []

    category_totals = {}
    for e in user_expenses:
        category = e["Category"]
        amount = float(e["Amount"])
        category_totals[category] = category_totals.get(category, 0) + amount

    categories = list(category_totals.keys())
    amounts = list(category_totals.values())

    return render_template("reports.html", username=username, categories=categories, amounts=amounts)


# 🔹 Run Flask App with Dynamic Port (for Render)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(debug=False, host="0.0.0.0", port=port)
