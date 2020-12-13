import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS
from src.database.models import db_drop_and_create_all, setup_db, Drink
from src.auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)


# db_drop_and_create_all()

## ROUTES

@app.route('/drinks', methods=[ 'GET' ])
def get_drinks_brief():
    all_drinks = Drink.query.order_by('id').all()
    drinks = [ drink.short() for drink in all_drinks ]

    return jsonify({
        "success": True,
        "drinks": drinks
    })


@app.route('/drinks-detail', methods=[ 'GET' ])
@requires_auth(permission='get:drinks-detail')
def get_drinks_details(permission):
    all_drinks = Drink.query.order_by('id').all()
    drinks = [ drink.long() for drink in all_drinks ]

    return jsonify({
        "success": True,
        "drinks": drinks
    })


@app.route('/drinks', methods=[ 'POST' ])
@requires_auth(permission='post:drinks')
def add_new_drink(permission):
    body = request.get_json()

    title = body.get('title', None)
    recipe = body.get('recipe', None)
    try:
        if title is None or recipe is None:

            abort(400)
        else:
            drink = Drink(
                title=title,
                recipe=recipe if type(recipe) == str else json.dumps(recipe)
            )
            drink.insert()


    except:
        abort(422)

    finally:
        new_drink = Drink.query.filter(Drink.title == title).first()
        drink = [new_drink.long()]
        return jsonify({
            'success': True,
            'drinks': drink
        })


@app.route('/drinks/<int:drink_id>', methods=[ 'PATCH' ])
@requires_auth(permission='patch:drinks')
def update_drink_details(permession, drink_id):
    body = request.get_json()
    drink = Drink.query.filter_by(id=drink_id).one_or_none()
    if drink:
        if 'title' in body or 'recipe' in body:
            if 'recipe' in body:
                recipe = body.get('recipe')
                drink.recipe = recipe if type(recipe) == str else json.dumps(recipe)
            if 'title' in body:
                drink.title = body.get('title')
            drink.update()
            new_drink = Drink.query.get(drink_id)
            drink = [new_drink.long()]
            return jsonify({
                'success': True,
                'drinks': drink

            })

        else:
            abort(400)
    else:
        abort(404)


@app.route('/drinks/<int:drink_id>', methods=[ 'DELETE' ])
@requires_auth(permission='delete:drinks')
def delete_user_drink(permession, drink_id):
    drink = Drink.query.get(drink_id)
    if drink:
        drink.delete()
        return jsonify({

            'success': True,
            'delete': drink_id
        })
    else:
        abort(404)


# ----------------------------------------------------------------------------#
# Error Handlers.
# ----------------------------------------------------------------------------#
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": 'Not found!!! : please check your Data or maybe your request is currently not available.'
    }), 404


@app.errorhandler(422)
def not_processable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": 'Unprocessable!!! : The request was well-formed but was unable to be followed'
    }), 422


@app.errorhandler(405)
def not_allowed_method(error):
    return jsonify({
        "success": False,
        "error": 405,
        "message": 'Method Not Allowed!!!: Your request method not supported by that API '
    }), 405


@app.errorhandler(400)
def not_good_request(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": 'Bad Request!!!! Please make sure the data you entered is correct'
    }), 400


@app.errorhandler(500)
def server_error(error):
    return jsonify({
        "success": False,
        "error": 500,
        "message": 'Internal Server Error!!!: Please try again later or reload request. '
    }), 500


'''
@TODO implement error handler for AuthError
    error handler should conform to general task above 
'''


@app.errorhandler(401)
def Unauthorized(error):
    return jsonify({
        "success": False,
        "error": 401,
        "message": 'Unauthorized. '
    }), 401


@app.errorhandler(403)
def forbidden_access(error):
    return jsonify({
        "success": False,
        "error": 403,
        "message": 'Access to the requested resource is forbidden. '
    }), 403


@app.errorhandler(AuthError)
def handle_auth_error(ex):
    """
    handling authorization errors
    """
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response
