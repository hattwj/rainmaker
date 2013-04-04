import lib

def run(app):
    print app.root
    print app.home_dir
    lib.tasks.install(app)    
