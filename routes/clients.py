from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, current_user
import supabase
from datetime import datetime
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv
from flask import *
from routes.auth import login_required
import uuid
import qrcode
import io
import base64
from datetime import datetime
from supabase import create_client, Client
from routes.superbase_client import *
import qrcode, io, base64
from routes.financeclient import PesaPal







load_dotenv()

client_bp = Blueprint('client', __name__, url_prefix='/client')



# Initialize Supabase client outside routes to reuse
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase_client = supabase.create_client(supabase_url, supabase_key)

STATUS_COLORS = {
    'registered': 'bg-blue-100 text-blue-800',
    'documents_verified': 'bg-purple-100 text-purple-800',
    'financed': 'bg-green-100 text-green-800',
    'travelled': 'bg-indigo-100 text-indigo-800',
    'repayment_active': 'bg-yellow-100 text-yellow-800',
    'completed': 'bg-emerald-100 text-emerald-800',
    'defaulted': 'bg-red-100 text-red-800'
}

import cloudinary
import cloudinary.uploader
import cloudinary.api

# Configure Cloudinary with your credentials
cloudinary.config(
    cloud_name="dym6vdlhb",
    api_key="257776185988175",
    api_secret="pjjo4TR7bGBI2BNwreXpFQ_DoV0"
)



@client_bp.route('/nabirah')
@login_required
def clients_list():
    user_data = session.get('user')
    search_query = request.args.get('search', '').strip()
    
    # Query clients with their identification info
    query = supabase_client.table('clients').select('*, identification(nin_number, primary_phone)')
    
    if search_query:
        try:
            # Option 1: Search client fields only (simpler)
            clients = query.ilike('full_name', f'%{search_query}%').execute().data
            
            # If no results, try searching identification fields
            if not clients:
                # Need to join tables properly for related field searches
                clients = supabase_client.rpc('search_clients', {
                    'search_term': search_query
                }).execute().data
                
                # Or alternative approach:
                # clients = supabase_client.table('clients') \
                #     .select('*, identification!inner(nin_number, primary_phone)') \
                #     .or_(f"full_name.ilike.%{search_query}%," \
                #          f"identification.nin_number.ilike.%{search_query}%," \
                #          f"identification.primary_phone.ilike.%{search_query}%") \
                #     .execute().data
                
        except Exception as e:
            print(f"Search error: {str(e)}")  # Debugging
            flash('Error searching clients', 'error')
            clients = []
    else:
        clients = query.execute().data
    
    return render_template('clients/list.html', 
                         clients=clients, 
                         search_query=search_query,
                         status_colors=STATUS_COLORS,
                         user=user_data)
    
    
@client_bp.route('/<uuid:client_id>')
@login_required
def client_detail(client_id):
    user_data = session.get('user')
    # Get client with all related data
    client_data = supabase_client.table('clients').select('*, identification(*), family_members(*), academic_history(*), work_experience(*), referrals(*)').eq('id', str(client_id)).execute()
    
    if not client_data.data:
        flash('Client not found', 'error')
        return redirect(url_for('client.clients_list'))
    
    client = client_data.data[0]
    if isinstance(client["date_of_birth"], str):
        client["date_of_birth"] = datetime.strptime(client["date_of_birth"], "%Y-%m-%d").date()
        
    return render_template('clients/detail.html', 
                         client=client,
                         status_colors=STATUS_COLORS,
                         user=user_data)

