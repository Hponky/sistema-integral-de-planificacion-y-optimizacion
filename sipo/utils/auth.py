
import jwt
import datetime
from functools import wraps
from flask import request, jsonify, current_app

def generate_token(user_data, expires_in=3153600000):  # 100 years in seconds
    """
    Generates a JWT token signed with HS256 and the app's secret key.
    
    Args:
        user_data (dict): Data to store in the token payload.
        expires_in (int): Expiration time in seconds.
        
    Returns:
        str: The generated token.
    """
    try:
        payload = {
            'iat': datetime.datetime.utcnow(),
            **user_data
        }
        
        token = jwt.encode(
            payload,
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        return token
    except Exception as e:
        return None

def validate_token(token):
    """
    Validates a JWT token.
    
    Args:
        token (str): The token to validate.
        
    Returns:
        dict: The decoded payload if valid, None otherwise.
        
    Raises:
        jwt.ExpiredSignatureError: If the token has expired.
        jwt.InvalidTokenError: If the token is invalid.
    """
    try:
        payload = jwt.decode(
            token, 
            current_app.config['SECRET_KEY'], 
            algorithms=['HS256']
        )
        return payload
    except Exception as e:
        raise e

def token_required(f):
    """
    Decorator to protect routes with JWT authentication.
    Expects Authorization: Bearer <token>
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Permite peticiones OPTIONS para CORS sin validar token
        if request.method == 'OPTIONS':
            return '', 200
            
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0] == 'Bearer':
                token = parts[1]
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
            
        try:
            payload = validate_token(token)
            # You can inject the current_user into kwargs or g if needed
            # For now, we optionally pass the payload or user_id if the function expects it
            # But usually we store it in flask.g
            from flask import g
            g.user = payload
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token!'}), 401
        except Exception as e:
            return jsonify({'message': f'Token validation failed: {str(e)}'}), 401
            
        return f(*args, **kwargs)
        
    return decorated
