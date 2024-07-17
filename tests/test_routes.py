
import pytest
from fastapi import FastAPI
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
from src.genroutes.generic_routes import Routes, HttpMethods
from fastapi.testclient import TestClient
from sqlalchemy.orm import declarative_base
from mock_alchemy.mocking import UnifiedAlchemyMagicMock
from typing import Union
# import sys
# sys.path.insert(0, os.path.abspath('.'))
# # print(sys.path)
# from multiprocessing import Process
# import uvicorn
# import requests




#TODO add sqlalchemy mock database for test

app = FastAPI(swagger_ui_parameters={"defaultModelsExpandDepth": -1})
client: TestClient = None

def init():
    # SQLALCHEMY_DATABASE_URL = "postgresql://user:password@postgresserver/db"
    # engine = create_engine(
    #     SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    # )
    # SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    SessionLocal = UnifiedAlchemyMagicMock()
    Base = declarative_base()

    @app.get("/")
    def home():
        return {'home': 'welcome'}

    class User(Base):
        __tablename__ = "Users"

        id = Column("user_id",Integer, primary_key = True, index = True)
        username = Column(String, nullable = False, unique = True)
        email = Column(String, nullable = False, unique = True)
        password = Column("password_hash", String, nullable = False)

    class UserEntity(BaseModel):
        id: Union[int, None] = None
        username : str
        email : str
        password : str

    '''Create crud routes for User model / UserEntity schema combo'''
    routes = Routes(SessionLocal, auth_route=None)
    user_routes = routes.get_router("user", User, UserEntity, UserEntity,
                                    response_exclude=["password"],
                                    access_mode=HttpMethods.ALL_METHODS, id_field = 'id')

    '''Add crud router to app'''
    app.include_router(router=user_routes)
    routes.add_options(app)

host = '127.0.0.1'
port = 8001
# def run_server():
    # init()
    # uvicorn.run(app=app,host=host,port=port)

@pytest.fixture()
def setup_teardown():
    # proc = Process(target=run_server, args=(), daemon=True)
    # proc.start()
    init()
    global client
    client = TestClient(app)
    yield
    # proc.kill()
    client.close()
    print('teardown')


def test_read_user(setup_teardown):
    # resp = requests.get('http://'+host+':'+str(port)+'/user')
    resp = client.get("/user")
    print(resp.status_code)
    assert resp.status_code == 200


def test_post_user(setup_teardown):
    # resp = requests.post('http://'+host+':'+str(port)+'/user')
    content='{"id": 0, "username": "string", "email": "string", "password": "string"}'
    json={'id': '1', 'username': 'test', 'email': 'test@test.test', 'password': 'password'}
    resp = client.post("/user", json=json)
    print(resp.status_code)
    assert resp.status_code == 201

def test_patch_user(setup_teardown):
    # resp = requests.post('http://'+host+':'+str(port)+'/user')
    content='{"id": 0, "username": "string", "email": "string", "password": "string"}'
    test_post_user(setup_teardown)
    json={'username': 'testxxx'}
    resp = client.patch("/user/1", json=json)
    print(resp.status_code)
    assert resp.status_code == 200


def test_put_user(setup_teardown):
    # resp = requests.post('http://'+host+':'+str(port)+'/user')
    content='{"id": 0, "username": "string", "email": "string", "password": "string"}'
    test_post_user(setup_teardown)

    json={'username': 'testxxx'} #Invalid data for put
    resp = client.put("/user/1", json=json)
    assert resp.status_code == 422

    json = {'id': '1', 'username': 'test', 'email': 'test@test.testxx', 'password': 'password'}#Valid data
    resp = client.put("/user/1", json=json)
    print(resp.status_code)
    assert resp.status_code == 200

def test_delete_user(setup_teardown):
    # resp = requests.post('http://'+host+':'+str(port)+'/user')
    content='{"id": 0, "username": "string", "email": "string", "password": "string"}'
    test_post_user(setup_teardown)

    json={'username': 'testxxx'} #Invalid data for put
    resp = client.delete("/user/1")
    assert resp.status_code == 200

    resp = client.delete("/user/2")
    print(resp.status_code)
    assert resp.status_code == 200

def test_options_user(setup_teardown):
    # resp = requests.post('http://'+host+':'+str(port)+'/user')

    resp = client.options("/user")
    print(resp.headers)
    assert resp.status_code == 200


