from typing import Type

from pydantic import BaseModel
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session


def get_all(db: Session, schema) -> list[dict]:
    results = db.query(schema).all()
    result_list = []

    for r in results:
        result_list.append(r.__dict__)
    return result_list


def get_by_id(db: Session, schema: Type[declarative_base()], id_value) -> dict | None:
    results = db.query(schema).filter(schema.id == id_value).first()
    if results is None:
        return results
    return results.__dict__


def create(db: Session, schema: Type[declarative_base()], data: BaseModel) -> dict:
    db_row_object = schema(**data.dict())
    db.add(db_row_object)
    db.commit()
    db.refresh(db_row_object)
    return db_row_object.__dict__


def update(db: Session, schema: Type[declarative_base()], data: BaseModel, row_id) -> dict:
    db.query(schema).filter_by(id=row_id).update(data.dict(exclude_unset=True), synchronize_session="fetch")
    db.commit()
    db_row_object = db.query(schema).filter_by(id=row_id).first()
    return db_row_object.__dict__


def update_by_attribute(db: Session, schema: Type[declarative_base()], data: BaseModel,
                        attribute, value, **kwargs) -> list[dict]:
    # filter = {attribute: value}
    additional_attribute: dict = kwargs.get('additional_attributes', None)
    if additional_attribute is not None:
        if not isinstance(additional_attribute, dict):
            raise Exception("Arguments must be of type dict")

    additional_attribute = {} if additional_attribute is None else additional_attribute
    all_filter_attributes = {attribute: value, **additional_attribute}

    # rows = db.query(schema).filter_by(**filter)
    rows = db.query(schema).filter(*filter_model(schema, all_filter_attributes))

    if len(rows.all()) == 0:
        return []

    if not isinstance(data, dict):
        data = data.dict(exclude_unset=True)

    rows.update(data, synchronize_session="fetch")
    db.commit()
    result_list = []
    # db_row_objects = db.query(schema).filter_by(**filter).all()
    db_row_objects = db.query(schema).filter(*filter_model(schema, all_filter_attributes)).all()

    for r in db_row_objects:
        result_list.append(r.__dict__)
    return result_list


def get_by_attribute(db: Session, schema: Type[declarative_base()], attribute, value, **kwargs) -> list[dict]:
    additional_attribute: dict = kwargs.get('additional_attributes', None)
    if additional_attribute is not None:
        if not isinstance(additional_attribute, dict):
            raise Exception("Arguments must be of type dict")

    additional_attribute = {} if additional_attribute is None else additional_attribute
    all_filter_attributes = {attribute: value, **additional_attribute}

    results = db.query(schema).filter(*filter_model(schema, all_filter_attributes)).all()
    result_list = []

    for r in results:
        result_list.append(r.__dict__)

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
            raise Exception("Arguments must be of type dict")

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
            filters = [*filters, schema.__dict__[k] == v]
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
