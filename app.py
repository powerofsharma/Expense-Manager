import os
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Set file paths
EXPENSES_FOLDER = "expenses_files"
EXPENSES_FILE = os.path.join(EXPENSES_FOLDER, "expenses.xlsx")
BUDGET_FILE = os.path.join(EXPENSES_FOLDER, "budget.xlsx")

# Ensure the expenses folder exists
if not os.path.exists(EXPENSES_FOLDER):
    os.makedirs(EXPENSES_FOLDER)

# Ensure the expense file exists
if not os.path.exists(EXPENSES_FILE):
    df_expense = pd.DataFrame(columns=["ID", "Date", "Amount", "Category", "Description", "Type", "Username"])
    df_expense.to_excel(EXPENSES_FILE, index=False, engine='openpyxl')

# Ensure the budget file exists
if not os.path.exists(BUDGET_FILE):
    df_budget = pd.DataFrame(columns=["Username", "Monthly_Budget"])
    df_budget.to_excel(BUDGET_FILE, index=False, engine='openpyxl')


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        username = request.form.get("username")
        return redirect(url_for("dashboard", username=username))
    return render_template("index.html")


@app.route("/dashboard/<username>", methods=["GET", "POST"])
def dashboard(username):
    df_expense = pd.read_excel(EXPENSES_FILE, engine='openpyxl')
    df_budget = pd.read_excel(BUDGET_FILE, engine='openpyxl')

    user_expenses = df_expense[df_expense["Username"] == username]
    user_budget = df_budget[df_budget["Username"] == username]

    total_expense = user_expenses[user_expenses["Type"] == "Expense"]["Amount"].sum() if not user_expenses.empty else 0
    total_income = user_expenses[user_expenses["Type"] == "Income"]["Amount"].sum() if not user_expenses.empty else 0
    monthly_budget = user_budget["Monthly_Budget"].values[0] if not user_budget.empty else 0
    balance = monthly_budget - total_expense

    return render_template(
        "dashboard.html",
        username=username,
        expenses=user_expenses.to_dict(orient="records"),
        total_expense=total_expense,
        total_income=total_income,
        monthly_budget=monthly_budget,
        balance=balance
    )


@app.route("/add_transaction/<username>", methods=["POST"])
def add_transaction(username):
    date = request.form.get("date")
    amount = float(request.form.get("amount"))
    category = request.form.get("category")
    description = request.form.get("description")
    trans_type = request.form.get("type")

    df = pd.read_excel(EXPENSES_FILE, engine='openpyxl')
    new_id = df["ID"].max() + 1 if not df.empty else 1

    new_entry = pd.DataFrame([{
        "ID": new_id,
        "Date": date,
        "Amount": amount,
        "Category": category,
        "Description": description,
        "Type": trans_type,
        "Username": username
    }])

    df = pd.concat([df, new_entry], ignore_index=True)
    df.to_excel(EXPENSES_FILE, index=False, engine='openpyxl')

    return redirect(url_for("dashboard", username=username))


@app.route("/set_budget/<username>", methods=["POST"])
def set_budget(username):
    budget = float(request.form.get("budget"))
    df_budget = pd.read_excel(BUDGET_FILE, engine='openpyxl')

    if username in df_budget["Username"].values:
        df_budget.loc[df_budget["Username"] == username, "Monthly_Budget"] = budget
    else:
        new_budget = pd.DataFrame([{"Username": username, "Monthly_Budget": budget}])
        df_budget = pd.concat([df_budget, new_budget], ignore_index=True)

    df_budget.to_excel(BUDGET_FILE, index=False, engine='openpyxl')
    return redirect(url_for("dashboard", username=username))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")