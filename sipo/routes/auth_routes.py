
from flask import Blueprint, jsonify, request, g
from utils.auth import token_required, generate_token

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/auth/exchange-token', methods=['POST'])
def exchange_token():
    """
    Exchanges an Active Directory token for a backend JWT token.
    This endpoint accepts the AD authentication data and issues a backend JWT.
    
    Expected payload:
    {
        "adToken": "...",
        "userData": {
            "username": "...",
            "idLegal": "...",
            "role": "...",
            ...
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'message': 'No data provided'}), 400
            
        # Extract user data from the request
        # The frontend should send the user information after AD authentication
        user_data = data.get('userData', {})
        
        if not user_data:
            return jsonify({'message': 'User data is required'}), 400
        
        # Generate a backend JWT token with the user data
        # This token will be signed with our secret key
        token_payload = {
            'username': user_data.get('username'),
            'idLegal': user_data.get('idLegal'),
            'role': user_data.get('role'),
            'id': user_data.get('id'),
            'fullName': user_data.get('fullName')
        }
        
        backend_token = generate_token(token_payload)
        
        if not backend_token:
            return jsonify({'message': 'Error generating backend token'}), 500
            
        return jsonify({
            'status': 'success',
            'token': backend_token,
            'message': 'Backend token generated successfully'
        })
        
    except Exception as e:
        return jsonify({'message': f'Error exchanging token: {str(e)}'}), 500

@auth_bp.route('/api/auth/renew', methods=['POST'])
@token_required
def renew_token():
    """
    Renews the current valid token.
    Requires a valid Bearer token in the Authorization header.
    Returns a new token with refreshed expiration.
    """
    try:
        current_user = g.user
        # Remove 'exp' along with 'iat' to generate fresh timestamps
        current_user.pop('exp', None)
        current_user.pop('iat', None)
        
        new_token = generate_token(current_user)
        
        if not new_token:
            return jsonify({'message': 'Error generating token'}), 500
            
        return jsonify({
            'status': 'success',
            'token': new_token
        })
    except Exception as e:
        return jsonify({'message': f'Error renewing token: {str(e)}'}), 500
