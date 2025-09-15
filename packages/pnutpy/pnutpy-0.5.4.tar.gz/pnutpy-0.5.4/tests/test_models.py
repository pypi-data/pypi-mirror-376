import time
import unittest

from tests.config import PnutpyTestCase

test_post_id = 1


class PnutpyModelTests(PnutpyTestCase):
    """Unit tests"""

    def test_post(self):
        text = u'Testing posts indvidually'
        post, meta = self.api.create_post(data={'text': text})
        post.bookmark()
        post.unbookmark()
        post.delete()
        post, meta = self.api.get_post(1309208)
        post.repost()
        post.unrepost()

    def test_user(self):
        new_display_name = u'tester %s' % (time.time())
        user, meta = self.api.get_user('me')

        user.name = new_display_name
        user.update_user()
        self.assertEqual(user.name, new_display_name)

        user, meta = self.api.get_user(9)
        user.follow_user()
        user.unfollow_user()

        user.mute_user()
        user.unmute_user()

        user.block_user()
        user.unblock_user()

    def test_channel(self):
        # normal public channel
        user_id = 9
        channel, meta = self.api.get_channel(85)
        self.assertEqual(user_id, channel.user.id)
        # channel where the owner user account has been deleted
        user_id = 213
        channel, meta = self.api.get_channel(955)
        self.assertEqual(user_id, channel.user_id)

if __name__ == '__main__':
    unittest.main()
