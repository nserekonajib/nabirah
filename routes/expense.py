from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from supabase import create_client, Client
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv

from routes.auth import login_required

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

expense_bp = Blueprint('expense', __name__, url_prefix='/expenses')

# Define your categories here or fetch dynamically if you want
CATEGORIES = [
    "Travel",
    "Accommodation",
    "Meals",
    "Office Supplies",
    "Utilities",
    "Salaries",
    "Marketing",
    "Miscellaneous"
]

@expense_bp.app_template_global()
def category_color_class(category):
    colors = {
        "Travel": "bg-blue-500 text-white",
        "Accommodation": "bg-green-500 text-white",
        "Meals": "bg-yellow-500 text-black",
        "Office Supplies": "bg-purple-500 text-white",
        "Utilities": "bg-indigo-500 text-white",
        "Salaries": "bg-red-500 text-white",
        "Marketing": "bg-pink-500 text-white",
        "Miscellaneous": "bg-gray-500 text-white",
    }
    return colors.get(category, "bg-gray-300 text-black")


@expense_bp.route('/expense_dashboard', methods=['GET'])


@login_required
def expense_dashboard():
    user_data = session.get('user')

    # Fetch all expenses sorted descending by created_at
    expenses_resp = supabase.table('expenses').select('*').order('created_at', desc=True).execute()
    expenses_raw = expenses_resp.data or []

    # Map expenses keys for template (ensure keys match Jinja template)
    expenses = []
    for e in expenses_raw:
        expenses.append({
            'id': e.get('id'),
            'date': e.get('date') or '',
            'description': e.get('description') or '',
            'amount': float(e.get('amount') or 0),
            'category': e.get('category') or '',
            'payee': e.get('payee') or '',
            'approvedBy': e.get('approved_by') or '',
            'voucherNumber': e.get('voucher_number') or '',
            'createdAt': e.get('created_at') or ''
        })

    # Fetch partners to calculate total capital
    partners_resp = supabase.table('partners').select('initial_capital').execute()
    partners = partners_resp.data or []

    total_capital = sum(float(p.get("initial_capital", 0)) for p in partners)
    total_expenses = sum(e['amount'] for e in expenses)
    available_capital = total_capital - total_expenses

    capital = {
        "totalCapital": total_capital,
        "totalExpenses": total_expenses,
        "availableCapital": available_capital
    }

    # Calculate utilization percentage (expenses as % of capital)
    utilization = 0.0
    if total_capital > 0:
        utilization = (total_expenses / total_capital) * 100

    # Clamp utilization to max 100%
    utilization_clamped = min(utilization, 100)

    return render_template(
        'expenses/expense.html',
        expenses=expenses,
        capital=capital,
        categories=CATEGORIES,
        utilization=utilization_clamped,
        user=user_data
    )


@expense_bp.route('/add', methods=['POST'])
@login_required
def add_expense():
    user_data = session.get('user')
    data = request.form

    try:
        # Validate inputs (you can extend this with better validation)
        date_str = data.get('date')
        if not date_str:
            flash("Date is required.", "error")
            return redirect(url_for('expense.expense_dashboard'))

        description = data.get('description', '').strip()
        if not description:
            flash("Description is required.", "error")
            return redirect(url_for('expense.expense_dashboard'))

        amount = float(data.get('amount') or 0)
        if amount <= 0:
            flash("Amount must be greater than zero.", "error")
            return redirect(url_for('expense.expense_dashboard'))

        category = data.get('category')
        if category not in CATEGORIES:
            flash("Invalid category selected.", "error")
            return redirect(url_for('expense.expense_dashboard'))

        payee = data.get('payee', '').strip()
        approved_by = data.get('approved_by', '').strip()

        expense = {
            'id': str(uuid.uuid4()),
            'date': date_str,
            'description': description,
            'amount': amount,
            'category': category,
            'payee': payee,
            'approved_by': approved_by,
            'voucher_number': generate_voucher_number(),
            'created_at': datetime.utcnow().isoformat()
        }

        insert_resp = supabase.table('expenses').insert(expense).execute()

        if insert_resp.error:
            flash(f"Failed to save expense: {insert_resp.error.message}", "error")
        else:
            flash("Expense recorded successfully.", "success")

    except Exception as e:
        flash(f"Error saving expense: {str(e)}", "error")

    return redirect(url_for('expense.expense_dashboard'))


def generate_voucher_number():
    now = datetime.utcnow()
    # e.g. EXP-20250714-1a2b
    return f"EXP-{now.strftime('%Y%m%d')}-{str(uuid.uuid4())[:4]}"
