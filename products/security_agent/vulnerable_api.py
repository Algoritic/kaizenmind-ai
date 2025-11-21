from flask import Flask, request, jsonify
import time

app = Flask(__name__)

# --- DATABASE MOCK ---
users = {
    "101": {"name": "Alice", "role": "user", "balance": 50, "data": "Alice's Private Secrets"},
    "102": {"name": "Bob", "role": "user", "balance": 100, "data": "Bob's Sensitive Medical Data"},
    "103": {"name": "Charlie", "role": "admin", "balance": 9999, "data": "Admin Keys"}
}

# --- VULNERABILITY 1: API1 (BOLA) ---
# Vulnerable: It doesn't check if the logged-in user matches the requested ID
@app.route('/users/<user_id>/data', methods=['GET'])
def get_user_data(user_id):
    # Fake Auth Check (In reality, this is where the BOLA check is missing)
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"error": "Unauthorized"}), 401
    
    if user_id in users:
        return jsonify(users[user_id])
    return jsonify({"error": "User not found"}), 404

# --- VULNERABILITY 2: API3 (Mass Assignment) ---
# Vulnerable: It accepts any field in JSON, including 'role' and 'is_admin'
@app.route('/users', methods=['POST'])
def create_user():
    data = request.json
    # SECURITY FLAW: blindly accepting 'role' or 'is_admin' from user input
    response = {
        "message": "User created",
        "username": data.get("username"),
        "role": data.get("role", "user"), # VULNERABLE: echoes back injected role
        "is_admin": data.get("is_admin", False) # VULNERABLE: echoes back injected admin status
    }
    return jsonify(response), 201

# --- VULNERABILITY 3: API5 (Broken Function Level Auth) ---
# Vulnerable: No check to see if the user is actually an admin
@app.route('/admin/system_reset', methods=['DELETE'])
def admin_reset():
    auth_header = request.headers.get('Authorization')
    # SECURITY FLAW: Only checking if a token exists, not if it's an admin token
    if not auth_header:
        return jsonify({"error": "Unauthorized"}), 401
    
    return jsonify({"message": "CRITICAL: System reset initiated by standard user!"}), 200

# --- VULNERABILITY 4: API7 (SSRF) ---
# Vulnerable: Fetches any URL provided in the 'url' parameter
@app.route('/fetch_avatar', methods=['GET'])
def fetch_avatar():
    target_url = request.args.get('url')
    if not target_url:
        return jsonify({"error": "Missing url parameter"}), 400
    
    # SECURITY FLAW: No whitelist on the domain
    if "localhost" in target_url or "127.0.0.1" in target_url or "169.254" in target_url:
         return jsonify({"status": "Fetched internal resource successfully (Vulnerable!)"}), 200
         
    return jsonify({"status": "Fetched external image"}), 200

# --- VULNERABILITY 5: API4 (Rate Limiting) ---
# Vulnerable: No logic to block rapid requests
@app.route('/public/info', methods=['GET'])
def public_info():
    # Simulating work
    time.sleep(0.05)
    return jsonify({"info": "Public API Data", "timestamp": time.time()}), 200

if __name__ == '__main__':
    # Run on port 5000
    app.run(debug=True, port=5000)