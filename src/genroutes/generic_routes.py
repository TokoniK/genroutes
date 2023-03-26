from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from . import crud
from sqlalchemy.orm import Session
from enum import Enum
from pydantic import BaseModel
from sqlalchemy.orm import sessionmaker


class HttpMethods(Enum):
    """HTTP Methods defining access modes for gen routes"""

    GET = 1
    GET_BY_ATTRIBUTE = 2
    POST = 3
    PUT = 4
    DELETE = 5
    ALL_METHODS = [GET, GET_BY_ATTRIBUTE, POST, PUT, DELETE]
    NO_UPDATE = [GET, GET_BY_ATTRIBUTE, POST, DELETE]
    NO_CREATE = [GET, GET_BY_ATTRIBUTE, PUT, DELETE]
    NO_DELETE = [GET, GET_BY_ATTRIBUTE, POST, PUT]
    READ_ONLY = [GET, GET_BY_ATTRIBUTE]


def create(db: Session, model, key_attribute, data):
    """Create records of model on datasource using data object.

    ``key_attribute`` is used to check for duplicates before creation

    """

    obj = crud.get_by_attribute(db, model, key_attribute, data[key_attribute])

    if len(obj) > 0:
        raise HTTPException(status_code=401, detail="data already exists")

    new_object = crud.create(db, model, data)
    return new_object


# def update(db: Session, model, data, id):
#     obj = crud.get_by_id(db, model, id)
#
#     if obj is None:
#         raise HTTPException(status_code=401, detail="data not found")
#
#     updated = crud.update(db, model, data, id)
#     return updated

def update(db: Session, model, data, attribute, value):
    """Update all records of model from datasource filtered by 'attribute = value' """

    obj = crud.get_by_attribute(db, model, attribute, value)

    if obj is None:
        raise HTTPException(status_code=401, detail="data not found")

    updated = crud.update_by_attribute(db, model, data, attribute, value)
    return updated


# def delete(db: Session, model, id):
#     obj = crud.get_by_id(db, model, id)
#
#     if obj is None:
#         raise HTTPException(status_code=401, detail="data not found")
#
#     msg = crud.delete(db, model, id)
#     return {"message": msg}


def delete(db: Session, model, attribute, value):
    """Delete all records of model from datasource filtered by 'attribute = value' """

    obj = crud.get_by_attribute(db, model, attribute, value)

    if obj is None:
        raise HTTPException(status_code=401, detail="data not found")

    msg = crud.delete_by_attribute(db, model, attribute, value)
    return {"message": msg}


def read(db: Session, model):
    """Read all records of model from datasource"""

    obj = crud.get_all(db, model)
    # print(obj)
    return obj


def read_by_attribute(db: Session, model, attribute, value):
    """Read records of model from datasource filtered by 'attribute = value' """

    obj = crud.get_by_attribute(db, model, attribute, value)
    return obj


def create_any(db: Session, model, data):
    """Create records without validating against unique fields"""
    try:
        new_object = crud.create(db, model, data)
    except BaseException as ex:
        raise HTTPException(status_code=401, detail=str(ex.orig))

    return new_object


def _method_name(name):
    """Rename methods with decorator"""

    def decorator(func):
        func.__name__ = name
        return func

    return decorator


