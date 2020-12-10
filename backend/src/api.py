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
def get_drinks_details():
    all_drinks = Drink.query.order_by('id').all()
    drinks = [ drink.long() for drink in all_drinks ]

    return jsonify({
        "success": True,
        "drinks": drinks
    })


@app.route('/drinks', methods=[ 'POST' ])
@requires_auth(permission='post:drinks')
def add_new_drink():
    body = request.get_json()

    title = body.get('title', None)
    recipe = json.dumps(body.get('recipe', None))

    try:
        if title is None or recipe is None:

            abort(400)
        else:
            drink = Drink(
                title=title,
                recipe=recipe
            )
            drink.insert()


    except:
        abort(422)

    finally:
        new_drink = Drink.query.filter(Drink.title == title).first()
        drink = new_drink.long()
        return jsonify({
            'success': True,
            'drinks': drink
        })


@app.route('/drinks/<int:drink_id>', methods=[ 'PATCH' ])
@requires_auth(permission='patch:drinks')
def update_drink_details(drink_id):
    body = request.get_json()
    drink = Drink.query.filter_by(id=drink_id).one_or_none()
    if drink:
        if 'title' in body:
            if 'recipe' in body:
                drink.title = body.get('title')
                drink.recipe = json.dumps(body.get('recipe'))
                drink.update()
                new_drink = Drink.query.get(drink_id)
                drink = new_drink.long()
                return jsonify({
                    'success': True,
                    'drinks': drink

                })

            else:
                abort(400)
        else:
            abort(400)
    else:
        abort(404)


@app.route('/drinks/<int:drink_id>', methods=[ 'DELETE' ])
@requires_auth(permission='delete:drinks')
def delete_user_drink(drink_id):
    drink = Drink.query.get(drink_id)
    if drink:
        drink.delete()
        return jsonify({

            'success': True,
            'delete': drink_id
        })
    else:
        abort(404)


## Error Handling
'''
Example error handling for unprocessable entity
'''


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


@app.errorhandler(404)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "Not-Found"
    }), 404


@app.errorhandler(400)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": "Bad-Request"
    }), 400


'''
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False, 
                    "error": 404,
                    "message": "resource not found"
                    }), 404

'''

'''
@TODO implement error handler for 404
    error handler should conform to general task above 
'''

'''
@TODO implement error handler for AuthError
    error handler should conform to general task above 
'''
