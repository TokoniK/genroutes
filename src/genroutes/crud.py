from typing import Type, Union
from pydantic import BaseModel
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import Session
from sqlalchemy import func, VARCHAR, TEXT, CHAR, NVARCHAR

from sqlalchemy.inspection import inspect
import base64


def to_json(obj) -> dict:
    """" Safe conversion for byte to base64 for HTTP response
    """
    return {i.key: getattr(obj, i.key) if not type(getattr(obj, i.key)) == bytes
    else base64.b64encode(getattr(obj, i.key)).decode('utf-8')
            for i in inspect(obj).mapper.column_attrs}


def from_json(obj: dict) -> dict:
    """" Safe conversion from base64 to bytes from HTTP request """
    return {k: v if not type(v) == bytes else base64.b64decode(v)
            for k, v in obj.items()}


def get_all(db: Session, schema) -> list[dict]:
    results = db.query(schema).all()
    result_list = []

    for r in results:
        result_list.append(to_json(r))

    return result_list


def get_by_id(db: Session, schema: Type[declarative_base()], id_value) -> dict | None:
    results = db.query(schema).filter(schema.id == id_value).first()
    if results is None:
        return results
    return to_json(results)  # results.__dict__


def create(db: Session, schema: Type[declarative_base()], data: BaseModel) -> dict:
    obj = from_json(data.model_dump())
    db_row_object = schema(**obj)
    db.add(db_row_object)
    db.commit()
    db.refresh(db_row_object)
    return to_json(db_row_object)  # db_row_object.__dict__


def update(db: Session, schema: Type[declarative_base()], data: BaseModel, row_id) -> dict:
    obj = from_json(data.model_dump(exclude_unset=True))
    db.query(schema).filter_by(id=row_id).update(obj, synchronize_session="fetch")
    db.commit()
    db_row_object = db.query(schema).filter_by(id=row_id).first()
    return to_json(db_row_object)  # db_row_object.__dict__


def update_by_attribute(db: Session, schema: Type[declarative_base()], data: BaseModel,
                        attribute, value, **kwargs) -> list[dict]:
    additional_attribute: dict = kwargs.get('additional_attributes', None)
    if additional_attribute is not None:
        if not isinstance(additional_attribute, dict):
            raise Exception("update_by_attribute: Arguments must be of type dict")

    additional_attribute = {} if additional_attribute is None else additional_attribute
    all_filter_attributes = {attribute: value, **additional_attribute}

    rows = db.query(schema).filter(*filter_model(schema, all_filter_attributes))

    if len(rows.all()) == 0:
        return []

    if not isinstance(data, dict):
        data = data.model_dump(exclude_unset=True)

    obj = from_json(data)
    rows.update(obj, synchronize_session="fetch")

    db.commit()
    result_list = []
    # db_row_objects = db.query(schema).filter_by(**filter).all()
    db_row_objects = db.query(schema).filter(*filter_model(schema, all_filter_attributes)).all()

    for r in db_row_objects:
        result_list.append(to_json(r))

    return result_list


def get_by_attribute(db: Session, schema: Type[declarative_base()], attribute, value, **kwargs) -> list[dict]:
    additional_attribute: dict = kwargs.get('additional_attributes', None)
    if additional_attribute is not None:
        if not isinstance(additional_attribute, dict):
            raise Exception("get_by_attribute: Arguments must be of type dict")

    additional_attribute = {} if additional_attribute is None else additional_attribute
    all_filter_attributes = {attribute: value, **additional_attribute}

    results = db.query(schema).filter(*filter_model(schema, all_filter_attributes)).all()
    result_list = []

    for r in results:
        result_list.append(to_json(r))

    return result_list

def get_by_attribute_paginated(db: Session, schema: Type[declarative_base()], attribute, value, page, limit, **kwargs) -> dict[str, list|int]:
    additional_attribute: dict = kwargs.get('additional_attributes', None)
    if additional_attribute is not None:
        if not isinstance(additional_attribute, dict):
            raise Exception("get_by_attribute: Arguments must be of type dict")

    additional_attribute = {} if additional_attribute is None else additional_attribute
    all_filter_attributes = {attribute: value, **additional_attribute}

    attr_names = [attr for attr in list(schema.__dict__.keys()) if
                  not callable(getattr(schema, attr)) and not attr.startswith("__")]

    # Access attribute by index
    index = 0
    attr_name = attr_names[index]
    attr_value = getattr(schema, attr_name)

    results = db.query(schema).order_by(attr_value) \
        .filter(*filter_model(schema, all_filter_attributes)) \
        .offset(page * limit) \
        .limit(limit) \
        .all()

    count = db.query(schema).filter(*filter_model(schema, all_filter_attributes)).count()

    # results = db.query(schema).filter(*filter_model(schema, all_filter_attributes)).all()
    result_list = []

    for r in results:
        result_list.append(to_json(r))

    return {'rows': result_list, 'count': count}


def delete(db: Session, schema: Type[declarative_base()], row_id) -> str:
    db.query(schema).filter_by(id=row_id).delete(synchronize_session="fetch")

    db.commit()
    return "Success"


def delete_by_attribute(db: Session, schema: Type[declarative_base()], attribute, value, **kwargs) -> str:
    # filter = {attribute: value}
    additional_attribute: dict = kwargs.get('additional_attributes', None)
    if additional_attribute is not None:
        if not isinstance(additional_attribute, dict):
            raise Exception("delete_by_attribute: Arguments must be of type dict")

    additional_attribute = {} if additional_attribute is None else additional_attribute
    all_filter_attributes = {attribute: value, **additional_attribute}

    db.query(schema).filter(*filter_model(schema, all_filter_attributes)).delete(synchronize_session="fetch")

    db.commit()
    return "Success"


def filter_model(schema, filter_attributes):
    filters = []
    for k, v in filter_attributes.items():
        try:
            # filters = [*filters, to_json(schema)[k] == v]

            # make case-insensitive for string
            # print(to_json(schema)[k].type)
            if isinstance(to_json(schema)[k].type, (VARCHAR, CHAR, NVARCHAR, TEXT)):
                filters = [*filters, func.lower(to_json(schema)[k]) == func.lower(v)]
            else:
                filters = [*filters, to_json(schema)[k] == v]

        except KeyError:
            pass

    return filters
