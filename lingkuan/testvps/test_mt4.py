import requests
def test_mt4_login():
    params={
        "user":"",
        "password":"",
        "host":"",
        "port":"",
        "connectTimeoutSeconds":"",
    }
    response = requests.get('https://mt4.mtapi.io/Connect')