import pika
import json
import pika.exceptions
import logging
from users import *
from constants import *
from datetime import date, datetime
from pymongo import MongoClient, ReturnDocument
from collections import deque
from constants import *

MONGO_DB = 'detest'
#MONGO_DB = 'chatroom'
logging.basicConfig(filename='chatroom.log', level=logging.DEBUG, filemode='w')

class MessageProperties():
    """ Class for holding the properties of a message: type, sent_to, sent_from, rec_time, send_time
        NOTE: The sequence number is defaulted to -1
    """
    def __init__(self, room_name: str, to_user: str, from_user: str, mess_type: int, sequence_num: int = -1, sent_time: datetime = datetime.now(), rec_time: datetime = datetime.now()) -> None:
        self.__mess_type = mess_type
        self.__room_name = room_name
        self.__to_user = to_user
        self.__from_user = from_user
        self.__sent_time = sent_time
        self.__rec_time = rec_time     
        self.__sequence_num = sequence_num

    def to_dict(self):
        return {'room_name': self.__room_name, 
            'mess_type': self.__mess_type,
            'to_user': self.__to_user, 
            'from_user': self.__from_user,
            'sent_time': self.__sent_time,
            'rec_time': self.__rec_time, 
            'sequence_num': self.__sequence_num,
        } 

    def __str__(self):
        return str(self.to_dict())

class ChatMessage():
    """ Class for holding individual messages in a chat thread/queue. Each message a message, rabbitmq properties, sequence number, timestamp and type
    """
    def __init__(self, message: str, mess_id = None, mess_props: MessageProperties = None) -> None:
        self.__message = message
        self.__mess_props = mess_props
        self.__rmq_props = None
        self.__dirty = True
        self.__mess_id = mess_id

    def to_dict(self):
        mess_props_dict = self.mess_props.to_dict()
        return {'message': self.message, 'mess_props': mess_props_dict}

    def __str__(self):
        return f'Chat Message: {self.message} - message props: {self.mess_props}'

class ChatRoom(deque):
    """ Docstring
        We reuse the constructor for creating new or grabbing an existing instance. If owner_alias is empty and user_alias is not, 
            this is assuming an existing instance. The opposite (owner_alias set and user_alias empty) means we're creating new
            members is always optional, and room_type is only relevant if we're creating new.
    """
    def __init__(self, room_name: str, member_list: list = None, owner_alias: str = "", room_type: int = ROOM_TYPE_PRIVATE, create_new: bool = False) -> None:
        super(ChatRoom, self).__init__()
        self.__room_name = room_name
        self.__user_list = UserList()
        # Set up mongo - client, db, collection, sequence_collection
        self.__mongo_client = MongoClient(host='34.94.157.136', port=27017, username='class', password='CPSC313', authSource='detest', authMechanism='SCRAM-SHA-256')
        self.__mongo_db = self.__mongo_client.detest
        self.__mongo_collection = self.__mongo_db.get_collection(self.__room_name) 
        self.__mongo_seq_collection = self.__mongo_db.get_collection("sequence")
        if self.__mongo_collection is None:
            self.__mongo_collection = self.__mongo_db.create_collection(self.__room_name)
        # Restore from mongo if possible, if not (or we're creating new) then setup properties

    # property to get the name of a room
    @property
    def room_name(self):
        return self.__room_name

    # property to get the list of users for a room
    @property
    def room_user_list(self):
        return self.__user_list

    def __get_next_sequence_num(self):
        """ This is the method that you need for managing the sequence. Note that there is a separate collection for just this one document
        """
        sequence_num = self.__mongo_seq_collection.find_one_and_update(
                                                        {'_id': 'userid'},
                                                        {'$inc': {'seq': 1}},
                                                        projection={'seq': True, '_id': False},
                                                        upsert=True,
                                                        return_document=ReturnDocument.AFTER)
        return sequence_num

    #Overriding the queue type put and get operations to add type hints for the ChatMessage type
    def put(self, message: ChatMessage = None) -> None:
        ''' This method will put the current message to the left side of the deque
            TODO: put the message on the left using appendLeft() method
        '''
        logging.info(f'Caliing the put() method with current message being {message} appending to the left of the deque.')

    # overriding parent and setting block to false so we don't wait for messages if there are none
    def get(self) -> ChatMessage:
        ''' This method will take a ChatMessage from the right side of the deque.
            NOTE: the method pop() to take a value from the right of the deque
        '''
        pass

    def find_message(self, message_text: str) -> ChatMessage:
        ''' Traverse through the deque of the Chatroom and find the ChatMessage 
                with the message_text input from the user.
            TODO: Understand how the deque works and how to traverse the deque.
            NOTE: To traverse through the deque, we can use list(self) as an iterable to find the message
            NOTE: an example would be (for current_message in list(self))
        '''
        pass

    def get_messages(self, user_alias: str, num_messages:int=GET_ALL_MESSAGES, return_objects: bool = True):
        ''' This method will get num_messages from the deque and get their text, objects and a total count of the messages
            NOTE: Refer to Dans code about message objects and message_texts
            NOTE: total # of messages seems to just be num messages, but if getting all then just return the length of the list
        '''
        # return message texts, full message objects, and total # of messages
        pass

    def send_message(self, message: str, from_alias: str, mess_props: MessageProperties) -> bool:
        pass

    def restore(self) -> bool:
        ''' This method will restore the metadata and the messages that a certain ChatRoom instance needs
            NOTE: a ChatRoom will contain it's own collection, if we are creating a new collection, we don't
                    need to restore
            NOTE: if the collection exists, then we do want to restore.
        '''
        pass

    def persist(self):
        ''' This method will maintain the data inside of a ChatRoom instance:  
                - The metadata
                - The messages in the room.
            NOTE: we want to iterate through the deque
        '''
        pass

