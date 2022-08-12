"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, Message, User, Like

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app

from app import app, CURR_USER_KEY

app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageBaseViewTestCase(TestCase):
    def setUp(self):
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)
        db.session.flush()

        m1 = Message(text="m1-text", user_id=u1.id)
        db.session.add_all([m1])
        db.session.commit()

        self.u1_id = u1.id
        self.u2_id = u2.id
        self.m1_id = m1.id

        self.client = app.test_client()


class MessageAddViewTestCase(MessageBaseViewTestCase):
    def test_add_message_logged_in(self):
        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            # Now, that session setting is saved, so we can have
            # the rest of ours test
            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects = True)
            html = resp.get_data(as_text=True)

            message = Message.query.filter_by(text="Hello").one()

            self.assertEqual(resp.status_code, 200)
            self.assertIn(f"This is a test message {message.id}", html)

    #test when not logged in
    def test_add_message_when_logged_out(self):
        """Test that a message cannot be added if logged out"""
        with self.client as c:
            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects = True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)

class MessageShowViewTestCase(MessageBaseViewTestCase):
    def test_show_message_logged_in(self):
        """ Test that a message is displayed while logged in."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get(f"/messages/{self.m1_id}")
            html = resp.get_data(as_text = True)
            bad_resp = c.get(f"/messages/bad")

            self.assertEqual(resp.status_code, 200)
            self.assertEqual(bad_resp.status_code, 404)
            self.assertIn("m1-text", html)

    def test_show_message_logged_out(self):
        """ Test that a message cannot be displayed when logged out. """
        with self.client as c:
            resp = c.get(f"/messages/{self.m1_id}", follow_redirects=True)
            html = resp.get_data(as_text = True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)

class MessageDeleteViewTestCase(MessageBaseViewTestCase):
    def test_delete_message_logged_in(self):
        """Test that a message is deleted when logged in. """
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post(f"/messages/{self.m1_id}/delete", follow_redirects=True)
            html = resp.get_data(as_text = True)

            self.assertEqual(resp.status_code, 200)
            self.assertNotIn(f"This is a test message {self.m1_id}", html)

    def test_delete_if_wrong_user(self):
        """ Test that a message cannot be deleted off a different users profile """
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u2_id

            resp = c.post(f"/messages/{self.m1_id}/delete", follow_redirects=True)
            html = resp.get_data(as_text = True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("You can&#39;t delete someone else&#39;s message!", html)

    def test_delete_message_logged_out(self):
        """ Test that a message cannot be deleted when logged out. """
        with self.client as c:

            resp = c.post(f"/messages/{self.m1_id}/delete", follow_redirects=True)
            html = resp.get_data(as_text = True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)

class MessageLikingViewTestCase(MessageBaseViewTestCase):
    def test_liking_logged_in(self):
        """ Test that a message is successfully liked while logged in."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u2_id

            resp = c.post(f"/messages/{self.m1_id}/like", follow_redirects = True)
            html = resp.get_data(as_text = True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Warble liked!", html)

    def test_liking_own_message(self):
        """Test that a user cannot like their own message."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post(f"/messages/{self.m1_id}/like", follow_redirects = True)
            html = resp.get_data(as_text = True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("You can&#39;t like your own messages!", html)

    def test_liking_logged_out(self):
        """Test that a message cannot be liked when logged out."""
        with self.client as c:
            resp = c.post(f"/messages/{self.m1_id}/like", follow_redirects = True)
            html = resp.get_data(as_text = True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)

    def test_unlike_logged_in(self):
        """ Test that a message is successfully unliked when logged in."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u2_id

            #like a message to be unliked
            liked = Like(user_id = self.u2_id, message_id=self.m1_id)
            db.session.add(liked)
            db.session.commit()

            resp = c.post(f"/messages/{self.m1_id}/unlike", follow_redirects = True)
            html = resp.get_data(as_text = True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Warble removed from likes.", html)

    def test_unlike_logged_out(self):
        """Test that a message cannot be unliked while logged out."""
        with self.client as c:

            #like a message to be unliked
            liked = Like(user_id = self.u2_id, message_id=self.m1_id)
            db.session.add(liked)
            db.session.commit()

            resp = c.post(f"/messages/{self.m1_id}/unlike", follow_redirects = True)
            html = resp.get_data(as_text = True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)

#install Coverage