class Routes:
    """Crud routes generator for FastAPI projects using SQLAlchemy
    Generate crud routes using pydantic schemas and their corresponding SQLAlchemy models

    The example below shows genroutes in use for the creation of crud routes for the ``User`` moodel

    e.g.::

        from fastapi import FastAPI
        from sqlalchemy import create_engine, Column, Integer, String
        from genroutes import Routes, HttpMethods
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.ext.declarative import declarative_base
        from pydantic import BaseModel


        SQLALCHEMY_DATABASE_URL = "postgresql://user:password@postgresserver/db"
        engine = create_engine(
            SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
        )
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base = declarative_base()


        app = FastAPI(swagger_ui_parameters={"defaultModelsExpandDepth": -1})

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
        routes = Routes(SessionLocal, auth_route='auth')
        user_routes = routes.get_router("user", User, UserEntity, UserEntity,
                    response_exclude=["password"],
                    access_mode=HttpMethods.NO_CREATE, id_field = 'id')

        '''Add crud router to app'''
        app.include_router(router=user_routes)

    """

    def __init__(self, session: sessionmaker, auth_route: str | None = None):
        self.session = session
        self.oauth2_scheme = None

        if auth_route is not None:
            if str(auth_route):
                print(auth_route)
                self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl=auth_route)

    def get_router(self, path: str, model,
                   schema: BaseModel, schema_create: BaseModel, **kwargs):
        """ Generate and return router.

            :param path: endpoint for routes.
            :param model: SQLAlchemy model representing data table structure.
            :param schema: corresponding pydantic schema for model.
            :param schema_create: pydantic schema to be used for data creation (``POST`` HTTPMethod).
            :param kwargs: see below.

            :Keyword Arguments:.

             * *response_exclude* (``list``) -- list of schema fields to be excluded from response.
             * *access_mode* (``dict``) -- dict of HTTPMethods to be generated (e.g. GET, POST).

            :return: router (``APIRouter``)

        """

        response_model_exclude: list = kwargs.get('response_exclude', None)
        access_mode: HttpMethods = kwargs.get('access_mode', HttpMethods.ALL_METHODS)
        id_field: str = kwargs.get('id_field', 'id')

        '''Process access methods in to list of HTTPMethods'''
        if isinstance(access_mode, HttpMethods):
            if not isinstance(access_mode.value, list):
                access_mode = [access_mode.value]
            else:
                access_mode = access_mode.value

        router = APIRouter(prefix="/" + path)

        def get_db() -> Session:
            db = self.session()
            try:
                yield db
            finally:
                db.close()

        def get_model():
            return model

        @_method_name('create_' + model.__name__.lower())
        def create(data: schema_create, db: Session = Depends(get_db)
                   , token=Depends(self.oauth2_scheme), model=Depends(get_model)):
            return create_any(db, model, data)

        # @self.router.get("", response_model=list[schema], response_model_exclude=response_model_exclude)
        @_method_name('get_' + model.__name__.lower())
        def get(db: Session = Depends(get_db), token=Depends(self.oauth2_scheme), model=Depends(get_model)):
            return read(db, model)

        # @self.router.get("/{attribute}/{value}", response_model=list[schema]
        #                   , response_model_exclude=response_model_exclude)
        @_method_name('get_' + model.__name__.lower() + "_by_attribute")
        def get_by_attribute(attribute, value, db: Session = Depends(get_db), token=Depends(self.oauth2_scheme),
                             model=Depends(get_model)):
            return read_by_attribute(db, model, attribute, value)

        # @self.router.put("/{id}", response_model=schema, response_model_exclude=response_model_exclude)
        @_method_name('update_' + model.__name__.lower())
        def update_data(id, data: schema, db: Session = Depends(get_db), token=Depends(self.oauth2_scheme),
                        model=Depends(get_model)):
            return update(db, model, data, id_field, id)

        # @self.router.delete("/{id}")
        @_method_name('delete_' + model.__name__.lower())
        def delete_data(id, db: Session = Depends(get_db),
                        token=Depends(self.oauth2_scheme), model=Depends(get_model)):
            return delete(db, model, id_field, id)

        if HttpMethods.POST.value in access_mode:
            router.add_api_route("", create, methods=["POST"]
                                 , response_model=schema | dict | list[schema | dict]
                                 , response_model_exclude=response_model_exclude)
        if HttpMethods.GET.value in access_mode:
            router.add_api_route("", get, methods=["GET"]
                                 , response_model=list[schema | dict]
                                 , response_model_exclude=response_model_exclude)
        if HttpMethods.GET_BY_ATTRIBUTE.value in access_mode:
            router.add_api_route("/{attribute}/{value}", get_by_attribute, methods=["GET"]
                                 , response_model=list[schema | dict]
                                 , response_model_exclude=response_model_exclude)
        if HttpMethods.PUT.value in access_mode:
            router.add_api_route("/{id}", update_data, methods=["PUT"]
                                 , response_model=list[schema | dict]
                                 , response_model_exclude=response_model_exclude)
        if HttpMethods.DELETE.value in access_mode:
            router.add_api_route("/{id}", delete_data, methods=["DELETE"])

        return router

    def add_router(self, app, path: str, model,
                   schema: BaseModel, schema_create: BaseModel, **kwargs):
        """Generate router and add to FastAPI app.

            :param app: FastAPI app.
            :param path: endpoint for routes.
            :param model: SQLAlchemy model representing data table structure.
            :param schema: corresponding pydantic schema for model.
            :param schema_create: pydantic schema to be used for data creation (``POST`` HTTPMethod).
            :param kwargs: see below.

            :Keyword Arguments:.

             * *response_exclude* (``list``) -- list of schema fields to be excluded from response.
             * *access_mode* (``dict``) -- dict of HTTPMethods to be generated (e.g. GET, POST)

        """

        router = self.get_router(path, model, schema, schema_create, **kwargs)
        app.include_router(router=router)
