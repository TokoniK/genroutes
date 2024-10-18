# import re
# import inflect
# import os
# import psycopg2
import argparse

from .generate import generate_routes
from .metafactory import generate_models


def main():

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')

    parser_generate = subparsers.add_parser('generate', help='Generate routers based on sqlalchemy schemas and pydantic models')
    # parser_generate.add_argument('arg1', type=str, help='Argument 1 for script 1')
    parser_generate.add_argument("-schemadir", "--schema", help="database schema directory", dest="schema")
    parser_generate.add_argument("-modeldir", "--model", help="pydantic model directory", dest="model")
    parser_generate.add_argument("-idfields", "--id", help="include id fields per schema object", dest="id" )


    parser_models = subparsers.add_parser('models', help='Generate sqlalchemy schemas and models')
    # parser_models.add_argument('arg1', type=int, help='Argument 1 for script 2')
    # parser_models.add_argument('arg2', type=str, help='Argument 2 for script 2')
    parser_models.add_argument("-host", "--hostname", help="Hostname", dest="hostname")
    parser_models.add_argument("-db", "--database", help="Database name", dest="database")
    parser_models.add_argument("-user", "--username", help="User name", dest="username")
    parser_models.add_argument("-pass", "--password", help="Password", dest="password")
    parser_models.add_argument("-sch", "--schemaname", help="Schema name", dest="schemaname", default="public")
    parser_models.add_argument("-file", "--filename", help="Output file name", dest="file")
    parser_models.add_argument("-port", "--port", help="port", dest="port")
    parser_models.add_argument("-full", "--full", help="generate relationships serializer", dest="full",
                               const=True, nargs='?')

    args = parser.parse_args()

    if args.command == 'generate':
        if not args.schema or not args.model:
            print('include args -schema & -model')
            return

        id = True if args.id else False
        generate_routes(args.schema, args.model,id)

    elif args.command == 'models':
        # full = False
        # if args.full:
        #     full = True
        generate_models(args.database, args.username, args.hostname, args.port, args.password, args.schemaname, args.full)
