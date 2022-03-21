import queue
from constants import *
from datetime import date, datetime
from pymongo import MongoClient
from constants import *
        
class ChatUser():
    """ class for users of the chat system. Users must be registered 
    """
    def __init__(self, alias: str, create_time: datetime = datetime.now(), modify_time: datetime = datetime.now()) -> None:
        self.__alias = alias
        self.__create_time = create_time
        self.__modify_time = modify_time

    @property
    def alias(self):
        return self.__alias
    
    @property
    def dirty(self):
        return self.__dirty

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
        self.__setup_list_name = list_name
        self.__user_list = list()
        self.__mongo_client = MongoClient('mongodb://34.94.157.136:27017/')
        self.__mongo_db = self.__mongo_client.detest
        self.__mongo_collection = self.__mongo_db.users    
        if self.__restore() is True:
            #raise Exception('No name and no document to restore')
            print('Document is found')
        else:
            self.__list_name = list_name
            self.__create_time = datetime.now()
            self.__modify_time = datetime.now()

    @property
    def user_list(self):
        ''' This property is just to the the list of users
        '''
        return self.__user_list
    
    def register(self, new_alias: str) -> ChatUser:
        """ This method will just return a new ChatUser that will need to be added to the UserList
            This only creates the user, it does not add them to the list of users yet.
        """
        return ChatUser(alias = new_alias)

    def get(self, target_alias: str) -> ChatUser:
        ''' This method will return the user from the user_list
            TODO: Learn how to traverse through the list.
        '''
        for user in self.__user_list:
            if target_alias == user.__alias:
                return user

    def get_all_users(self) -> list:
        ''' This method will just return the list of names as a result.
            NOTE: This list should not be empty as there should at least be an owner to the list
            TODO: Return the user list
        '''
        return self.__user_list

    def append(self, new_user: ChatUser) -> None:
        ''' This method will add the user to the to the list of users
            NOTE: May want to make sure that the new_user is valid
        '''
        self.__user_list.append(new_user)
        self.__persist()

    def __restore(self) -> bool:
        """ First get the document for the queue itself, then get all documents that are not the queue metadata
        """
        queue_metadata = self.__mongo_collection.find_one( { 'name': self.__setup_list_name })
        if queue_metadata is None:
            return False
        self.__list_name = queue_metadata["name"]
        self.__create_time = queue_metadata["create_time"]
        self.__modify_time = queue_metadata["modify_time"]
        self.__user_list = queue_metadata['user_names']

        return True

    def __persist(self):
        """ First save a document that describes the user list (name of list, create and modify times)
            Second, for each user in the list create and save a document for that user
        """
        if self.__mongo_collection.find_one({ 'name': self.__list_name }) is None:
            self.__mongo_collection.insert_one({ "name": self.__list_name, "create_time": self.__create_time, "modify_time": self.__modify_time, 'user_names' : self.__user_list})