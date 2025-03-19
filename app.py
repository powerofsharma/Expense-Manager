import gspread
import json
import os
import matplotlib.pyplot as plt
import io
import base64
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# 🔹 Google Sheets API Setup
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# 🔹 Load Credentials from Environment Variable (Render Deployment)
creds_json = json.loads(os.getenv("GOOGLE_SHEETS_CREDENTIALS"))
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, SCOPE)
client = gspread.authorize(creds)

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


@app.route("/transactions/<username>")
def transactions(username):
    expenses_data = expenses_sheet.get_all_records()
    user_expenses = [e for e in expenses_data if e["Username"] == username]

    # ✅ Show only the last 10 transactions
    user_expenses = user_expenses[-10:]

    return render_template("transactions.html", username=username, expenses=user_expenses)


@app.route("/delete_transaction/<username>/<int:row>", methods=["POST"])
def delete_transaction(username, row):
    expenses_sheet.delete_rows(row + 2)  # Adjust for Google Sheets row numbering
    return redirect(url_for("transactions", username=username))


@app.route("/set_budget/<username>", methods=["GET", "POST"])
def set_budget(username):
    if request.method == "POST":
        budget = request.form.get("budget")
        budget_sheet.append_row([username, budget])
        return redirect(url_for("dashboard", username=username))
    return render_template("set_budget.html", username=username)


@app.route("/reports/<username>")
def reports(username):
    report_image = generate_report(username)  # Get the base64 chart
    return render_template("reports.html", username=username, report_image=report_image)


@app.route("/generate_report/<username>")
def generate_report(username):
    expenses_data = expenses_sheet.get_all_records()
    user_expenses = [e for e in expenses_data if e["Username"] == username]

    categories = {}
    for e in user_expenses:
        categories[e["Category"]] = categories.get(e["Category"], 0) + float(e["Amount"])

    plt.figure(figsize=(6, 6))
    plt.pie(categories.values(), labels=categories.keys(), autopct='%1.1f%%')
    plt.title("Expense Breakdown")

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)

    return base64.b64encode(img.getvalue()).decode()


# 🔹 Run Flask App with Dynamic Port (for Render)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(debug=False, host="0.0.0.0", port=port)
