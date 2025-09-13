#!/usr/bin/python3

#
#   Developer: Alexey Zakharov (alexey.zakharov@vectioneer.com)
#   All rights reserved. Copyright (c) 2016-2025 VECTIONEER.
#
import base64
import hashlib
import json
import tempfile

from motorcortex.reply import Reply
from motorcortex.setup_logger import logger
from motorcortex.state_callback_handler import StateCallbackHandler

import os
from threading import Event  # Add this import
from concurrent.futures import ThreadPoolExecutor
from pynng import Req0, TLSConfig
from enum import Enum


class ConnectionState(Enum):
    CONNECTING = 0
    CONNECTION_OK = 1
    CONNECTION_LOST = 2
    CONNECTION_FAILED = 3
    DISCONNECTING = 4
    DISCONNECTED = 5


class Request(object):

    def __init__(self, protobuf_types, parameter_tree):
        self.__socket = None
        self.__url = None
        self.__connected_event = None
        self.__connected = False
        self.__protobuf_types = protobuf_types
        self.__parameter_tree = parameter_tree
        self.__connection_state = ConnectionState.DISCONNECTED
        self.__pool = ThreadPoolExecutor(max_workers=1)
        self.__callback_handler = StateCallbackHandler()
        logger.debug("Request object initialized with state: DISCONNECTED")

    def url(self):
        return self.__url

    def connect(self, url, **kwargs):
        logger.debug(f"[CONNECT] Starting connection to {url}")
        logger.debug(f"[CONNECT] Current state: {self.__connection_state.name}")

        self.__connection_state = ConnectionState.CONNECTING
        conn_timeout_ms, recv_timeout_ms, certificate, state_update = self.parse(**kwargs)

        logger.debug(f"[CONNECT] Parameters - timeout: {conn_timeout_ms} ms, recv_timeout: {recv_timeout_ms} ms, "
                     f"has_cert: {certificate is not None}, has_state_update: {state_update is not None}")

        if state_update:
            logger.debug("[CONNECT] Starting state callback handler")
            self.__callback_handler.start(state_update)

        self.__url = url
        tls_config = None
        if certificate:
            logger.debug(f"[CONNECT] Using TLS with certificate: {certificate}")
            tls_config = TLSConfig(TLSConfig.MODE_CLIENT, ca_files=certificate)

        logger.debug(f"[CONNECT] Creating Req0 socket with recv_timeout={recv_timeout_ms}ms")
        self.__socket = Req0(recv_timeout=recv_timeout_ms, tls_config=tls_config)
        self.__connected_event = Event()  # Create a fresh event for each connection
        self.__connected = False  # Reset state

        logger.debug("[CONNECT] Socket created, registering callbacks")

        def pre_connect_cb(_pipe):
            logger.debug(f"[CALLBACK] PRE_CONNECT fired - Connection established")
            old_state = self.__connection_state.name
            self.__connected = True
            self.__connection_state = ConnectionState.CONNECTION_OK
            logger.debug(f"[CALLBACK] State transition: {old_state} -> {self.__connection_state.name}")
            self.__callback_handler.notify(self, self.connectionState())
            self.__connected_event.set()
            logger.debug("[CALLBACK] Connection event set, connected=True")

        def post_remove_cb(_pipe):
            logger.debug(f"[CALLBACK] POST_REMOVE fired - Connection lost/failed")
            old_state = self.__connection_state.name

            if self.__connection_state == ConnectionState.DISCONNECTING:
                self.__connection_state = ConnectionState.DISCONNECTED
                logger.debug(f"[CALLBACK] Clean disconnect: {old_state} -> DISCONNECTED")
            elif self.__connection_state == ConnectionState.CONNECTING:
                self.__connection_state = ConnectionState.CONNECTION_FAILED
                logger.debug(f"[CALLBACK] Connection failed: {old_state} -> CONNECTION_FAILED")
            elif self.__connection_state == ConnectionState.CONNECTION_OK:
                self.__connection_state = ConnectionState.CONNECTION_LOST
                logger.debug(f"[CALLBACK] Connection lost: {old_state} -> CONNECTION_LOST")

            self.__connected = False
            self.__callback_handler.notify(self, self.connectionState())
            self.__connected_event.set()
            logger.debug("[CALLBACK] Connection event set, connected=False")

        self.__socket.add_pre_pipe_connect_cb(pre_connect_cb)
        self.__socket.add_post_pipe_remove_cb(post_remove_cb)
        logger.debug("[CONNECT] Callbacks registered successfully")

        logger.debug(f"[CONNECT] Starting dial to {url} (non-blocking)")
        self.__socket.dial(url, block=False)

        logger.debug(f"[CONNECT] Submitting waitForConnection to thread pool with timeout={conn_timeout_ms / 1000.0}s")
        return Reply(self.__pool.submit(self.waitForConnection, self.__connected_event,
                                        conn_timeout_ms / 1000.0, lambda: self.__connected))

    def close(self):
        logger.debug("[CLOSE] Closing connection")
        logger.debug(f"[CLOSE] Current state: {self.__connection_state.name}, connected: {self.__connected}")

        self.__connection_state = ConnectionState.DISCONNECTING
        if self.__connected_event:
            self.__connected = False
            self.__connected_event.set()
            logger.debug("[CLOSE] Connection event set for shutdown")
        else:
            logger.debug("[CLOSE] No connection event to set")

        if self.__socket:
            logger.debug("[CLOSE] Closing socket")
            self.__socket.close()
        else:
            logger.debug("[CLOSE] No socket to close")

        logger.debug("[CLOSE] Stopping callback handler")
        self.__callback_handler.stop()

        logger.debug("[CLOSE] Shutting down thread pool (blocking)")
        self.__pool.shutdown(wait=True)
        logger.debug("[CLOSE] Connection closed successfully")

    def send(self, encoded_msg, do_not_decode_reply=False):
        if self.__socket is not None:
            return Reply(self.__pool.submit(self.__send, self.__socket, encoded_msg,
                                            None if do_not_decode_reply else self.__protobuf_types))
        logger.debug("[SEND] Attempted to send on null socket - connection not established?")
        return None

    def login(self, login, password):
        """Send a login request to the server

            Args:
                login(str): user login
                password(str): user password

            Results:
                Reply(StatusMsg): A Promise, which resolves if login is successful and fails otherwise.
                The returned message has a status code, which indicates the status of the login.

            Examples:
                >>> login_reply = req.login('operator', 'iddqd')
                >>> login_msg = login_reply.get()
                >>> if login_msg.status == motorcortex_msg.OK
                >>>     print('User logged-in')

        """

        login_msg = self.__protobuf_types.createType('motorcortex.LoginMsg')
        login_msg.password = password
        login_msg.login = login

        return self.send(self.__protobuf_types.encode(login_msg))

    def connectionState(self):
        return self.__connection_state

    def getParameterTreeHash(self):
        """Request a parameter tree hash from the server.

            Returns:
                Reply(ParameterTreeMsg): A Promise, which resolves when a parameter tree hash is received or fails
                otherwise. ParameterTreeHashMsg message has a status field to check the status of the operation.

            Examples:
                >>> param_tree_hash_reply = req.getParameterTreeHash()
                >>> value = param_tree_hash_reply.get()

        """

        # getting and instantiating data type from the loaded dict
        param_tree_hash_msg = self.__protobuf_types.createType('motorcortex.GetParameterTreeHashMsg')

        # encoding and sending data
        return self.send(self.__protobuf_types.encode(param_tree_hash_msg))

    def getParameterTree(self):
        """Request a parameter tree from the server.

            Returns:
                Reply(ParameterTreeMsg): A Promise, which resolves when a parameter tree is received or fails
                otherwise. ParameterTreeMsg message has a status field to check the status of the operation.

            Examples:
                >>> param_tree_reply = req.getParameterTree()
                >>> value = param_tree_reply.get()
                >>> parameter_tree.load(value)

        """

        return Reply(self.__pool.submit(self.__getParameterTree,
                                        self.getParameterTreeHash(), self.__protobuf_types, self.__socket))

    def save(self, path, file_name):
        """Request a server to save a parameter tree to a file.

            Args:
                path(str): path where to save
                file_name(str): file name

            Returns:
                Reply(StatusMsg): A promise, which resolves when the save operation is completed,
                fails otherwise.

        """

        param_save_msg = self.__protobuf_types.createType('motorcortex.SaveMsg')
        param_save_msg.path = path
        param_save_msg.file_name = file_name

        return self.send(self.__protobuf_types.encode(param_save_msg))

    def setParameter(self, path, value, type_name=None, offset=0, length=0):
        """Set a new value to a parameter with a given path

            Args:
                path(str): parameter path in the tree
                value(any): new parameter value
                type_name(str): type of the value (by default, resolved automatically)
                offset(int): offset of the elements to update in the destination array, (by default, is 0)
                length(int): number of the elements to update in the destination array, (by default, takes length of the
                value argument)

            Returns:
                  Reply(StatusMsg): A Promise, which resolves when a parameter value is updated or fails otherwise.

            Examples:
                  >>> reply = req.setParameter("root/Control/activateSemiAuto", False)
                  >>> reply.get()
                  >>> reply = req.setParameter("root/Control/targetJointAngles", [0.2, 3.14, 0.4])
                  >>> reply.get()
        """

        if (offset == 0) and (length == 0):
            return self.send(self.__protobuf_types.encode(self.__buildSetParameterMsg(path, value,
                                                                                      type_name, self.__protobuf_types,
                                                                                      self.__parameter_tree)))
        else:
            return self.send(
                self.__protobuf_types.encode(self.__buildSetParameterWithOffsetMsg(offset, length, path, value,
                                                                                   type_name, self.__protobuf_types,
                                                                                   self.__parameter_tree)))

    def setParameterList(self, param_list):
        """Set new values to a parameter list

            Args:
                 param_list([{'path'-`str`,'value'-`any`}]): a list of the parameters which values update

            Returns:
                Reply(StatusMsg): A Promise, which resolves when parameters from the list are updated,
                otherwise fails.

            Examples:
                  >>>  req.setParameterList([
                  >>>   {'path': 'root/Control/generator/enable', 'value': False},
                  >>>   {'path': 'root/Control/generator/amplitude', 'value': 1.4}])

        """

        # instantiating message type
        set_param_list_msg = self.__protobuf_types.createType("motorcortex.SetParameterListMsg")
        # filling with sub messages
        for param in param_list:
            type_name = None
            if "type_name" in param:
                type_name = param["type_name"]
            set_param_list_msg.params.extend([self.__buildSetParameterMsg(param["path"], param["value"],
                                                                          type_name, self.__protobuf_types,
                                                                          self.__parameter_tree)])

        # encoding and sending data
        return self.send(self.__protobuf_types.encode(set_param_list_msg))

    def getParameter(self, path):
        """Request a parameter with description and value from the server.

            Args:
                path(str): parameter path in the tree.

            Returns:
                 Reply(ParameterMsg): Returns a Promise, which resolves when a parameter
                 message is successfully obtained, fails otherwise.

            Examples:
                >>> param_reply = req.getParameter('root/Control/actualActuatorPositions')
                >>> param_full = param_reply.get() # Value and description
        """

        return self.send(self.__protobuf_types.encode(self.__buildGetParameterMsg(path, self.__protobuf_types)))

    def getParameterList(self, path_list):
        """Get description and values of requested parameters.

            Args:
                path_list(list(str)): a list of parameter paths in the tree.

            Returns:
                Reply(ParameterListMsg): A Promise, which resolves when a list of the parameter values is received, fails
                otherwise.

            Examples:
                >>> params_reply = req.getParameter(['root/Control/joint1', 'root/Control/joint2'])
                >>> params_full = params_reply.get() # Values and descriptions
                >>> print(params_full.params)
        """

        # instantiating message type
        get_param_list_msg = self.__protobuf_types.createType('motorcortex.GetParameterListMsg')
        # filling with sub messages
        for path in path_list:
            get_param_list_msg.params.extend([self.__buildGetParameterMsg(path, self.__protobuf_types)])

        # encoding and sending data
        return self.send(self.__protobuf_types.encode(get_param_list_msg))

    def overwriteParameter(self, path, value, force_activate=False, type_name=None):
        """Overwrites actual value of the parameter and depending on the flag forces this value to stay active.
           This method of setting values is useful during the debug and installation process, it is not recommended to use
           this method during normal operation.

            Args:
                path(str): parameter path in the tree
                value(any): new parameter value
                force_activate(bool): forces the new value to stay active. (by default, is set to 'False')
                type_name(str): type of the value (by default, resolved automatically)

            Returns:
                  Reply(StatusMsg): A Promise, which resolves when a parameter value is updated or fails otherwise.

            Examples:
                  >>> reply = req.overwriteParameter("root/Control/dummyBool", False, True)
                  >>> reply.get()
        """

        return self.send(self.__protobuf_types.encode(self.__buildOverwriteParameterMsg(path, value, force_activate,
                                                                                        type_name,
                                                                                        self.__protobuf_types,
                                                                                        self.__parameter_tree)))

    def releaseParameter(self, path):
        """Deactivate the overwrite operation of the parameter.

            Args:
                path(str): parameter path in the tree

            Returns:
                  Reply(StatusMsg): A Promise, which resolves when a parameter value is released or fails otherwise.

            Examples:
                  >>> reply = req.releaseParameter("root/Control/dummyBool")
                  >>> reply.get()
        """

        return self.send(self.__protobuf_types.encode(self.__buildReleaseParameterMsg(path, self.__protobuf_types)))

    def createGroup(self, path_list, group_alias, frq_divider=1):
        """Create a subscription group for a list of the parameters.

            This method is used inside Subscription class, use subscription class instead.

            Args:
                path_list(list(str)): list of the parameters to subscribe to
                group_alias(str): name of the group
                frq_divider(int): frequency divider is a downscaling factor for the group publish rate

            Returns:
                Reply(GroupStatusMsg): A Promise, which resolves when the subscription is complete,
                fails otherwise.
        """

        # instantiating message type
        create_group_msg = self.__protobuf_types.createType('motorcortex.CreateGroupMsg')
        create_group_msg.alias = group_alias
        create_group_msg.paths.extend(path_list if type(path_list) is list else [path_list])
        create_group_msg.frq_divider = frq_divider if frq_divider > 1 else 1
        # encoding and sending data
        return self.send(self.__protobuf_types.encode(create_group_msg))

    def removeGroup(self, group_alias):
        """Unsubscribe from the group.

            This method is used inside Subscription class, use subscription class instead.

            Args:
                group_alias(str): name of the group to unsubscribe from

            Returns:
                Reply(StatusMsg): A Promise, which resolves when the unsubscribe operation is complete,
                fails otherwise.
        """

        # instantiating message type
        remove_group_msg = self.__protobuf_types.createType('motorcortex.RemoveGroupMsg')
        remove_group_msg.alias = group_alias
        # encoding and sending data
        return self.send(self.__protobuf_types.encode(remove_group_msg))

    @staticmethod
    def __buildSetParameterMsg(path, value, type_name, protobuf_types, parameter_tree):
        param_value = None
        if not type_name:
            type_id = parameter_tree.getDataType(path)
            if type_id:
                param_value = protobuf_types.getTypeByHash(type_id)
        else:
            param_value = protobuf_types.createType(type_name)

        if not param_value:
            logger.error("Failed to find encoder for the path: %s type: %s" % (path, type_name))

        # creating type instance
        set_param_msg = protobuf_types.createType("motorcortex.SetParameterMsg")
        set_param_msg.path = path
        # encoding parameter value
        set_param_msg.value = param_value.encode(value)

        return set_param_msg

    @staticmethod
    def __buildSetParameterWithOffsetMsg(offset, length, path, value, type_name, protobuf_types, parameter_tree):
        param_value = None
        if not type_name:
            type_id = parameter_tree.getDataType(path)
            if type_id:
                param_value = protobuf_types.getTypeByHash(type_id)
        else:
            param_value = protobuf_types.createType(type_name)

        if not param_value:
            logger.error("Failed to find encoder for the path: %s type: %s" % (path, type_name))

        # check an offset
        if offset < 0:
            offset = 0

        # check length, if == 0 assign length of the value
        if length < 0:
            length = 0
        if length == 0:
            if hasattr(value, '__len__'):
                length = len(value)
            else:
                length = 1

        # creating type instance
        set_param_msg = protobuf_types.createType("motorcortex.SetParameterMsg")
        set_param_msg.offset.type = 1
        set_param_msg.offset.offset = offset
        set_param_msg.offset.length = length
        set_param_msg.path = path
        # encoding parameter value
        set_param_msg.value = param_value.encode(value)

        return set_param_msg

    @staticmethod
    def __buildGetParameterMsg(path, protobuf_types):
        # getting and instantiating data type from the loaded dict
        get_param_msg = protobuf_types.createType('motorcortex.GetParameterMsg')
        get_param_msg.path = path

        return get_param_msg

    @staticmethod
    def __buildOverwriteParameterMsg(path, value, activate, type_name, protobuf_types, parameter_tree):
        param_value = None
        if not type_name:
            type_id = parameter_tree.getDataType(path)
            if type_id:
                param_value = protobuf_types.getTypeByHash(type_id)
        else:
            param_value = protobuf_types.createType(type_name)

        if not param_value:
            logger.error("Failed to find encoder for the path: %s type: %s" % (path, type_name))

        # creating type instance
        overwrite_param_msg = protobuf_types.createType("motorcortex.OverwriteParameterMsg")
        overwrite_param_msg.path = path
        overwrite_param_msg.activate = activate
        # encoding parameter value
        overwrite_param_msg.value = param_value.encode(value)

        return overwrite_param_msg

    @staticmethod
    def __buildReleaseParameterMsg(path, protobuf_types):
        release_param_msg = protobuf_types.createType('motorcortex.ReleaseParameterMsg')
        release_param_msg.path = path

        return release_param_msg

    @staticmethod
    def parse(conn_timeout_ms=0, timeout_ms=None, recv_timeout_ms=None, certificate=None, login=None, password=None,
              state_update=None):
        if timeout_ms and not conn_timeout_ms:
            conn_timeout_ms = timeout_ms

        return conn_timeout_ms, recv_timeout_ms, certificate, state_update

    @staticmethod
    def __send(req, encoded_msg, protobuf_types):
        try:
            req.send(encoded_msg)
            buffer = req.recv()
            if buffer:
                if protobuf_types:
                    return protobuf_types.decode(buffer)
                else:
                    return buffer
        except Exception as e:
            logger.error(f"[__SEND] Error during send/recv: {type(e).__name__}: {e}")
            raise

        return None

    @staticmethod
    def waitForConnection(event, timeout_sec, is_connected_fn=None):
        logger.debug(f"[WAIT] waitForConnection started with timeout={timeout_sec}s")

        # Wait for the condition to be set or timeout
        if timeout_sec <= 0:
            logger.debug("[WAIT] Waiting indefinitely for connection event")
            result = event.wait()
        else:
            logger.debug(f"[WAIT] Waiting up to {timeout_sec}s for connection event")
            result = event.wait(timeout_sec)

        if not result:
            logger.error(f"[WAIT] Connection timeout after {timeout_sec}s - no event received")
            raise TimeoutError(f"Connection timeout after {timeout_sec}s")

        logger.debug("[WAIT] Event received - checking connection status")

        # Check if we actually connected (event could be set by close() or failure)
        if is_connected_fn:
            connected = is_connected_fn()
            logger.debug(f"[WAIT] Connection status check: connected={connected}")
            if not connected:
                logger.error("[WAIT] Event was set but connection failed or was closed")
                raise ConnectionError("Connection failed or was closed before completion")
        else:
            logger.debug("[WAIT] No connection status check function provided")

        logger.debug("[WAIT] Connection successfully established")
        return True

    @staticmethod
    def __getParameterTree(hash_reply, protobuf_types, socket):
        tree_hash = hash_reply.get()
        path = os.sep.join([tempfile.gettempdir(), "mcx-python-pt-" + str(tree_hash.hash)])
        tree = Request.loadParameterTreeFile(path, protobuf_types)
        if tree:
            logger.debug('Found parameter tree in the cache')
            return tree
        else:
            logger.debug('Failed to find parameter tree in the cache')

        # getting and instantiating data type from the loaded dict
        param_tree_msg = protobuf_types.createType('motorcortex.GetParameterTreeMsg')
        handle = Request.__send(socket, protobuf_types.encode(param_tree_msg), protobuf_types)

        # encoding and sending data
        return Request.saveParameterTreeFile(path, handle)

    @staticmethod
    def saveParameterTreeFile(path, parameter_tree):
        logger.debug('Saved parameter tree to the cache')
        json_data = {}
        base64_data = base64.b64encode(parameter_tree.SerializeToString())
        json_data['md5'] = hashlib.md5(base64_data).hexdigest()
        json_data['data'] = base64_data.decode('utf-8')

        with open(path, "w") as outfile:
            outfile.write(json.dumps(json_data))

        return parameter_tree

    @staticmethod
    def loadParameterTreeFile(path, protobuf_types):
        logger.debug('Loaded parameter tree from the cache')
        param_tree_hash_msg = None
        if os.path.exists(path):
            with open(path, "r") as outfile:
                json_data = json.load(outfile)

            if json_data:
                if "md5" in json_data and "data" in json_data:
                    if hashlib.md5(json_data['data'].encode()).hexdigest() == json_data['md5']:
                        param_tree_hash_msg = protobuf_types.createType('motorcortex.ParameterTreeMsg')
                        tree_raw = base64.b64decode(json_data['data'])
                        param_tree_hash_msg.ParseFromString(tree_raw)

        return param_tree_hash_msg
