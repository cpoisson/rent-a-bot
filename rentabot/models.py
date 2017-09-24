from rentabot import app
from flask_sqlalchemy import SQLAlchemy
import os

# Set database
db_path = '/tmp/rent-a-bot.sqlite'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# TODO: Add BotModel Class, Mandatory to limit bot models possibility


class Bot(db.Model):
    """ Bot class.

        Bot class describes the model of a bot.
    """
    id = db.Column(db.Integer, primary_key=True)            # Id
    name = db.Column(db.String(80), unique=True)            # Unique name
    ip_address = db.Column(db.String(80), unique=True)      # IPV4 Address
    model = db.Column(db.String(160))                       # Bot model
    status = db.Column(db.Integer)                          # Bot Status
    status_details = db.Column(db.String(160))              # Bot Status Details

    BOT_STATUS = {
        'disabled': 0,
        'ready': 1,
        'busy': 2
    }

    def __init__(self, name, ip_address, model):
        self.name = name
        self.ip_address = ip_address
        self.model = model
        self.status = self.BOT_STATUS['disabled']
        self.status_details = 'Initialising...'

    @property
    def dict(self):
        bot = {
            'id': self.id,
            'name': self.name,
            'ip_address': self.ip_address,
            'model': self.model,
            'status': self.status,
            'status_details': self.status_details
        }
        return bot

    def __repr__(self):
        return str(self.dict)


# Create database if the file does not exist
if not os.path.exists(db_path):
    db.create_all()
    db.session.commit()
