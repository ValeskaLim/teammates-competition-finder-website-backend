from flask import Blueprint, send_from_directory, request
from app.models import ProofTransaction, Teams, Users, Competition
from app.routes.generic import UPLOAD_FOLDER
from app.utils.response import success_response, error_response

proof_transaction_bp = Blueprint('proof_transaction', __name__, url_prefix="/proof-transaction")

@proof_transaction_bp.route("/get-all-transactions", methods=["POST"])
def get_all_transactions():
    try:
        query = ProofTransaction.query
        team_query = Teams.query

        transactions = query.filter(ProofTransaction.status == "CONFIRMED").all()

        results = []
        for txn in transactions:
            results.append({
                "proof_transaction_id": txn.proof_transaction_id,
                "txn_hash": txn.txn_hash,
                "team_name": team_query.filter(Teams.team_id == txn.team_id).first().team_name,
                "proof_image_path": txn.proof_image_path,
                "txn_hash_path": txn.txn_hash_path,
                "status": txn.status,
                "block_number": txn.block_number,
                "competition_name": Competition.query.filter(Competition.competition_id == txn.competition_id).first().title,
            })

        return success_response("Transactions retrieved successfully", data=results, status=200)

    except Exception as e:
        return error_response(f"Error fetching transactions: {str(e)}", status=500)
     
@proof_transaction_bp.route("/uploads/<filename>", methods=['GET'])
def get_uploaded_file(filename):
    try:
        print("File name:", filename, flush=True)
        return send_from_directory("/app/uploads/proof_txn", filename)
    except Exception as e:
        return error_response(f"File not found: {str(e)}", status=404)
    
@proof_transaction_bp.route("/get-proof-transaction", methods=['POST'])
def get_proof_transaction_by_team_id():
    try:
        data = request.get_json()
        team_id = data.get("team_id")
        query = ProofTransaction.query
        
        txn = query.filter(ProofTransaction.team_id == team_id).first()
        
        if not txn:
            return error_response("No proof transaction found for the given team ID", status=404)
        
        custom_txn = {
            "txn_hash_path": txn.txn_hash_path,
            "proof_image_path": txn.proof_image_path,
        }

        return success_response("Proof transaction retrieved successfully", data=custom_txn, status=200)

    except Exception as e:
        return error_response(f"Error fetching proof transaction: {str(e)}", status=500)