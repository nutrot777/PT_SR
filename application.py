from app import app

# Elastic Beanstalk expects the application object to be called 'application'
application = app

if __name__ == "__main__":
    application.run()