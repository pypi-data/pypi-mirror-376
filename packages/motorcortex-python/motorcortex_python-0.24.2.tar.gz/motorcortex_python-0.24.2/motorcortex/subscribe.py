#!/usr/bin/python3

#
#   Developer: Alexey Zakharov (alexey.zakharov@vectioneer.com)
#   All rights reserved. Copyright (c) 2016-2025 VECTIONEER.
#

import pynng
from motorcortex.request import Request, Reply, ConnectionState
from motorcortex.subscription import Subscription
from motorcortex.state_callback_handler import StateCallbackHandler
from motorcortex.setup_logger import logger
from pynng import Sub0, TLSConfig
from concurrent.futures import ThreadPoolExecutor
from threading import Event


class Subscribe:
    """Subscribe class is used to receive continuous parameter updates from the motorcortex server.

        Subscribe class simplifies creating and removing subscription groups.

        Args:
            req(Request): reference to a Request instance
            protobuf_types(MessageTypes): reference to a MessageTypes instance

    """

    def __init__(self, req, protobuf_types):
        self.__socket = None
        self.__connected_event = None  # Will be created per connection
        self.__is_connected = False
        self.__url = None
        self.__req = req
        self.__protobuf_types = protobuf_types
        self.__subscriptions = dict()
        self.__pool = ThreadPoolExecutor()
        self.__callback_handler = StateCallbackHandler()
        self.__connection_state = ConnectionState.DISCONNECTED
        logger.debug("[SUBSCRIBE] Subscribe object initialized with state: DISCONNECTED")

    def connect(self, url, **kwargs):
        """Open a subscription connection.

            Args:
                url(str): motorcortex server URL

            Returns:
                bool: True - if connected, False otherwise
        """
        logger.debug(f"[SUBSCRIBE-CONNECT] Starting subscription connection to {url}")
        logger.debug(f"[SUBSCRIBE-CONNECT] Current state: {self.__connection_state.name}")

        self.__connection_state = ConnectionState.CONNECTING
        conn_timeout_ms, recv_timeout_ms, certificate, state_update = Request.parse(**kwargs)

        logger.debug(
            f"[SUBSCRIBE-CONNECT] Parameters - timeout: {conn_timeout_ms}ms, recv_timeout: {recv_timeout_ms}ms, "
            f"has_cert: {certificate is not None}, has_state_update: {state_update is not None}")

        if state_update:
            logger.debug("[SUBSCRIBE-CONNECT] Starting state callback handler")
            self.__callback_handler.start(state_update)

        if not recv_timeout_ms:
            recv_timeout_ms = 500
            logger.debug(f"[SUBSCRIBE-CONNECT] Using default recv_timeout: {recv_timeout_ms}ms")

        self.__url = url
        tls_config = None
        if certificate:
            logger.debug(f"[SUBSCRIBE-CONNECT] Using TLS with certificate: {certificate}")
            tls_config = TLSConfig(TLSConfig.MODE_CLIENT, ca_files=certificate)

        logger.debug(f"[SUBSCRIBE-CONNECT] Creating Sub0 socket with recv_timeout={recv_timeout_ms}ms")
        self.__socket = Sub0(recv_timeout=recv_timeout_ms, tls_config=tls_config)

        self.__connected_event = Event()
        self.__is_connected = False

        logger.debug("[SUBSCRIBE-CONNECT] Socket created, registering callbacks")

        def pre_connect_cb(_pipe):
            logger.debug(f"[SUBSCRIBE-CALLBACK] PRE_CONNECT fired - Subscription connection established")
            old_state = self.__connection_state.name
            self.__is_connected = True
            self.__connection_state = ConnectionState.CONNECTION_OK
            logger.debug(f"[SUBSCRIBE-CALLBACK] State transition: {old_state} -> {self.__connection_state.name}")
            self.__callback_handler.notify(self.__req, self, self.connectionState())
            self.__connected_event.set()  # Wake up all waiting threads
            logger.debug("[SUBSCRIBE-CALLBACK] Connection event set, is_connected=True")

        def post_remove_cb(_pipe):
            logger.debug(f"[SUBSCRIBE-CALLBACK] POST_REMOVE fired - Subscription connection lost/failed")
            old_state = self.__connection_state.name

            if self.__connection_state == ConnectionState.DISCONNECTING:
                self.__connection_state = ConnectionState.DISCONNECTED
                logger.debug(f"[SUBSCRIBE-CALLBACK] Clean disconnect: {old_state} -> DISCONNECTED")
            elif self.__connection_state == ConnectionState.CONNECTING:
                self.__connection_state = ConnectionState.CONNECTION_FAILED
                logger.debug(f"[SUBSCRIBE-CALLBACK] Connection failed: {old_state} -> CONNECTION_FAILED")
            elif self.__connection_state == ConnectionState.CONNECTION_OK:
                self.__connection_state = ConnectionState.CONNECTION_LOST
                logger.debug(f"[SUBSCRIBE-CALLBACK] Connection lost: {old_state} -> CONNECTION_LOST")

            self.__is_connected = False
            self.__callback_handler.notify(self.__req, self, self.connectionState())
            self.__connected_event.set()
            logger.debug("[SUBSCRIBE-CALLBACK] Connection event set, is_connected=False")

        self.__socket.add_pre_pipe_connect_cb(pre_connect_cb)
        self.__socket.add_post_pipe_remove_cb(post_remove_cb)
        logger.debug("[SUBSCRIBE-CONNECT] Callbacks registered successfully")

        logger.debug(f"[SUBSCRIBE-CONNECT] Starting dial to {url} (non-blocking)")
        self.__socket.dial(url, block=False)

        logger.debug("[SUBSCRIBE-CONNECT] Submitting run() to thread pool")
        self.__pool.submit(self.run, self.__socket)

        logger.debug(f"[SUBSCRIBE-CONNECT] Submitting waitForConnection with timeout={conn_timeout_ms / 1000.0}s")
        return Reply(self.__pool.submit(Request.waitForConnection, self.__connected_event,
                                        conn_timeout_ms / 1000.0, lambda: self.__is_connected))

    def close(self):
        """Close connection to the server"""
        logger.debug("[SUBSCRIBE-CLOSE] Closing subscription connection")
        logger.debug(
            f"[SUBSCRIBE-CLOSE] Current state: {self.__connection_state.name}, is_connected: {self.__is_connected}")
        logger.debug(f"[SUBSCRIBE-CLOSE] Active subscriptions: {len(self.__subscriptions)}")

        self.__connection_state = ConnectionState.DISCONNECTING
        if self.__connected_event:
            self.__is_connected = False
            self.__connected_event.set()
            logger.debug("[SUBSCRIBE-CLOSE] Connection event set for shutdown")
        else:
            logger.debug("[SUBSCRIBE-CLOSE] No connection event to set")

        if self.__socket:
            logger.debug("[SUBSCRIBE-CLOSE] Closing socket")
            self.__socket.close()
        else:
            logger.debug("[SUBSCRIBE-CLOSE] No socket to close")

        logger.debug("[SUBSCRIBE-CLOSE] Stopping callback handler")
        self.__callback_handler.stop()

        logger.debug("[SUBSCRIBE-CLOSE] Shutting down thread pool (blocking)")
        self.__pool.shutdown(wait=True)
        logger.debug("[SUBSCRIBE-CLOSE] Subscription connection closed successfully")

    def run(self, socket):
        logger.debug("[SUBSCRIBE-RUN] Subscription receive loop started")

        # Wait for initial connection
        while not self.__is_connected:
            logger.debug("[SUBSCRIBE-RUN] Waiting for connection...")
            self.__connected_event.wait()  # Wait until connected

            # Check if we're shutting down
            if not self.__is_connected:
                if self.__connection_state in (ConnectionState.DISCONNECTING,
                                               ConnectionState.DISCONNECTED,
                                               ConnectionState.CONNECTION_FAILED):
                    logger.debug("[SUBSCRIBE-RUN] Connection closed or failed during startup, exiting")
                    return
                logger.debug("[SUBSCRIBE-RUN] Spurious wakeup, continuing to wait")

        logger.debug("[SUBSCRIBE-RUN] Connection established, starting receive loop")
        message_count = 0

        while True:
            try:
                buffer = socket.recv()
                message_count += 1
                if message_count % 100 == 0:  # Log every 100 messages to avoid spam
                    logger.debug(f"[SUBSCRIBE-RUN] Received {message_count} messages so far")

            except pynng.Timeout:
                # This is normal - just continue
                continue

            except pynng.Closed:
                logger.debug('[SUBSCRIBE-RUN] Socket closed, exiting subscription loop')
                break

            except RuntimeError as e:
                if "pool" in str(e).lower():
                    logger.debug('[SUBSCRIBE-RUN] Thread pool shutting down, exiting')
                    break
                logger.error(f'[SUBSCRIBE-RUN] RuntimeError in subscription loop: {e}')
                continue

            except Exception as e:
                logger.error(f'[SUBSCRIBE-RUN] Unexpected error in subscription loop: {type(e).__name__}: {e}')
                continue

            if buffer:
                sub_id_buf = buffer[:4]
                protocol_version = sub_id_buf[3]
                sub_id = sub_id_buf[0] + (sub_id_buf[1] << 8) + (sub_id_buf[2] << 16)
                sub = self.__subscriptions.get(sub_id)

                if sub:
                    length = len(buffer)
                    if protocol_version == 1:
                        sub._updateProtocol1(buffer[4:], length - 4)
                    elif protocol_version == 0:
                        sub._updateProtocol0(buffer[4:], length - 4)
                    else:
                        logger.error(
                            f'[SUBSCRIBE-RUN] Unknown protocol version: {protocol_version} for sub_id: {sub_id}')
                else:
                    logger.debug(f'[SUBSCRIBE-RUN] Received data for unknown subscription id: {sub_id}')

        logger.debug('[SUBSCRIBE-RUN] Subscription loop ended')

    def subscribe(self, param_list, group_alias, frq_divider=1):
        """Create a subscription group for a list of the parameters.

            Args:
                param_list(list(str)): list of the parameters to subscribe to
                group_alias(str): name of the group
                frq_divider(int): frequency divider is a downscaling factor for the group publish rate

            Returns:
                  Subscription: A subscription handle, which acts as a JavaScript Promise,
                  it is resolved when the subscription is ready or failed. After the subscription
                  is ready, the handle is used to retrieve the latest data.
        """
        logger.debug(
            f"[SUBSCRIBE] Creating subscription group '{group_alias}' with {len(param_list)} parameters, frq_divider={frq_divider}")
        logger.debug(
            f"[SUBSCRIBE] Parameters: {param_list[:5]}{'...' if len(param_list) > 5 else ''}")  # Show first 5 params

        subscription = Subscription(group_alias, self.__protobuf_types, frq_divider, self.__pool)
        reply = self.__req.createGroup(param_list, group_alias, frq_divider)
        reply.then(self.__complete, subscription, self.__socket).catch(subscription._failed)

        return subscription

    def unsubscribe(self, subscription):
        """Unsubscribe from the group.

            Args:
                subscription(Subscription): subscription handle

            Returns:
                  Reply: Returns a Promise, which resolves when the unsubscribe
                  operation is complete, fails otherwise.

        """
        sub_id = subscription.id()
        sub_id_buf = Subscribe.__idBuf(subscription.id())

        logger.debug(f"[UNSUBSCRIBE] Unsubscribing from group '{subscription.alias()}' (id={sub_id})")

        # stop receiving sub
        try:
            self.__socket.unsubscribe(sub_id_buf)
            logger.debug(f"[UNSUBSCRIBE] Socket unsubscribed from id={sub_id}")
        except Exception as e:
            logger.debug(f"[UNSUBSCRIBE] Failed to unsubscribe socket: {e}")

        # find and remove subscription
        if sub_id in self.__subscriptions:
            sub = self.__subscriptions[sub_id]
            # stop sub update thread
            sub.done()
            del self.__subscriptions[sub_id]
            logger.debug(
                f"[UNSUBSCRIBE] Removed subscription from internal dict, remaining: {len(self.__subscriptions)}")
        else:
            logger.debug(f"[UNSUBSCRIBE] Subscription id={sub_id} not found in internal dict")

        # send remove group request to the server
        return self.__req.removeGroup(subscription.alias())

    def connectionState(self):
        return self.__connection_state

    def resubscribe(self):
        logger.debug(f"[RESUBSCRIBE] Starting resubscription for {len(self.__subscriptions)} groups")
        old_sub = self.__subscriptions.copy()
        self.__subscriptions.clear()

        for i, (sub_id, s) in enumerate(old_sub.items()):
            logger.debug(f"[RESUBSCRIBE] Resubscribing group {i + 1}/{len(old_sub)}: '{s.alias()}' (old_id={sub_id})")
            try:
                # unsubscribe from the old group
                self.__socket.unsubscribe(Subscribe.__idBuf(s.id()))
            except Exception as e:
                logger.debug(f"[RESUBSCRIBE] Failed to unsubscribe old id: {e}")

            # subscribe again, update id
            msg = self.__req.createGroup(s.layout(), s.alias(), s.frqDivider()).get()
            s._updateId(msg.id)
            self.__socket.subscribe(Subscribe.__idBuf(s.id()))
            self.__subscriptions[s.id()] = s
            logger.debug(f"[RESUBSCRIBE] Group '{s.alias()}' resubscribed with new id={s.id()}")

        logger.debug(f"[RESUBSCRIBE] Completed resubscription for {len(self.__subscriptions)} groups")

    @staticmethod
    def __idBuf(msg_id):
        return bytes([msg_id & 0xff, (msg_id >> 8) & 0xff, (msg_id >> 16) & 0xff])

    def __complete(self, msg, subscription, socket):
        logger.debug(f"[SUBSCRIBE-COMPLETE] Subscription '{subscription.alias()}' completed with id={msg.id}")
        if subscription._complete(msg):
            id_buf = Subscribe.__idBuf(msg.id)
            socket.subscribe(id_buf)
            self.__subscriptions[msg.id] = subscription
            logger.debug(f"[SUBSCRIBE-COMPLETE] Subscription '{subscription.alias()}' active (id={msg.id}), "
                         f"total active: {len(self.__subscriptions)}")
        else:
            logger.debug(f"[SUBSCRIBE-COMPLETE] Failed to complete subscription '{subscription.alias()}'")
