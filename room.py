import pika
import json
import pika.exceptions
import logging
from users import *
from datetime import date, datetime
from pymongo import MongoClient, ReturnDocument
from collections import deque
from constants import *

MONGO_DB = 'detest'
#MONGO_DB = 'chatroom'
logging.basicConfig(filename='chatroom.log', level=logging.DEBUG, filemode='w')

class MessageProperties():
    """ Class for holding the properties of a message: type, sent_to, sent_from, rec_time, send_time
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

    @property
    def dirty(self):
        return self.__dirty

    def to_dict(self):
        mess_props_dict = self.__mess_props.to_dict()
        return {'message': self.__message, 'mess_props': mess_props_dict}

    def __str__(self):
        return f'Chat Message: {self.__message} - message props: {self.__mess_props}'

class ChatRoom(deque):
    """ Docstring
        We reuse the constructor for creating new or grabbing an existing instance. If owner_alias is empty and user_alias is not, 
            this is assuming an existing instance. The opposite (owner_alias set and user_alias empty) means we're creating new
            members is always optional, and room_type is only relevant if we're creating new.
    """
    def __init__(self, room_name: str, member_list: list = None, owner_alias: str = "", room_type: int = ROOM_TYPE_PRIVATE, create_new: bool = False) -> None:
        super(ChatRoom, self).__init__()
        self.__room_name = room_name
        self.__member_list = member_list
        self.__owner_alias = owner_alias
        self.__room_type = room_type
        self.__create_time = datetime.now()
        self.__modify_time = datetime.now()
        # Set up mongo - client, db, collection, sequence_collection
        self.__mongo_client = MongoClient(host='34.94.157.136', port=27017, username='class', password='CPSC313', authSource='detest', authMechanism='SCRAM-SHA-256')
        self.__mongo_db = self.__mongo_client.detest
        self.__mongo_collection = self.__mongo_db.get_collection(self.__room_name) 
        self.__mongo_seq_collection = self.__mongo_db.get_collection("sequence")
        if self.__mongo_collection is None:
            self.__mongo_collection = self.__mongo_db.create_collection(self.__room_name)
        # Restore from mongo if possible, if not (or we're creating new) then setup properties
        self.__rmq_creds = pika.PlainCredentials(RMQ_LOGIN, RMQ_PASS)
        self.__rmq_connection_params = pika.ConnectionParameters(RMQ_HOST, RMQ_PORT, RMQ_VIRTUALHOST, self.__rmq_creds)
        self.__rmq_connection = pika.BlockingConnection(self.__rmq_connection_params)
        self.__rmq_channel = self.__rmq_connection.channel()
        self.__rmq_queue = self.__rmq_channel.queue_declare(queue=DEFAULT_QUEUE_NAME)
        self.__rmq_exchange = self.__rmq_channel.exchange_declare(exchange = RMQ_DEFAULT_PUBLIC_EXCHANGE, exchange_type = 'fanout') 
        self.__rmq_channel.queue_bind(exchange = RMQ_DEFAULT_PUBLIC_EXCHANGE, queue = DEFAULT_QUEUE_NAME)

    @property
    def room_name(self):
        return self.__room_name

    @property
    def owner_alias(self):
        return self.__owner_alias

    @property
    def list_of_users(self):
        return self.__member_list.get_all_users()

    def to_dict(self):
        return {
                'room_name': self.__alias,
                'user_list': self.__member_list,
                'owner_alias': self.__owner_alias,
                'room_type': self.__room_type,
                'create_time': self.__create_time,
                'modify_time': datetime.now()

        }

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
        """ Overriding the queue type put and get operations to add type hints for the ChatMessage type
            Also, since we can insert messages at either end, we're choosing (arbitrarily) to put on left, read from right
        """
        logging.info(f'Calling Queue put method. message is {message}')
        if message is not None:
            super().appendleft(message)
            self.persist()

    # overriding parent and setting block to false so we don't wait for messages if there are none
    def get(self) -> ChatMessage:
        """ overriding parent and setting block to false so we don't wait for messages if there are none
            Return the last message in the deque (indexing at -1 gets you the last element)
        """
        try:
            new_message = super()[-1]
        except:
            logging.debug("No message in chatqueue.get!!")
            return None
        else:
            return new_message

    def find_message(self, message_text: str) -> ChatMessage:
        """ Go through the deque to find a message object that matches the text. Will return the first such message
            TODO: this should ultimately be done by ID 
        """
        for chat_message in deque:
            if chat_message.message == message_text:
                return chat_message

    def restore(self) -> bool:
        """ We're restoring data from Mongo. 
            First get the metadata record, but looking for a name key with find_one. If it exists, then we have the doc. If not, bail
                Fill in the metadata (name, create, modify times - we'll do more later)
            Second, we're getting the actual messages. Now we look for the key "message". Note that we're using find so we'll get all that 
                match (every document with a key called 'message')
                For each dictionary we get back (the documents), create a message properties instance and a message instance and
                    put them in the deque by calling the put method
            TODO: We are missing some properties we need to implement like sequence_num and room_name
        """
        queue_metadata = self.__mongo_collection.find_one( { 'name': { '$exists': 'true'}})
        if queue_metadata is None:
            return False
        self.__name = queue_metadata["name"]
        self.__create_time = queue_metadata["create_time"]
        self.__modify_time = queue_metadata["modify_time"]
        for mess_dict in self.__mongo_collection.find({ 'message': { '$exists': 'true'}}):
            new_mess_props = MessageProperties(
                mess_dict['mess_props']['mess_type'],
                mess_dict['mess_props']['to_user'],
                mess_dict['mess_props']['from_user'],
                mess_dict['mess_props']['sent_time'],
                mess_dict['mess_props']['rec_time']
            )
            new_message = ChatMessage(mess_dict['message'], new_mess_props, None)
            new_message.dirty = False
            self.put(new_message)
        return True

    def persist(self):
        """ First save a document that describes the user list (metadata: name of list, create and modify times) if it isn't already there
            Second, for each message in the list create and save a document for that user
                NOTE: We're using our custom to_dict so we give Mongo what it wants
        """
        if self.__mongo_collection.find_one({ 'name': { '$exists': 'false'}}) is None:
            self.__mongo_collection.insert_one({"name": self.__room_name, "create_time": self.__create_time, "modify_time": self.__modify_time})
        for message in list(self):
            if message.dirty is True:
                serialized2 = message.to_dict()
                self.__mongo_collection.insert_one(serialized2)

    def get_messages(self, user_alias: str, num_messages: int = GET_ALL_MESSAGES, return_objects: bool = True):
        # return message texts, full message objects, and total # of messages
        message_obj_list = []
        message_body_list = []
        logging.info("Starting retreive_messages")
        if self.__rmq_channel.is_closed:
            logging.warning(f'Inside __retrieve messages, the channel is CLOSED!!')
        logging.info(f'Inside retreive_messages, queue is {DEFAULT_QUEUE_NAME}, exchange: {RMQ_DEFAULT_PUBLIC_EXCHANGE}, cache: {self}, channel: {self.__rmq_channel}')
        num_mess_received = 0
        for m_f, props, body in self.__rmq_channel.consume(DEFAULT_QUEUE_NAME, auto_ack=True, inactivity_timeout=2):
            logging.info(f"inside retreive messages, processing a messsage. body = {body}")
            if body != None:
                num_mess_received += 1
                message_body_list.append(body.decode(BYTE_to_STRING))
                new_mess_props = MessageProperties(
                    self.__room_name, # this is now received, the original will be sent
                    props.headers['_MessageProperties__to_user'],
                    props.headers['_MessageProperties__from_user'],
                    MESSAGE_TYPE_RECEIVED,
                    props.headers['_MessageProperties__sequence_num'],
                    props.headers['_MessageProperties__sent_time'],
                    props.headers['_MessageProperties__rec_time']
                )
                new_message = ChatMessage(body.decode(BYTE_to_STRING), new_mess_props)
                message_obj_list.append(new_message)
                logging.info(f'Inside retrieve, here is the new chatmessage: {new_message}')
                logging.info(f'Inside retrieve, chatmessage body: {body}\n mess_props: {new_mess_props}\n')
                self.put(new_message)
                if num_mess_received >= num_messages and num_messages is not GET_ALL_MESSAGES:
                    break
            else:
                break
        requeued_messages = self.__rmq_channel.cancel()
        logging.info(f'Called cancel after retreive messages, result of that call is {requeued_messages}')
        if return_objects:
            return message_obj_list, message_body_list, num_mess_received
        else:
            return message_body_list, num_mess_received

    def send_message(self, message: str, mess_props: MessageProperties) -> bool:
        """ Send a message through rabbit, but also create the message instance and add it to our internal queue by calling the internal put method
        """
        try:
            self.__rmq_channel.basic_publish(RMQ_DEFAULT_PUBLIC_EXCHANGE, 
                                        routing_key = DEFAULT_QUEUE_NAME, 
                                        properties = pika.BasicProperties(headers=mess_props.__dict__),
                                        body = message, mandatory = True)
            logging.info(f'Publish to messaging server succeeded. Message: {message}')
            self.put(ChatMessage(message=message, mess_props=mess_props))
            return(True)
        except pika.exceptions.UnroutableError:
            logging.debug(f'Message was returned undeliverable. Message: {message} and target queue: {self.rmq_queue}')
            return(False) 

class RoomList():
    """ Note, I chose to use an explicit private list instead of inheriting the list class
    """
    def __init__(self, name: str = DEFAULT_ROOM_LIST_NAME) -> None:
        """ Try to restore from mongo 
        """
        self.__room_list_name = name
        self.__chat_rooms_list = list()
        # Set up mongo - client, db, collection, sequence_collection
        self.__mongo_client = MongoClient(host='34.94.157.136', port=27017, username='class', password='CPSC313', authSource='detest', authMechanism='SCRAM-SHA-256')
        self.__mongo_db = self.__mongo_client.detest
        self.__mongo_collection = self.__mongo_db.get_collection(name) 
        if self.__mongo_collection is None:
            self.__mongo_collection = self.__mongo_db.create_collection(name)
        # Restore from mongo if possible, if not (or we're creating new) then setup properties
        if self.__restore() is not True:
            self.__room_list_create = datetime.now()
            self.__room_list_modify = datetime.now()

    def create(self, room_name: str, owner_alias: str, member_list: list = None, room_type: int = ROOM_TYPE_PRIVATE) -> ChatRoom:
        ''' This method will create a new chatroom
            NOTE: There is a param in the init of ChatRoom, look out for the create_new
        '''
        return ChatRoom(room_name = room_name, owner_alias = owner_alias, member_list = member_list, room_type = room_type)

    def add(self, new_room: ChatRoom):
        ''' This method will append a newly created chat room to the list of chat rooms
        '''
        self.__chat_rooms_list.append(new_room)
        self.__persist()

    def find_room_in_metadata(self, room_name: str) -> dict:
        return self.__chat_rooms_list[room_name].to_dict()

    def get_rooms(self) -> list:
        ''' This method will return the list of the chat rooms
            NOTE: It is possible for there to be no rooms in the chat room list
        '''
        return self.__chat_rooms_list

    def get(self, room_name: str) -> ChatRoom:
        for current_room in self.__chat_rooms_list:
            if room_name == current_room.room_name:
                return current_room
    
    def find_by_member(self, member_alias: str) -> list:
        ''' This method will go through the chat rooms list and return a list of 
            chat rooms based on the member input
        '''
        rooms_by_members = list()
        for current_room in self.__chat_rooms_list:
            if member_alias in current_room.list_of_users:
                rooms_by_members.append(current_room)
        return rooms_by_members

    def find_by_owner(self, owner_alias: str) -> list:
        ''' This method will go through the chat rooms list and return a list of 
            chat rooms based on the member input
            NOTE: This just needs to focus on the owner_alias portion to sort it out
        '''
        rooms_by_owners = list()
        for current_room in self.__chat_rooms_list:
            if owner_alias == current_room.owner_alias:
                rooms_by_owners.append(current_room)
        return rooms_by_owners

    def remove(self, room_name: str) -> None:
        ''' This method will focus on removing a chat room from the chat room list
        '''
        for current_room in self.__chat_rooms_list:
            if room_name == current_room.__room_name:
                self.__chat_rooms_list.pop(current_room)

    def __persist(self):
        ''' This method will make sure that there is not a document for the data for a
                list of rooms in the collection yet.
            NOTE: the room names will persist as metadata in the mongo collection.
        '''
        if self.__mongo_collection.find_one({ 'name': self.__room_list_name }) is None:
            self.__mongo_collection.insert_one({ "name": self.__room_list_name, "create_time": self.__room_list_create, "modify_time": self.__room_list_modify, 'room_names' : self.__chat_rooms_list})

    def __restore(self) -> bool:
        ''' This method will restore all the metadata from the mongo collection.
        '''
        queue_metadata = self.__mongo_collection.find_one( { 'name': self.__room_list_name })
        if queue_metadata is None:
            return False
        self.__room_list_name = queue_metadata["name"]
        self.__room_list_create = queue_metadata["create_time"]
        self.__room_list_modify = datetime.now()
        self.__chat_rooms_list = queue_metadata['room_names']