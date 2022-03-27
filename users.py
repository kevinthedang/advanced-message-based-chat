import queue
import logging
from constants import *
from datetime import date, datetime
from pymongo import MongoClient
from constants import *

logging.basicConfig(filename='user.log', level=logging.DEBUG, format = LOG_FORMAT)
        
class ChatUser():
    """ class for users of the chat system. Users must be registered 
    """
    def __init__(self, alias: str, user_id = None, create_time: datetime = datetime.now(), modify_time: datetime = datetime.now()) -> None:
        self.__alias = alias
        self.__user_id = user_id
        self.__create_time = create_time
        self.__modify_time = modify_time
        if self.__user_id is not None:
            self.__dirty = False
        else:
            self.__dirty = True

    @property
    def alias(self):
        return self.__alias

    @property
    def user_id(self):
        return self.__user_id
    
    @property
    def dirty(self):
        return self.__dirty

    @dirty.setter
    def dirty(self, new_value: bool):
        self.__dirty = new_value

    def to_dict(self):
        return {
                'alias': self.__alias,
                'create_time': self.__create_time,
                'modify_time': self.__modify_time
        }
        
class UserList():
    """ List of users, inheriting list class
    """
    def __init__(self, list_name: str = DEFAULT_USER_LIST_NAME) -> None:
        self.__list_name = list_name
        self.__user_list = list()
        self.__mongo_client = MongoClient('mongodb://34.94.157.136:27017/')
        self.__mongo_db = self.__mongo_client.detest
        self.__mongo_collection = self.__mongo_db.users    
        if self.__restore() is True:
            print('UserList Document is found')
            self.__dirty = False
        else:
            self.__create_time = datetime.now()
            self.__modify_time = datetime.now()
            self.__dirty = True

    # This property is just to the the list of users
    @property
    def user_list(self):
        return self.__user_list

    # This property is to get the list of user_aliases
    @property
    def user_aliases(self):
        return self.get_all_users_aliases
    
    def register(self, new_alias: str) -> ChatUser:
        """ This method will just return a new ChatUser that will need to be added to the UserList
            This only creates the user, it does not add them to the list of users yet.
            NOTE: we check if the user already exists, if so, don't make another user with that alias
        """
        if self.get(new_alias) is not None:
            logging.debug(f'Registered new user with name {new_alias}.')
            return ChatUser(alias = new_alias)
        else:
            logging.debug(f'User {new_alias} already exists.')
            return None

    def get(self, target_alias: str) -> ChatUser:
        ''' This method will return the user from the user_list
            NOTE: this method will utilize the index to find the user
        '''
        for user_index in range(1, len(self.__user_list)):
            if target_alias == self.__user_list[user_index].alias:
                logging.debug(f'User {target_alias} was found in user list {self.__list_name}.')
                return self.__user_list[user_index]
        logging.debug(f'User {target_alias} was not found in user list {self.__list_name}.')
        return None

    def get_all_users_aliases(self) -> list:
        ''' This method will just return the list of names as a result.
            NOTE: This list should not be empty as there should at least be an owner to the list
        '''
        logging.debug(f'Attempting to get all user aliases in {self.__list_name}.')
        return [user.alias for user in self.__user_list]

    def append(self, new_user: ChatUser) -> None:
        ''' This method will add the user to the to the list of users
            NOTE: May want to make sure that the new_user is valid
            TODO: make sure the user does not already exist in the users (check the user_list_alias or user_list)
        '''
        if new_user in self.__user_aliases:
            logging.debug(f'Alias {new_user.alias} is an already existing user.')
            return None
        self.__user_list.append(new_user)
        logging.debug(f'Alias {new_user.alias} added to the list of users.')
        self.__persist()

    def __restore(self) -> bool:
        """ First get the document for the queue itself, then get all documents that are not the queue metadata
            NOTE: we should have a list of aliases of the for the members that belong in a certain group chat.
            NOTE: we may not need the user aliases since we just want to restore all of the users
            TODO: restore the list of users to the user_list (list of user classes) through mongodb collection of users
        """
        queue_metadata = self.__mongo_collection.find_one( { 'name': self.__list_name })
        if queue_metadata is None:
            return False
        self.__list_name = queue_metadata["list_name"]
        self.__create_time = queue_metadata["create_time"]
        self.__modify_time = queue_metadata["modify_time"]
        self.__user_aliases = queue_metadata['user_aliases']
        # below we want to restore the users to the userList using the user aliases and checking the mongo collection

        return True

    def __persist(self):
        """ First save a document that describes the user list (name of list, create and modify times)
            Second, for each user in the list create and save a document for that user
            TODO: Persist every user in the userlist if they are dirty
        """
        logging.info(f'Attemping to persist user list {self.__list_name}.')
        if self.__mongo_collection.find_one({ 'name': self.__list_name }) is None:
            self.__mongo_collection.insert_one({ "name": self.__list_name,
                                                "create_time": self.__create_time,
                                                "modify_time": self.__modify_time,
                                                'user_names' : self.get_all_users_aliases})
            logging.debug(f'New user list {self.__list_name} added to the collection.')
        else:
            if self.__dirty == True:
                self.__mongo_collection.replace_one({ "name": self.__list_name,
                                                    "create_time": self.__create_time, 
                                                    "modify_time": self.__modify_time, 
                                                    'user_names' : self.get_all_users_aliases},
                                                    upsert = True)
                logging.debug(f'User list {self.__list_name} has been updated in the collection.')
        self.__dirty = False
        for current_user in self.__user_list:
            if current_user.dirty == True:
                if current_user.user_id is None or self.__mongo_collection.find_one({ 'alias' : current_user.alias }) is None:
                    serialized = current_user.to_dict()
                    self.__mongo_collection.insert_one(serialized)
                    logging.debug(f'User {current_user.alias} has been added to the collection.')
                    current_user.dirty = False
