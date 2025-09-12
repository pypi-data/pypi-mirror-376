import json


class EngineAppApi:
    """
    API class for interacting with Qlik Sense engine's app-related functionalities, such as script management,
    reloading, and object creation.

    Methods:
        get_script(doc_handle): Retrieves the script of the app.
        set_script(doc_handle, script): Sets the script of the app.
        do_reload(doc_handle, param_list): Triggers a reload of the app.
        do_reload_ex(doc_handle, param_list): Triggers an extended reload of the app.
        get_app_layout(doc_handle): Retrieves the layout structure of the app.
        get_object(doc_handle, object_id): Retrieves a specific object from the app.
        get_field(doc_handle, field_name, state_name): Retrieves a specific field from the app.
        create_object(doc_handle, q_id, q_type, struct_name, ob_struct): Creates a new object in the app.
    """

    def __init__(self, socket):
        """
        Initializes the EngineAppApi with a given socket connection.

        Parameters:
            socket (object): The socket connection to the Qlik Sense engine.
        """
        self.engine_socket = socket

    def get_script(self, doc_handle: int):
        """
        Retrieves the script of the app identified by the document handle.

        Parameters:
            doc_handle (int): The handle identifying the app document.

        Returns:
            str: The script of the app (qScript). In case of an error, returns the error information.
        """
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": doc_handle, "method": "GetScript", "params": []})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response['result']['qScript']
        except KeyError:
            return response['error']

    def set_script(self, doc_handle: int, script):
        """
        Sets the script of the app identified by the document handle.

        Parameters:
            doc_handle (int): The handle identifying the app document.
            script (str): The script content to be set.

        Returns:
            dict: The result of setting the script. In case of an error, returns the error information.
        """
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": doc_handle, "method": "SetScript", "params": [script]})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response['result']
        except KeyError:
            return response['error']

    def do_reload(self, doc_handle: int, param_list=[]):
        """
        Triggers a reload of the app identified by the document handle.

        Parameters:
            doc_handle (int): The handle identifying the app document.
            param_list (list): A list of parameters for the reload operation. Default is an empty list.

        Returns:
            dict: The result of the reload operation. In case of an error, returns the error information.
        """
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": doc_handle, "method": "DoReload", "params": param_list})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response['result']
        except KeyError:
            return response['error']

    def do_reload_ex(self, doc_handle: int, param_list={}):
        """
        Triggers an extended reload of the app identified by the document handle.

        Parameters:
            doc_handle (int): The handle identifying the app document.
            param_list (list): A list of parameters for the extended reload operation. Default is an empty list.

        Returns:
            dict: The result of the extended reload operation. In case of an error, returns the error information.
        """
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": doc_handle, "method": "DoReloadEx",
                          "params": {"qParams": param_list}})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response["result"]["qResult"]
        except KeyError:
            return response['error']

    def get_app_layout(self, doc_handle: int):
        """
        Retrieves the layout structure of the app identified by the document handle.

        Parameters:
            doc_handle (int): The handle identifying the app document.

        Returns:
            dict: The layout structure of the app (qLayout). In case of an error, returns the error information.
        """
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": doc_handle, "method": "GetAppLayout", "params": []})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response['result']['qLayout']
        except KeyError:
            return response['error']

    def get_object(self, app_handle: int, object_id: str):
        """
        Retrieves a specific object from the app identified by the document handle.

        Parameters:
            app_handle (int): The handle identifying the app document.
            object_id (str): The ID of the object to retrieve.

        Returns:
            dict: The retrieved object (qReturn). In case of an error, returns the error information.
        """
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": app_handle, "method": "GetObject",
                          "params": {"qId": object_id}})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response['result']['qReturn']
        except KeyError:
            return response['error']


    def get_objects(self, app_handle: int, options: dict):
        """
        Retrieves a specific object from the app identified by the document handle.

        Parameters:
            app_handle (int): The handle identifying the app document.
            object_id (str): The ID of the object to retrieve.

        Returns:
            dict: The retrieved object (qReturn). In case of an error, returns the error information.
        """
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": app_handle, "method": "GetObjects",
                          "params": {"qOptions": options}})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response["result"]["qList"]
        except KeyError:
            return response["error"]


    def get_field(self, doc_handle: int, field_name, state_name=""):
        """
        Retrieves a specific field from the app identified by the document handle.

        Parameters:
            doc_handle (int): The handle identifying the app document.
            field_name (str): The name of the field to retrieve.
            state_name (str): The name of the alternate state. Default state is current selections.

        Returns:
            dict: Object interface.
        """
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": doc_handle, "method": "GetField",
                          "params": {"qFieldName": field_name, "qStateName": state_name}})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response['result']['qReturn']
        except KeyError:
            return response['error']

    def create_object(self, doc_handle: int, prop):
        """
        Creates a new object in the app identified by the document handle.

        Parameters:
            doc_handle (int): The handle identifying the app document.
            prop (dict): Information about the object.

        Returns:
            dict: The created object (qReturn). In case of an error, returns the error information.
        """
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "method": "CreateObject", "handle": doc_handle,
                          "params": {"qProp": prop}})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response['result']['qReturn']
        except KeyError:
            return response['error']

    # AddAlternateState method: Create an alternate state in app  # NOQA
    # You can create multiple states within a Qlik Sense app and apply these states to specific objects within the app.  # NOQA
    # Objects in a given state are not affected by user selections in the other states.  # NOQA
    # Call GetAppLayout() afterwards to get the latest states
    def add_alternate_state(self, doc_handle: int, state_name):
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": doc_handle, "method": "AddAlternateState",
                          "params": [state_name]})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response['result']
        except KeyError:
            return response['error']

    # AddFieldFromExpression method: Adds a field on the fly. !! The expression of a field on the fly is persisted but  # NOQA
    # not its values. !!
    def add_field_from_expression(self, doc_handle: int, field_name, expr_value):
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": doc_handle, "method": "AddFieldFromExpression",
                          "params": [field_name, expr_value]})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response['result']
        except KeyError:
            return response['error']

    # CheckExpression method: Checks whether an expression is valid or not
    # qErrorMsg is empty if it's valid
    def check_expression(self, doc_handle: int, expr_value):
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": doc_handle, "method": "CheckExpression",
                          "params": [expr_value]})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response['result']
        except KeyError:
            return response['error']

    # CheckScriptSyntax method: Checks whether a load script is valid or not
    # Used AFTER doing SetScript method
    # errors are displayed in an array discussing positions of characters in script where failing  # NOQA
    def check_script(self, doc_handle: int):
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": doc_handle, "method": "CheckScriptSyntax", "params": {}})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response['result']
        except KeyError:
            return response['error']

    def clear_all(self, doc_handle: int, locked_also=False, alt_state=""):
        """
        Clear selections in fields for current state. Locked fields are not cleared by default.

        Parameters:
            doc_handle (int): The handle identifying the app document.
            locked_also (bool): When true, clears the selection for locked fields.
            alt_state (str): Alternate state name. When set, applies to alternate state instead of current.
        """
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": doc_handle, "method": "ClearAll",
                          "params": {"qLockedAlso": locked_also, "qStateName": alt_state}})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response['result']
        except KeyError:
            return response['error']

    # CreateConnection method: Creates a connection. A connection indicates from which data source, the data should  # NOQA
    # be taken. The connection can be: an ODBC connection, OLEDB connection, a custom connection, a folder connection  # NOQA
    #  (lib connection), an internet connection, Single Sign-On
    def create_connection(self, doc_handle: int, connect_name, connect_string, connect_type, user_name, password,
                          mod_date="", meta="", sso_passthrough="LOG_ON_SERVICE_USER"):
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": doc_handle, "method": "CreateConnection",
                          "params": [{"qName": connect_name, "qMeta": meta, "qConnectionString": connect_string,
                                      "qType": connect_type}]})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response['result']
        except KeyError:
            return response['error']

    # CreateDimension method: Creates a master dimension.
    # A Master Dimension is stored in the library of an app and can be used in many objects. Several generic objects  # NOQA
    # can contain the same dimension.
    # Parameters:
    # qProp (MANDATORY: send dim_id, dim_title, dim_grouping, dim_field, dim_label, meta_def (optional)  # NOQA
    def create_dimension(self, doc_handle: int, prop):
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": doc_handle, "method": "CreateDimension",
                          "params": {"qProp": prop}})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response["result"]["qReturn"]
        except KeyError:
            return response['error']

    # DestroyDimension method: Removes a dimension
    def destroy_dimension(self, doc_handle: int, dim_id):
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": doc_handle, "method": "DestroyDimension",
                          "params": {"qId": dim_id}})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response["result"]["qSuccess"]
        except KeyError:
            return response["error"]

    # DestroyMeasure method: Removes a measure
    def destroy_measure(self, doc_handle: int, measure_id):
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": doc_handle, "method": "DestroyDimension",
                          "params": [{measure_id}]})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response['result']
        except KeyError:
            return response['error']

    # DestroyObject method: Removes an app object. The children of the object (if any) are removed as well.  # NOQA
    def destroy_object(self, doc_handle: int, object_id):
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": doc_handle, "method": "DestroyObject",
                          "params": [{object_id}]})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response['result']
        except KeyError:
            return response['error']

    # DestroySessionObject method: Removes a session object. The children of the object (if any) are removed as well.  # NOQA
    def destroy_session_object(self, doc_handle: int, object_id):
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": doc_handle, "method": "DestroySessionObject",
                          "params": [{object_id}]})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response['result']
        except KeyError:
            return response['error']

    # DestroySessionVariable method: Removes an transient variable.
    def destroy_session_variable(self, doc_handle: int, var_id):
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": doc_handle, "method": "DestroySessionVariable",
                          "params": [{var_id}]})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response['result']
        except KeyError:
            return response['error']

    # DestroyVariableById method: Removes a varable..
    # Script-defined variables cannot be removed using the DestroyVariableById method or the  # NOQA
    # DestroyVariableByName method.
    def destroy_variable_by_id(self, doc_handle: int, var_name):
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": doc_handle, "method": "DestroyVariableById",
                          "params": [{var_name}]})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response['result']
        except KeyError:
            return response['error']

    # CreateMeasure method: Creates a master dimension.
    # A Master Dimension is stored in the library of an app and can be used in many objects. Several generic objects  # NOQA
    # can contain the same dimension.
    # Parameters:
    # qProp (MANDATORY: send dim_id, dim_title, dim_grouping, dim_field, dim_label, meta_def (optional)  # NOQA
    def create_measure(self, doc_handle: int, prop):
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": doc_handle, "method": "CreateMeasure",
                          "params": {"qProp": prop}})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response["result"]["qReturn"]
        except KeyError:
            return response['error']

    # CreateObject method: Creates a generic object at app level.  It is possible to create a generic object that is  # NOQA
    # linked to another object. A linked object is an object that points to a linking object. The linking object is  # NOQA
    # defined in the properties of the linked object (in qExtendsId). The linked object has the same properties as the  # NOQA
    # linking object.
    # TODO: Come back to this - Very important that it is well understood how we want to create objects / datasets from  # NOQA
    # python in app
    # Convert hypercube to dict or some other data set

    # CreateSession Object method: Creates a generic object at app level.  It is possible to create a generic object that is linked to another object.  # NOQA
    # A linked object is an object that points to a linking object. The linking object is defined in the properties of the linked object (in qExtendsId).  # NOQA
    # The linked object has the same properties as the linking object.
    # TODO: Come back to this - Very important that it is well understood how we want to create objects / datasets from  # NOQA
    #  python in app
    # Convert hypercube to dict or some other data set

    # CreateSessionVariable method:
    # A variable in Qlik Sense is a named entity, containing a data value. This value can be static or be the result of a calculation.  # NOQA
    # A variable acquires its value at the same time that the variable is created or after when updating the properties of the variable.  # NOQA
    # Variables can be used in bookmarks and can contain numeric or alphanumeric data.  # NOQA
    # Any change made to the variable is applied everywhere the variable is used.  # NOQA
    # When a variable is used in an expression, it is substituted by its value or the variable's definition.  # NOQA
    # ### Example:  The variable x contains the text string Sum(Sales). In a chart, you define the expression $(x)/12.  # NOQA
    # The effect is exactly the same as having the chart expression Sum(Sales)/12. However, if you change the value of the variable x to Sum(Budget),  # NOQA
    # the data in the chart are immediately recalculated with the expression interpreted as Sum(Budget)/12.  # NOQA
    def create_session_variable(self, app_handle: int, var_id="", var_name="", var_comment="", var_def=""):
        msg = json.dumps(
            {"jsonrpc": "2.0", "id": 0, "handle": app_handle,
             "method": "CreateSessionVariable", "params": [{
                "qInfo": {
                    "qId": var_id,
                    "qType": "Variable"
                },
                "qName": var_name,
                "qComment": var_comment,
                "qDefinition": var_def
                }]
             })
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response['result']
        except KeyError:
            return response['error']

    # CreateVariable method:
    # A variable in Qlik Sense is a named entity, containing a data value. This value can be static or be the result of a calculation.   # NOQA
    # A variable acquires its value at the same time that the variable is created or after when updating the properties of the variable.   # NOQA
    # Variables can be used in bookmarks and can contain numeric or alphanumeric data.   # NOQA
    # Any change made to the variable is applied everywhere the variable is used.  # NOQA
    # When a variable is used in an expression, it is substituted by its value or the variable's definition.  # NOQA
    # ### Example:  The variable x contains the text string Sum(Sales). In a chart, you define the expression $(x)/12.   # NOQA
    # The effect is exactly the same as having the chart expression Sum(Sales)/12.   # NOQA
    # However, if you change the value of the variable x to Sum(Budget),
    # the data in the chart are immediately recalculated with the expression interpreted as Sum(Budget)/12.  # NOQA
    def create_variable(self, app_handle: int, var_id="", var_name="", var_comment="", var_def=""):
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": app_handle,
                          "method": "CreateVariable", "params": [{
                                "qInfo": {
                                    "qId": var_id,
                                    "qType": "Variable"
                                },
                                "qName": var_name,
                                "qComment": var_comment,
                                "qDefinition": var_def
                            }]
                          })
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response['result']
        except KeyError:
            return response['error']

        # DoReload method: Reloads the script that is set in an app.
        # Parameters:
        # qMode (optional): Error handling mode (Integer).. 0: for default mode,   # NOQA
        # 1: for ABEND; the reload of the script ends if an error occurs.,
        # 2: for ignore; the reload of the script continues even if an error is detected in the script.  # NOQA
        # qPartial (optional): Set to true for partial reload, The default value is false.  # NOQA
        # qDebug (optional): Set to true if debug breakpoints are to be honored. The execution of the script will be in debug mode. The default value is false.  # NOQA

    # Original do_reload function
    # def do_reload(self, doc_handle, reload_mode=0,
    #               partial_mode=False, debug_mode=False):
    #     msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": doc_handle,
    #                       "method": "DoReload",
    #                       "params": [reload_mode, partial_mode, debug_mode]})
    #     response = json.loads(self.engine_socket.send_call(self.engine_socket,  # NOQA
    #                                                        msg)
    #                           )
    #     try:
    #         return response['result']
    #     except KeyError:
    #         return response['error']

    # DoSave method: Saves an app - All objects and data in the data model are saved.  # NOQA
    # Desktop only - server auto saves
    def do_save(self, doc_handle: int, file_name=""):
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": doc_handle, "method": "DoSave",
                          "params": {"qFileName": file_name}})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response['result']
        except KeyError:
            return response['error']

    # Evaluate method: Evaluates an expression as a string. (Actually uses EvaluateEx, which is better for giving the data type back to python)  # NOQA
    # Parameters: qExpression
    def expr_eval(self, app_handle: int, expr):
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": app_handle, "method": "EvaluateEx",
                          "params": {"qExpression": expr}})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response['result']
        except KeyError:
            return response['error']

    # GetAllInfos method: Get the identifier and the type of any generic object in an app by using the GetAllInfos method.  # NOQA
    def get_all_infos(self, app_handle: int):
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": app_handle, "method": "GetAllInfos", "params": []})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response['result']['qInfos']
        except KeyError:
            return response['error']

    # GetAppProperties method: Gets the properties of an app.
    def get_app_properties(self, doc_handle: int):
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": doc_handle, "method": "GetAppProperties", "params": []})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response['result']['qProp']
        except KeyError:
            return response['error']

    # GetConnection method: Retrieves a connection and returns: The creation time of the connection, The identifier of  # NOQA
    # the connection, The type of the connection, The name of the connection, The connection string  # NOQA
    def get_connection(self, doc_handle: int, connection_id):
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": doc_handle, "method": "GetConnection",
                          "params": [connection_id]})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response['result']['qConnection']
        except KeyError:
            return response['error']

    # GetConnections method: Lists the connections in an app
    def get_connections(self, doc_handle: int):
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": doc_handle, "method": "GetConnections", "params": []})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response['result']['qConnections']
        except KeyError:
            return response['error']

    # GetDatabaseInfo: Get information about an ODBC, OLEDB or CUSTOM connection  # NOQA
    def get_db_info(self, doc_handle: int, connection_id):
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": doc_handle, "method": "GetDatabaseInfo",
                          "params": [connection_id]})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response['result']['qInfo']
        except KeyError:
            return response['error']

    # GetDatabaseOwners: List the owners of a database for a ODBC, OLEDB or CUSTOM connection  # NOQA
    def get_db_owners(self, doc_handle: int, connection_id):
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": doc_handle, "method": "GetDatabaseOwners",
                          "params": [connection_id]})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response['result']['qOwners']
        except KeyError:
            return response['error']

    # GetDatabases: List the databases of a ODBC, OLEDB or CUSTOM connection
    def get_databases(self, doc_handle: int, connection_id):
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": doc_handle, "method": "GetDatabases",
                          "params": [connection_id]})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response['result']['qDatabases']
        except KeyError:
            return response['error']

    # GetDatabaseTableFields: List the fields in a table for a ODBC, OLEDB or CUSTOM connection  # NOQA
    # Parameters taken are: connection_id (mandatory), db_name, db_owner, table_name (mandatory)  # NOQA
    def get_db_table_fields(self, doc_handle: int, connection_id, db_name="", db_owner="", table_name=""):
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": doc_handle, "method": "GetDatabaseTableFields",
                          "params": [connection_id, db_name, db_owner, table_name]})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response['result']['qFields']
        except KeyError:
            return response['error']

    # GetDatabaseTablePreview: Preview the data in the fields in a table for a ODBC, OLEDB or CUSTOM connection  # NOQA
    # Parameters taken are: connection_id (mandatory), db_name, db_owner, table_name (mandatory)  # NOQA
    def get_db_table_preview(self, doc_handle: int, connection_id, db_name="", db_owner="", table_name=""):
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": doc_handle, "method": "GetDatabaseTablePreview",
                          "params": [connection_id, db_name, db_owner, table_name]})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response['result']
        except KeyError:
            return response['error']

    # GetDatabaseTables: List the tables in a database for a specific owner and for a ODBC, OLEDB or CUSTOM connection  # NOQA
    # Parameters taken are: connection_id (mandatory), db_name, db_owner
    def get_db_tables(self, doc_handle: int, connection_id, db_name="", db_owner=""):
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": doc_handle, "method": "GetDatabaseTables",
                          "params": [connection_id, db_name, db_owner]})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response['result']['qTables']
        except KeyError:
            return response['error']


    # GetEmptyScript: Creates a script that contains one section. This section contains Set statements that give  # NOQA
    # localized information from the regional settings of the computer.
    # Parameter: none
    def get_empty_script(self, doc_handle: int):
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": doc_handle, "method": "GetEmptyScript", "params": []})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response['result']['qReturn']
        except KeyError:
            return response['error']

    # GetFieldDescription: Get the description of a field
    # Parameter: field name
    def get_field_descr(self, doc_handle: int, field_name):
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": doc_handle, "method": "GetFieldDescription",
                          "params": {"qFieldName": field_name}})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response['result']['qReturn']
        except KeyError:
            return response['error']

        # GetFileTableFields method: Lists the fields of a table for a folder connection.  # NOQA
        # Parameters:
        # qConnectionId (MANDATORY): Identifier of the connection.
        # qRelativePath: Path of the connection file
        # qDataFormat: Type of the file
        # qTable (MOSTLY MANDATORY): Name of the table ***This parameter must be set for XLS, XLSX, HTML and XML files.***  # NOQA
    def get_file_table_fields(self, doc_handle: int, connection_id,
                              rel_path="", data_fmt="", table_name=""):
        msg = json.dumps(
            {"jsonrpc": "2.0", "id": 0, "handle": doc_handle,
             "method": "GetFileTableFields", "params": [
                connection_id, rel_path, {"qType": data_fmt}, table_name]})
        response = json.loads(self.engine_socket.send_call(self.engine_socket,
                                                           msg)
                              )
        try:
            return response['result']
        except KeyError:
            return response['error']

        # GetFileTablePreview method: Preview the data in the fields of a table for a folder connection.  # NOQA
        # Parameters:
        # qConnectionId (MANDATORY): Identifier of the connection.
        # qRelativePath: Path of the connection file
        # qDataFormat: Type of the file
        # qTable (MOSTLY MANDATORY): Name of the table ***This parameter must be set for XLS, XLSX, HTML and XML files.***  # NOQA
    def get_file_table_preview(self, doc_handle: int, connection_id, rel_path="", data_fmt="", table_name=""):
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": doc_handle, "method": "GetFileTablePreview",
                          "params": [connection_id, rel_path, {"qType": data_fmt}, table_name]})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response['result']
        except KeyError:
            return response['error']

        # GetFileTablesEx method: List the tables and fields of a XML file or from a JSON file, for a folder connection  # NOQA
        # Parameters:
        # qConnectionId (MANDATORY): Identifier of the connection.
        # qRelativePath: Path of the connection file
        # qDataFormat: Type of the file (XML, JSON)
        # qTable (MOSTLY MANDATORY): Name of the table ***This parameter must be set for XLS, XLSX, HTML and XML files.***  # NOQA
    def get_file_table_ex(self, doc_handle: int, connection_id,
                          rel_path="", data_fmt=""):
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": doc_handle, "method": "GetFileTablesEx",
                          "params": [connection_id, rel_path, {"qType": data_fmt}]})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response['result']
        except KeyError:
            return response['error']

        # GetFileTables method: Lists the tables for a folder connection.
        # Parameters:
        # qConnectionId (MANDATORY): Identifier of the connection.
        # qRelativePath: Path of the connection file
        # qDataFormat: Type of the file (XML, JSON)
    def get_file_tables(self, doc_handle: int, connection_id, rel_path="", data_fmt=""):
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": doc_handle, "method": "GetFileTables",
                          "params": [connection_id, rel_path, {"qType": data_fmt}]})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response['result']
        except KeyError:
            return response['error']

    # GetFolderItemsForConnection method: List the items for a folder connection  # NOQA
    # Parameter: connection_id
    def get_folder_items_for_connection(self, doc_handle: int, connection_id):
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": doc_handle, "method": "GetFolderItemsForConnection",
                          "params": [connection_id]})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response['result']
        except KeyError:
            return response['error']

    # GetAllInfos method: Get the identifier and the type of any generic object in an app by using the GetAllInfos method.  # NOQA
    def get_lineage(self, doc_handle: int):
        """
        Gets the lineage information of the app. The lineage information includes the LOAD and STORE statements from
        the data load script associated with this app.

        Parameters:
            doc_handle (int): The handle identifying the app document.

        Returns:
            list: Information about the lineage of the data in the app.
        """
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": doc_handle, "method": "GetLineage", "params": {}})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response['result']['qLineage']
        except KeyError:
            return response['error']

    def create_session_object(self, doc_handle: int, prop):
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": doc_handle, "method": "CreateSessionObject",
                          "params": {"qProp": prop}})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response['result']['qReturn']
        except KeyError:
            return response['error']

    def get_set_analysis(self, doc_handle: int, state_name="", bookmark_id=""):
        msg = json.dumps({"jsonrpc": "2.0", "id": 3, "handle": doc_handle, "method": "GetSetAnalysis",
                          "params": {"qStateName": state_name, "qBookmarkId": bookmark_id}})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response['result']['qSetExpression']
        except KeyError:
            return response['error']

    def apply_bookmark(self, doc_handle, bookmark_id):
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": doc_handle, "method": "ApplyBookmark",
                          "params": [bookmark_id]})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response['result']
        except KeyError:
            return response['error']

    def get_variable_by_id(self, doc_handle: int, variable_id):
        """
        Gets the handle of a variable.

        Parameters:
            doc_handle (int): The handle identifying the document.
            variable_id (str): The id of the variable.

        Returns:
            dict: The handle of the generic variable.
        """
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": doc_handle, "method": "GetVariableById",
                          "params": {"qId": variable_id}})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response['result']['qReturn']
        except KeyError:
            return response['error']


    def create_bookmark(self, doc_handle: int, prop: dict):
        """
        Creates a bookmark.

        Parameters:
            doc_handle (int): The handle identifying the document.
            prop (dict): Bookmark properties.

        Returns:
            dict: The handle of the generic bookmark.
        """
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": doc_handle, "method": "CreateBookmark",
                          "params": {"qProp": prop}})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response['result']['qReturn']
        except KeyError:
            return response['error']


    def get_bookmarks(self, doc_handle: int, options: dict):
        """
        Returns all bookmarks compatible with options.

        Parameters:
            doc_handle (int): The handle identifying the document.
            qOptions (dict): Bookmark type filter and requested properties.

        Returns:
            list: The resulting list.
        """
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": doc_handle, "method": "GetBookmarks",
                          "params": {"qOptions": options}})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response['result']
        except KeyError:
            return response['error']


    def get_bookmark(self, app_handle: int, bookmark_id: str):
        """
        Retrieves a specific bookmark from the app identified by the document handle.

        Parameters:
            app_handle (int): The handle identifying the app document.
            bookmark_id (str): The ID of the bookmark to retrieve.

        Returns:
            dict: The retrieved object (qReturn). In case of an error, returns the error information.
        """
        msg = json.dumps({"jsonrpc": "2.0", "id": 0, "handle": app_handle, "method": "GetBookmark",
                          "params": {"qId": bookmark_id}})
        response = json.loads(self.engine_socket.send_call(self.engine_socket, msg))
        try:
            return response['result']['qReturn']
        except KeyError:
            return response['error']