import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink, db
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
todo: Add comments, rerun the postman tests to comfirm one more time, use pip8 to format it, commit and push
run some final tests, zip and submit
'''

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
db_drop_and_create_all()

# ROUTES


@app.route('/drinks')
def drinks():
    # Get the short details of all drinks and put them in an array
    drinks = Drink.query.all()
    drinkList = [drink.short() for drink in drinks]

    return jsonify({
        'status': "OK",
        'success': True,
        'drinks': drinkList
    })


@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')  # authentication and authorization
def drinksDetails(payload):
    # get the full details of the drink
    drinks = Drink.query.all()
    drinkList = [drink.long() for drink in drinks]

    return jsonify({
        'status': "OK",
        'success': True,
        'drinks': drinkList
    })


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def addDrinks(payload):
    # get the json body from the request
    drinkTitle = request.json.get('title')
    drinkRecipe = request.json.get('recipe')

    if drinkTitle is None or drinkRecipe is None:
        abort(422)
    else:
        # get all drink titles and compare to the drinkTitle to check for
        # uniqueness
        titles = Drink.query.all()
        getTitles = [title.title for title in titles]

        if drinkTitle not in getTitles:
            recipe = json.dumps(drinkRecipe)
            drinks = Drink(title=drinkTitle, recipe=recipe)
            drinks.insert()

            return jsonify({
                'success': True,
                'drinks': drinks.long()
            })
        else:
            return jsonify({
                'success': False,
                'Message': 'Title already exist.'
            })


@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def editDrinks(payload, id):
    # get the json body
    drinkTitle = request.json.get('title')
    getRecipe = request.json.get('recipe')

    drink = Drink.query.get(id)  # Get the object to be edited

    # get all drink titles and compare to the drinkTitle to check for
    # uniqueness
    titles = Drink.query.all()
    getTitles = [title.title for title in titles]

    if drinkTitle not in getTitles:
        if drinkTitle and getRecipe:
            recipe = json.dumps(getRecipe)
            drink.title = drinkTitle
            drink.recipe = recipe
            drink.update()

        elif drinkTitle:
            drink.title = drinkTitle
            drink.update()

        elif getRecipe:
            recipe = json.dumps(getRecipe)
            drink.recipe = recipe
            drink.update()

        else:
            abort(422)

        # make the drink object a list before passed to the frontend
        drinkList = [drink.long()]

        return jsonify({
            'success': True,
            'drinks': drinkList
        })
    else:
        return jsonify({
            'success': False,
            'Message': 'Title already exist.'
        })


@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def deleteDrinks(payload, id):
    try:
        drink = Drink.query.get(id)
        drink.delete()

        return jsonify({
            "success": True,
            "delete": id
        })
    except BaseException:
        db.session.rollback()
        abort(404)
    finally:
        db.session.close()


# Error Handling
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
        "message": "Not Found"
    }), 404


@app.errorhandler(400)
def badRequest(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": "Bad Request. One or more headers are missing"
    }), 400


@app.errorhandler(500)
def serverError(error):
    return jsonify({
        "success": False,
        "error": 500,
        "message": "Server error"
    }), 500


@app.errorhandler(AuthError)
def auth_error(error):
    return jsonify({
        "success": False,
        "error": error.status_code,
        "message": error.error['description']
    }), error.status_code
