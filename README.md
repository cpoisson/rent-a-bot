# Rent-A-Bot

[![Build Status](https://travis-ci.org/cpoisson/rent-a-bot.svg?branch=master)](https://travis-ci.org/cpoisson/rent-a-bot)
[![codecov](https://codecov.io/gh/cpoisson/rent-a-bot/branch/master/graph/badge.svg)](https://codecov.io/gh/cpoisson/rent-a-bot)
[![pipeline status](https://gitlab.com/cpoisson/rent-a-bot/badges/master/pipeline.svg)](https://gitlab.com/cpoisson/rent-a-bot/commits/master)
[![coverage report](https://gitlab.com/cpoisson/rent-a-bot/badges/master/coverage.svg)](https://gitlab.com/cpoisson/rent-a-bot/commits/master)

---

Rent-a-bot, your automation resource provider.

Exclusive access to a static resource is a common problem in automation, rent-a-bot allows you to abstract your resources 
and lock them to prevent any concurrent access.


## Origin 

Jenkins users can install [Lockable Resource Plugin](https://wiki.jenkins.io/display/JENKINS/Lockable+Resources+Plugin).

This tool works quite well, but the resource lock scope is limited to a Jenkins instance.

Rent-A-Bot vocation is to fill the same needs in an environment where multiple automation applications exist.

e.g.
- Multiple Jenkins application servers
- Mixed automation application, gitlab CI + Jenkins
- Shared resources between humans and automates.


## What is a resource? 

A resource is defined by a **name** and the existence of a **lock token** indicating if the resource is locked.

Optional available fields help you customize you resources with additional information:

- Resource description
- Lock description
- Endpoint
- Tags


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
pip install .   # pip install -e . if you want to install it in editable mode
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
- [HTTP status code](https://restpatterns.mindtouch.us/HTTP_Status_Codes)
- [Implementing API Exceptions](http://flask.pocoo.org/docs/0.12/patterns/apierrors/)
