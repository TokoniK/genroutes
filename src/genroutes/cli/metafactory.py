from sqlalchemy.sql.elements import Null

__author__ = 'Ahmet Erkan ÇELİK'

import re
import inflect
import os
import psycopg2


def generate_models(database, username, hostname, port, password, schemaname):
    conn = None
    try:
        conn = psycopg2.connect(
            "dbname='%s' user='%s' host='%s' port='%s' password='%s' options='-c search_path=dbo,%s'" % (
                database, username, hostname, port, password, schemaname))
        # conn = psycopg2.connect("dbname='%s' user='%s' host='%s' port='%s'  password='%s'" % ('postgres', 'postgres', 'localhost','5437', 'test' ))

    except:
        print("Unable to connect to the database!")
        quit()

    cur = conn.cursor()
    # file = open(args.file, "w", encoding='utf-8')
    # file = open('db.py', "w", encoding='utf-8')
    # file.write("""from sqlalchemy import *
    # from sqlalchemy.orm import relationship
    # from sqlalchemy.ext.declarative import declarative_base
    # from sqlalchemy.dialects.postgresql import *
    # import json
    #
    # DatabaseTable = declarative_base()
    #
    #
    # """)
    # file.write(metafactory.tables(cur))
    # file.close()

    # create data package / sub packeages
    data_path = os.path.abspath('./data')
    models_path = os.path.abspath('data/models')
    schemas_path = os.path.abspath('data/schemas')

    try:
        os.mkdir(data_path)
    except OSError as error:
        print(error)

    try:
        os.mkdir(models_path)
    except OSError as error:
        print(error)

    try:
        os.mkdir(schemas_path)
    except OSError as error:
        print(error)

    with open(data_path + "/__init__.py", "w", encoding='utf-8') as file:
        file.write("")
    with open(models_path + "/__init__.py", "w", encoding='utf-8') as file:
        file.write("")
    with open(schemas_path + "/__init__.py", "w", encoding='utf-8') as file:
        file.write("from .database_env import DatabaseTable, SessionLocal, SQLALCHEMY_DATABASE_URL, engine")

    with open(schemas_path + "/database_env.py", "w", encoding='utf-8') as file:
        file.write('"""Initialize base objects for database schema model"""\n\n')
        file.write("from sqlalchemy import create_engine\n"
                   "from sqlalchemy.orm import declarative_base\n"
                   "from sqlalchemy.orm import sessionmaker\n\n"
                   "SQLALCHEMY_DATABASE_URL = 'postgresql://user:password@postgresserver/db'\n"
                   "engine = create_engine(\n"
                   "    SQLALCHEMY_DATABASE_URL\n"
                   ")\n"
                   "SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)\n\n"
                   "DatabaseTable = declarative_base()")

    metafactory.tables(cur, schemaname)


