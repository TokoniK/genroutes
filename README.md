# genroutes

----
Generate CRUD routes for FastAPI projects, reduce boilerplate code, accelerate development of FastAPI backend!
![last_commit](https://img.shields.io/github/last-commit/TokoniK/genroutes?style=)
![license](https://img.shields.io/github/license/TokoniK/genroutes?style=)


## Description
In order to build a webservice with FastAPI, some sections of code for defining api endpoints needs to be repeated.  
Code repetition makes maintenance of such services more difficult.  
genroutes helps address the issue of code repetition and also speeds up development of
FastAPI projects, by allowing the developer to focus development efforts on areas that require creativity.  

In most projects that require interaction with a datasource, CRUD (**C**reate, **R**ead, **U**pdate, **D**elete) endpoints often need to be created to enable
such functionality.
With genroutes, CRUD endpoints can easily be generated for specified data objects in simple steps.

## Installation
####  Prerequisites
genroutes requires these packages in most cases

- fastapi~=0.95.0
- SQLAlchemy~=2.0.7
- pydantic~=1.10.6

Install package with pip:

``pip install git+https://github.com/TokoniK/genroutes@main ``

# Usage
Import Routes & HttpMethods into module
``from genroutes import Routes, HttpMethods``

Create CRUD endpoints for SQLAlchemy schema object (e.g ``User``) and a pydantic model (e.g ``UserModel``)
with an SQLAlchemy session object (e.g ``Session``) using the example below:




**main.py**
```
from fastapi import FastAPI
from genroutes import Routes, HttpMethods
from pydantic import BaseModel
from sqlalchemy import Column, VARCHAR, INTEGER, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

#SQLAlchemy Schema Class
class User(Base):
    __tablename__ = u'users'

    # column definitions
    user_id = Column(INTEGER(), primary_key=True, nullable=False)
    username = Column(VARCHAR, nullable=False)
    email_address = Column(VARCHAR)
    password_hash = Column(VARCHAR)

#Corresponding BaseModel Class for validation
class UserModel(BaseModel):
    # column definitions
    user_id: int | None
    username: str
    email_address: str | None = None
    password_hash: str | None = None


#Dummy Database
SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@postgresserver/db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(swagger_ui_parameters={"defaultModelsExpandDepth": -1})

Base.metadata.tables['users'].create(engine)

# Create crud routes for User schema / UserModel model combo
routes = Routes(Session)

# Use auth_route param to specify authentication endpoint
# routes = Routes(Session, auth_route='auth')

user_routes = routes.get_router("user", User, UserModel, UserModel,
                                response_exclude=["password"],
                                access_mode=HttpMethods.ALL_METHODS, id_field='id')

# Add crud router to app
app.include_router(router=user_routes)
```

Run the app on a web server such as uvicorn:  
```
uvicorn main:app
```

Following this, the openapi docs will look like as seen below:
![Openapi Doc](assets/apidoc.png)

Routes for all supported methods are created according to the ``access_mode`` param
specified at route generation:
``access_mode=HttpMethods.ALL_METHODS``
