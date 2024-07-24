import os


def generate_routes(schema, model):
    schema_pkg = schema.replace('/', '.')
    model_pkg = model.replace('/', '.')

    sc = schema_pkg.split('.')
    imp_sc = 'from %s import %s' % ('.'.join(sc[0:-1]), sc[-1])
    md = model_pkg.split('.')
    imp_md = 'from %s import %s' % ('.'.join(md[0:-1]), md[-1])

    imp = 'from genroutes import Routes, HttpMethods\n'
    imp += 'from fastapi import FastAPI\n'
    # imp +='import %s \nimport %s\n\n' % (schema_pkg, model_pkg)
    imp +='%s\n%s\n\n' % (imp_sc, imp_md)


    sc_path = os.path.abspath(('./'+schema).replace('//','/'))
    md_path = os.path.abspath(('./'+model_pkg).replace('//','/'))

    files = os.listdir(sc_path)

    init = 'app = FastAPI()\n\n# inject db session maker object\nroutes = Routes(SessionLocal) \n\n'

    print(imp)
    print(init)
    existing = ""
    with open('main.py', 'r') as file:
        existing = file.read()

    with open('main.py', 'w') as file:
        file.write('# organize imports\n\n')
        file.write(imp)
        file.write('# end imports\n\n')

        file.write(existing)

        file.write('\n\n# initialize FastAPI\n')
        file.write(init)
        file.write('# verify id_field param of routes.get_router\n\n')
        for f in files:
            if f.endswith('.py') and not f.startswith('__'):
                # print(f[0].upper()+f[1:-3])
                clsName = f[0].upper()+f[1:-3]
                names = clsName.split('_')
                names = [f[0].upper()+f[1:] for f in names]
                clsName = ''.join(names)
                router_declare = "app.include_router(routes.get_router('%s', schemas.%s, models.%s, models.%s))\n" \
                                 % (f[0:-3], clsName, clsName, clsName)
                file.write(router_declare)
                print(router_declare)
        file.write('# end\n\n')
