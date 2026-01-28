# Rent-A-Bot

Rent-a-bot, your automation resource provider.

Exclusive access to a static resource is a common problem in automation. Rent-a-bot allows you to abstract your resources and lock them to prevent any concurrent access.


## Purpose

Rent-a-bot pursues the same objective as Jenkins [Lockable Resource Plugin](https://wiki.jenkins.io/display/JENKINS/Lockable+Resources+Plugin).

The plugin works quite well, but only if you use... well... Jenkins.

Rent-A-Bot's purpose is to fill the same needs in an environment where multiple automation applications exist.

Examples:
- Multiple Jenkins application servers
- Mixed automation applications (e.g., GitHub Actions + Jenkins)
- Shared resources between humans and automation systems


## What is a resource?

A resource is defined by a **name** and the existence of a **lock token** indicating if the resource is locked.

Optional available fields help you customize your resources with additional information:

- Resource description
- Lock description
- Endpoint
- Tags


## How to install and run

### Prerequisites

This project uses [uv](https://github.com/astral-sh/uv) for fast, reliable Python package management.

Install uv:
```commandline
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or on macOS:
```commandline
brew install uv
```

### Installation

Clone the repository from GitHub:

```commandline
git clone git@github.com:cpoisson/rent-a-bot.git
```

Navigate to the project directory:
```commandline
cd rentabot
```

Install the package and dependencies using uv:

```commandline
uv sync              # Install dependencies and create virtual environment
uv pip install -e .  # Install the package in editable mode
```

## How to run

### Using the CLI (recommended)

The easiest way to run Rent-A-Bot is using the built-in CLI:

```commandline
# Run directly with uvx (no installation needed)
uvx rentabot

# Or install and run
uv pip install -e .
rentabot
```

**CLI Options:**

```commandline
rentabot --help                           # Show help
rentabot --version                        # Show version
rentabot --config path/to/config.yaml     # Use specific config file
rentabot --host 0.0.0.0 --port 8080       # Custom host and port
rentabot --reload                         # Enable auto-reload for development
rentabot --log-level debug                # Set log level
```

**Configuration File Discovery:**

The CLI automatically searches for configuration files in this order:
1. Explicit `--config` argument
2. `./.rentabot.yaml` or `./rentabot.yaml` in current directory
3. `~/.rentabot/config.yaml` in home directory
4. `RENTABOT_RESOURCE_DESCRIPTOR` environment variable
5. No config (starts with empty resources)

### Using uvicorn directly

You can also start the FastAPI server directly:

```commandline
# With environment variable
RENTABOT_RESOURCE_DESCRIPTOR="path/to/config.yaml" uvicorn rentabot.main:app --reload --port 8000

# Or with uv
uv run uvicorn rentabot.main:app --reload --port 8000
```

The API will be available at:
- **Main API**: http://127.0.0.1:8000/
- **Interactive API Docs**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

## How to use it

Alright, rent-a-bot is up and running.

At this stage you can connect to the web interface at http://127.0.0.1:8000/ or explore the interactive API documentation at http://127.0.0.1:8000/docs.

You will notice that the resource list is empty (dang...), let's populate it.

### Populate the resources

You will need a resource descriptor file to populate the resources at startup.

```commandline
RENTABOT_RESOURCE_DESCRIPTOR="/absolute/path/to/your/resource/descriptor.yml"
```

### Resource descriptor

The resource descriptor is a YAML file. Its purpose is to declare the resources you want to make available on rent-a-bot.

```yaml
# Resources Description
# This file describes resources to populate in the database at rent-a-bot startup

coffee-machine:
    description: "Kitchen coffee machine"
    endpoint: "tcp://192.168.1.50"
    tags: "coffee,kitchen,food"

3d-printer-1:
    description: "Basement 3d printer 1"
    endpoint: "tcp://192.168.1.60"
    tags: "3d-printer,basement,tool"

another-resource:
    description: "yet another resource"
    endpoint: ""
    tags: ""
```

Once set, (re)start the application with the environment variable:

```commandline
RENTABOT_RESOURCE_DESCRIPTOR=/path/to/your/resources.yaml uvicorn rentabot.main:app --reload --port 8000
```

The web view should be populated with your resources.

### RESTful API

#### List resources
GET /api/v1/resources

e.g.
```commandline
curl -X GET -i http://localhost:8000/api/v1/resources
```

#### Access to a given resource
GET /api/v1/resources/{resource_id}

e.g.
```commandline
curl -X GET -i http://localhost:8000/api/v1/resources/2
```

#### Lock a resource
POST /api/v1/resources/{resource_id}/lock

e.g.
```commandline
curl -X POST -i http://localhost:8000/api/v1/resources/6/lock
```
**Note:** If the resource is available, a lock-token will be returned. Otherwise an error code is returned.

### Lock a resource using it's resource id (id), name (name) or tag (tag).
POST /api/v1/resources/lock

e.g.
```commandline
curl -X POST -i "http://localhost:8000/api/v1/resources/lock?id=6"
curl -X POST -i "http://localhost:8000/api/v1/resources/lock?name=coffee-maker"
curl -X POST -i "http://localhost:8000/api/v1/resources/lock?tag=coffee&tag=kitchen"
```

**Notes:**
- If multiple available resources match the criteria, the first available will be returned.
- If criteria types are exclusive, resource id is prioritized over the name and tags, and name is prioritized over tags.

#### Unlock a resource
POST /api/v1/resources/{resource_id}/unlock?lock-token={resource/lock/token}

```commandline
curl -X POST -i "http://localhost:8000/api/v1/resources/6/unlock?lock-token={resource/lock/token}"
```

**Note:** If the resource is already unlocked or the lock-token is not valid, an error code is returned.


## How to test

### Test implementation

Unit tests are done using pytest and coverage.

### How to run unit tests

```commandline
uv run pytest
```

Or with the virtual environment activated:
```commandline
source .venv/bin/activate
pytest
```

## Versioning

This project uses [Semantic Versioning](https://semver.org/) for its versioning scheme.
Versions are formatted as `MAJOR.MINOR.PATCH`, where:
- **MAJOR** version is incremented for incompatible API changes.
- **MINOR** version is incremented for adding functionality in a backward-compatible manner.
- **PATCH** version is incremented for backward-compatible bug fixes.

---

## Helpful documentation used to design this application

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Put versus Post](https://knpuniversity.com/screencast/rest/put-versus-post)
- [Best practice for a pragmatic restful API](http://www.vinaysahni.com/best-practices-for-a-pragmatic-restful-api#ssl)
- [HTTP status code](https://restpatterns.mindtouch.us/HTTP_Status_Codes)
- [OpenAPI Specification](https://swagger.io/specification/)
