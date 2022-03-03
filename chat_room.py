from chat_message import ChatMessage
from  message_prop import MessageProperties

# constants
ROOM_TYPE_PUBLIC = 100
ROOM_TYPE_PRIVATE = 200

# generic methods
def get_messages(num_messaes: int, return_objects: bool) -> list:
    ''' Will be called from the API to get the messages from a room.
    '''

def send_message(message: str, mess_props: MessageProperties) -> bool:
    ''' Will send a message to the room type with the corresponding message properties.
    '''

def find_message(message_text: str) -> ChatMessage:
    ''' Will find a certain messages from a room chat, given that the message exists in the room.
    '''

def get() -> ChatMessage:
    ''' Will get the next message from the deque from the right side.
    '''
def put(message: ChatMessage) -> None:
    ''' Will put the message onto the left side of the queue.
    '''