# -*- coding: utf-8 -*-
"""
rentabot.views
~~~~~~~~~~~~~~

This module contains rent-a-bot RESTful interface.
"""


from rentabot import app
from rentabot.models import Resource
from rentabot.controllers import lock_resource, unlock_resource
from rentabot.exceptions import ResourceAlreadyLocked, ResourceAlreadyUnlocked, InvalidLockToken, ResourceNotFound

from flask import jsonify, render_template
from flask import request


# - [ Web View ] --------------------------------------------------------------

@app.route('/')
def index():
    # Query all resources
    resources = [resource for resource in Resource.query.all()]
    return render_template('display_resources.html', resources=resources)


# - [ API ] ------------------------------------------------------------------


# - [ GET : Access to resources information ]

@app.route('/rentabot/api/v1.0/resources', methods=['GET'])
def get_resources():
    # Query all resources
    resources = [resource.dict for resource in Resource.query.all()]
    return jsonify({'resources': resources})


@app.route('/rentabot/api/v1.0/resources/<int:resource_id>', methods=['GET'])
def get_resource(resource_id):

    resource = Resource.query.filter_by(id=resource_id).first()

    if resource is None:
        raise ResourceNotFound(message="Resource not found",
                               payload={'resource_id': resource_id})
    return jsonify({'resource': resource.dict})


# - [ POST : Acquire and release resource lock ]

@app.route('/rentabot/api/v1.0/resources/<int:resource_id>/lock', methods=['POST'])
def lock_by_id(resource_id):

    resource = Resource.query.filter_by(id=resource_id).first()

    if resource is None:
        raise ResourceNotFound(message="Resource not found",
                               payload={'resource_id': resource_id})
    try:
        lock_token = lock_resource(resource)
    except ResourceAlreadyLocked:
        raise ResourceAlreadyLocked(message="Cannot lock resource, resource is already locked",
                                    payload={'resource': resource.dict})
    else:
        response = {
            'message': 'Resource locked',
            'lock-token': lock_token,
            'resource': resource.dict
        }
        return jsonify(response), 200


@app.route('/rentabot/api/v1.0/resources/<int:resource_id>/unlock', methods=['POST'])
def unlock_by_id(resource_id):

    resource = Resource.query.filter_by(id=resource_id).first()

    if resource is None:
        raise ResourceNotFound(message="Resource not found",
                               payload={'resource_id': resource_id})

    lock_token = request.args.get('lock-token')

    try:
        unlock_resource(resource, lock_token)
    except ResourceAlreadyUnlocked:
        raise ResourceAlreadyUnlocked(message="Cannot unlock resource, the resource is already unlocked.",
                                      payload={'resource': resource.dict})
    except InvalidLockToken:
        raise InvalidLockToken(message="Cannot unlock resource, the lock token is not valid.",
                               payload={'resource': resource.dict,
                                        'invalid-lock-token': lock_token})
    else:
        response = {
            'message': 'Resource unlocked',
            'resource': resource.dict
        }
        return jsonify(response), 200


# - [ API : Error Responses Handler ] ----------------------------------------

@app.errorhandler(ResourceNotFound)          # 404 - NOT FOUND
@app.errorhandler(ResourceAlreadyLocked)     # 403 - FORBIDDEN
@app.errorhandler(ResourceAlreadyUnlocked)   # 403 - FORBIDDEN
@app.errorhandler(InvalidLockToken)          # 403 - FORBIDDEN
def handle_error_response(error):
    response = jsonify(error.dict)
    response.status_code = error.status_code
    return response