class RoomList():
    """ This is the RoomList class instance that will handle a list of ChatRooms and obtaining them
        TODO: complete this class by writing its functions.
    """
    def __init__(self, name: str = DEFAULT_ROOM_LIST_NAME) -> None:
        """ Try to restore from mongo and establish variables for the room list
            TODO: RoomList takes a name, set the name
            TODO: inherit a list, or create an internal variable for a list of rooms
            TODO: restore the mongoDB collection
        """
        pass

    def create(self, room_name: str, owner_alias: str, member_list: list = None, room_type: int = ROOM_TYPE_PRIVATE) -> ChatRoom:
        ''' This method will create a new ChatRoom given that the room_name is not already taken for the collection.
            NOTE: This can just be a checker for the chatroom name existing in the list when restored or if it's in the collection
            NOTE: Maybe check with the collection as it is possible for all names to not be in the list and removed, due to the option for removal
        '''
        pass

    def add(self, new_room: ChatRoom):
        ''' This method will add a ChatRoom instance to the list of ChatRooms
            NOTE: This should not need to check as the create() should already check for the class.
        '''
        pass

    def remove(self, room_name: str):
        ''' This method will remove a ChatRoom instance from the list of ChatRooms
            NOTE: we want to make sure that the ChatRoom instance with the given room_name exists
        '''
        pass

    def find_room_in_metadata(self, room_name: str) -> dict:
        pass

    def get_rooms(self):
        ''' This method will return the rooms in the room list.
            NOTE: The room list can be empty
        '''
        pass

    def get(self, room_name: str) -> ChatRoom:
        ''' This method will return a ChatRoom instance, given the name of the room, room_name
            NOTE: It is possible for a ChatRoom instance to not be in the list of rooms.
        '''
        pass

    def __find_pos(self, room_name: str) -> int:
        ''' This method is most likely a helper method for getting the position of a ChatRoom instance is in a list
            NOTE: This maybe just for find_by_member and find_by_owner. 
        '''
        pass
    
    def find_by_member(self, member_alias: str) -> list:
        ''' This method will return a list of ChatRoom instances that has the the current alias within the list of
                member_aliases in the ChatRoom instance.
            NOTE: it is possible for all rooms to not have a the member_alias within their instance. return a empty list
            NOTE: create a new list and append the ChatRooms to the list.
        '''
        pass

    def find_by_owner(self, owner_alias: str) -> list:
        ''' This method will return a list of ChatRoom instances that have an owner_alias that the user is searching for.
            NOTE: it is possible for all rooms to not have the current owner_alias.
            NOTE: create a new list and append ChatRooms that have the same alias.
        '''
        pass

    def __persist(self):
        ''' This method will save the metadata of the RoomList class and push it to the collections
            NOTE: the metadata should contain the list of room_names in the metadata where we would collect the room_names and find the room based on 
        '''
        pass

    def __restore(self) -> bool:
        pass