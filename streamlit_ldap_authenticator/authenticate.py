# Author    : Nathan Chen
# Date      : 13-Mar-2024


import time
import json
import rsa
import jwt
import re
import streamlit as st
from streamlit_cookies_controller import CookieController
from streamlit_rsa_auth_ui import Encryptor, SigninEvent, SignoutEvent, Object, signinForm, signoutForm, getEvent
from datetime import datetime, timedelta
from typing import Union, Callable, Literal, Optional, Dict
from .ldap_authenticate import Connection, LdapAuthenticate
from .exceptions import CookieError
from .configs import LdapConfig, SessionStateConfig, CookieConfig, EncryptorConfig, FormLocation, AttrDict, UserInfos, getForm, getContainer

ss = st.session_state


RegexDomain = re.compile(r'^(.*)\\(.*)$')
RegexEmail = re.compile(r'^[\w\-\.]+@([\w\-]+\.)+[\w\-]{2,4}$')


class Authenticate:
    """ Authentication using active directory.
        Reauthentication method avaliable
        * steamlit session_state: Valid for the current session. if the page is refreshed, session_state will reset thus loose stored data for reauthentication.
        * cookie in the client's browser: Valid until the cookie in the browser is expired

    ## Properties
    session_configs: SessionStateConfig
        Streamlit session state key names.

    cookie_configs: CookieConfig | None
        Optional configuration to encode user information to cookie in the client's browser.
        Reauthorization using cookie in the client's browser feature will be disabled when `None`.
    """
    
    session_configs: SessionStateConfig
    cookie_configs: Optional[CookieConfig]


    def __init__(self,
                 ldap_configs: Union[LdapConfig, AttrDict],
                 session_configs: Union[SessionStateConfig, AttrDict, None] = None,
                 cookie_configs: Union[CookieConfig, AttrDict, None] = None,
                 encryptor_configs: Union[EncryptorConfig, AttrDict, None] = None):
        """ Create a new instance of `Authenticate`

        ## Arguments
        ldap_config: LdapConfig | dict | streamlit.runtime.secrets.AttrDict
            Config for Ldap authentication

        session_configs: SessionStateConfig | dict | streamlit.runtime.secrets.AttrDict | None
            Optional streamlit session state key names.

        cookie_configs: CookieConfig | dict | streamlit.runtime.secrets.AttrDict | None
            Optional configuration to encode user information to cookie in the client's browser.
            Reauthorization using cookie in the client's browser feature will be disabled when `None`.
        """
        self.session_configs = SessionStateConfig.getInstance(session_configs)
        self.cookie_configs = CookieConfig.getInstance(cookie_configs)
        self.ldap_auth = LdapAuthenticate(ldap_configs)

        if cookie_configs is not None:
            self.cookie_manager = CookieController()
        
        encryptor_configs = EncryptorConfig.getInstance(encryptor_configs)
        self.encryptor = Encryptor.load(encryptor_configs.folderPath, encryptor_configs.keyName) if encryptor_configs is not None else None


    # streamlit session_state variables
    def __getUser(self) -> Optional[UserInfos]:
        """ Get the user information from streamlit session_state
            if reauthorization using streamlit session_state is enabled

        ## Returns
        UserInfos | None
            User information if it is avaliable. otherwise, `None`
        """
        if self.session_configs.user not in st.session_state: return None
        user = st.session_state[self.session_configs.user]
        return user if type(user) is dict else None

    def __setUser(self, user: Optional[UserInfos]):
        """ Assign the user information to session_state of streamlit
            if reauthorization using streamlit session_state is enabled

        ## Arguments
        user : UserInfos | None
            User information to assign to streamlit session_state
        """
        if self.session_configs.user is None: return
        else: st.session_state[self.session_configs.user] = user

    def __setRememberMe(self, remember_me: bool):
        st.session_state[self.session_configs.remember_me] = remember_me

    def __getRememberMe(self) -> bool:
        if self.session_configs.remember_me in st.session_state:
            remember_me = st.session_state[self.session_configs.remember_me]
            if type(remember_me) is bool: return remember_me

        self.__setRememberMe(True)
        return True
    

    # For reauthentication using cookie from client's browser
    def __tokenEncode(self, cookie_configs: CookieConfig, user: UserInfos):
        """ Encodes the contents for the reauthentication cookie.

        ## Arguments
        user: UserInfos
            User Information

        ## Returns
        str
            The JWT cookie for passwordless reauthentication.
        """
        exp_date = datetime.utcnow() + timedelta(days=cookie_configs.expiry_days)
        # print(f"ExpiryDate: {exp_date}")
        return jwt.encode({
            'user': user,
            'exp_date': exp_date.timestamp()
        }, cookie_configs.key, algorithm='HS256')
    
    def __tokenDecode(self, cookie_configs: CookieConfig, token) -> Optional[UserInfos]:
        """ Decodes the contents of the reauthentication cookie.

        ## Arguments:
        token: any
            Encoded cookie token

        ## Returns:
        UserInfos | False
            User information if cookie is correct.
            otherwise, return `None`
        """
        try:
            if token is None: raise CookieError('No cookie found')
            if type(token) is not str: raise CookieError('Cookie value is expected to be `str`')
            
            value = jwt.decode(token, cookie_configs.key, algorithms=['HS256'])
            if type(value) is not dict: raise CookieError('Decoded cookie is not dict')

            if 'exp_date' not in value: raise CookieError('exp_date is not found')
            exp_date = value['exp_date']
            if type(exp_date) is not float: raise CookieError('exp_date is not float')
            if exp_date < datetime.utcnow().timestamp(): raise CookieError('Cookie expired')
            
            if 'user' not in value: raise CookieError('user is not found')
            user = value['user']
            if type(user) is not dict: raise CookieError('user is not dict')

            return user
        except Exception as e:
            # print(f'Token decode error: {e}')
            return None

    def __getCookie(self) -> Optional[UserInfos]:
        """ Get the decoded user information from cookie in the client's browser.
            if reauthorization using cookie in the client's browser is enabled

        ## Returns
        UserInfos | None
            user information if it is avaliable and valid, otherwise `None`
        """
        if self.cookie_configs is None: return None

        token = self.cookie_manager.get(self.cookie_configs.name)
        return self.__tokenDecode(self.cookie_configs, token)

    def __setCookie(self, user: Optional[UserInfos]):
        """ Assign the encoded user information to cookie in the client's browser
            if reauthorization using cookie in the client's browser is enabled

        ## Arguments
        user: UserInfos
            User information to assign to cookie in the client's browser
        """
        if user is None: return
        if self.cookie_configs is None: return

        remember_me = self.__getRememberMe()
        if not remember_me: return

        token = self.__tokenEncode(self.cookie_configs, user)
        exp_date = datetime.now() + timedelta(days=self.cookie_configs.expiry_days)
        self.cookie_manager.set(self.cookie_configs.name, token, expires=exp_date)

    def __deleteCookie(self):
        """ Delete the cookie in the client's browser
            if reauthorization using cookie in the client's browser is enabled
        """
        if self.cookie_configs is None: return

        cookies = self.cookie_manager.getAll()
        if self.cookie_configs.name in cookies:
            self.cookie_manager.remove(self.cookie_configs.name)



    def __getLoginConfig(self, config: Optional[Object] = None):
        if config is None: config = {}
        if self.cookie_configs is not None and 'remember' not in config:
            config['remember'] = {}
        
        busy_message = config.get("busy_message")
        config.pop('busy_message', "")
        if type(busy_message) is not str: busy_message = "Logging in..."

        error_icon = config.get("error_icon", None)
        config.pop('error_icon', "")
        if type(error_icon) is not str: error_icon = None

        _location = config.get("location")
        location: FormLocation = 'main' if _location != 'sidebar' else 'sidebar'
        return (config, busy_message, error_icon, location)

    def __createLoginForm(self,
                          additionalCheck: Optional[Callable[[Optional[Connection], UserInfos], Union[Literal[True], str]]] = None,
                          getLoginUserName: Optional[Callable[[str], str]] = None,
                          getInfo: Optional[Callable[[Connection, str], Optional[UserInfos]]] = None,
                          config: Optional[Object] = None,):
        getInfo = getInfo if getInfo is not None else self.getInfo
        getLoginUserName = getLoginUserName if getLoginUserName is not None else self.getLoginUserName
        default = {'remember': self.__getRememberMe()} if self.cookie_configs is not None else None
        (config, busy_message, error_icon, location) = self.__getLoginConfig(config)

        # Create form
        publickey = self.encryptor.publicKeyPem if self.encryptor is not None else None
        result = signinForm(publickey, default, config)
        if result is None: return None
        
        # Check if the result is the same as previous result
        if self.encryptor is not None and type(result) is str: #If it is encrypted
            if self.session_configs.auth_result in ss and ss[self.session_configs.auth_result] == result: return None
            ss[self.session_configs.auth_result] = result
            result = self.encryptor.decrypt(result)
        elif self.encryptor is None and type(result) is dict: #If it is not encrypted
            _json = json.dumps(result)
            if self.session_configs.auth_result in ss and ss[self.session_configs.auth_result] == _json: return None
            ss[self.session_configs.auth_result] = _json
        else: result = None

        event = getEvent(result)
        if type(event) is not SigninEvent: return None

        self.__setRememberMe(event.remember)

        if location == 'sidebar':
            with st.sidebar:
                with st.spinner(busy_message):
                    username = event.username
                    login_name = getLoginUserName(username)
                    result = self.ldap_auth.login(login_name, event.password, lambda conn: getInfo(conn, username), additionalCheck)
                    
                    if type(result) is str: # If it is error message
                        st.error(result, icon=error_icon)
                    elif type(result) is dict:
                        del ss[self.session_configs.auth_result]
                        return result
                    else:
                        st.error(f'Unexpected Return: {result}', icon=error_icon)
        else:
            with st.spinner(busy_message):
                username = event.username
                login_name = getLoginUserName(username)
                result = self.ldap_auth.login(login_name, event.password, lambda conn: getInfo(conn, username), additionalCheck)
                
                if type(result) is str: # If it is error message
                    st.error(result, icon=error_icon)
                elif type(result) is dict:
                    del ss[self.session_configs.auth_result]
                    return result
                else:
                    st.error(f'Unexpected Return: {result}', icon=error_icon)

    def __checkReauthentication(self,
                   user: Optional[UserInfos],
                   additionalCheck: Optional[Callable[[Optional[Connection], UserInfos], Union[Literal[True], str]]] = None):
        """ Check user information during reauthorization

        ## Arguments
        user : Person | None
            Optional user information to check
        connection: Connection | None
            Optional active directory connection
        additionalCheck: ((connection: Connection | None, user: UserInfos) -> (True | str)) | None
            * Function to perform addtional authentication check.
            * Function must return `True` if additional authentication is successful, otherwise must return error message
            * Passing `None` will ignore additional authentication check.

        ## Returns
        bool
            * `True` when user is authorized to use.
            * `None` when user is not UserInfos.
            * `str` error message when authentication fail.
        """
        if type(user) is not dict: return False
        if additionalCheck is None: return True # No additional check is required
        result = additionalCheck(None, user)
        if result != True: return False

        if self.cookie_configs is not None and self.cookie_configs.auto_renewal: self.__setCookie(user)
        return True

    def login(self,
              additionalCheck: Optional[Callable[[Optional[Connection], UserInfos], Union[Literal[True], str]]] = None,
              getLoginUserName: Optional[Callable[[str], str]] = None,
              getInfo: Optional[Callable[[Connection, str], Optional[UserInfos]]] = None,
              config: Optional[Object] = None) -> Optional[UserInfos]:
        """ Authentication using ldap. Reauthorize if it is valid and create login form if authorization fail.

        ## Arguments
        additionalCheck: ((connection: Connection | None, user: UserInfos) -> (True | str)) | None
            * Function to perform addtional authentication check.
            * Function must return `True` if additional authentication is successful, otherwise must return error message
            * Passing `None` will ignore additional authentication check.

        getLoginUserName: ((username: str) -> str) | None
            Optional function to decode the username entered by user to active directory login username

        getInfo: ((conneciton: Connection, username: str) -> UserInfos | None) | None
            Optional function to retrieve user information from active directory

        config: LoginFormConfig | None
            Optional config for login form

        ## Returns
        UserInfos | None
            User information if authentication is successful.
            otherwise, `None`
        """
        # check user authentication if it is found in streamlit session_state
        user = self.__getUser()
        if self.__checkReauthentication(user, additionalCheck):
            return user
            
        # check user authentication if it is found cookie in client's browser
        user = self.__getCookie()
        if self.__checkReauthentication(user, additionalCheck):
            self.__setUser(user)
            return user

        # ask user to log in
        user = self.__createLoginForm(additionalCheck, getLoginUserName, getInfo, config)
        if type(user) is not dict: return None
        self.__setUser(user)
        self.__setCookie(user)
        try: return user
        finally: st.rerun()


    def __getLogoutConfig(self, config: Optional[Object] = None):
        if config is None: config = {}

        # For backward compatibility
        if 'title' not in config and 'message' in config:
            message = config['message']
            config.pop('message', '')
            if type(message) is str:
                config['title'] = { 'text': message }

        _location = config.get("location")
        location: FormLocation = 'sidebar' if _location != 'main' else 'main'
        return (config, location)

    def createLogoutForm(self, config: Optional[Object]) -> None:
        (config, location) = self.__getLogoutConfig(config)

        # Create form
        publickey = self.encryptor.publicKeyPem if self.encryptor is not None else None
        result = signoutForm(publickey, configs=config)
        if result is None: return None

        if self.encryptor is not None and type(result) is str: result = self.encryptor.decrypt(result)

        event = getEvent(result)
        if type(event) is not SignoutEvent: return None

        self.__setUser(None)
        self.__deleteCookie()
        # give sometime for the browser cookie to get deleted
        if location == 'sidebar':
            with st.sidebar:
                with st.spinner():
                    time.sleep(0.1)
        else:
            with st.spinner():
                time.sleep(0.1)
        st.rerun()


    # Default decoding of login user name and get user information from active directory
    def getInfo(self, conn: Connection, username: str) -> Optional[UserInfos]:
        match = RegexEmail.match(username)
        if match is not None: return self.ldap_auth.getInfoByUserPrincipalName(conn, username)

        match = RegexDomain.match(username)
        groups = match.groups() if match is not None else None
        name = username if groups is None else groups[1]
        return self.ldap_auth.getInfoBySamAccountName(conn, name)
    
    def getLoginUserName(self, username: str) -> str:
        match = RegexEmail.match(username)
        if match is not None: return username

        match = RegexDomain.match(username)
        groups = match.groups() if match is not None else None
        domain = self.ldap_auth.config.domain if groups is None else groups[0]
        name = username if groups is None else groups[1]
        return f"{domain}\\{name}"
        
