"""Generate CRUD routes for FastAPI projects, reduce boilerplate code, accelerate development of FastAPI backend!"""
__version__ = "0.0.1"

from .generic_routes import Routes, HttpMethods, Service
from .crud import to_json_non_recursive, to_json, filter_model, query_with_all_relationships, recursive_load