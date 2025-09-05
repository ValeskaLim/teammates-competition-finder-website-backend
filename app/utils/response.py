from flask import jsonify

def success_response(message = "Success", data=None, status=200):
    return jsonify({
        "data": data,
        "message": message,
        "success": True,
    }), status

def error_response(message = "Error", data=None, status=500):
    return jsonify({
        "data": data,
        "message": message,
        "success": False,
    }), status