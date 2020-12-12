import json
from flask import request, _request_ctx_stack
from functools import wraps
from jose import jwt
from urllib.request import urlopen

AUTH0_DOMAIN = 'mfragab.eu.auth0.com'
ALGORITHMS = [ 'RS256' ]
API_AUDIENCE = 'app'

## AuthError Exception
'''
AuthError Exception
A standardized way to communicate auth failure modes
'''


class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


## Auth Header

def get_token_auth_header():
    # check if Authorization is sent in request headers
    if 'Authorization' not in request.headers:
        raise AuthError({
            'code': 'authorization_header_notFound',
            'description': 'Authorization header was expected but not found.'
        }, 401)
    else:
        auth_head = request.headers[ 'Authorization' ]
        auth_parts = auth_head.split(' ')

        if len(auth_parts) < 2:
            raise AuthError({
                'code': 'authorization_header_invalid_token',
                'description': 'Authorization header must contain token after type space separated.'
            }, 401)
        elif len(auth_parts) > 2:
            raise AuthError({
                'code': 'authorization_header_invalid',
                'description': 'Authorization header must contain only type and token space separated.'
            }, 401)

        elif len(auth_parts) == 2:
            auth_type = auth_parts[ 0 ].lower()
            if auth_type != 'bearer':
                raise AuthError({
                    'code': 'authorization_header_invalid_type',
                    'description': 'Authorization header must be of a type bearer.'
                }, 401)
            token = auth_parts[ 1 ]
            return token


def check_permissions(permission, payload):
    if 'permissions' not in payload:
        raise AuthError({
            'code': 'invalid_payload',
            'description': 'Unable to find permissions.'
        }, 400)
    elif permission not in payload[ 'permissions' ]:
        raise AuthError({
            'code': 'Access_Forbidden',
            'description': 'Permission not granted.'
        }, 403)
    else:
        return True


def verify_decode_jwt(token):
    jsonurl = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks = json.loads(jsonurl.read())
    unverified_header = jwt.get_unverified_header(token)
    rsa_key = {}
    if 'kid' not in unverified_header:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization malformed.'
        }, 401)

    for key in jwks[ 'keys' ]:
        if key[ 'kid' ] == unverified_header[ 'kid' ]:
            rsa_key = {
                'kty': key[ 'kty' ],
                'kid': key[ 'kid' ],
                'use': key[ 'use' ],
                'n': key[ 'n' ],
                'e': key[ 'e' ]
            }
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer='https://' + AUTH0_DOMAIN + '/'
            )

            return payload

        except jwt.ExpiredSignatureError:
            raise AuthError({
                'code': 'token_expired',
                'description': 'Token expired.'
            }, 401)

        except jwt.JWTClaimsError:
            raise AuthError({
                'code': 'invalid_claims',
                'description': 'Incorrect claims. Please, check the audience and issuer.'
            }, 401)
        except Exception:
            raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to parse authentication token.'
            }, 400)
    raise AuthError({
        'code': 'invalid_header',
        'description': 'Unable to find the appropriate key.'
    }, 400)


def requires_auth(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            try:
                payload = verify_decode_jwt(token)
                check_permissions(permission, payload)
            except:
                raise AuthError({
                    'code': 'Authorization_Failed',
                    'description': 'sorry permission not granted.'
                }, 401)
            return f(payload, *args, **kwargs)

        return wrapper

    return requires_auth_decorator