class metafactory:
    @staticmethod
    def tables(cur, schema="public"):
        cur.execute("""SELECT * FROM  pg_tables WHERE schemaname = '%s'""" % schema)
        ts = cur.fetchall()
        models = ""
        classes = ""
        p = inflect.engine()
        models_path = os.path.abspath('data/models')
        schemas_path = os.path.abspath('data/schemas')

        for t in ts:
            # models_ineed += "%sTable = Table(u'%s', Base.metadata,\n %s%s,\n\n    #schema\n    schema='%s'\n)\n\n" % (str(t[1]).title(), t[1], metafactory.colums(cur, t[1]), metafactory.fk(cur, t[1], schema),schema)
            if classes != "":
                classes += "\n\n\n"
            tableName = str(t[1])
            # className = tableName.title().replace('_', '')
            # names = tableName.split('_')
            # names = [n[0].upper()+n[1:] for n in names if n]
            className = metafactory.buildClassName(tableName)  # ''.join(names)
            # className = tableName.replace('_', '')
            colums = metafactory.colums(cur, tableName)
            br = metafactory.br(cur, t[1])
            print(className)
            singularClassName = p.singular_noun(className) if p.singular_noun(className) else className
            fileName = p.singular_noun(tableName) if p.singular_noun(tableName) else tableName

            # classes += "class %s(DatabaseTable):\n    __tablename__ = u'%s'%s%s\n\n%s" % (className, tableName, colums, br, metafactory.toJsonMethod(cur, t[1]))
            model_class = "class %s(DatabaseTable):\n    __tablename__ = u'%s'%s%s\n\n%s\n" % (
                singularClassName, tableName, colums, br,
                metafactory.toJsonMethod(cur, t[1]))
            print(model_class)

            # file_path = os.path.abspath(schemas_path + '/%s.py' % singularClassName.lower())
            file_path = os.path.abspath(schemas_path + '/%s.py' % fileName.lower())

            # try:
            #     os.mkdir(dir_path)
            # except OSError as error:
            #     print(error)

            file = open(file_path, "w", encoding='utf-8')
            file.write("""from sqlalchemy import *
from sqlalchemy.orm import relationship
# from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import *
import json
from ..schemas import DatabaseTable
from sqlalchemy.orm import Mapped, mapped_column

# DatabaseTable = declarative_base()


""")
            file.write(model_class)
            file.close()

            file_path = os.path.abspath(schemas_path + '/__init__.py')
            with open(file_path, "a", encoding='utf-8') as file:
                imp = '\nfrom .%s import %s' % (fileName, singularClassName)
                file.write(imp)

            # file_path = os.path.abspath(models_path + '/%s.py' % singularClassName.lower())
            file_path = os.path.abspath(models_path + '/%s.py' % fileName.lower())

            # try:
            #     os.mkdir(dir_path)
            # except OSError as error:
            #     print(error)

            with open(file_path, "w", encoding='utf-8') as file:
                print('build model class ' + tableName)
                file.write(metafactory.buildModel(cur, tableName, singularClassName))

            file_path = os.path.abspath(models_path + '/__init__.py')
            with open(file_path, "a", encoding='utf-8') as file:
                imp = '\nfrom .%s import %s' % (fileName, singularClassName)
                file.write(imp)

        file_path = os.path.abspath(schemas_path + '/__init__.py')
        with open(file_path, "a", encoding='utf-8') as file:
            imp = '\n'
            file.write(imp)

        file_path = os.path.abspath(models_path + '/__init__.py')
        with open(file_path, "a", encoding='utf-8') as file:
            imp = '\n'
            file.write(imp)

        # return classes

    @staticmethod
    def buildClassName(tableName: str):
        names = tableName.split('_')
        names = [n[0].upper() + n[1:] for n in names if n]
        className = ''.join(names)
        return className

    # def buildFileName(tableName: str):
    #     names = tableName.split('_')
    #     names = [n[0].upper() + n[1:] for n in names if n]
    #     className = '_'.join(names)
    #     return className

    @staticmethod
    def colums(cur, tablename):
        print(cur, tablename)
        cur.execute("""
                        SELECT DISTINCT ON (attnum) pg_attribute.attnum,pg_attribute.attname as column_name,
                           format_type(pg_attribute.atttypid, pg_attribute.atttypmod) as data_type,
                           pg_attribute.attlen as lenght, pg_attribute.atttypmod as lenght_var,
                           pg_attribute.attnotnull as is_notnull,
                           pg_attribute.atthasdef as has_default,
                           --adsrc as default_value,
                           '' as default_value,
                           pg_constraint.contype,
                           pg_attribute.attidentity identity_type

                        FROM
                          pg_attribute
                          INNER JOIN pg_class ON (pg_attribute.attrelid = pg_class.oid)
                          INNER JOIN pg_type ON (pg_attribute.atttypid = pg_type.oid)
                          LEFT OUTER JOIN pg_attrdef ON (pg_attribute.attrelid = pg_attrdef.adrelid AND pg_attribute.attnum=pg_attrdef.adnum)
                          LEFT OUTER JOIN pg_index ON (pg_class.oid = pg_index.indrelid AND pg_attribute.attnum = any(pg_index.indkey))
                          LEFT OUTER JOIN pg_constraint ON (pg_constraint.conrelid = pg_class.oid AND pg_constraint.conkey[1]= pg_attribute.attnum)
                         WHERE pg_class.relname = '%s'
                         AND pg_attribute.attnum>0
                    """ % tablename)
        cs = cur.fetchall()
        cols = ""
        for c in cs:
            print(c)
            dt = c[2]
            if re.search("character varying", dt):
                # print(c[4])
                dt = "VARCHAR%s" % ('' if c[4] == -1 else '(%s)' % (int(c[4]) - 4))
            elif re.search("character", dt):
                dt = "CHAR%s" % ('' if c[4] == -1 else '(%s)' % (int(c[4]) - 4))
            elif re.search("timestamp", dt):
                dt = "TIMESTAMP()"
            elif re.search("date", dt) or re.search("datetime", dt):
                dt = "DATETIME()"
            elif re.search("bigint", dt):
                dt = "BIGINT"
            else:
                # print('xxxxxxxxxxxx ' + dt)
                dt = dt.replace(" ", "_").upper() + "()"
            if cols != "":
                cols += "\n"
            cols += "    %s = Column(%s" % (c[1], dt)
            if c[9] == "d":
                cols += ", Identity()"
            elif c[9] == "a":
                cols += ", Identity(always=True)"
            if c[6]:
                if re.search("nextval\('", c[7]):
                    cols += ", Sequence('%s')" % str(c[7]).replace("nextval('", "").replace("'::regclass)", "")
                else:
                    cols += ", server_default=text('%s')" % c[7]
            if c[8] == "p":
                cols += ", primary_key=True"
            elif c[8] == "f":
                cols += ", ForeignKey('%s')" % metafactory.isFk(cur, tablename, c[1])
            if c[5]:
                cols += ", nullable=False"
            cols += ")"
        cols = "\n\n    # column definitions\n" + cols
        return cols

    @staticmethod
    def isFk(cur, tablename, column):
        fks = metafactory.forein_keys(cur, tablename)
        for c in fks:
            if c[1] == column:
                return "%s.%s" % (c[2], c[3])
        else:
            return Null

    @staticmethod
    def fk(cur, tablename, schema="public"):
        fks = metafactory.forein_keys(cur, tablename)
        foreignkeys = ""
        for f in fks:
            if foreignkeys != "":
                foreignkeys += ",\n"
            foreignkeys += "    ForeignKeyConstraint(['%s'],['%s.%s.%s'],name='%s')" % (f[1], schema, f[2], f[3], f[0])

        if foreignkeys != "":
            foreignkeys = ",\n\n    #foreign keys\n" + foreignkeys

        return foreignkeys

    def br(cur, tablename):
        fks = metafactory.forein_keys(cur, tablename)
        p = inflect.engine()

        foreignkeys = ""
        for f in fks:
            if foreignkeys != "":
                foreignkeys += "\n"
            col = str(f[1])
            parentTable = metafactory.buildClassName(f[2])  # str(f[2]).title().replace("_", "")
            tableClass = metafactory.buildClassName(tablename)  # str(tablename).title().replace("_", "")
            singularParentTable = p.singular_noun(parentTable) if p.singular_noun(parentTable) else parentTable
            singularTableClass = p.singular_noun(tableClass) if p.singular_noun(tableClass) else tableClass
            var = tableClass + ''.join(col.rsplit('_id', 1)).title().replace('_', '')
            parentCol = f[3]
            # foreignkeys += "    %s = relationship('%s', primaryjoin='%s.%s == %s.%s')" % (
            #     var, parentTable, tableClass, col, parentTable, parentCol)
            foreignkeys += "    %s = relationship('%s', primaryjoin='%s.%s == %s.%s')" % (
                var, singularParentTable, singularTableClass, col, singularParentTable, parentCol)
            # foreignkeys += "    %s = relationship('%s')" % (var, parentTable)

        if foreignkeys != "":
            foreignkeys = "\n\n    #relation definitions: many to one with backref (also takes care of one to many)\n" + foreignkeys

        return foreignkeys

    @staticmethod
    def forein_keys(cur, tablename, many_to_one=False):
        cur.execute("""
            SELECT pg_constraint.conname  as fkname, pga2.attname as colname, pc2.relname as referenced_table_name, pga1.attname as referenced_column_name
            FROM pg_class pc1, pg_class pc2, pg_constraint, pg_attribute pga1, pg_attribute pga2
            WHERE pg_constraint.conrelid = pc1.oid
            AND pc2.oid = pg_constraint.confrelid
            AND pga1.attnum = pg_constraint.confkey[1]
            AND pga1.attrelid = pc2.oid
            AND pga2.attnum = pg_constraint.conkey[1]
            AND pga2.attrelid = pc1.oid
            AND pc1.relname = '%s'
        """ % tablename)
        return cur.fetchall()

    @staticmethod
    def toJsonMethod(cur, tablename):
        metod = "    def to_json(self):\n        obj = {"
        cur.execute("""
                        SELECT DISTINCT ON (attnum) pg_attribute.attnum,pg_attribute.attname as column_name,
                           format_type(pg_attribute.atttypid, pg_attribute.atttypmod) as data_type,
                           pg_attribute.attlen as lenght, pg_attribute.atttypmod as lenght_var,
                           pg_attribute.attnotnull as is_notnull,
                           pg_attribute.atthasdef as has_default,
                           --adsrc as default_value,
                           '' as default_value,
                           pg_constraint.contype
                        FROM
                          pg_attribute
                          INNER JOIN pg_class ON (pg_attribute.attrelid = pg_class.oid)
                          INNER JOIN pg_type ON (pg_attribute.atttypid = pg_type.oid)
                          LEFT OUTER JOIN pg_attrdef ON (pg_attribute.attrelid = pg_attrdef.adrelid AND pg_attribute.attnum=pg_attrdef.adnum)
                          LEFT OUTER JOIN pg_index ON (pg_class.oid = pg_index.indrelid AND pg_attribute.attnum = any(pg_index.indkey))
                          LEFT OUTER JOIN pg_constraint ON (pg_constraint.conrelid = pg_class.oid AND pg_constraint.conkey[1]= pg_attribute.attnum)
                         WHERE pg_class.relname = '%s'
                         AND pg_attribute.attnum>0
                    """ % tablename)
        cs = cur.fetchall()
        for c in cs:
            if re.search("timestamp", c[2]):
                metod += ("\n            '%s': self.%s" % (
                    c[1], c[1])) + ".strftime('%a, %d %b %Y %H:%M:%S +0000') if " + ("self.%s else None," % (c[1]))
            else:
                metod += "\n            '%s': self.%s," % (c[1], c[1])
        metod += "\n        }\n        return obj  # return json.dumps(obj)"
        return metod

    def buildModel(cur, tablename, className):
        print(cur, tablename)
        cur.execute("""
                        SELECT DISTINCT ON (attnum) pg_attribute.attnum,pg_attribute.attname as column_name,
                           format_type(pg_attribute.atttypid, pg_attribute.atttypmod) as data_type,
                           pg_attribute.attlen as lenght, pg_attribute.atttypmod as lenght_var,
                           pg_attribute.attnotnull as is_notnull,
                           pg_attribute.atthasdef as has_default,
                           --adsrc as default_value,
                           '' as default_value,
                           pg_constraint.contype
                        FROM
                          pg_attribute
                          INNER JOIN pg_class ON (pg_attribute.attrelid = pg_class.oid)
                          INNER JOIN pg_type ON (pg_attribute.atttypid = pg_type.oid)
                          LEFT OUTER JOIN pg_attrdef ON (pg_attribute.attrelid = pg_attrdef.adrelid AND pg_attribute.attnum=pg_attrdef.adnum)
                          LEFT OUTER JOIN pg_index ON (pg_class.oid = pg_index.indrelid AND pg_attribute.attnum = any(pg_index.indkey))
                          LEFT OUTER JOIN pg_constraint ON (pg_constraint.conrelid = pg_class.oid AND pg_constraint.conkey[1]= pg_attribute.attnum)
                         WHERE pg_class.relname = '%s'
                         AND pg_attribute.attnum>0
                    """ % tablename)
        cs = cur.fetchall()
        imports = "from pydantic import BaseModel"
        class_header = "class %s(BaseModel): \n" % className
        has_date = False
        cols = ""

        for c in cs:
            dt = c[2]
            if re.search("character varying", dt):
                dt = "str"
            elif re.search("character", dt):
                dt = "str"
            elif re.search("timestamp", dt) or re.search("date", dt):
                dt = "datetime"
                has_date = True
            elif re.search("integer", dt):
                dt = "int"
            elif re.search("numeric", dt):
                dt = "int | float"
            elif re.search("text", dt):
                dt = "str"
            elif re.search("text", dt):
                dt = "str"
            elif re.search("json", dt):
                dt = "dict"
            elif re.search("int", dt):
                dt = "int"
            else:
                dt = dt.replace(" ", "_").upper() + "()"
            if cols != "":
                cols += "\n"
            cols += "    %s: %s" % (c[1], dt)

            if c[8] == "p":
                cols += " | None"
            elif c[8] == "f":
                pass
                # print(metafactory.isFk(cur, tablename, c[1]))
                # cols += ", ForeignKey('%s')" % metafactory.isFk(cur, tablename, c[1])
            if not c[5]:
                cols += " | None = None"

        if has_date:
            imports = imports + "\nfrom datetime import datetime"
        imports += "\n\n\n"
        cols = "\n    # column definitions\n" + cols + "\n"

        return imports + class_header + cols
