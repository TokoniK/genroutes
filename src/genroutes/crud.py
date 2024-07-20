from typing import Type, Union
from pydantic import BaseModel
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

from sqlalchemy.inspection import inspect
import base64


def bytes_to_binary(byte_data):
    """" Helper util convert from bytes to binary """
    return ' '.join(format(byte, '08b') for byte in byte_data)


def binary_to_bytearray(binary):
    """" Helper util convert from binary to byte array """
    binary_values = binary.split()
    byte_array = bytearray(int(bv, 2) for bv in binary_values)
    return byte_array


def to_json(obj) -> dict:
    """" Safe conversion for byte to base64 for HTTP response"""
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
        # result_list.append(r.__dict__)
        result_list.append(to_json(r))

    return result_list


def get_by_id(db: Session, schema: Type[declarative_base()], id_value) -> dict | None:
    results = db.query(schema).filter(schema.id == id_value).first()
    if results is None:
        return results
    return to_json(results)  # results.__dict__


def create(db: Session, schema: Type[declarative_base()], data: BaseModel) -> dict:
    obj = from_json(data.dict())
    # db_row_object = schema(**data.dict())
    db_row_object = schema(**obj)
    db.add(db_row_object)
    db.commit()
    db.refresh(db_row_object)
    return to_json(db_row_object)  # db_row_object.__dict__


def update(db: Session, schema: Type[declarative_base()], data: BaseModel, row_id) -> dict:
    obj = from_json(data.dict(exclude_unset=True))
    # db.query(schema).filter_by(id=row_id).update(data.dict(exclude_unset=True), synchronize_session="fetch")
    db.query(schema).filter_by(id=row_id).update(obj, synchronize_session="fetch")
    db.commit()
    db_row_object = db.query(schema).filter_by(id=row_id).first()
    return to_json(db_row_object)  # db_row_object.__dict__


def update_by_attribute(db: Session, schema: Type[declarative_base()], data: BaseModel,
                        attribute, value, **kwargs) -> list[dict]:
    # filter = {attribute: value}
    additional_attribute: dict = kwargs.get('additional_attributes', None)
    if additional_attribute is not None:
        if not isinstance(additional_attribute, dict):
            raise Exception("update_by_attribute: Arguments must be of type dict")

    additional_attribute = {} if additional_attribute is None else additional_attribute
    all_filter_attributes = {attribute: value, **additional_attribute}

    # rows = db.query(schema).filter_by(**filter)
    rows = db.query(schema).filter(*filter_model(schema, all_filter_attributes))

    if len(rows.all()) == 0:
        return []

    if not isinstance(data, dict):
        data = data.dict(exclude_unset=True)

    obj = from_json(data)
    rows.update(obj, synchronize_session="fetch")

    db.commit()
    result_list = []
    # db_row_objects = db.query(schema).filter_by(**filter).all()
    db_row_objects = db.query(schema).filter(*filter_model(schema, all_filter_attributes)).all()

    for r in db_row_objects:
        # result_list.append(r.__dict__)
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
        # result_list.append(r.__dict__)
        result_list.append(to_json(r))

    return result_list


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

    # db.query(schema).filter_by(**filter).delete(synchronize_session="fetch")
    db.query(schema).filter(*filter_model(schema, all_filter_attributes)).delete(synchronize_session="fetch")

    db.commit()
    return "Success"


def filter_model(schema, filter_attributes):
    # filters = [schema.__dict__[attribute] == value]
    filters = []
    # if additional_attribute is not None:
    for k, v in filter_attributes.items():
        try:
            # filters = [*filters, schema.__dict__[k] == v]
            filters = [*filters, to_json(schema)[k] == v]

        except KeyError:
            pass

    return filters

# class Crud:
#     def __init__(self, session: sessionmaker):
#         self.session = session
#
#     def get_db(self):
#         db = self.session()
#         try:
#             yield db
#         finally:
#             db.close()
#
#     def get_all(self, model) -> list[dict]:
#         db = next(self.get_db())
#         results = db.query(model).all()
#         result_list = []
#
#         for r in results:
#             result_list.append(r.__dict__)
#         return result_list
#
#     def get_by_id(self, model, id) -> dict:
#         db = next(self.get_db())
#         results = db.query(model).filter(model.id == id).first()
#         if results is None: return results
#         return results.__dict__
#
#     def create(self, model, data: BaseModel) -> dict:
#         db = next(self.get_db())
#         db_row_object = model(**data.dict())
#         db.add(db_row_object)
#         db.commit()
#         db.refresh(db_row_object)
#         return db_row_object.__dict__
#
#     def update(self, model, data: BaseModel, row_id) -> dict:
#         db = next(self.get_db())
#         db.query(model).filter_by(id=row_id).update(data.dict(exclude_unset=True), synchronize_session="fetch")
#         db.commit()
#         db_row_object = db.query(model).filter_by(id=row_id).first()
#         return db_row_object.__dict__
#
#     def update_by_attribute(self, model, data: BaseModel, attribute, value) -> list[dict]:
#         db = next(self.get_db())
#         filter = {attribute: value}
#         rows = db.query(model).filter_by(**filter)
#         if len(rows.all()) == 0:
#             return []
#
#         if not isinstance(data, dict):
#             data = data.dict(exclude_unset=True)
#
#         rows.update(data, synchronize_session="fetch")
#         db.commit()
#         result_list = []
#         db_row_objects = db.query(model).filter_by(**filter).all()
#         for r in db_row_objects:
#             result_list.append(r.__dict__)
#         return result_list
#
#     def get_by_attribute(self, model, attribute, value) -> list[dict]:
#         db = next(self.get_db())
#         results = db.query(model).filter(model.__dict__[attribute] == value).all()
#         result_list = []
#
#         for r in results:
#             result_list.append(r.__dict__)
#         return result_list
#
#     def delete(self, model, row_id) -> str:
#         db = next(self.get_db())
#         db.query(model).filter_by(id=row_id).delete(synchronize_session="fetch")
#
#         db.commit()
#         return "Success"
#
#     def delete_by_attribute(self, model, attribute, value) -> str:
#         db = next(self.get_db())
#         filter_values = {attribute: value}
#         db.query(model).filter_by(**filter_values).delete(synchronize_session="fetch")
#
#         db.commit()
#         return "Success"
