from datetime import datetime
from unittest import TestCase
import unittest
from constants import *
from room import ChatRoom, MessageProperties, RoomList
from users import *

PRIVATE_ROOM_NAME = 'kevin'
PUBLIC_ROOM_NAME = 'general'
SENDER_NAME = 'testing'
DEFAULT_PRIVATE_TEST_MESS = 'DE: Test Private Queue at '
DEFAULT_PUBLIC_TEST_MESS = 'DE: Test Public Queue at '
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
        """
        self.assertTrue(self.__private_chat_channel.send_message(private_message, self.__private_message_properties_send))
        self.assertTrue(self.__public_chat_channel.send_message(public_message, self.__public_message_properties_send))

    def test_get(self) -> list:
        """ Testing the get messages functionality
        """
        pass

    def test_full(self):
        """ Doing both and make sure that what we sent is in what we get back
        """
        pass

if __name__ == "__main__":
    unittest.main()