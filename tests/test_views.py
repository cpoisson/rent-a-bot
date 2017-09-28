import pytest
import rentabot


@pytest.fixture
def app():
    rentabot.app.testing = True
    return rentabot.app.test_client()


def test_views_index(app):
    response = app.get('/')
    if response.status_code != 200:
        pytest.fail("The index did not returned 200 but {}".format(response))


def test_get_bots_no_bots(app):
    response = app.get('/rentabot/api/v1.0/resources')
    if response.status_code != 200:
        pytest.fail("GET bots did not returned 200 but {}".format(response))


def test_get_bot_id_bot_doesnt_exist(app):
    response = app.get('/rentabot/api/v1.0/ressources/3000')
    if response.status_code != 404:
        pytest.fail("GET bots did not returned 404 but {}".format(response))

