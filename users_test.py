import unittest
from unittest import TestCase
from constants import *
from users import *

TESTING_USER_NAMES = ['ethan', 'kevin', 'evan', 'alex', 'jacob']

class UserTest(TestCase):
    """ Docstring
    """
    def setUp(self) -> None:
#        super().__init__(methodName)
        self.__cur_users = UserList('test_users_kevin')
        self.__testing_users_list = list()

    @property
    def users(self):
        return self.__cur_users

    def test_adding(self):
        ''' This test should do the following:
                - register a new user to the DB
                - add the user to the list
                - the UserList will persist and restore every time when adding a new user
        '''
        for new_user in TESTING_USER_NAMES:
            self.__cur_users = UserList('test_users_kevin')
            new_user = self.__cur_users.register(new_alias = new_user)
            self.__testing_users_list.append(new_user)
            self.__cur_users.append(new_user)
            self.assertIn(new_user, self.users.user_list)

    def test_getting(self):
        ''' This test should make sure that the usernames in the user list above are found and persisted
                from the previous test
        '''
        self.__cur_users = UserList('test_users_kevin')
        for registered_user in self.__testing_users_list:
            self.assertIn(registered_user, self.__cur_users.user_list)
    
if __name__ == "__main__":
    unittest.main()