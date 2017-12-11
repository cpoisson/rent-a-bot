# -*- coding: utf-8 -*-
"""
rentabot.views
~~~~~~~~~~~~~~

This module contains rent-a-bot RESTful interface.
"""


from rentabot import app
from rentabot.controllers import get_all_ressources, get_resource_from_id, lock_resource, unlock_resource
from rentabot.exceptions import ResourceException, ResourceNotFound
from rentabot.exceptions import ResourceAlreadyLocked, ResourceAlreadyUnlocked, InvalidLockToken

from flask import jsonify, render_template
from flask import request


# - [ Web View ] --------------------------------------------------------------

@app.route('/')
def index():
    # Query all resources
    resources = get_all_ressources()
    return render_template('display_resources.html', resources=resources)


# - [ API ] ------------------------------------------------------------------


# - [ GET : Access to resources information ]

@app.route('/rentabot/api/v1.0/resources', methods=['GET'])
def get_resources():
    # Query all resources
    resources = [resource.dict for resource in get_all_ressources()]
    return jsonify({'resources': resources})


@app.route('/rentabot/api/v1.0/resources/<int:resource_id>', methods=['GET'])
def get_resource(resource_id):
    resource = get_resource_from_id(resource_id)
    return jsonify({'resource': resource.dict})


# - [ POST : Acquire and release resource lock ]

@app.route('/rentabot/api/v1.0/resources/<int:resource_id>/lock', methods=['POST'])
def lock_by_id(resource_id):
    lock_token, resource = lock_resource(rid=resource_id)
    response = {
        'message': 'Resource locked',
        'lock-token': lock_token,
        'resource': resource.dict
    }
    return jsonify(response), 200


@app.route('/rentabot/api/v1.0/resources/<int:resource_id>/unlock', methods=['POST'])
def unlock_by_id(resource_id):
    lock_token = request.args.get('lock-token')
    unlock_resource(resource_id, lock_token)
    response = {
        'message': 'Resource unlocked'
    }
    return jsonify(response), 200


@app.route('/rentabot/api/v1.0/resources/lock', methods=['POST'])
def lock_by_criterias():
    resource_id = request.args.get('id')
    resource_name = request.args.get('name')
    resource_tags = request.args.getlist('tag')
    lock_token, resource = lock_resource(rid=resource_id, name=resource_name, tags=resource_tags)
    response = {
        'message': 'Resource locked',
        'lock-token': lock_token,
        'resource': resource.dict
    }
    return jsonify(response), 200


# - [ API : Error Responses Handler ] ----------------------------------------

@app.errorhandler(ResourceException)         # 400 - BAD REQUEST
@app.errorhandler(ResourceNotFound)          # 404 - NOT FOUND
@app.errorhandler(ResourceAlreadyLocked)     # 403 - FORBIDDEN
@app.errorhandler(ResourceAlreadyUnlocked)   # 403 - FORBIDDEN
@app.errorhandler(InvalidLockToken)          # 403 - FORBIDDEN
def handle_error_response(error):
    response = jsonify(error.dict)
    response.status_code = error.status_code
    return response



