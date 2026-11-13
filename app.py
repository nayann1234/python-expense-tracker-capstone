import logging
import sqlite3
from flask import Flask, jsonify, render_template_string, request

# Objective 2: Configure application logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

app = Flask(__name__)
DB_NAME = "expenses.db"


def init_db():
  """Initialize the SQLite database schema."""
  try:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                date TEXT NOT NULL
            )
        """)
    conn.commit()
    conn.close()
    logging.info("Database initialized successfully.")
  except sqlite3.Error as e:
    logging.error(f"Database initialization failed: {e}")


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Python Expense Tracker Capstone</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 700px; margin: 40px auto; padding: 20px; background: #f4f7f6; }
        h1 { color: #2c3e50; text-align: center; }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 20px; }
        input, select, button { width: 100%; padding: 10px; margin: 8px 0; border-radius: 4px; border: 1px solid #ccc; box-sizing: border-box; }
        button { background: #27ae60; color: white; font-weight: bold; border: none; cursor: pointer; }
        button:hover { background: #219150; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 10px; border-bottom: 1px solid #ddd; text-align: left; }
        th { background: #2c3e50; color: white; }
        .delete-btn { background: #e74c3c; padding: 5px 10px; width: auto; }
        .total { font-size: 1.2em; font-weight: bold; text-align: right; margin-top: 15px; color: #2c3e50; }
    </style>
</head>
<body>
    <h1>Python Expense Tracker</h1>
    <div class="card">
        <h3>Add New Expense</h3>
        <input type="text" id="title" placeholder="Expense Title (e.g., Groceries)" required>
        <select id="category">
            <option value="Food">Food</option>
            <option value="Transport">Transport</option>
            <option value="Utilities">Utilities</option>
            <option value="Entertainment">Entertainment</option>
            <option value="Other">Other</option>
        </select>
        <input type="number" id="amount" placeholder="Amount (₹)" step="0.01" required>
        <input type="date" id="date" required>
        <button onclick="addExpense()">Add Expense</button>
    </div>

    <div class="card">
        <h3>Expense History</h3>
        <table>
            <thead>
                <tr><th>Date</th><th>Title</th><th>Category</th><th>Amount</th><th>Action</th></tr>
            </thead>
            <tbody id="expense-list"></tbody>
        </table>
        <div class="total" id="total-amount">Total: ₹0.00</div>
    </div>

    <script>
        async function loadExpenses() {
            const res = await fetch('/api/expenses');
            const data = await res.json();
            const list = document.getElementById('expense-list');
            list.innerHTML = '';
            let total = 0;
            data.expenses.forEach(exp => {
                total += exp.amount;
                list.innerHTML += `<tr>
                    <td>${exp.date}</td>
                    <td>${exp.title}</td>
                    <td>${exp.category}</td>
                    <td>₹${exp.amount.toFixed(2)}</td>
                    <td><button class="delete-btn" onclick="deleteExpense(${exp.id})">Delete</button></td>
                </tr>`;
            });
            document.getElementById('total-amount').innerText = `Total: ₹${total.toFixed(2)}`;
        }

        async function addExpense() {
            const title = document.getElementById('title').value;
            const category = document.getElementById('category').value;
            const amount = parseFloat(document.getElementById('amount').value);
            const date = document.getElementById('date').value;
            if (!title || isNaN(amount) || !date) return alert('Please fill all fields');

            await fetch('/api/expenses', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, category, amount, date })
            });
            document.getElementById('title').value = '';
            document.getElementById('amount').value = '';
            loadExpenses();
        }

        async function deleteExpense(id) {
            await fetch(`/api/expenses/${id}`, { method: 'DELETE' });
            loadExpenses();
        }

        loadExpenses();
    </script>
</body>
</html>
"""


@app.route("/")
def index():
  return render_template_string(HTML_TEMPLATE)


@app.route("/api/expenses", methods=["GET"])
def get_expenses():
  try:
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM expenses ORDER BY date DESC")
    rows = cursor.fetchall()
    conn.close()
    return jsonify({"expenses": [dict(row) for row in rows]}), 200
  except Exception as e:
    logging.error(f"Error fetching expenses: {e}")
    return jsonify({"error": "Failed to fetch expenses"}), 500


@app.route("/api/expenses", methods=["POST"])
def add_expense():
  try:
    data = request.get_json()
    if (
        not data
        or "title" not in data
        or "amount" not in data
        or "date" not in data
    ):
      return jsonify({"error": "Missing required fields"}), 400

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO expenses (title, category, amount, date) VALUES (?, ?, ?,"
        " ?)",
        (
            data["title"],
            data.get("category", "Other"),
            float(data["amount"]),
            data["date"],
        ),
    )
    conn.commit()
    conn.close()
    logging.info(f"Added expense: {data['title']}")
    return jsonify({"message": "Expense added"}), 201
  except Exception as e:
    logging.error(f"Error adding expense: {e}")
    return jsonify({"error": "Failed to add expense"}), 500


@app.route("/api/expenses/<int:expense_id>", methods=["DELETE"])
def delete_expense(expense_id):
  try:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    conn.close()
    logging.info(f"Deleted expense ID: {expense_id}")
    return jsonify({"message": "Expense deleted"}), 200
  except Exception as e:
    logging.error(f"Error deleting expense: {e}")
    return jsonify({"error": "Failed to delete expense"}), 500


init_db()

import os

if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)
