import string
from enum import Enum
from typing import Annotated, Union, Type
from typing import Iterator

from fastapi import APIRouter, HTTPException, Depends, Response, status, Body, Header, Request
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from starlette.responses import JSONResponse

from . import crud


class HttpMethods(Enum):
    """HTTP Methods defining access modes for gen routes"""

    GET = 1
    GET_BY_ATTRIBUTE = 2
    POST = 3
    PUT = 4
    PATCH = 5
    DELETE = 6
    ALL_METHODS = [GET, GET_BY_ATTRIBUTE, POST, PUT, PATCH, DELETE]
    NO_UPDATE = [GET, GET_BY_ATTRIBUTE, POST, PATCH, DELETE]
    NO_CREATE = [GET, GET_BY_ATTRIBUTE, PUT, PATCH, DELETE]
    NO_DELETE = [GET, GET_BY_ATTRIBUTE, POST, PUT, PATCH]
    READ_ONLY = [GET, GET_BY_ATTRIBUTE]


def create(db: Session, schema, key_attribute, data: BaseModel, *args):
    """Create records of model on datasource using data object.

    ``key_attribute`` is used to check for duplicates before creation
    ``*args`` additional key fields to be used in duplication check

    """
    additional_attribute = {}
    for arg in args:
        additional_attribute = {**additional_attribute, str(arg): data.dict(exclude_unset=True)[str(arg)]}

    # obj = crud.get_by_attribute(db, schema, key_attribute, data[key_attribute])

    obj = crud.get_by_attribute(db, schema, key_attribute, data.dict(exclude_unset=True)[key_attribute],
                                **{'additional_attributes': additional_attribute})

    if len(obj) > 0:
        raise HTTPException(status_code=409, detail="data already exists")

    new_object = crud.create(db, schema, data)

    db.close()
    return new_object


# def update(db: Session, model, data, id):
#     obj = crud.get_by_id(db, model, id)
#
#     if obj is None:
#         raise HTTPException(status_code=401, detail="data not found")
#
#     updated = crud.update(db, model, data, id)
#     return updated

def update(db: Session, schema, data, attribute, value, **kwargs):
    """Update all records of model from datasource filtered by 'attribute = value' """
    additional_attribute: dict = kwargs.get('additional_attributes', None)
    if additional_attribute is not None:
        if not isinstance(additional_attribute, dict):
            raise Exception("Arguments must be of type dict")

    try:
        obj = crud.get_by_attribute(db, schema, attribute, value, **kwargs)
    except BaseException as ex:
        raise HTTPException(status_code=400, detail=str(ex.orig))

    if obj is None:
        raise HTTPException(status_code=404, detail="data not found")

    try:
        updated = crud.update_by_attribute(db, schema, data, attribute, value, **kwargs)
    except BaseException as ex:
        raise HTTPException(status_code=400, detail=str(ex.orig))

    db.close()
    return updated


def patch(db: Session, schema, data, attribute, value, **kwargs):
    """Update all records of model from datasource filtered by 'attribute = value' """
    additional_attribute: dict = kwargs.get('additional_attributes', None)
    if additional_attribute is not None:
        if not isinstance(additional_attribute, dict):
            raise Exception("Arguments must be of type dict")

    try:
        obj = crud.get_by_attribute(db, schema, attribute, value, **kwargs)
    except BaseException as ex:
        raise HTTPException(status_code=400, detail=str(ex.orig))

    if obj is None:
        raise HTTPException(status_code=404, detail="data not found")

    try:
        updated = crud.update_by_attribute(db, schema, data, attribute, value, **kwargs)
    except BaseException as ex:
        raise HTTPException(status_code=400, detail=str(ex.orig))

    db.close()
    return updated


# def delete(db: Session, model, id):
#     obj = crud.get_by_id(db, model, id)
#
#     if obj is None:
#         raise HTTPException(status_code=401, detail="data not found")
#
#     msg = crud.delete(db, model, id)
#     return {"message": msg}


