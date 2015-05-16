from rainmaker.main import Application

def test_simple_workflow():
    print(Application.user_dir)
    Application.autorun()
