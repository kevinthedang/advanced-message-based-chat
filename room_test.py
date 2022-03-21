from datetime import datetime
from unittest import TestCase
import unittest
from constants import *
from room import ChatRoom, MessageProperties, RoomList
from users import *

PRIVATE_ROOM_NAME = 'kevin'
PUBLIC_ROOM_NAME = 'general'
SENDER_NAME = 'testing'
DEFAULT_PRIVATE_TEST_MESS = 'Test Private Queue'
DEFAULT_PUBLIC_TEST_MESS = 'Test Public Queue'
USER_ALIAS = 'testing'
TEST_OWNER_ALIAS = 'kevin'

class RoomTest(TestCase):
    """ Docstring
    """
    def setUp(self) -> None:
        ''' This setup method will just declare the public and private room to test on.
        '''
        self.__private_chat_channel = ChatRoom(room_name = PRIVATE_ROOM_NAME, member_list = UserList(), owner_alias = TEST_OWNER_ALIAS, room_type = ROOM_TYPE_PRIVATE)
        self.__private_message_properties_send = MessageProperties(room_name = PRIVATE_ROOM_NAME, to_user = SENDER_NAME, from_user = TEST_OWNER_ALIAS, mess_type = MESSAGE_TYPE_SEND)
        self.__private_message_properties_receive = MessageProperties(room_name = PRIVATE_ROOM_NAME, to_user = SENDER_NAME, from_user = TEST_OWNER_ALIAS, mess_type = MESSAGE_TYPE_RECEIVED)
        self.__public_chat_channel = ChatRoom(room_name = PUBLIC_ROOM_NAME, member_list = UserList(), owner_alias = TEST_OWNER_ALIAS, room_type = ROOM_TYPE_PUBLIC)
        self.__public_message_properties_send = MessageProperties(room_name = PUBLIC_ROOM_NAME, to_user = SENDER_NAME, from_user = TEST_OWNER_ALIAS, mess_type = MESSAGE_TYPE_SEND)
        self.__public_message_properties_receive = MessageProperties(room_name = PUBLIC_ROOM_NAME, to_user = SENDER_NAME, from_user = TEST_OWNER_ALIAS, mess_type = MESSAGE_TYPE_RECEIVED)

    def test_send(self, private_message: str = DEFAULT_PRIVATE_TEST_MESS, public_message: str = DEFAULT_PUBLIC_TEST_MESS) -> bool:
        """ Testing the send message functionality
            NOTE: These assertions should come back as true from the method calling
                    A true means that the message was sent to Rabbit
        """
        self.assertTrue(self.__private_chat_channel.send_message(private_message, self.__private_message_properties_send))
        self.assertTrue(self.__public_chat_channel.send_message(public_message, self.__public_message_properties_send))

    def test_get(self) -> list:
        """ Testing the get messages functionality
            NOTE: Should make sure that the sequence of the messages are correct
        """
        self.assertEqual(self.__public_chat_channel.find_message(DEFAULT_PUBLIC_TEST_MESS), DEFAULT_PUBLIC_TEST_MESS)
        self.assertEqual(self.__private_chat_channel.find_message(DEFAULT_PRIVATE_TEST_MESS), DEFAULT_PRIVATE_TEST_MESS)

    def test_full(self):
        """ Doing both and make sure that what we sent is in what we get back
        """
        self.assertTrue(self.__private_chat_channel.send_message(DEFAULT_PRIVATE_TEST_MESS, self.__private_message_properties_send))
        self.assertTrue(self.__public_chat_channel.send_message(DEFAULT_PUBLIC_TEST_MESS, self.__public_message_properties_send))
        num_body_list_private, num_message_private = self.__private_chat_channel.get_messages(user_alias = USER_ALIAS, return_objects = False)
        num_body_list_public, num_message_public = self.__public_chat_channel.get_messages(user_alias = USER_ALIAS, return_objects = False)
        self.assertEqual(num_message_private, 1)
        self.assertEqual(num_message_public, 1)
        self.assertEqual(num_body_list_private, DEFAULT_PRIVATE_TEST_MESS)
        self.assertEqual(num_body_list_public, DEFAULT_PUBLIC_TEST_MESS)

if __name__ == "__main__":
    unittest.main()