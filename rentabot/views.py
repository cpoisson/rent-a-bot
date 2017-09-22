from rentabot import app


@app.route('/')
def index():
    return '<h1>Rent-A-Bot</h1>'
