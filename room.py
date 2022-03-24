from email import message
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
        TODO: make getters for all of the private variables
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

    # the following properties are to get functions to get message properties
    @property
    def message_type(self):
        return self.__mess_type

    @property
    def room_name(self):
        return self.__room_name

    @property
    def to_user(self):
        return self.__to_user

    @property
    def from_user(self):
        return self.__from_user

    @property
    def sent_time(self):
        return self.__sent_time

    @property
    def rec_time(self):
        return self.__rec_time

    @property
    def sequence_number(self):
        return self.__sequence_num

    def __str__(self):
        return str(self.to_dict())

class ChatMessage():
    """ Class for holding individual messages in a chat thread/queue. Each message a message, rabbitmq properties, sequence number, timestamp and type
    """
    def __init__(self, message: str, mess_id = None, mess_props: MessageProperties = None) -> None:
        self.__message = message
        self.__mess_props = mess_props
        self.__mess_id = mess_id
        self.__dirty = True

    # the following 4 properties are set so information about a ChatMessage instance can be obtained
    @property
    def message(self):
        return self.__message

    @property
    def message_properties(self):
        return self.__mess_props
    
    @property
    def dirty(self):
        return self.__dirty

    @property
    def message_id(self):
        return self.__mess_id

    def to_dict(self):
        mess_props_dict = self.mess_props.to_dict()
        return {'message': self.message, 'mess_props': mess_props_dict}

    def __str__(self):
        return f'Chat Message: {self.message} - message props: {self.mess_props}'

