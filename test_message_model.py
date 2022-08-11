# from unittest import TestCase

# from app import app, db
# from models import Message

# # Let's configure our app to use a different database for tests
# app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql:///warbler_test_message_model"

# # Make Flask errors be real errors, rather than HTML pages with error info
# app.config['TESTING'] = True

# # This is a bit of hack, but don't use Flask DebugToolbar
# app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']

# # Create our tables (we do this here, so we only create the tables
# # once for all tests --- in each test, we'll delete the data
# # and create fresh new clean test data

# db.create_all()

# class MessageModelTestCase(TestCase):