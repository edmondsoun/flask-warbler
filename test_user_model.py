"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows
from sqlalchemy.exc import IntegrityError

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    def setUp(self):
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)

        db.session.commit()
        self.u1_id = u1.id
        self.u2_id = u2.id

        self.client = app.test_client()

    def tearDown(self):
        db.session.rollback()

    def test_user_model(self):
        u1 = User.query.get(self.u1_id)

        # User should have no messages & no followers
        self.assertEqual(len(u1.messages), 0)
        self.assertEqual(len(u1.followers), 0)

    def test_repr_method(self):
        """ Test whether the repr method on User model works as expected."""
        u1 = User.query.get(self.u1_id)

        repr = u1.__repr__()

        self.assertEqual(repr, f"<User #{u1.id}: u1, u1@email.com>")


    def test_is_following_method_true(self):
        """ Test whether is_following method on User model returns true
        when user1 follows user2"""

        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)

    #u1.followers.append(u2)
        new_follow = Follows(user_following_id = u1.id,
            user_being_followed_id = u2.id)
        db.session.add(new_follow)
        db.session.commit()

        result = u1.is_following(u2)

        self.assertTrue(result)

    def test_is_following_false(self):
        """ Test whether is_following method on User model returns false
        when user1 is not following user2"""

        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)

        result = u1.is_following(u2)

        self.assertFalse(result)

#test_is_followed_by_user (in case true/false changed)
    def test_is_followed_by_true(self):
        """ Test whether is_followed_by method returns true when user2 is
        following user1"""
        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)

        new_follow = Follows(user_following_id = u2.id,
            user_being_followed_id = u1.id)
        db.session.add(new_follow)
        db.session.commit()

        result = u1.is_followed_by(u2)

        self.assertTrue(result)


    def test_is_followed_by_false(self):
        """ Test whether is_followed_by method returns false when user2 is not
        following user1"""

        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)

        result = u1.is_followed_by(u2)

        self.assertFalse(result)

    def test_user_signup_success(self):
        """ Upon User.signup, is a new user created successfully given valid
        credentials"""
        new_user = User.signup("u3", "u3@email.com", "password", None)
        db.session.commit()

        query = User.query.get(new_user.id)
        self.assertEqual(query.username, "u3")

    def test_user_signup_fail(self):
        """ User.signup failure on non-unique usernames or missing non-nullable
        fields."""

        #failure on non-unique username
        new_user = User.signup("u1", "u3@email.com", "password", None)
        with self.assertRaises(IntegrityError):
            db.session.commit()

        #failure on non-nullable field
        with self.assertRaises(ValueError):
            User.signup("u4", "u4@email.com", None)


    def test_user_authenticate_success(self):
        """ Given a valid username and password, does User.authenticate return
        the user instance"""
        u1 = User.query.get(self.u1_id)
        test = User.authenticate(u1.username, "password")

        self.assertEqual(test, u1)

#could be one grouping
    def test_user_authenticate_fail_on_username(self):
        """ Given an incorrect username, User.authenticate returns false. """

        test = User.authenticate("bad_username", "password")

        self.assertFalse(test)

    def test_user_authenticate_fail_on_pw(self):
        """Given an incorrect password, User.authenticate returns false. """
        u1 = User.query.get(self.u1_id)
        test = User.authenticate(u1.username, "bad_pw")

        self.assertFalse(test)