class ChatRoom(deque):
    """ We reuse the constructor for creating new or grabbing an existing instance. If owner_alias is empty and user_alias is not, 
            this is assuming an existing instance. The opposite (owner_alias set and user_alias empty) means we're creating new
            members is always optional, and room_type is only relevant if we're creating new.
            NOTE: variables will be instantiated when restore is true.
    """
    def __init__(self, room_name: str, member_list: list = None, owner_alias: str = "", room_type: int = ROOM_TYPE_PRIVATE, create_new: bool = False) -> None:
        super(ChatRoom, self).__init__()
        self.__room_name = room_name
        self.__user_list = UserList()
        # Set up mongo - client, db, collection, sequence_collection
        self.__mongo_client = MongoClient(host = MONGO_DB_HOST, port = MONGO_DB_PORT, username = MONGO_DB_USER, password = MONGO_DB_PASS, authSource = MONGO_DB_AUTH_SOURCE, authMechanism = MONGO_DB_AUTH_MECHANISM)
        self.__mongo_db = self.__mongo_client.detest
        self.__mongo_collection = self.__mongo_db.get_collection(self.__room_name) 
        self.__mongo_seq_collection = self.__mongo_db.get_collection("sequence")
        if self.__mongo_collection is None:
            self.__mongo_collection = self.__mongo_db.create_collection(self.__room_name)
        # Restore from mongo if possible, if not (or we're creating new) then setup ChatRoom properties
        if create_new is True or self.restore() is False:
            self.__room_type = room_type
            if member_list is not None:
                self.__member_list = member_list
                if owner_alias not in member_list:
                    member_list.append(owner_alias)
            else:
                self.__member_list = list()
                self.__member_list.append(owner_alias)

    # property to get the name of a room
    @property
    def room_name(self):
        return self.__room_name

    # property to get the list of users for a room
    @property
    def room_user_list(self):
        return self.__user_list

    # property to get the owner_alias of the 
    @property
    def owner_alias(self):
        return self.__owner_alias

    # property to get the length of the deque
    @property
    def num_messages(self):
        return len(list(self))

    def __get_next_sequence_num(self):
        """ This is the method that you need for managing the sequence. Note that there is a separate collection for just this one document
        """
        sequence_num = self.__mongo_seq_collection.find_one_and_update(
                                                        {'_id': 'userid'},
                                                        {'$inc': {self.__room_name: 1}},
                                                        projection={self.__room_name: True, '_id': False},
                                                        upsert=True,
                                                        return_document=ReturnDocument.AFTER)
        return sequence_num

    #Overriding the queue type put and get operations to add type hints for the ChatMessage type
    def put(self, message: ChatMessage = None) -> None:
        ''' This method will put the current message to the left side of the deque
            TODO: put the message on the left using appendLeft() method
        '''
        logging.info(f'Caliing the put() method with current message being {message} appending to the left of the deque.')
        if message is not None:
            super().appendleft(message)
            logging.info(f'{message} was appended to the left of the queue.')
            logging.info(f'Beginning persistence of message {message}.')
            # self.persist()


    # overriding parent and setting block to false so we don't wait for messages if there are none
    def get(self) -> ChatMessage:
        ''' This method will take a ChatMessage from the right side of the deque.
            NOTE: the method pop() to take a value from the right of the deque
        '''
        try:
            message_right = super()[-1]
        except:
            logging.debug(f'There is no message in the deque for room {self.__room_name}')
            return None
        else:
            logging.debug(f'Message {message} was found on the deque.')
            return message_right

    def find_message(self, message_text: str) -> ChatMessage:
        ''' Traverse through the deque of the Chatroom and find the ChatMessage 
                with the message_text input from the user.
            TODO: Understand how the deque works and how to traverse the deque.
            NOTE: To traverse through the deque, we can use list(self) as an iterable to find the message
            NOTE: an example would be (for current_message in list(self))
        '''
        for current_message in list(self):
            if current_message.message == message_text:
                logging.debug(f'found {message_text} in deque.')
                return current_message
        logging.debug(f'{message_text} was not found in the deque.')
        return None
            
    def get_messages(self, user_alias: str, num_messages: int = GET_ALL_MESSAGES, return_objects: bool = True):
        ''' This method will get num_messages from the deque and get their text, objects and a total count of the messages
            NOTE: Refer to Dans code about message objects and message_texts
            NOTE: total # of messages seems to just be num messages, but if getting all then just return the length of the list
            NOTE: indecies 0 and 1 is to access the values in the tuple for the objects and the number of objects
            TODO: get message_objects if the user wants the objects
        '''
        # return message texts, full message objects, and total # of messages
        if user_alias not in self.__member_list:
            logging.warning(f'User with alias {user_alias} is not a member of {self.__room_name}.')
            return [], [], 0
        if return_objects is True:
            message_objects = self.__get_message_objects(num_messages = num_messages)
            if num_messages == GET_ALL_MESSAGES:
                return [], message_objects[0], message_objects[1]

    def __get_message_objects(self, num_messages: int = GET_ALL_MESSAGES):
        ''' This is a helper method to get the actual message objects rather than just the message from the object
            TODO: write instance where num_messages is not GET_ALL_MESSAGES
        '''
        if num_messages == GET_ALL_MESSAGES:
            return list(self), len(self)

    def send_message(self, message: str, from_alias: str, mess_props: MessageProperties = None) -> bool:
        ''' This method will send a message to the ChatRoom instance
            NOTE: we are assuming that message is not None or empty
            NOTE: we most likely will need to utilize the put function to put the message on the queue
            NOTE: we also need to create an instance of ChatMessage to put on the queue
            NOTE: should we persist after putting the message on the deque.
        '''
        if mess_props is not None:
            new_message = ChatMessage(message = message, mess_props = mess_props)
            logging.info(f'New ChatMessage created with message {message}')
            self.put(new_message)
            return True
        return False

    def restore(self) -> bool:
        ''' This method will restore the metadata and the messages that a certain ChatRoom instance needs
            NOTE: a ChatRoom will contain it's own collection, if we are creating a new collection, we don't
                    need to restore
            NOTE: if the collection exists, then we do want to restore.
            TODO: Get room metadata and check if it is None, then use the metadata to get all messages and put them in the deque
            TODO: load all messages into the chatroom
        '''
        logging.info('Beginning the restore process.')
        room_metadata = self.__mongo_collection.find_one({})
        pass

    def persist(self):
        ''' This method will maintain the data inside of a ChatRoom instance:  
                - The metadata
                - The messages in the room.
            NOTE: we want to iterate through the deque
            TODO: since _id is autogenerated, this will be the message id for any message, even for the id of a room, upsert is used to update anything
        '''
        logging.info('Beginning the persistence process.')
        if self.__mongo_collection.find_one({ 'room_name': self.__room_name }) is None:
            self.__room_id = self.__mongo_collection.insert_one() # metadata here
        else:
            if self.__dirty == True:
                self.__mongo_collection.replace_one() # metadata here and upsert = True
        self.__dirty = False
        # put messages in the collection now
        for current_message in list(self):
            if current_message.dirty == True:
                if current_message.message_id is None or self.__mongo_collection.find_one({ '_id' : current_message.message_id }) is None:
                    current_message.message_properties.sequence_number = self.__get_next_sequence_num()
                    # continue here

