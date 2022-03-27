import socket
import logging
import json
from fastapi import FastAPI, Request, status, Form
from fastapi.responses import JSONResponse, ORJSONResponse, Response
from fastapi.templating import Jinja2Templates
from room import *
from constants import *
from users import *

MY_IPADDRESS = ""

# This is an extremely rare case where I have global variables. The first is the documented way to deal with running the app in uvicorn, the second is the 
# instance of the rmq class that is necessary across all handlers that behave essentially as callbacks. 


app = FastAPI()
room_list = RoomList()
users = UserList()
templates = Jinja2Templates(directory="")
logging.basicConfig(filename='chat_api.log', level=logging.INFO, format = LOG_FORMAT)

@app.get("/")
async def index():
    """ Default page
        NOTE: when the user accesses the main page, they will get the following JSON response (dictionary)
    """
    return { 'message' : { 'from' : 'kevin', 'to' : 'you :)'} }

@app.get("/page/send", status_code=200)
async def send_form(request: Request):
    """ HTML GET page form sending a message
    """
    pass

@app.post("/page/send", status_code=201)
async def get_form(request: Request, room_choice: str = Form(...), message: str = Form(...), alias: str = Form(...)):
    """ HTML POST page for sending a message
    """
    pass

@app.get("/page/messages", status_code=200)
async def form_messages(request: Request, room_name: str = DEFAULT_PUBLIC_ROOM):
    """ HTML GET page for seeing messages
    """
    pass

@app.post("/page/messages", status_code=201)
async def form_messages(request: Request, room_name: str = Form(...)):
    """ HTML POST page for seeing messages in a different room or different quantities
    """
    pass


@app.get("/messages/", status_code=200)
async def get_messages(request: Request, alias: str, room_name: str, messages_to_get: int = GET_ALL_MESSAGES):
    """ API for getting messages from a room
        NOTE: this user must be a valid member of the room to access the messages to the room.
        TODO: make sure the alias is valid
        TODO: access the room, if it exists
    """
    pass

@app.get("/users/", status_code=200)
async def get_users():
    """ API for getting users
        NOTE: this will just access the userList from the call above and attempt to get the users, most likely just aliases.
    """
    pass

@app.post("/alias", status_code=201)
async def register_client(client_alias: str, group_alias: bool = False):
    """ API for adding a user alias
        TODO: access the UserList var above and attempt to register and add the user to the UserList
    """
    pass

@app.post("/room")
async def create_room(room_name: str, owner_alias: str, room_type: int = ROOM_TYPE_PRIVATE):
    """ API for creating a room
        TODO: verify the user and the owner alias is valid
        TODO: check if room_name is already taken, this should return None if so, (method call is create in RoomList)
    """
    pass

@app.post("/message/", status_code=201)
async def send_message(room_name: str, message: str, from_alias: str, to_alias: str):
    """ API for sending a message
        TODO: make sure the user is a valid user, make sure the to_alias is valid too
        TODO: access the room from the room list, if it exists
        TODO: this may want to access the send_message feature from a chatroom
    """
    pass

def main():
    ''' Main method to get the current user alias
    '''
    logging.basicConfig(filename='chat.log', level=logging.INFO)
    MY_IPADDRESS = socket.gethostbyname(socket.gethostname())
    MY_NAME = input("Please enter your name: ")

if __name__ == "__main__":
    main()
