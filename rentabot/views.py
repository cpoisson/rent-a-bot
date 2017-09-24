from rentabot import app
from rentabot.models import Bot

from flask import jsonify
from flask import abort, make_response
from flask import url_for


@app.route('/')
def index():
    return '<h1>Rent-A-Bot</h1>'


def make_public_bot(bot):
    bot = bot.dict
    new_bot = dict()
    for field in bot:
        if field == 'id':
            new_bot['uri'] = url_for('get_bot', bot_id=bot['id'], _external=True)
        else:
            new_bot[field] = bot[field]
    return new_bot


@app.route('/rentabot/api/v1.0/bots', methods=['GET'])
def get_bots():
    return jsonify({'bots': map(make_public_bot, Bot.query.all())})


@app.route('/rentabot/api/v1.0/bots/<int:bot_id>', methods=['GET'])
def get_bot(bot_id):
    bot = Bot.query.filter_by(id=bot_id).first()
    if bot is None:
        abort(404)
    return jsonify({'bot': bot.dict})


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)