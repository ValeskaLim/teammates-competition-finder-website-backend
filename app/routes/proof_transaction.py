from flask import Blueprint, send_from_directory
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