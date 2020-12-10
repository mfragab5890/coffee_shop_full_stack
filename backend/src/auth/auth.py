import json
from flask import request, _request_ctx_stack
from functools import wraps
from jose import jwt
from urllib.request import urlopen


AUTH0_DOMAIN = 'mfragab.eu.auth0.com'
ALGORITHMS = ['RS256']
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
            auth_type = auth_parts[0].lower()
            if auth_type != 'bearer':
                raise AuthError({
                    'code': 'authorization_header_invalid_type',
                    'description': 'Authorization header must be of a type bearer.'
                }, 401)
            token = auth_parts[ 1 ]
            return token

'''
@TODO implement check_permissions(permission, payload) method
    @INPUTS
        permission: string permission (i.e. 'post:drink')
        payload: decoded jwt payload

    it should raise an AuthError if permissions are not included in the payload
        !!NOTE check your RBAC settings in Auth0
    it should raise an AuthError if the requested permission string is not in the payload permissions array
    return true otherwise
'''
def check_permissions(permission, payload):
    raise Exception('Not Implemented')

'''
@TODO implement verify_decode_jwt(token) method
    @INPUTS
        token: a json web token (string)

    it should be an Auth0 token with key id (kid)
    it should verify the token using Auth0 /.well-known/jwks.json
    it should decode the payload from the token
    it should validate the claims
    return the decoded payload

    !!NOTE urlopen has a common certificate error described here: https://stackoverflow.com/questions/50236117/scraping-ssl-certificate-verify-failed-error-for-http-en-wikipedia-org
'''

def verify_decode_jwt(token):
    json_url = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks = json.loads(json_url.read())
    unverified_header = jwt.get_unverified_header(token)
    rsa_key = {}
    if 'kid' not in unverified_header:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization malformed.'
        }, 401)

    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
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

'''
@TODO implement @requires_auth(permission) decorator method
    @INPUTS
        permission: string permission (i.e. 'post:drink')

    it should use the get_token_auth_header method to get the token
    it should use the verify_decode_jwt method to decode the jwt
    it should use the check_permissions method validate claims and check the requested permission
    return the decorator which passes the decoded payload to the decorated method
'''
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