def delete(db: Session, schema, attribute, value, **kwargs):
    """Delete all records of model from datasource filtered by 'attribute = value' """
    additional_attribute: dict = kwargs.get('additional_attributes', None)
    if additional_attribute is not None:
        if not isinstance(additional_attribute, dict):
            raise Exception("Arguments must be of type dict")
    try:
        obj = crud.get_by_attribute(db, schema, attribute, value, **kwargs)
    except BaseException as ex:
        raise HTTPException(status_code=400, detail=str(ex.orig))

    if obj is None:
        raise HTTPException(status_code=404, detail="data not found")

    try:
        msg = crud.delete_by_attribute(db, schema, attribute, value, **kwargs)
    except BaseException as ex:
        raise HTTPException(status_code=400, detail=str(ex.orig))

    db.close()
    return {"message": msg}


def read(db: Session, schema, deep=False):
    """Read all records of model from datasource"""
    try:
        obj = crud.get_all(db, schema, deep=deep)
    except BaseException as ex:
        raise HTTPException(status_code=400, detail=str(ex.orig))
    # print(obj)
    db.close()
    return obj


def read_paginated(db: Session, schema, page: int, limit: int, deep=False):
    """Read all records of model from datasource"""
    try:
        obj = crud.get_all_paginated(db, schema, page, limit, deep=deep)
    except BaseException as ex:
        raise HTTPException(status_code=400, detail=str(ex.orig))
    # print(obj)
    db.close()
    return obj


def read_by_attribute(db: Session, schema, attribute, value, deep=False,**kwargs):
    """Read records of model from datasource filtered by 'attribute = value' """
    additional_attribute: dict = kwargs.get('additional_attributes', None)
    if additional_attribute is not None:
        if not isinstance(additional_attribute, dict):
            raise Exception("Arguments must be of type dict")

    try:
        obj = crud.get_by_attribute(db, schema, attribute, value, deep=deep,**kwargs)
    except BaseException as ex:
        raise HTTPException(status_code=400, detail=str(ex.orig))
    db.close()
    return obj


def read_by_id(db: Session, schema, id_field, value, deep=True):
    """Read records of model from datasource filtered by 'attribute = value' """
    try:
        obj = crud.get_by_id(db, schema, id_field, value, deep=deep)
    except BaseException as ex:
        raise HTTPException(status_code=400, detail=str(ex.orig))
    db.close()
    return obj


def read_by_attribute_paginated(db: Session, schema, attribute, value, page, limit, deep=False, **kwargs):
    """Read records of model from datasource filtered by 'attribute = value' """
    additional_attribute: dict = kwargs.get('additional_attributes', None)
    if additional_attribute is not None:
        if not isinstance(additional_attribute, dict):
            raise Exception("Arguments must be of type dict")

    try:
        obj = crud.get_by_attribute_paginated(db, schema, attribute, value, page, limit, deep=deep, **kwargs)
    except BaseException as ex:
        raise HTTPException(status_code=400, detail=str(ex.orig))
    db.close()
    return obj