class RoomList():
    """ This is the RoomList class instance that will handle a list of ChatRooms and obtaining them.
        NOTE: no need to have properties as this will be the main handler of all other class instances.
        TODO: complete this class by writing its functions.
    """
    def __init__(self, room_list_name: str = DEFAULT_ROOM_LIST_NAME) -> None:
        """ Try to restore from mongo and establish variables for the room list
            TODO: RoomList takes a name, set the name
            TODO: inherit a list, or create an internal variable for a list of rooms
            TODO: restore the mongoDB collection
            NOTE: restore will handle putting the rooms into the room_list
        """
        self.__room_list_name = room_list_name
        self.__room_list = list()
        # Set up mongo - client, db, collection
        self.__mongo_client = MongoClient(host = MONGO_DB_HOST, port = MONGO_DB_PORT, username = MONGO_DB_USER, password = MONGO_DB_PASS, authSource = MONGO_DB_AUTH_SOURCE, authMechanism = MONGO_DB_AUTH_MECHANISM)
        self.__mongo_db = self.__mongo_client.detest
        self.__mongo_collection = self.__mongo_db.get_collection(room_list_name)
        if self.__mongo_collection is None:
            self.__mongo_collection = self.__mongo_db.create_collection(room_list_name)
        # Restore from mongo if possible, if not (or we're creating new) then setup properties
        if self.__restore() is not True:
            self.__room_list_create = datetime.now()
            self.__room_list_modify = datetime.now()

    def create(self, room_name: str, owner_alias: str, member_list: list = None, room_type: int = ROOM_TYPE_PRIVATE) -> ChatRoom:
        ''' This method will create a new ChatRoom given that the room_name is not already taken for the collection.
            NOTE: This can just be a checker for the chatroom name existing in the list when restored or if it's in the collection
            NOTE: Maybe check with the collection as it is possible for all names to not be in the list and removed, due to the option for removal
            TODO: make sure to add a memberlist
        '''
        logging.info(f'Attempting to create a ChatRoom instance with name {room_name}.')
        if self.__mongo_db.get_collection(room_name) is None:
            return ChatRoom(room_name = room_name, member_list = member_list, owner_alias = owner_alias, room_type = room_type, create_new = True)
        return ChatRoom(room_name = room_name, member_list = member_list, owner_alias = owner_alias, room_type = room_type)

    def add(self, new_room: ChatRoom):
        ''' This method will add a ChatRoom instance to the list of ChatRooms
            NOTE: This should not need to check as the create() should already check for the class.
        '''
        pass

    def remove(self, room_name: str):
        ''' This method will remove a ChatRoom instance from the list of ChatRooms.
            NOTE: we want to make sure that the ChatRoom instance with the given room_name exists.
            NOTE: the use of -1 is to tell us that the ChatRoom instance was not found in the room list.
        '''
        chat_room_to_remove = self.__find_pos(room_name)
        if chat_room_to_remove is not CHAT_ROOM_INDEX_NOT_FOUND:
            self.__room_list.pop(chat_room_to_remove)
            logging.debug(f'ChatRoom {room_name} was removed from the room list.')
        else:
            logging.debut(f'ChatRoom {room_name} was not found in the room list.')

    def find_room_in_metadata(self, room_name: str) -> dict:
        ''' This method will return a dictionary of information, relating to the metadata...?
            TODO: connect to MongoDB and attempt to see how the metadata looks
        '''
        pass

    def get_rooms(self):
        ''' This method will return the rooms in the room list.
            NOTE: The room list can be empty
            NOTE: this may just be the room names or not
        '''
        return self.__room_list

    def get(self, room_name: str) -> ChatRoom:
        ''' This method will return a ChatRoom instance, given the name of the room, room_name.
            NOTE: It is possible for a ChatRoom instance to not be in the list of rooms.
            NOTE: do we create a new ChatRoom if the chatroom was not found?
        '''
        for chat_room in self.__room_list:
            if chat_room.room_name == room_name:
                return chat_room

    def __find_pos(self, room_name: str) -> int:
        ''' This method is most likely a helper method for getting the position of a ChatRoom instance is in a list.
            NOTE: This maybe just for find_by_member and find_by_owner.
            NOTE: returning -1 if the room instance cannot be found.
            NOTE: This is used for removing a chatroom instance in the list
        '''
        for chat_room_index in range(len(self.__room_list)):
            if self.__room_list[chat_room_index].room_name is room_name:
                return chat_room_index
        return CHAT_ROOM_INDEX_NOT_FOUND
    
    def find_by_member(self, member_alias: str) -> list:
        ''' This method will return a list of ChatRoom instances that has the the current alias within the list of
                member_aliases in the ChatRoom instance.
            NOTE: it is possible for all rooms to not have a the member_alias within their instance. return a empty list
            NOTE: create a new list and append the ChatRooms to the list.
            TODO: using the member_alias, find all rooms with a members_list that has this alias
            TODO: check if this member_alias is valid
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
        ''' This method will load the metadata from the collection of the RoomList class and load it to the instance.
            NOTE: the collection will have to be checked for all ChatRoom aliases
        '''
        pass