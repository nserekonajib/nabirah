from flask import Blueprint, render_template, request, redirect, url_for, flash
from supabase import create_client
import os
import uuid
from dotenv import load_dotenv
from routes.auth import login_required
from routes.financeclient import PesaPal

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

partners_bp = Blueprint('partners', __name__, url_prefix='/partners')

@partners_bp.route('/patners', methods=['GET'])
@login_required
def list_partners():
    user_data = request.args.get('user_data', None)

    try:
        # Get partners data
        partners_response = supabase.table("partners").select("*").order("created_at", desc=True).execute()
        raw_partners = partners_response.data or []

        # Get client financing data for expected payback
        financing_response = supabase.table("client_financing").select("expected_payback").execute()
        financed_clients = financing_response.data or []
        
         # Get client repayments data for expected payback
        client_repayment_response = supabase.table("repayments").select("amount_paid").execute()
        client_repayment = client_repayment_response.data or []
        print("Client repayments:", client_repayment)
        total_repaid = sum(item.get('amount_paid', 0) or 0 for item in client_repayment)
        print("Total repaid:", total_repaid)
        
        #get client registration_charge
        client_registration_response = supabase.table("clients").select("registration_charge").execute()
        client_registration = client_registration_response.data or []
        total_registration_charge = sum(item.get('registration_charge', 0) or 0 for item in client_registration)
        
        #get client total number
        client_count_response = supabase.table("clients").select("id").execute()
        client_count = client_count_response.data or []
        total_clients = len(client_count)
        
        #get total number of travelled clients
        travelled_clients_response = supabase.table("clients").select("id").eq("status", "travelled").execute()
        travelled_clients = travelled_clients_response.data or []
        total_travelled_clients = len(travelled_clients)
        print("Total travelled clients:", total_travelled_clients)
       

        # First calculate totals that are needed for individual partner calculations
        total_capital = sum(float(p.get("initial_capital", 0)) for p in raw_partners)
        x = sum(float(client.get("expected_payback", 0)) for client in financed_clients)
        total_expected_payback = x - total_repaid

        partners = []
        total_returns = 0
        corporate_count = 0
        individual_count = 0
        total_expected_returns = 0
        total_available_capital = 0
        

        for p in raw_partners:
            
            
            
            initial_capital = float(p.get("initial_capital") or 0)
            total_return = float(p.get("total_returns") or 0)
            available_capital = float(p.get("available_capital", initial_capital))

            # Expected returns: business rule
            expected_returns = (initial_capital / 500_000) * 1_000_000 if initial_capital else 0
            total_expected_returns += expected_returns
            total_available_capital += available_capital
            
           

            # NEW: Capital percentage (partner's capital as % of total capital)
            capital_percentage = (initial_capital / total_capital * 100) if total_capital else 0

            # Performance ratio = actual / expected (keep this for ranking)
            performance_ratio = (total_return / expected_returns) if expected_returns else 0

            # Rank performance (based on performance ratio)
            if performance_ratio >= 1.5:
                rank = "Excellent"
            elif performance_ratio >= 1.0:
                rank = "Good"
            elif performance_ratio >= 0.5:
                rank = "Average"
            else:
                rank = "Below Average"
                
            if capital_percentage >= 60:
                rank = "Excellent"
            elif capital_percentage >= 50:
                rank = "Good"
            elif capital_percentage >= 30:
                rank = "Average"
            else:
                rank = "Below Average"

            # Distribution classification
            name = p.get("partner_name", "").lower()
            if "group" in name or "ltd" in name or "limited" in name:
                corporate_count += 1
            else:
                individual_count += 1

            partners.append({
                "id": p.get("id"),
                "partner_name": p.get("partner_name", ""),
                "email": p.get("email", ""),
                "phone_number": p.get("phone_number", ""),
                "initial_capital": initial_capital,
                "available_capital": available_capital,
                "total_returns": total_return,
                "expected_returns": expected_returns,
                "capital_percentage": capital_percentage,  # NEW: Partner's % of total capital
                "performance_ratio": capital_percentage,     # Kept for ranking
                "performance_rank": rank,
                "created_at": p.get("created_at", "")[:10],
                "is_active": p.get("is_active", True)
            })

            total_returns += total_return

        average_investment = total_capital / len(partners) if partners else 0
        portfolio_utilization = (total_returns / total_capital) * 100 if total_capital else 0

    except Exception as e:
        flash(f"Failed to load partners: {e}", "error")
        partners = []
        average_investment = 0
        portfolio_utilization = 0
        corporate_count = 0
        individual_count = 0
        total_expected_returns = 0
        total_available_capital = 0
        total_expected_payback = 0

    return render_template(
        'partners/list.html',
        partners=partners,
        user=user_data,
        individual_investors_count=individual_count,
        corporate_partners_count=corporate_count,
        average_investment=round(average_investment),
        portfolio_utilization=round(portfolio_utilization),
        total_capital_invested=round(total_capital),
        expected_returns=round(total_expected_returns),
        total_available_capital=round(total_available_capital),
        total_expected_payback=round(total_expected_payback),
        total_repaid=round(total_repaid),
        total_registration_charge=round(total_registration_charge),
        total_clients=total_clients
        
    )
    
    
@partners_bp.route('/add', methods=['POST'])
@login_required
def add_partner():
    user_data = request.args.get('user_data', None)
    name = request.form.get('partner_name')
    email = request.form.get('email')
    phone = request.form.get('phone_number')
    capital = request.form.get('initial_capital')

    if not (name and email and phone and capital):
        flash("All fields are required!", "error")
        return redirect(url_for('partners.list_partners'))

    try:
        new_partner = {
            "id": str(uuid.uuid4()),
            "partner_name": name,
            "email": email,
            "phone_number": phone,
            "initial_capital": float(capital),
            "available_capital": float(capital),
            "total_returns": 0,
            "is_active": True  # Optional default
        }
        res = supabase.table("partners").insert(new_partner).execute()

        if hasattr(res, "status_code") and res.status_code != 201:
            flash(f"Failed to add partner: {res.data}", "error")
        else:
            flash("Partner added successfully!", "success")

    except Exception as e:
        flash(f"Error adding partner: {e}", "error")

    return redirect(url_for('partners.list_partners'))

@partners_bp.route('/add-capital', methods=['POST'])
@login_required
def add_capital():
    partner_id = request.form.get('partner_id')
    additional_capital = request.form.get('additional_capital')

    if not partner_id or not additional_capital:
        flash("Missing partner or capital amount", "error")
        return redirect(url_for('partners.list_partners'))

    try:
        # Get current values
        res = supabase.table("partners").select("initial_capital, available_capital").eq("id", partner_id).single().execute()
        if res.data:
            initial = float(res.data.get("initial_capital") or 0)
            available = float(res.data.get("available_capital") or 0)
            add = float(additional_capital)

            updated = {
                "initial_capital": initial + add,
                "available_capital": available + add
            }

            # Update in Supabase
            update_res = supabase.table("partners").update(updated).eq("id", partner_id).execute()

            if hasattr(update_res, "status_code") and update_res.status_code in [200, 204]:
                flash("Capital added successfully", "success")
            else:
                flash("Failed to update capital", "error")
        else:
            flash("Partner not found", "error")

    except Exception as e:
        flash(f"Error adding capital: {e}", "error")

    return redirect(url_for('partners.list_partners'))

