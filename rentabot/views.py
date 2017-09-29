# -*- coding: utf-8 -*-
"""
rentabot.views
~~~~~~~~~~~~~~

This module contains rent-a-bot RESTful interface.
"""


from rentabot import app
from rentabot.models import Resource
from rentabot.controllers import lock_resource, unlock_resource
from rentabot.exceptions import ResourceNotAvailable, InvalidLockKey

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


# - [ GET ]

@app.route('/rentabot/api/v1.0/resources', methods=['GET'])
def get_resources():
    return jsonify({'resources': map(make_public_uri, Resource.query.all())})


@app.route('/rentabot/api/v1.0/resources/<int:resource_id>', methods=['GET'])
def get_resource(resource_id):
    resource = Resource.query.filter_by(id=resource_id).first()
    if resource is None:
        abort(404)
    return jsonify({'resource': make_public_uri(resource)})


# - [ GET : Acquire and release resource lock ]

@app.route('/rentabot/api/v1.0/resources/<int:resource_id>/lock', methods=['GET'])
def lock_by_id(resource_id):
    resource = Resource.query.filter_by(id=resource_id).first()
    if resource is None:
        abort(404)
    try:
        lock_key = lock_resource(resource)
    except ResourceNotAvailable:
        abort(404)
    return jsonify({'lock-key': lock_key})


# TODO: Add an unlock directly by lock_key e.g. resources/unlock?lock-key=xxxxx
@app.route('/rentabot/api/v1.0/resources/<int:resource_id>/unlock', methods=['GET'])
def unlock_by_id(resource_id):
    resource = Resource.query.filter_by(id=resource_id).first()
    if resource is None:
        abort(404)
    lock_key = request.args.get('lock-key')

    try:
        unlock_resource(resource, lock_key)
    except InvalidLockKey:
        abort(404)
    return jsonify({'lock-key': 'Resource released.'})


# - [ 404 ]

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)