@client_bp.route('/<uuid:client_id>/update-status', methods=['POST'])
@login_required
def update_status(client_id):
    user_data = session.get('user')
    new_status = request.form.get('status')
    notes = request.form.get('notes', '')  # Optional for now

    if new_status not in STATUS_COLORS:
        return jsonify({'success': False, 'message': 'Invalid status'}), 400

    try:
        supabase_client.table('clients').update({'status': new_status}).eq('id', str(client_id)).execute()

        supabase_client.table('client_status_history').insert({
            'client_id': str(client_id),
            'status': new_status,
            'changed_by': user_data['id'],
            'notes': notes or 'Auto update from dropdown'
        }).execute()

        return jsonify({
            'success': True,
            'new_status': new_status,
            'color_class': STATUS_COLORS[new_status],
            'status_display': new_status.replace('_', ' ').title()
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

    
    

@client_bp.route('/<uuid:client_id>/delete', methods=['POST'])
@login_required
def delete_client(client_id):
    try:
        supabase_client.table('clients').delete().eq('id', str(client_id)).execute()
        supabase_client.table('identification').delete().eq('client_id', str(client_id)).execute()
        supabase_client.table('family_members').delete().eq('client_id', str(client_id)).execute()
        supabase_client.table('academic_history').delete().eq('client_id', str(client_id)).execute()
        supabase_client.table('work_experience').delete().eq('client_id', str(client_id)).execute()
        supabase_client.table('referrals').delete().eq('client_id', str(client_id)).execute()
        supabase_client.table('client_financing').delete().eq('client_id', str(client_id)).execute()

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500



@client_bp.route('/<uuid:client_id>/print')
@login_required
def print_client(client_id):
    user_data = session.get('user')
    
    # Get client data from Supabase
    client_data = supabase_client.table('clients')\
        .select('*, identification(*), family_members(*), academic_history(*), work_experience(*), referrals(*)')\
        .eq('id', str(client_id)).execute()
    
    if not client_data.data:
        flash('Client not found', 'error')
        return redirect(url_for('client.clients_list'))
    
    client = client_data.data[0]

    # ✅ Convert string to date
    if isinstance(client.get('date_of_birth'), str):
        try:
            client['date_of_birth'] = datetime.strptime(client['date_of_birth'], '%Y-%m-%d').date()
        except ValueError:
            client['date_of_birth'] = None

    current_date = datetime.now().strftime('%d/%m/%Y %H:%M')
    
    return render_template('clients/print.html', 
                         client=client,
                         now=current_date,
                         user=user_data)
import uuid
import json
from datetime import datetime

@client_bp.route('/submit', methods=['GET', 'POST'])
@login_required
def add_client():
    import uuid, json
    from datetime import datetime

    user_data = session.get('user')

    if request.method == 'POST':
        try:
            tmp_dir = os.path.join(current_app.root_path, 'tmp_uploads')
            os.makedirs(tmp_dir, exist_ok=True)
            os.makedirs("temp_clients", exist_ok=True)

            # Flatten form data
            form_data = {k: v[0] for k, v in request.form.to_dict(flat=False).items()}

            photo_url, nin_doc_url = None, None

            photo = request.files.get('photo')
            if photo and allowed_image_file(photo.filename):
                photo_path = os.path.join(tmp_dir, f"{uuid.uuid4()}_{photo.filename}")
                photo.save(photo_path)
                with open(photo_path, 'rb') as f:
                    result = cloudinary.uploader.upload(f, folder="clients/photos")
                photo_url = result.get("secure_url")
                os.remove(photo_path)

            nin_doc = request.files.get('nin_doc')
            if nin_doc and allowed_doc_file(nin_doc.filename):
                nin_path = os.path.join(tmp_dir, f"{uuid.uuid4()}_{nin_doc.filename}")
                nin_doc.save(nin_path)
                with open(nin_path, 'rb') as f:
                    result = cloudinary.uploader.upload(f, folder="clients/nin_docs")
                nin_doc_url = result.get("secure_url")
                os.remove(nin_path)

            temp_id = str(uuid.uuid4())
            global temp_file_path 
            temp_file_path = f"temp_clients/{temp_id}.json"
            global payment_file_path 
            payment_file_path = f"temp_clients/payment_{temp_id}.json"

            temp_data = {
                "created_at": datetime.utcnow().isoformat(),
                "form_data": form_data,
                "photo_url": photo_url,
                "nin_doc_url": nin_doc_url
            }

            with open(temp_file_path, "w") as f:
                json.dump(temp_data, f)

            # Initiate payment
            pesapal = PesaPal()
            amount = 1000
            email = form_data.get("primary_phone", "") + "@dummy.com"
            full_name = form_data.get("full_name", "Unknown Unknown")
            first_name = full_name.split()[0]
            last_name = full_name.split()[-1]
            reference_id = f"TXN-{temp_id}"
            callback_url = url_for('client.payment_callback', _external=True)

            order = pesapal.submit_order(amount, reference_id, callback_url, email, first_name, last_name)

            if order and 'redirect_url' in order:
                # Save payment session data to JSON
                payment_data = {
                    "order_id": order['order_tracking_id'],
                    "reference_id": reference_id,
                    "temp_id": temp_id
                }
                with open(payment_file_path, "w") as f:
                    json.dump(payment_data, f)

                return redirect(order['redirect_url'])

            # Cleanup if payment fails
            os.remove(temp_file_path)
            flash("Payment initiation failed.", "error")

        except Exception as e:
            flash(f"Error: {str(e)}", "error")

    return render_template("client_form.html", user=user_data)


@client_bp.route('/payment-callback')
@login_required
def payment_callback():
    import json, os

    try:
    
        with open(payment_file_path, "r") as f:
            payment_data = json.load(f)
            order_id = payment_data.get("order_id")
            temp_id = payment_data.get("temp_id")
            reference_id = payment_data.get("reference_id")

        pesapal = PesaPal()
        status = pesapal.verify_transaction_status(order_id)

        if status and status.get("payment_status_description", "").strip().lower() == "completed":
            
            if not os.path.exists(temp_file_path):
                flash("Client data missing. Please contact support.", "error")
                return redirect(url_for('client.add_client'))

            with open(temp_file_path, "r") as f:
                temp_data = json.load(f)

            form = temp_data['form_data']
            photo_url = temp_data['photo_url']
            nin_doc_url = temp_data['nin_doc_url']

            # Save client
            client_data = {
                "full_name": form['full_name'],
                "date_of_birth": form['date_of_birth'],
                "marital_status": form['marital_status'],
                "religion": form['religion'],
                "tribe": form['tribe'],
                "district_of_origin": form['district_of_origin'],
                "number_of_children": int(form.get('number_of_children', 0)),
                "occupation": form['occupation'],
                "medical_history": form['medical_history'],
                "status": "registered",
                "nok_name": form['nok_name'],
                "nok_relationship": form['nok_relationship'],
                "nok_contact": form['nok_contact'],
                "nok_address": form['nok_address'],
                "registration_charge": 200000
            }

            client_response = supabase_client.table("clients").insert(client_data).execute()
            client_id = client_response.data[0]["id"]

            identification = {
                "client_id": client_id,
                "nin_number": form['nin_number'],
                "passport_number": form['passport_number'],
                "primary_phone": form['primary_phone'],
                "secondary_phone": form['secondary_phone'],
                "photo_url": photo_url,
                "nin_doc_url": nin_doc_url
            }

            supabase_client.table("identification").insert(identification).execute()

            # Clean up temp files
            os.remove(temp_file_path)
            os.remove(payment_file_path)

            flash("Client successfully registered after payment!", "success")
            return redirect(url_for('client.clients_list'))

        else:
            flash("Payment not completed or failed.", "error")
            return redirect(url_for('client.add_client'))

    except Exception as e:
        flash(f"Payment verification error: {str(e)}", "error")
        return redirect(url_for('client.add_client'))



@client_bp.route('/finance', methods=['GET'])
@login_required

def finance():
    user_data = session.get('user')
    
    clients_resp = supabase_client.table('clients').select('id, full_name').execute()
    clients = clients_resp.data
    return render_template('clients/finance_form.html', clients=clients, user=user_data)



from flask import render_template, redirect, request, url_for, flash
import io, base64, qrcode


@client_bp.route('/handle_finance', methods=['POST'])
@login_required
def handle_finance():
    user_data = session.get('user')
    client_id = request.form['client_id']
    amount = float(request.form['amount'])
    investment_date = request.form['investment_date']
    expected_payback = float(request.form['expected_payback'])

    # 1. Fetch client
    client_resp = supabase_client.table('clients').select('full_name').eq('id', client_id).single().execute()
    client = client_resp.data

    if not client:
        flash("Client not found.", "error")
        return redirect(url_for('client.finance'))

    # 2. Get available capital from all partners (FIFO by created_at)
    partners_resp = supabase_client.table("partners") \
        .select("id, available_capital") \
        .gt("available_capital", 0) \
        .order("created_at", desc=False) \
        .execute()


    partners = partners_resp.data or []
    total_available_capital = sum(float(p["available_capital"]) for p in partners)

    # 3. Check if amount exceeds total available capital
    if amount > total_available_capital:
        flash(f"Insufficient available capital from partners (UGX {total_available_capital:,.0f}). Requested: UGX {amount:,.0f}", "error")
        return redirect(url_for('client.finance'))

    # 4. Deduct from partners using FIFO
    remaining = amount
    for partner in partners:
        partner_id = partner["id"]
        available = float(partner["available_capital"])

        if remaining <= 0:
            break

        used = min(available, remaining)
        new_available = available - used

        supabase_client.table("partners").update({
            "available_capital": new_available
        }).eq("id", partner_id).execute()

        remaining -= used

    # 5. Insert financing record
    supabase_client.table('client_financing').insert({
        'client_id': client_id,
        'amount': amount,
        'investment_date': investment_date,
        'expected_payback': expected_payback
    }).execute()

    # 6. Update client status
    supabase_client.table('clients').update({'status': 'financed'}).eq('id', client_id).execute()

    # 7. Generate QR Code
    qr_data = f"Client: {client['full_name']}, Amount: UGX {amount:,.0f}, Date: {investment_date}"
    qr_img = qrcode.make(qr_data)
    buf = io.BytesIO()
    qr_img.save(buf)
    qr_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')

    return render_template(
        'clients/finance_receipt.html',
        client=client,
        user=user_data,
        amount=amount,
        investment_date=investment_date,
        expected_payback=expected_payback,
        qr_code=qr_base64
    )


@client_bp.route('/documents', methods=['GET'])
@login_required
def documents_list():
    user_data = session.get('user')

    # Fetch all data
    clients_resp = supabase_client.table('clients').select('id, full_name').execute()
    clients = clients_resp.data or []

    docs_resp = supabase_client.table('documents').select('*').execute()
    documents = docs_resp.data or []

    # Calculate stats
    total_documents = len(documents)
    type_counts = {
        'passport': 0,
        'academic': 0,
        'medical': 0,
        'contract': 0,
        'visa': 0,
        'other': 0,
    }
    for doc in documents:
        if doc['type'] in type_counts:
            type_counts[doc['type']] += 1

    # Completion by client
    required_per_client = 4  # you can change this dynamically if needed
    completion_by_client = {}
    for client in clients:
        count = sum(1 for d in documents if d['client_id'] == client['id'])
        completion_by_client[client['id']] = count

    return render_template(
        'documents/list.html',
        clients=clients,
        documents=documents,
        type_counts=type_counts,
        total_documents=total_documents,
        completion_by_client=completion_by_client,
        required_per_client=required_per_client,
        user=user_data
    )


@client_bp.route('/documents/upload', methods=['POST'])
@login_required
def upload_document():
    user_data = session.get('user')
    client_id = request.form.get('client_id')
    doc_type = request.form.get('type')
    notes = request.form.get('notes', '')
    file = request.files.get('file')

    if not client_id or not doc_type or not file:
        flash('Missing fields or file', 'error')
        return redirect(url_for('client.documents_list'))

    filename = secure_filename(file.filename)

    # Check if file is an allowed image
    if not allowed_image_file(filename):
        flash('Invalid file type. Please upload an image file (png, jpg, jpeg, gif, bmp, tiff, webp).', 'error')
        return redirect(url_for('client.documents_list'))

    # Upload image to Cloudinary
    try:
        result = cloudinary.uploader.upload(file, folder="client_documents")
        image_url = result.get("secure_url")

        # Insert only the image URL and meta info in the database
        supabase_client.table('documents').insert({
            'client_id': client_id,
            'type': doc_type,
            'file_name': filename,
            'file_url': image_url,
            'uploaded_by_name': user_data.get('full_name', 'Unknown'),
            'notes': notes
        }).execute()

        flash('Image document uploaded successfully.', 'success')
        return redirect(url_for('client.documents_list'))

    except Exception as e:
        flash(f'Error uploading image: {str(e)}', 'error')
        return redirect(url_for('client.documents_list'))



@client_bp.route('/documents/delete/<doc_id>', methods=['POST'])
@login_required
def delete_document(doc_id):
    supabase_client.table('documents').delete().eq('id', doc_id).execute()
    flash("Document deleted", "success")
    return redirect(url_for('client.documents_list'))


@client_bp.route('/record_repayment', methods=['POST'])
@login_required
def record_repayment():
    client_id = request.form.get('client_id')
    financing_id = request.form.get('financing_id')
    amount_paid = float(request.form.get('paid_amount', 0))
    paid_date = request.form.get('paid_date')
    method = request.form.get('payment_method')
    notes = request.form.get('notes', '')

    if not client_id or not financing_id or amount_paid <= 0:
        flash("Incomplete or invalid repayment data.", "error")
        return redirect(url_for('client.view_financing'))

    # Validate client-financing relationship
    fin_resp = supabase_client.table('client_financing') \
        .select('id, expected_payback, paid_so_far, client_id') \
        .eq('id', financing_id).eq('client_id', client_id).single().execute()
    fin = fin_resp.data

    if not fin:
        flash("Invalid financing or client selected.", "error")
        return redirect(url_for('client.view_financing'))

    remaining = float(fin['expected_payback']) - float(fin.get('paid_so_far') or 0)
    if amount_paid > remaining:
        flash(f"Payment UGX {amount_paid:,.0f} exceeds outstanding UGX {remaining:,.0f}", "error")
        return redirect(url_for('client.view_financing'))

    # Insert repayment
    supabase_client.table('repayments').insert({
        'client_financing_id': financing_id,
        'amount_paid': amount_paid,
        'paid_date': paid_date,
        'payment_method': method,
        'notes': notes
    }).execute()

    # Update financing record
    new_paid = (fin.get('paid_so_far') or 0) + amount_paid
    new_status = 'paid' if abs(new_paid - float(fin['expected_payback'])) < 1e-2 else 'pending'

    supabase_client.table('client_financing').update({
        'paid_so_far': new_paid,
        'status': new_status
    }).eq('id', financing_id).execute()

    flash("Repayment recorded successfully.", "success")
    return redirect(url_for('client.view_financing'))



@client_bp.route('/view_financing')
@login_required
def view_financing():
    user_data = session.get('user')

    # Fetch clients
    clients_resp = supabase_client.table('clients').select('id, full_name').execute()
    clients = clients_resp.data or []

    # Fetch financing records
    financings_resp = supabase_client.table('client_financing') \
        .select('id, client_id, expected_payback, paid_so_far, amount, status') \
        .execute()
    financings = financings_resp.data or []

    # Fetch repayments and enrich with client names
    repayments_resp = supabase_client.table('repayments') \
        .select('id, client_financing_id, amount_paid, paid_date, payment_method, notes, client_financing(client_id)') \
        .execute()

    repayments_raw = repayments_resp.data or []

    # Add client_name to each repayment
    client_dict = {client['id']: client['full_name'] for client in clients}
    repayments = []
    for r in repayments_raw:
        client_id = r.get('client_financing', {}).get('client_id')
        repayments.append({
            'amount_paid': r['amount_paid'],
            'paid_date': r['paid_date'],
            'payment_method': r['payment_method'],
            'notes': r.get('notes'),
            'client_name': client_dict.get(client_id, 'Unknown')
        })

    return render_template(
        'clients/repayments.html',
        user=user_data,
        clients=clients,
        financings=financings,
        repayments=repayments,
        current_date=datetime.now().date().isoformat()  # optional, for default date
    )


def allowed_image_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png'}

def allowed_doc_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'pdf', 'jpg', 'jpeg', 'png'}