def create_any(db: Session, schema, data):
    """Create records without validating against unique fields"""
    try:
        new_object = crud.create(db, schema, data)
    except BaseException as ex:
        raise HTTPException(status_code=400, detail=str(ex.orig))
    db.close()
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

    def __init__(self, session: sessionmaker, auth_route: str = None):
        self.session = session
        self.oauth2_scheme = None

        if auth_route is not None:
            if str(auth_route):
                # print(auth_route)
                self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl=auth_route)

    def get_router(self, path: str, schema,
                   model: Union[BaseModel, Type[BaseModel]], model_create: Union[BaseModel, Type[BaseModel]], **kwargs):
        """ Generate and return router.

            :param path: endpoint for routes.
            :param schema: SQLAlchemy model representing data table structure.
            :param model: corresponding pydantic schema for model.
            :param model_create: pydantic schema to be used for data creation (``POST`` HTTPMethod).
            :param kwargs: see below.

            :Keyword Arguments:.

             * *response_exclude* (``list``) -- list of schema fields to be excluded from response.
             * *access_mode* (``dict``) -- dict of HTTPMethods to be generated (e.g. GET, POST).

            :return: router (``APIRouter``)

        """
        response_model_exclude: set = kwargs.get('response_exclude', None)
        access_mode: list = kwargs.get('access_mode', HttpMethods.ALL_METHODS)
        id_field: str = kwargs.get('id_field', 'id')

        tag: str = string.capwords(path.replace('_', ' '))  # string.capwords(schema.__name__)
        methodtag: str = path.lower()  # schema.__name__.lower()

        '''Process access methods in to list of HTTPMethods'''
        if isinstance(access_mode, HttpMethods):
            if not isinstance(access_mode.value, list):
                access_mode = [access_mode.value]
            else:
                access_mode = access_mode.value

        router = APIRouter(prefix="/" + path)

        def get_db() -> Iterator[Session]:
            db = self.session()
            try:
                yield db
            finally:
                db.close()

        def get_model():
            return schema

        # region crud_methods
        service = Service(self.session, schema)

        @_method_name('create_' + methodtag)
        def create(data: model_create,
                   token=Depends(self.oauth2_scheme), user_schema: Union[str, None] = Header(default=None)):
            # db: Session = Depends(get_db)
            # db = next(get_db())
            # return create_any(db, schema, data)
            # return service.create_any(data)
            if user_schema:
                service.set_dbschema({None: user_schema})
            else:
                service.set_dbschema(None)
            return JSONResponse(jsonable_encoder(service.create_any(data), exclude=response_model_exclude))

        @_method_name('create_' + methodtag)
        def create_na(data: model_create, user_schema: Union[str, None] = Header(default=None)):
            """No authentication """
            # db: Session = Depends(get_db)
            # db = next(get_db())
            # return create_any(db, schema, data)
            # return service.create_any(data)
            if user_schema:
                service.set_dbschema({None: user_schema})
            else:
                service.set_dbschema(None)
            return JSONResponse(jsonable_encoder(service.create_any(data), exclude=response_model_exclude))

        # @self.router.get("", response_model=list[schema]response_model_exclude=response_model_exclude,)

        @_method_name('get_' + methodtag)
        def get_paginated(page: Union[int, None] = None, limit: Union[int, None] = None,
                          token=Depends(self.oauth2_scheme),
                          user_schema: Union[str, None] = Header(default=None),
                          deep: Union[bool, None] = False):
            # db: Session = Depends(get_db)
            # db = next(get_db())
            # return read(db, schema)
            if user_schema:
                service.set_dbschema({None: user_schema})
            else:
                service.set_dbschema(None)

            if page is not None and limit is not None:
                # return service.get_all_paginated(page, limit)
                return JSONResponse(jsonable_encoder(service.get_all_paginated(page, limit, deep=deep),
                                                     exclude=response_model_exclude))
            # return service.get_all()
            return JSONResponse(jsonable_encoder(service.get_all(deep=deep), exclude=response_model_exclude))

        @_method_name('get_' + methodtag)
        def get_paginated_na(page: Union[int, None] = None, limit: Union[int, None] = None,
                             user_schema: Union[str, None] = Header(default=None),
                             deep: Union[bool, None] = False):
            """No authentication """
            # db: Session = Depends(get_db)
            # db = next(get_db())
            # return read(db, schema)

            # Control db schema using header value
            if user_schema:
                service.set_dbschema({None: user_schema})
            else:
                service.set_dbschema(None)

            if page is not None and limit is not None:
                # return service.get_all_paginated(page, limit)
                return JSONResponse(jsonable_encoder(service.get_all_paginated(page, limit, deep=deep),
                                                     exclude=response_model_exclude))
            # return service.get_all()
            return JSONResponse(jsonable_encoder(service.get_all(deep=deep), exclude=response_model_exclude))

        # @self.router.get("/{attribute}/{value}", response_model=list[schema]
        #                   response_model_exclude=response_model_exclude,)

        @_method_name('get_' + methodtag + "_by_attribute")
        def get_by_attribute_paginated(attribute, value, request: Request, token=Depends(self.oauth2_scheme),
                                       user_schema: Union[str, None] = Header(default=None),
                                       page: Union[int, None] = None,
                                       limit: Union[int, None] = None,
                                       deep: Union[bool, None] = False):
            # db: Session = Depends(get_db)
            # db = next(get_db())
            # return read_by_attribute(db, schema, attribute, value)

            param: dict = {k: v for k, v in request.query_params.items()}
            additional_attributes = {'additional_attributes': param} if param else {}
            # Control db schema using header value
            if user_schema:
                service.set_dbschema({None: user_schema})
            else:
                service.set_dbschema(None)

            if not page is None and not limit is None:
                # return service.get_by_attribute_paginated(value, attribute, page, limit, **additional_attributes)
                return JSONResponse(jsonable_encoder(service.get_by_attribute_paginated(
                    value, attribute, page, limit, deep=deep,**additional_attributes), exclude=response_model_exclude))
            # return service.get_by_attribute(value, attribute, **additional_attributes)
            return JSONResponse(jsonable_encoder(service.get_by_attribute(value, attribute,deep=deep **additional_attributes),
                                                 exclude=response_model_exclude))

        @_method_name('get_' + methodtag + "_by_attribute")
        def get_by_attribute_paginated_na(attribute, value
                                          , request: Request
                                          , user_schema: Union[str, None] = Header(default=None)
                                          , page: Union[int, None] = None, limit: Union[int, None] = None
                                          , deep: Union[bool, None] = False):
            """No authentication """
            # db: Session = Depends(get_db)
            # db = next(get_db())
            # return read_by_attribute(db, schema, attribute, value)

            param: dict = {k: v for k, v in request.query_params.items()}
            additional_attributes = {'additional_attributes': param} if param else {}
            # Control db schema using header value
            if user_schema:
                service.set_dbschema({None: user_schema})
            else:
                service.set_dbschema(None)

            if not page is None and not limit is None:
                # return service.get_by_attribute_paginated(value, attribute, page, limit, **additional_attributes)
                return JSONResponse(jsonable_encoder(service.get_by_attribute_paginated(
                    value, attribute, page, limit, deep=deep, **additional_attributes), exclude=response_model_exclude))
            # return service.get_by_attribute(value, attribute, **additional_attributes)
            return JSONResponse(jsonable_encoder(service.get_by_attribute(value, attribute, deep=deep, **additional_attributes),
                                                 exclude=response_model_exclude))

        @_method_name('get_' + methodtag + "_by_id")
        def get_by_id(id, token=Depends(self.oauth2_scheme), user_schema: Union[str, None] = Header(default=None),
                      deep: Union[bool, None] = True):
            # db: Session = Depends(get_db)
            # db = next(get_db())
            # return read_by_attribute(db, schema, id_field, value)

            # Control db schema using header value
            if user_schema:
                service.set_dbschema({None: user_schema})
            else:
                service.set_dbschema(None)
            # return service.get_one(id, id_field)
            return JSONResponse(jsonable_encoder(service.get_one(id, id_field, deep=deep), exclude=response_model_exclude))

        @_method_name('get_' + methodtag + "_by_id")
        def get_by_id_na(id, user_schema: Union[str, None] = Header(default=None),
                         deep: Union[bool, None] = True):
            """No authentication """
            # db: Session = Depends(get_db)
            # db = next(get_db())
            # return read_by_attribute(db, schema, id_field, value)

            # Control db schema using header value
            if user_schema:
                service.set_dbschema({None: user_schema})
            else:
                service.set_dbschema(None)
            # return service.get_one(id, id_field)
            return JSONResponse(jsonable_encoder(service.get_one(id, id_field, deep=deep), exclude=response_model_exclude))

        # @self.router.put("/{id}", response_model=schemaresponse_model_exclude=response_model_exclude,)
        @_method_name('update_' + methodtag)
        def update_data(id, data: model, token=Depends(self.oauth2_scheme),
                        user_schema: Union[str, None] = Header(default=None)):
            # db: Session = Depends(get_db)
            # db = next(get_db())
            # return update(db, schema, data, id_field, id_)

            # Control db schema using header value
            if user_schema:
                service.set_dbschema({None: user_schema})
            else:
                service.set_dbschema(None)
            # return service.update(data, id, id_field)
            return JSONResponse(jsonable_encoder(service.update(data, id, id_field), exclude=response_model_exclude))

        @_method_name('update_' + methodtag)
        def update_data_na(id, data: model, user_schema: Union[str, None] = Header(default=None)):
            """No authentication """
            # db: Session = Depends(get_db)
            # db = next(get_db())
            # return update(db, schema, data, id_field, id_)

            # Control db schema using header value
            if user_schema:
                service.set_dbschema({None: user_schema})
            else:
                service.set_dbschema(None)
            # return service.update(data, id, id_field)
            return JSONResponse(jsonable_encoder(service.update(data, id, id_field), exclude=response_model_exclude))

        @_method_name('patch_' + methodtag)
        def patch_data(id, data: Union[model, Annotated[dict, Body]],
                       token=Depends(self.oauth2_scheme), user_schema: Union[str, None] = Header(default=None)):
            # db: Session = Depends(get_db)
            # db = next(get_db())
            # return patch_data_na(id_, data, db)

            invalid = []
            for x in dict(data).keys():
                if x not in model.model_fields.keys():
                    invalid.append(x)

            if len(invalid) > 0:
                # print('Unsupported fields found: ' + (' ,'.join(invalid)))
                raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                    detail='Unsupported fields found: ' + (' ,'.join(invalid)))

            # Control db schema using header value
            if user_schema:
                service.set_dbschema({None: user_schema})
            else:
                service.set_dbschema(None)
            # return service.patch(data, id, id_field)
            return JSONResponse(jsonable_encoder(service.patch(data, id, id_field), exclude=response_model_exclude))

        @_method_name('patch_' + methodtag)
        def patch_data_na(id, data: Union[model, Annotated[dict, Body]],
                          user_schema: Union[str, None] = Header(default=None)):
            """No authentication """
            # db: Session = Depends(get_db)
            # db = next(get_db())
            invalid = []
            for x in dict(data).keys():
                if x not in model.model_fields.keys():
                    invalid.append(x)

            if len(invalid) > 0:
                # print('Unsupported fields found: ' + (' ,'.join(invalid)))
                raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                    detail='Unsupported fields found: ' + (' ,'.join(invalid)))

            # return patch(db, schema, data, id_field, id_)

            # Control db schema using header value
            if user_schema:
                service.set_dbschema({None: user_schema})
            else:
                service.set_dbschema(None)
            # return service.patch(data, id, id_field)
            return JSONResponse(jsonable_encoder(service.patch(data, id, id_field), exclude=response_model_exclude))

        # @self.router.delete("/{id}")
        @_method_name('delete_' + methodtag)
        def delete_data(id,
                        token=Depends(self.oauth2_scheme), user_schema: Union[str, None] = Header(default=None)):
            # db: Session = Depends(get_db)
            # db = next(get_db())
            # return delete(db, schema, id_field, id_)

            # Control db schema using header value
            if user_schema:
                service.set_dbschema({None: user_schema})
            else:
                service.set_dbschema(None)
            # return service.delete(id, id_field)
            return JSONResponse(jsonable_encoder(service.delete(id, id_field), exclude=response_model_exclude))

        @_method_name('delete_' + methodtag)
        def delete_data_na(id, user_schema: Union[str, None] = Header(default=None)):
            """No authentication """
            # db: Session = Depends(get_db)
            # db = next(get_db())
            # return delete(db, schema, id_field, id_)

            # Control db schema using header value
            if user_schema:
                service.set_dbschema({None: user_schema})
            else:
                service.set_dbschema(None)
            # return service.delete(id, id_field)
            return JSONResponse(jsonable_encoder(service.delete(id, id_field), exclude=response_model_exclude))

        # endregion crud_methods

        if HttpMethods.POST.value in access_mode:
            router.add_api_route("", create if self.oauth2_scheme else create_na, methods=["POST"],
                                 response_model=Union[model, dict, list[Union[model, dict]]],
                                 response_model_exclude=response_model_exclude,
                                 status_code=status.HTTP_201_CREATED,
                                 tags=[tag])
        if HttpMethods.GET.value in access_mode:
            router.add_api_route("", get_paginated if self.oauth2_scheme else get_paginated_na, methods=["GET"],
                                 response_model=Union[list[Union[model, dict]], dict[str, Union[list, int]]],
                                 response_model_exclude=response_model_exclude,
                                 status_code=status.HTTP_200_OK,
                                 tags=[tag])

            router.add_api_route("/{id}",
                                 get_by_id if self.oauth2_scheme else get_by_id_na,
                                 methods=["GET"],
                                 response_model=Union[model, dict],
                                 response_model_exclude=response_model_exclude,
                                 status_code=status.HTTP_200_OK,
                                 tags=[tag])
        if HttpMethods.GET_BY_ATTRIBUTE.value in access_mode:
            router.add_api_route("/{attribute}/{value}",
                                 get_by_attribute_paginated if self.oauth2_scheme else get_by_attribute_paginated_na,
                                 methods=["GET"],
                                 response_model=Union[list[Union[model, dict]], dict[str, Union[list, int]]],
                                 response_model_exclude=response_model_exclude,
                                 status_code=status.HTTP_200_OK,
                                 tags=[tag])
        if HttpMethods.PUT.value in access_mode:
            router.add_api_route("/{id}", update_data if self.oauth2_scheme else update_data_na, methods=["PUT"],
                                 response_model=list[Union[model, dict]],
                                 response_model_exclude=response_model_exclude,
                                 status_code=status.HTTP_200_OK,
                                 tags=[tag])
        if HttpMethods.PATCH.value in access_mode:
            router.add_api_route("/{id}", patch_data if self.oauth2_scheme else patch_data_na, methods=["PATCH"],
                                 response_model=list[Union[model, dict]],
                                 response_model_exclude=response_model_exclude,
                                 status_code=status.HTTP_200_OK,
                                 tags=[tag])
        if HttpMethods.DELETE.value in access_mode:
            router.add_api_route("/{id}", delete_data if self.oauth2_scheme else delete_data_na, methods=["DELETE"],
                                 tags=[tag])

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

    def add_options(self, app):

        def get_options_na(endpoint, response: Response):
            methods = set()
            for route in app.routes:
                if str(route.path).lower().startswith("/" + str(endpoint).lower()):
                    print(route.path)
                    print(route.methods)
                    for m in route.methods:
                        methods.add(m)

            allow = ','.join(methods)
            response.headers["Allow"] = allow
            # "OPTIONS, GET, HEAD, POST, PUT, DELETE"
            response.headers["Access-Control-Allow-Methods"] = allow
            # "OPTIONS, GET, HEAD, POST, PUT, DELETE"
            return None

        def get_options(endpoint, response: Response, token=Depends(self.oauth2_scheme)):
            return get_options_na(endpoint, response)

        # @app.options("/{endpoint}")
        app.add_api_route("/{endpoint}", get_options if self.oauth2_scheme else get_options_na, methods=["OPTIONS"],
                          tags=["Options"])


