from datetime import datetime
from unittest import TestCase
import unittest
from constants import *
from room import ChatRoom, MessageProperties, RoomList
from users import *

TEST_ROOM_NAME = 'test_room'
DEFAULT_TEST_MESSAGE = 'Kevin has sent this message.'
TEST_OWNER_ALIAS = 'kevin'

class RoomTest(TestCase):
    """ This test environment will test the functionality of the room file
        TODO: make user testing file first
    """
    def setUp(self) -> None:
        ''' This setup method will just declare the public and private room to test on.
            TODO: set up the room list class here
        '''

    def test_send(self, private_message: str = DEFAULT_PRIVATE_TEST_MESS, public_message: str = DEFAULT_PUBLIC_TEST_MESS) -> bool:
        """ Testing the send message functionality
            NOTE: These assertions should come back as true from the method calling
                    A true means that the message was sent to Rabbit
            TODO: just send a message to the deque and make sure it gets persisted
        """

    def test_get(self) -> list:
        """ Testing the get messages functionality
            NOTE: Should make sure that the sequence of the messages are correct
            TODO: we want to reload and restore the messages in the test chat and get the message
        """

    def test_full(self):
        """ Doing both and make sure that what we sent is in what we get back
            TODO: we want to test the send and receieve
        """

if __name__ == "__main__":
    unittest.main()