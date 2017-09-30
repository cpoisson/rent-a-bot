# -*- coding: utf-8 -*-
"""
rentabot.views
~~~~~~~~~~~~~~

This module contains rent-a-bot RESTful interface.
"""


from rentabot import app
from rentabot.models import Resource
from rentabot.controllers import lock_resource, unlock_resource
from rentabot.exceptions import ResourceAlreadyLocked, InvalidLockToken, ResourceNotFound

from flask import jsonify
from flask import abort, make_response
from flask import url_for
from flask import request


# - [ Web View ] --------------------------------------------------------------

@app.route('/')
def index():
    return '<h1>Rent-A-Bot</h1>'


# - [ API ] ------------------------------------------------------------------


def make_public_uri(resource):
    resource = resource.dict
    new_resource = dict()
    for field in resource:
        if field == 'id':
            new_resource['uri'] = url_for('get_resource', resource_id=resource['id'], _external=True)
        else:
            new_resource[field] = resource[field]
    return new_resource


# - [ GET : Access to resources information ]

@app.route('/rentabot/api/v1.0/resources', methods=['GET'])
def get_resources():
    return jsonify({'resources': map(make_public_uri, Resource.query.all())})


@app.route('/rentabot/api/v1.0/resources/<int:resource_id>', methods=['GET'])
def get_resource(resource_id):

    resource = Resource.query.filter_by(id=resource_id).first()

    if resource is None:
        raise ResourceNotFound(message="Resource not found",
                               payload={'resource_id': resource_id})
    return jsonify({'resource': make_public_uri(resource)})


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
    except InvalidLockToken:
        raise InvalidLockToken(message="Cannot unlock resource, the lock token is not valid.",
                               payload={'resource': resource.dict,
                                        'invalid-lock-token': lock_token})
    else:
        return jsonify({'lock-key': 'Resource unlocked'}), 200


# - [ API : Error Responses Handler ] ----------------------------------------

@app.errorhandler(ResourceNotFound)          # 404 - NOT FOUND
@app.errorhandler(ResourceAlreadyLocked)     # 423 - LOCKED
@app.errorhandler(InvalidLockToken)          # 403 - FORBIDDEN
def handle_error_response(error):
    response = jsonify(error.dict)
    response.status_code = error.status_code
    return response



