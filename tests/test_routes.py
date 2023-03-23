import os
import sys
sys.path.insert(0, os.path.abspath('.'))
# print(sys.path)

import pytest
from multiprocessing import Process
from fastapi import FastAPI
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
import uvicorn
from src.genroutes.generic_routes import Routes, HttpMethods
import requests
# from mock_alchemy.mocking import UnifiedAlchemyMagicMock

#TODO add sqlalchemy mock database for test

app = FastAPI(swagger_ui_parameters={"defaultModelsExpandDepth": -1})

def init():
    SQLALCHEMY_DATABASE_URL = "postgresql://user:password@postgresserver/db"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
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
        id: int | None = None
        username : str
        email : str
        password : str


    '''Create crud routes for User model / UserEntity schema combo'''
    routes = Routes(SessionLocal, auth_route=None)
    user_routes = routes.get_router("user", User, UserEntity, UserEntity,
                                    response_exclude=["password"],
                                    access_mode=HttpMethods.NO_CREATE, id_field = 'id')

    '''Add crud router to app'''
    app.include_router(router=user_routes)

host = '127.0.0.1'
port = 8001
def run_server():
    init()
    uvicorn.run(app=app,host=host,port=port)

@pytest.fixture()
def setup_teardown():
    proc = Process(target=run_server, args=(), daemon=True)
    proc.start()
    yield
    proc.kill()
    print('teardown')

def test_read_user(setup_teardown):
    resp = requests.get('http://'+host+':'+str(port)+'/user')
    print(resp.status_code)
    assert resp.status_code != 404

def test_post_user(setup_teardown):
    resp = requests.post('http://'+host+':'+str(port)+'/user')
    print(resp.status_code)
    assert resp.status_code != 404



