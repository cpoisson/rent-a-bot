# Rent-A-Bot


## Purpose
Rent-a-bot is a RestFull application dedicated to assign to a 3rd party application a network ressource.


## How to install and run

Clone the repository

```commandline
git clone git@gitlab.com:cpoisson/rent-a-bot.git
```

Create a virtual env (here using virtualenv wrapper)

```commandline
mkvirtualenv ren-t-abot
workon rent-a-bot
```

Install the package

```commandline
pip install .   # Add -e if you want to install it in dev mode
```
Add Flask environment variables

```commandline
export FLASK_APP=rentabot

export FLASK_DEBUG=true # If you need the debug mode
```

And... run!


```commandline
flask run
```

