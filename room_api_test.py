import json
import requests
import unittest
from users import *
from constants import *

NUM_MESSAGES = 4

class ChatTest(unittest.TestCase):
    ''' This Test Environment will test the functionality of the API and it's requests
    '''

    def test_startup(self):
        ''' This test will test the startup responce when running uvicorn.
            NOTE: status code 200 tells us a successful retrieval from a get call
        '''
        startup = requests.get(STARTUP_URL)
        self.assertEqual(startup.status_code, 200)
        json_load = json.loads(startup.text)
        json_message = json_load['message']['from']
        self.assertEqual(json_message, STARTUP_TEST_DICTIONARY['from'])
        json_message = json_load['message']['to']
        self.assertEqual(json_message, STARTUP_TEST_DICTIONARY['to'])

    def test_send(self):
        """ Testing the send api
        """
        requests.post(url = CREATE_ROOM_URL, params = { 'room_name': DEFAULT_TEST_ROOM,
                                                        'owner_alias': TEST_OWNER_ALIAS,
                                                    })
        send_message = requests.post(url = SEND_URL, params = { 'room_name': DEFAULT_TEST_ROOM,
                                                                'message': DEFAULT_TEST_API_MESSAGE,
                                                                'from_alias': TEST_OWNER_ALIAS,
                                                                'to_alias': TEST_OWNER_ALIAS
                                                            })
        self.assertEqual(send_message.status_code, 201)

    def test_get(self):
        """ Testing the get messages api
        """

    def test_register(self):
        """ Testing the user and room registration api's
            NOTE: This removal of all users only happens for the instance of this test environment
        """
        register_client = requests.post(url = REGISTER_CLIENT_URL, params = { 'client_alias': TEST_OWNER_ALIAS })
        self.assertEqual(register_client.status_code, 201)

    def test_get_users(self):
        """ Testing the get users api
        """
        list_of_users = requests.get(url = GET_USERS_URL)
        self.assertEqual(list_of_users.status_code, 200)
        json_load = json.loads(list_of_users.text)
        json_message = json_load['message']['list_of_users']
        self.assertIn(TEST_OWNER_ALIAS, json_message)


            

        

