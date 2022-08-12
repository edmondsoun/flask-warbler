"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py

import os
from unittest import TestCase

from models import db, Message, User, Like, Follows

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

from app import app, CURR_USER_KEY

app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

db.create_all()

app.config['WTF_CSRF_ENABLED'] = False


class UserBaseViewTestCase(TestCase):
    def setUp(self):
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)
        db.session.flush()

        #use ORM 
        m1 = Message(text="m1-text", user_id=u1.id)
        db.session.add_all([m1])
        db.session.commit()
        
        #use ORM (also tests db relationship)
        lm1 = Like(user_id = u2.id, message_id=m1.id )
        db.session.add_all([lm1])
        db.session.commit()

        self.u1_id = u1.id
        self.u2_id = u2.id
        self.m1_id = m1.id

        self.client = app.test_client()


class UserProfileViewTestCase(UserBaseViewTestCase):
    def test_list_users_logged_in(self):
        """ Test user directory view for logged in user. """
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get("/users")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("u1", html)
            self.assertIn("u2", html)
            
    def test_list_users_logged_out(self):
        """ Test user directory view for logged out user.  """
        with self.client as c:
            
            resp = c.get("/users", follow_redirects = True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)
    
    def test_user_own_profile_view(self):
        """ Test user can view own profile with appropriate UI. """
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get(f"/users/{self.u1_id}")
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Edit Profile", html)
            self.assertNotIn("<!--FOR TESTING: NOT YOUR PROFILE-->", html)
 
    def test_other_user_profile_view(self):
        """ Test user can view other profile with appropriate UI. """
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get(f"/users/{self.u2_id}")
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("<!--FOR TESTING: NOT YOUR PROFILE-->", html)
            self.assertNotIn("Edit Profile", html)

    def test_logged_out_profile_view_(self):
        """ Test user can view other profile with appropriate UI. """
        with self.client as c:

            resp = c.get(f"/users/{self.u2_id}", follow_redirects = True)
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)
            
    def test_logged_in_edit_own_user_profile(self):
        """ Test user edit own profile with correct credentials. """
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post('/users/profile', data={"username": "u1",
                                "email": "u1@email.com",
                                "bio": "NEW TEST BIO",
                                "location": "NEW TEST LOCATION",
                                "password": "password"
                                }, follow_redirects=True)
            
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("NEW TEST LOCATION", html)
            self.assertIn("NEW TEST BIO", html)

    def test_logged_in_edit_own_user_profile_bad_password(self):
        """ Test user cannot edit own profile with bad password. """
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post('/users/profile', data={"username": "u1",
                                "email": "u1@email.com",
                                "bio": "NEW TEST BIO",
                                "location": "NEW TEST LOCATION",
                                "password": "BAD_PASSWORD"
                                }, follow_redirects=True)
            
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Incorrect password!", html)
    
    def test_logged_out_edit_user_profile(self):
        """ Test user edit profile when logged out. """
        with self.client as c:

            resp = c.post('/users/profile', data={"username": "u1",
                                "email": "u1@email.com",
                                "bio": "NEW TEST BIO",
                                "location": "NEW TEST LOCATION",
                                "password": "password"
                                }, follow_redirects=True)
            
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)
            
            

    def test_logged_in_delete_user_profile(self):
        """ Test user can delete their profile while logged in."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id
                
            resp = c.post('/users/delete', follow_redirects=True)
            html = resp.get_data(as_text=True)

            #test route for 404 
            #instead of querying database
            all_user_ids = db.session.query(User.id).all()
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("User deleted!", html)
            self.assertNotIn((self.u1_id), all_user_ids)
            
    def test_logged_out_delete_user_profile(self):
        """ Test user cannot delete their profile while logged out."""
        with self.client as c:

            resp = c.post('/users/delete', follow_redirects=True)
            html = resp.get_data(as_text=True)
        
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)


class UserFollowViewTestCase(UserBaseViewTestCase):
    def test_logged_in_follow_functionality(self):
        """ Test adding a follow when logged in. """
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id
                
            resp = c.post(f'/users/follow/{self.u2_id}', follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("u2",html)

    def test_logged_out_follow_functionality(self):
        """ Test adding a follow when logged out. """
        with self.client as c:

            resp = c.post(f'/users/follow/{self.u2_id}', follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.",html)
        
    def test_logged_in_unfollow_functionality(self):
        """ Test removing a follow when logged in. """
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id
            
            #use ORM
            new_follow = Follows(user_being_followed_id=self.u2_id, user_following_id=self.u1_id)
            db.session.add(new_follow)
            db.session.commit()
            
            resp = c.post(f'/users/stop-following/{self.u2_id}', follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("u2", html)

    def test_logged_out_unfollow_functionality(self):
        """ Test removing a follow when logged out. """
        with self.client as c:
                
            new_follow = Follows(user_being_followed_id=self.u2_id, user_following_id=self.u1_id)
            db.session.add(new_follow)
            db.session.commit()
            
            resp = c.post(f'/users/stop-following/{self.u2_id}', follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)

    
    def test_logged_in_show_follower_page(self):
        """ Test viewing followers page on another profile when logged in. """
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id
            
            resp = c.get(f'/users/{self.u2_id}/followers')
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("<!--FOR TESTING FOLLOWERS PAGE-->", html)
    
    def test_logged_out_show_follower_page(self):
        """ Test viewing followers page on another profile when logged out. """
        with self.client as c:

            resp = c.get(f'/users/{self.u2_id}/followers', follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)
    
    def test_logged_in_show_following_page(self):
        """ Test viewing following page on another profile when logged in. """
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id
            
            resp = c.get(f'/users/{self.u2_id}/following')
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("<!--FOR TESTING FOLLOWING PAGE-->", html)
    
    def test_logged_out_show_following_page(self):
        """ Test viewing following page on another profile when logged out. """
        with self.client as c:

            resp = c.get(f'/users/{self.u2_id}/following', follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)
            

class UserLikeViewTestCase(UserBaseViewTestCase):
    def test_like_page_logged_in(self):
        """Test like page on user profile"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id
                
            resp = c.get(f'/users/{self.u1_id}/likes')
            html = resp.get_data(as_text = True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("<!--TESTING LIKED MESSAGES-->", html)

    def test_like_page_logged_out(self):
        """Test like page on user profile"""
        with self.client as c:

            resp = c.get(f'/users/{self.u1_id}/likes', follow_redirects=True)
            html = resp.get_data(as_text = True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)