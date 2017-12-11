# Rent-A-Bot

[![Build Status](https://travis-ci.org/cpoisson/rent-a-bot.svg?branch=master)](https://travis-ci.org/cpoisson/rent-a-bot)
[![codecov](https://codecov.io/gh/cpoisson/rent-a-bot/branch/master/graph/badge.svg)](https://codecov.io/gh/cpoisson/rent-a-bot)
[![pipeline status](https://gitlab.com/cpoisson/rent-a-bot/badges/master/pipeline.svg)](https://gitlab.com/cpoisson/rent-a-bot/commits/master)
[![coverage report](https://gitlab.com/cpoisson/rent-a-bot/badges/master/coverage.svg)](https://gitlab.com/cpoisson/rent-a-bot/commits/master)

---

Rent-a-bot, your automation resource provider.

Exclusive access to a static resource is a common problem in automation, rent-a-bot allows you to abstract your resources 
and lock them to prevent any concurrent access.


## Purpose

Rent-a-bot pursue the same objective as Jenkins [Lockable Resource Plugin](https://wiki.jenkins.io/display/JENKINS/Lockable+Resources+Plugin).

This latter works quite well, but only if you use... well... Jenkins.

Rent-A-Bot purpose is to fill the same needs in an environment where multiple automation applications exist.

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

## How to use it

Alright, rent-a-bot is up and running.

At this stage you can connect to the front end at http://127.0.0.1:5000/ (assuming your flask app listen to the port 500)

You will notice that the resource list is empty (dang...), let's populate it 

### Populate the database

You will need a resource descriptor file to populate the database at startup.

```commandline
RENTABOT_RESOURCE_DESCRIPTOR="/absolute/path/to/your/resource/descriptor.yml"
```

### Resource descriptor

The resource descriptor is a YAML file. It's purpose is to declare the resources you want to make available on rent-a-bot

```yaml
# Resources Description
# This file describes resources to populate in the database at rent-a-bot startup

coffee-machine:
    description: "Kitchen coffee machine"
    endpoint: "tcp://192.168.1.50"
    tags: "coffee kitchen food"

3d-printer-1:
    description: "Basement 3d printer 1"
    endpoint: "tcp://192.168.1.60"
    tags: "3d-printer basement tool"

another-resource:
    description: "yet another resource"
    endpoint: ""
    tags: ""
```

Once set, (re)start the flask application. The web view should be populated with your resources.

### RestFul API

#### List resources 
GET /api/v1.0/resources

e.g.
```commandline
curl -X GET -i http://localhost:5000/rentabot/api/v1.0/resources
```

#### Access to a given resource 
GET /api/v1.0/resources/{resource_id}

e.g.
```commandline
curl -X GET -i http://localhost:5000/rentabot/api/v1.0/resources/2
```

#### Lock a resource
POST /api/v1.0/resources/{resource_id}/lock

e.g.
```commandline
curl -X POST -i http://localhost:5000/rentabot/api/v1.0/resources/6/lock
```
**Note:** If the resource is available, a lock-token will be returned. Otherwise an error code is returned.

### Lock a resource using it's resource id (rid), name (name) or tag (tag).
POST /api/v1.0/resources/lock

e.g.
```commandline
curl -X POST -i http://localhost:5000/rentabot/api/v1.0/resources/lock\?rid\=6
curl -X POST -i http://localhost:5000/rentabot/api/v1.0/resources/lock\?name\=coffee-maker
curl -X POST -i http://localhost:5000/rentabot/api/v1.0/resources/lock\?tag\=coffee\&tag\=kitchen
```

**Notes:**
- If multiple available resources it the criteria, the first available will be returned.
- If criteria types are exclusive, resource id is prioritize over the name and tags, name is prioritize over tags.

#### Unlock a resource
POST /api/v1.0/resources/{resource_id}/unlock?lock-token={resource/lock/token}

```commandline
curl -X POST -i http://localhost:5000/rentabot/api/v1.0/resources/6/unlock\?lock-token\={resource/lock/token}
```

**Note:** If the resource is already unlocked or the lock-token is not valid, an error code is returned.
    

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
- [The Hitchhiker's Guide To Python](http://docs.python-guide.org/en/latest/)