class Service:
    DataTable = declarative_base()

    def __init__(self, session, schema: DataTable):
        self.session = session
        self.schema = schema
        self.db_schema = None
        with self.session() as s:
            self.engine = s.get_bind()
            self.base_execution_options = {**self.engine.get_execution_options()}

    def set_dbschema(self, dbschema: Union[dict[Union[str, None], str],None]):
        self.db_schema = dbschema

    # def get_engine(self):
    #     s = self.session()
    #     try:
    #         yield s.get_bind()
    #     finally:
    #         s.close()

    def _get_db(self) -> Iterator[Session]:
        # if self.db_schema:
        #     engine = next(self.get_engine())
        #     engine = engine.execution_options(schema_translate_map=self.db_schema)
        #     self.session.configure(bind=engine)
        # else:
        #     engine = next(self.get_engine())
        #     engine = engine.execution_options(schema_translate_map={None: "public"})
        #     self.session.configure(bind=engine)

        if self.db_schema:
            # engine = next(self.get_engine())
            e = self.engine.execution_options(schema_translate_map=self.db_schema)
            self.session.configure(bind=e)
        else:
            # engine = next(self.get_engine())
            e = self.engine.execution_options(**self.base_execution_options)
            self.session.configure(bind=e)

        db = self.session()
        try:
            yield db
        finally:
            db.close()

    def create_any(self, obj: Union[BaseModel, dict]) -> dict:
        db = next(self._get_db())
        return create_any(db, schema=self.schema, data=obj)

    def create(self, obj: Union[BaseModel, dict], key_attribute, *args) -> dict:
        db = next(self._get_db())
        return create(db, schema=self.schema, key_attribute=key_attribute, data=obj, *args)

    def get_all(self, deep=False) -> list:
        db = next(self._get_db())
        return read(db, deep=deep, schema=self.schema)

    def get_all_paginated(self, page, limit, deep=False) -> dict[str, Union[list, int]]:
        db = next(self._get_db())
        return read_paginated(db, page=page, limit=limit, deep=deep, schema=self.schema)

    def get_one(self, id_value, id_field='id', deep=True) -> Union[dict, None]:

        db = next(self._get_db())
        return read_by_id(db, schema=self.schema, id_field=id_field, value=id_value, deep=deep)

    def get_by_attribute(self, value, attribute, deep=False, **kwargs) -> list:
        additional_attribute: dict = kwargs.get('additional_attributes', None)
        if additional_attribute is not None:
            if not isinstance(additional_attribute, dict):
                raise Exception("Arguments must be of type dict")

        db = next(self._get_db())
        return read_by_attribute(db, schema=self.schema, attribute=attribute, value=value,deep=deep,
                                 **kwargs)

    def get_by_attribute_paginated(self, value, attribute, page: int, limit: int, deep = False, **kwargs) -> dict[
        str, Union[list, int]]:
        additional_attribute: dict = kwargs.get('additional_attributes', None)
        if additional_attribute is not None:
            if not isinstance(additional_attribute, dict):
                raise Exception("Arguments must be of type dict")

        db = next(self._get_db())
        return read_by_attribute_paginated(db, schema=self.schema, attribute=attribute, value=value, page=page
                                           , limit=limit, deep=deep
                                           , **kwargs)

    def update(self, obj: Union[BaseModel, dict], id_value, *args) -> list:
        id_field = args[0] if args else 'id'

        db = next(self._get_db())
        return update(db, schema=self.schema, data=obj, attribute=id_field, value=id_value)

    def update_by_attribute(self, obj: Union[BaseModel, dict], value, attribute='id', **kwargs) -> list:
        additional_attribute: dict = kwargs.get('additional_attributes', None)
        if additional_attribute is not None:
            if not isinstance(additional_attribute, dict):
                raise Exception("Arguments must be of type dict")

        db = next(self._get_db())
        return update(db, schema=self.schema, data=obj, attribute=attribute, value=value, **kwargs)

    def delete(self, id_value, *args) -> dict[str, str]:
        id_field = args[0] if args else 'id'

        db = next(self._get_db())
        return delete(db, schema=self.schema, attribute=id_field, value=id_value)

    def delete_by_attribute(self, value, attribute='id', **kwargs) -> dict[str, str]:
        additional_attribute: dict = kwargs.get('additional_attributes', None)
        if additional_attribute is not None:
            if not isinstance(additional_attribute, dict):
                raise Exception("Arguments must be of type dict")

        db = next(self._get_db())
        return delete(db, schema=self.schema, attribute=attribute, value=value, **kwargs)

    def patch(self, obj: Union[BaseModel, dict], id_value, *args) -> list:
        id_field = args[0] if args else 'id'

        db = next(self._get_db())
        return patch(db, schema=self.schema, data=obj, attribute=id_field, value=id_value)

    def patch_by_attribute(self, obj: Union[BaseModel, dict], value, attribute='id', **kwargs) -> list:
        additional_attribute: dict = kwargs.get('additional_attributes', None)
        if additional_attribute is not None:
            if not isinstance(additional_attribute, dict):
                raise Exception("Arguments must be of type dict")

        db = next(self._get_db())
        return patch(db, schema=self.schema, data=obj, attribute=attribute, value=value, **kwargs)
