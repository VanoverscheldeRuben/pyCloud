#!/usr/bin/env python

'''
This class is the main class that is used for a server.

@Author: Ruben Vanoverschelde
@Date: 19/12/2016
'''
class Server(object):
    def __init__(self, host="127.0.0.1", port=None, username=None, password=None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password

    '''
    Function for setting/adjusting the credentials.

    @Param: username, password
    @Author: Ruben Vanoverschelde
    @Date: 19/12/2016
    '''
    def setCredentials(self, username, password):
        self.setUsername(username)
        self.setPassword (assword)

    '''
    Getter for the host address.

    @Return: host
    @Author: Ruben Vanoverschelde
    @Date: 19/12/2016
    '''
    def getHost(self):
        return self.host

    '''
    Setter for the host address.

    @Param: host
    @Author: Ruben Vanoverschelde
    @Date: 19/12/2016
    '''
    def setHost(self, host):
        self.host = host

    '''
    Getter for the port.

    @Return: port
    @Author: Ruben Vanoverschelde
    @Date: 19/12/2016
    '''
    def getPort(self):
        return self.port

    '''
    Setter for the port.

    @Param: port
    @Author: Ruben Vanoverschelde
    @Date: 19/12/2016
    '''
    def setPort(self, port):
        self.port = port

    '''
    Getter for the username.

    @Return: username
    @Author: Ruben Vanoverschelde
    @Date: 19/12/2016
    '''
    def getUsername(self):
        return self.username

    '''
    Setter for the username.

    @Param: username
    @Author: Ruben Vanoverschelde
    @Date: 19/12/2016
    '''
    def setUsername(self, username):
        self.username = username

    '''
    Getter for the password.

    @Return: password
    @Author: Ruben Vanoverschelde
    @Date: 19/12/2016
    '''
    def getPassword(self):
        return self.password

    '''
    Setter for the password.

    @Param: password
    @Author: Ruben Vanoverschelde
    @Date: 19/12/2016
    '''
    def setPassword(self, password):
        self.password = password

    '''
    Summarizes server info. (sensitive information won't be given)

    @Author: Ruben Vanoverschelde
    @Date: 19/12/2016
    '''
    def toString(self):
        userInfo = "set"
        if self.username == None:
            userInfo = "not set"

        passInfo = "set"
        if self.password == None:
            passInfo = "not set"

        return "Host Address:\t" + str(self.host) + "\nUsername:\t" + userInfo + "\nPassword:\t" + passInfo