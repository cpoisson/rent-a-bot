# Rent-A-Bot

[![Build Status](https://travis-ci.org/cpoisson/rent-a-bot.svg?branch=master)](https://travis-ci.org/cpoisson/rent-a-bot)
[![codecov](https://codecov.io/gh/cpoisson/rent-a-bot/branch/master/graph/badge.svg)](https://codecov.io/gh/cpoisson/rent-a-bot)
[![pipeline status](https://gitlab.com/cpoisson/rent-a-bot/badges/master/pipeline.svg)](https://gitlab.com/cpoisson/rent-a-bot/commits/master)
[![coverage report](https://gitlab.com/cpoisson/rent-a-bot/badges/master/coverage.svg)](https://gitlab.com/cpoisson/rent-a-bot/commits/master)

---

## Purpose

Rent-a-bot, your automation resource provider.

Exclusive access to a resource is a common problem in automation, rent-a-bot allows you to define a pool of resources 
and obtain an exclusive access to a given resource.

---

## Resource 

A resource is defined by:

- A Name
- A Description
- An end point
- Tags
- A state (available or locked)
- A state description

---

## How to install and run

Clone the repository from GitLab or GitHub

```commandline
git clone git@gitlab.com:cpoisson/rent-a-bot.git
```

```commandline
git clone git@github.com:cpoisson/rent-a-bot.git
```

Create a virtual env (here using virtualenv wrapper)

```commandline
mkvirtualenv rent-a-bot
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

---

## How to tests

### Tests implementation

Unit tests are done using py.test and coverage

### How to run unit tests

```commandline
python setup.py test
```

---

## Helpful documentation used to design this application

- [Designing a RESTful API with Python and Flask](https://blog.miguelgrinberg.com/post/designing-a-restful-api-with-python-and-flask)
- [Testing Flask Applications](http://flask.pocoo.org/docs/0.12/testing/#testing)
- [Flask Project Template](https://github.com/xen/flask-project-template)
- [Flask SQLAlchemy](http://flask-sqlalchemy.pocoo.org/2.1/quickstart/)
- [Put versus Post](https://knpuniversity.com/screencast/rest/put-versus-post)
- [Best practice for a pragmatic restful API](http://www.vinaysahni.com/best-practices-for-a-pragmatic-restful-api#ssl)
- [Implementing a RESTful Web API with Python & Flask](http://blog.luisrei.com/articles/flaskrest.html)
