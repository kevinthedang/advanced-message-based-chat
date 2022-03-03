import pika

GET_ALL_MESSAGES = -1
RMQ_HOST = ''
RMQ_PORT = 5672
RMQ_USER = ''
RMQ_PASS = ''
RMQ_DEFAULT_PUBLIC_QUEUE = 'general'
RMQ_DEFAULT_PRIVATE_QUEUE = ''
RMQ_DEFAULT_VH = '/'
RMQ_DEFAULT_EXCHANGE_NAME = ''
RMQ_DEFAULT_EXCHANGE_TYPE = 'fanout'
RMQ_ROUTING_KEY = 'my_message'
BYTE_to_STRING = 'utf-8'

class MessageServer():
    ''' This is the RMQ Publisher
        - Only one connection needs to be made.
        - There should be two channels, followed by two queues.s
        - There should be one exchange, the queues will bind to the exchange.
    '''
    def __init__(self) -> None:
        ''' Establishing Variables needed to perform connection to RMQ
            The class just needs to handle a connection, an exchange, channels, etc.
        '''
        self._connection = None
        self._public_channel = None
        self._private_channel = None
        self._has_private_queue = False
        self._private_queue_name = None

        self.server_setup()

    def send_message(self, message_content: str, target_queue: str = RMQ_DEFAULT_PUBLIC_QUEUE) -> bool:
        ''' This will send a request to send a message to the exchange.
            The exchange will distribute it to the queue based on the target queue.
            it will only return a true if the message was sent correctly, false otherwise.
        '''
        target_channel = self._handle_queue(target_queue)
        return self.publish_message(message_content, target_channel)

    def receieve_messages(self, num_messages: int = GET_ALL_MESSAGES, take_from_queue : str = RMQ_DEFAULT_PUBLIC_QUEUE) -> list:
        ''' Get a set of messages and return them in a list
            messages will be strings, so it will return a list of strings

            Since we do not know the current private queue name. we will instantiate it from here when receiving from there.
        '''
        take_from_channel = self._handle_queue(take_from_queue)
        return self.consume_message(destination_queue = take_from_queue, max_messages = num_messages, channel_type = take_from_channel)

    def _handle_queue(self, queue_to_handle):
        ''' This method handles when an order is received for RabbitMQ.
            The method checks if there is a new private queue that wants to be accessed and
            closes the previous one if it exists
        '''
        if queue_to_handle != RMQ_DEFAULT_PUBLIC_QUEUE:
            if self._has_private_queue is True and queue_to_handle != self._private_queue_name:
                self._private_channel.queue_delete(self._private_queue_name)
            self.setup_queue(self._private_channel, queue_to_handle)
            self._has_private_queue = True
            self._private_queue_name = queue_to_handle
            return self._private_channel
        return self._public_channel

    def server_setup(self) -> bool:
        ''' This method sets up -> Server connection, The public and private channels, The public and private queues.
            This helps with testing the individual calls in the test file.
        '''
        self.establish_connection()
        self.setup_channels()
        self.setup_exchange()
        return True

    def establish_connection(self) -> bool:
        ''' This method will establish the connection to the RabbitMQ server.
            Proper authentication credentials and parameters are needed to access the server.

            If no exceptions are raised, then the function will return true (test purpose)
        '''
        credentials = pika.PlainCredentials(RMQ_USER, RMQ_PASS)
        parameters = pika.ConnectionParameters(host=RMQ_HOST, port=RMQ_PORT, virtual_host=RMQ_DEFAULT_VH, credentials=credentials)
        self._connection = pika.BlockingConnection(parameters=parameters)
        return True
    
    def setup_channels(self) -> bool:
        ''' This method will open both the public and the select private channel
            for sending messages.
        '''
        self._public_channel = self._connection.channel()
        self._private_channel = self._connection.channel()
        return True

    def setup_exchange(self) -> bool:
        ''' Set up the exchange on RabbitMQ. The exchange name and type are held
            as parameters to help with declaring the exchange.
            This method will setup the default public and private queue.
            The exchange will also be set on the public channel allowing other queues from other channels to connect
        '''
        self._public_channel.exchange_declare(
            exchange = RMQ_DEFAULT_EXCHANGE_NAME,
            exchange_type = RMQ_DEFAULT_EXCHANGE_TYPE,
            )   
        self.setup_queue(self._public_channel, RMQ_DEFAULT_PUBLIC_QUEUE)
        self.setup_queue(self._private_channel, RMQ_DEFAULT_PRIVATE_QUEUE)
        return True
        
    def setup_queue(self, queue_type, queue_name) -> bool:
        ''' This method will create a queue and immediately bind it to the exchange,
            with respect to the channel that it was created in.
        '''
        queue_type.queue_declare(queue = queue_name)
        queue_type.queue_bind(exchange = RMQ_DEFAULT_EXCHANGE_NAME, queue = queue_name, routing_key = RMQ_ROUTING_KEY)
        queue_type.basic_qos(prefetch_count = 1)
        return True

    def publish_message(self, message, channel_type) -> bool:
        ''' This method will attempt to publish a message to RabbitMQ.
            The method will inform of a successful publish or not through the terminal.
            The channel type will be either the public or private channel
        '''
        channel_type.confirm_delivery()
        try: 
            channel_type.basic_publish(exchange = RMQ_DEFAULT_EXCHANGE_NAME, routing_key = RMQ_ROUTING_KEY, body = message, properties = pika.BasicProperties(delivery_mode = 1), mandatory = True)
            print(f' [x] "{message}" was sent to the queue!')
        except pika.exceptions.UnroutableError:
            print('Message was returned.')
            return False
        return True
        
    def consume_message(self, destination_queue, max_messages, channel_type) -> list:
        ''' This method will consume a message from RabbitMQ.
            This method will handle receiving messages and will let the user know if there are no messages in the queue.
            The consume will be given 2 seconds for a response (after receiving some messages), then it will receive a NoneType and terminate
        '''
        message_list = []
        message_increment = 0
        try:
            print(f' [x] Waiting for Messages on {destination_queue}...')
            for method_frame, properties, body in channel_type.consume(queue = destination_queue, inactivity_timeout = 3, auto_ack = True):
                if not method_frame == None:
                    message_list.append(body.decode(BYTE_to_STRING))
                    print(f' [{message_increment + 1}] Current Message Received: ' + message_list[message_increment])
                    message_increment += 1
                    if message_increment == max_messages:
                        channel_type.basic_recover(requeue = True)
                        print(f' [x] {channel_type.get_waiting_message_count()} messages have been requeued.')
                        break
                else:
                    break
        except pika.exceptions.UnroutableError:
            print(f' [x] "{destination_queue}" queue not found')
        if len(message_list) == 0:
            print(f' [x] No messages in "{destination_queue}"')
            message_list.append('No messages currently in queue.')
        return message_list