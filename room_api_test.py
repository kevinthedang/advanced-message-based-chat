import json
import requests
import unittest
from users import *
from constants import *

MESSAGES = ["first"]
NUM_MESSAGES = 4

class ChatTest(unittest.TestCase):

    def test_send(self):
        """ Testing the send api
        """
        for loop_control in range(0, NUM_MESSAGES):
            response = requests.post(f'http://localhost:8081/send?room_name=eshner&message=testmess #{loop_control}&from_alias=test&to_alias=eshner&group_queue=false')
            self.assertEqual(response.status_code, 201)

    def test_get(self):
        """ Testing the get messages api
        """
        response = requests.get(f'http://localhost:8081/messages?alias=eshner&room_name=eshner&group_queue=false&messages_to_get=2') 
        self.assertEqual(response.status_code, 200)
        return response.text

    def test_register(self):
        """ Testing the user and room registration apis
        """
        try:
            users = UserList()
        except:
            users = UserList('chat_users')
        response = requests.post(f'http://localhost:8000/register$new_user=test_user1')
        try: 
            self.assertEqual(response.status_code, 201)
        except: 
            logging.warning(f'test for register failed. Response status: {response.status_code}. Total response: {response}')
        self.assertIsNotNone(users.get_by_alias('test_user1'))

    def test_get_users(self):
        """ Testing the get users api
        """
        try:
            users = UserList()
        except:
            users = UserList('chat_users')
        response = requests.post(f'http://localhost:8000/users')
        self.assertEqual(response.status_code, 201) 
        self.assertEqual(users.get_all_users(), response.text)


            

        

