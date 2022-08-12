"""Message and Like model tests."""

# run these tests like:
#
# python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows, Like
#from sqlalchemy.exc import IntegrityError

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

from app import app

db.create_all()


class MessageModelTestCase(TestCase):
    def setUp(self):
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)

        db.session.commit()

        self.u1_id = u1.id
        self.u2_id = u2.id

        m1 = Message(text="test message 1",user_id=self.u1_id)
        m2 = Message(text="test message 2",user_id=self.u2_id)

        db.session.add(m1,m2)
        db.session.commit()

        self.m1_id = m1.id
        self.m2_id = m2.id

        self.client = app.test_client()

    def tearDown(self):
        db.session.rollback()

    def test_message_model(self):
        """Test that a message is associated with the correct user."""
        m1 = Message.query.get(self.m1_id)

        self.assertEqual(m1.text, "test message 1")
        self.assertEqual(m1.user_id, self.u1_id)

    def test_messages_on_user(self):
        """Test relationship of user to message."""

        m1 = Message.query.get(self.m1_id)
        u1 = User.query.get(self.u1_id)

        self.assertIn(m1, u1.messages)


###################

class LikeModelTestCase(TestCase):
    def setUp(self):
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)

        db.session.commit()

        self.u1_id = u1.id
        self.u2_id = u2.id

        m1 = Message(text="test message 1",user_id=self.u1_id)
        m2 = Message(text="test message 2",user_id=self.u2_id)

        db.session.add(m1)
        db.session.add(m2)
        db.session.commit()

        self.m1_id = m1.id
        self.m2_id = m2.id

        liked_message1 = Like(user_id=self.u1_id, message_id=self.m2_id)

        db.session.add(liked_message1)
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        db.session.rollback()

    def test_liked_message_model(self):
        """Test user has a liked message and message matches correct message ID."""

        liked_message1 = Like.query.filter_by(user_id=self.u1_id).one()

        self.assertEqual(liked_message1.message_id, self.m2_id)
        self.assertNotEqual(liked_message1.message_id, self.m1_id)

    def test_user_likes_on_message(self):
        """Test a message is accessible through User.liked_messages"""

        m2 = Message.query.get(self.m2_id)

        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)

        self.assertIn(m2, u1.liked_messages)
        self.assertNotIn(m2, u2.liked_messages)

    def test_is_liked_success(self):
        """Test is_liked User method for success when a message is in a user's liked_messages"""

        u1 = User.query.get(self.u1_id)
        m2 = Message.query.get(self.m2_id)

        result = u1.is_liked(m2)

        self.assertTrue(result)

    def test_is_liked_failure(self):
        """Test is_liked User method for failure when a message is not in a user's liked_messages"""


        u2 = User.query.get(self.u2_id)
        m2 = Message.query.get(self.m2_id)

        result = u2.is_liked(m2)

        self.assertFalse(result)
