# Author    : Nathan Chen
# Date      : 16-Feb-2024


import time
import streamlit as st
import extra_streamlit_components as stx
import jwt
from streamlit.type_util import LabelVisibility
from datetime import datetime, timedelta
from typing import Union, Callable, Literal, Type
from ldap_authenticate import LdapConfig, Connection, Person, LdapAuthenticate
from exceptions import CookieError

FormLocation = Literal['main', 'sidebar']
def getForm(key: str, location: FormLocation):
    if location == 'main': return st.form(key)
    elif location == 'sidebar': return st.sidebar.form(key)
    else: raise ValueError("Location must be one of 'main' or 'sidebar'")

def getContainer(location: FormLocation):
    if location == 'main': return st.container()
    elif location == 'sidebar': return st.sidebar.container()
    else: raise ValueError("Location must be one of 'main' or 'sidebar'")


class TextInputConfig:
    """ Config for text input
    
    ## Properties:
    label: str | None
        Label of the text input. if None, lable of the text input will `collapsed`
    help: str | None
        An optional tooltip that gets displayed next to the input.
    placeholder: str | None
        An optional string displayed when the text input is empty. If None, no text is displayed.
    """
    label: Union[str, None]
    help: Union[str, None]
    placeholder: Union[str, None]

    def __init__(self,
                 label: Union[str, None] = None,
                 help: Union[str, None] = None,
                 placeholder: Union[str, None] = None):
        """ Create an instance of `TextInputConfig` object
        """
        self.label = label
        self.help = help
        self.placeholder = placeholder

    def get_label(self, default_label: str):
        """ Get the text input label
        """
        return default_label if self.label is None else self.label

    def get_label_visibility(self) -> LabelVisibility:
        """ Get the text input label visibliity
        """
        return 'visible' if self.label is not None else 'collapsed'


class ButtonConfig:
    """ Config for button

    ## Properties
    lable: str
        Label of the button
    help: str | None
        An optional tooltip that gets displayed next to the button.
    """
    label: str
    help: Union[str, None]

    def __init__(self,
                 label: str,
                 help: Union[str, None] = None) -> None:
        """ Create an instance of `ButtonConfig` object
        """
        self.label = label
        self.help = help


class LoginFormConfig:
    """ Config for login form
    
    ## Properties
    location: 'main' | 'sidebar'
        location of login form to render
    title: str | None
        form title. None will not show the title
    username: TextInputConfig
        Config for username input
    password: TextInputConfig
        Config for password input
    sign_in: ButtonConfig
        Config for sign-in button
    error_icon: str
        Icon for error message
    wrong_message: str
        Message for wrong username or password
    """
    location: FormLocation
    title: Union[str, None]
    username: TextInputConfig
    password: TextInputConfig
    sign_in: ButtonConfig
    error_icon: Union[str, None]
    wrong_message: str

    def __init__(self,
                 location: FormLocation = 'main',
                 title: Union[str, None] = 'User Log In',
                 username: TextInputConfig = TextInputConfig('User Name', placeholder='Your nt login username'),
                 password: TextInputConfig = TextInputConfig('Password', placeholder='Your nt login password'),
                 sign_in: ButtonConfig = ButtonConfig('🔑 Sign In'),
                 error_icon: Union[str, None] = '❌',
                 wrong_message: str = 'Wrong username or password.'):
        self.location = location
        self.title = title
        self.username = username
        self.password = password
        self.sign_in = sign_in
        self.error_icon = error_icon
        self.wrong_message = wrong_message


class LogoutFormConfig:
    """ Config for logout form

    ## Properties
    location: 'main' | 'sidebar'
        location of login form to render
    show_welcome: bool
        `True` will show the welcome message. `False` will hide the welcome message.
    sign_out: ButtonConfig
        Config for sign-out button
    """
    location: FormLocation
    show_welcome: bool
    sign_out: ButtonConfig

    def __init__(self,
                 location: FormLocation = 'sidebar',
                 show_welcome: bool = True,
                 sign_out: ButtonConfig = ButtonConfig('🔐 Sign Out')) -> None:
        """ Create an instance of `LogoutFormConfig` object
        """
        self.location = location
        self.show_welcome = show_welcome
        self.sign_out = sign_out


class Cookie_Secrets:
    """ Secrects to encode information to cookie in the client's browser

    ## Properties
    key: str
        key password to encode and decode information from cookie in the client's browser
    name: str
        name of the cookie to save in the client's browser
    expiry_days: float
        The number of days before the reauthentication cookie automatically expires on the client's browser.
    """
    key: str
    name: str
    expiry_days: float

    def __init__(self, key: str, name: str, expiry_days: float = 7.0):
        """ Create an instance of `Cookie_Secrets` object
        """
        self.key = key
        self.name = name
        self.expiry_days = expiry_days


class Authenticate:
    """ Authentication using ldap.
        Reauthentication method avaliable
        * steamlit session_state: Valid for the current session. if the page is refreshed, session_state will reset thus loose stored data for reauthentication.
        * cookie in the client's browser: Valid until the cookie in the browser is expired

    ## Properties
    ldap_configs: LdapConfig
        Config for ldap Authentication
    ss_user_name: 
        Optional username key to store in streamlit session_state.
        None will disable reauthorization using streamlit session_state
    cookie_secrets:
        Optional secrects to encode user information to cookie in the client's browser.
        None will disable reauthorization using cookie in the client's browser.
    """
    ldap_configs: LdapConfig
    ss_user_name: Union[str, None]
    cookie_secrets: Union[Cookie_Secrets, None]

    def __init__(self,
                 ldap_config: LdapConfig,
                 ss_user_name: Union[str, None] = None,
                 cookie_secrets: Union[Cookie_Secrets, None] = None):
        """ Create a new instance of `Authenticate`

        ## Arguments
        ldap_config: LdapConfig
            Config for Ldap authentication

        ss_user_name: str | None
            Optional username key to store in streamlit session_state.
            None will disable reauthorization using streamlit session_state

        cookie_secrets: Cookie_Secrets | None
            Optional secrects to encode user information to cookie in the client's browser.
            None will disable reauthorization using cookie in the client's browser.
        """
        self.ldap_configs = ldap_config
        self.ss_user_name = ss_user_name
        self.cookie_secrets = cookie_secrets

        self.ldap_auth = LdapAuthenticate(ldap_config)

        if cookie_secrets is not None:
            self.cookie_manager = stx.CookieManager()
            time.sleep(0.1)


    def _getUser(self) -> Union[Person, None]:
        """ Get the user information from streamlit session_state
            if reauthorization using streamlit session_state is enabled

        ## Returns
        Person | None
            user information if it is avaliable, otherwise `None`
        """
        if self.ss_user_name is None: return None
        if self.ss_user_name not in st.session_state: return None
        user = st.session_state[self.ss_user_name]
        return user if type(user) is Person else None

    def _setUser(self, user: Union[Person, None]):
        """ Assign the user information to session_state of streamlit
            if reauthorization using streamlit session_state is enabled

        ## Arguments
        user : Person | None
            user information to assign to session_state of streamlit
        """
        if self.ss_user_name is None: return
        else: st.session_state[self.ss_user_name] = user


    def _token_encode(self, cookie_secrets: Cookie_Secrets, user: Person):
        """ Encodes the contents for the reauthentication cookie.

        ## Arguments
        user: Person
            User Information
        ## Returns
        str
            The JWT cookie for passwordless reauthentication.
        """
        exp_date = datetime.utcnow() + timedelta(days=cookie_secrets.expiry_days)
        return jwt.encode({
            'user': user.toDict(),
            'exp_date': exp_date.timestamp()
        }, cookie_secrets.key, algorithm='HS256')
    
    def _token_decode(self, cookie_secrets: Cookie_Secrets, token):
        """ Decodes the contents of the reauthentication cookie.

        ## Arguments:
        token: any
        encoded cookie token

        ## Returns:
        Person | False
            the user information if cookie is correct.
            otherwise, return `None`
        """
        try:
            if token is None: raise CookieError('No cookie found')
            if type(token) is not str: raise CookieError('Cookie value is expected to be `str`')
            
            value = jwt.decode(token, cookie_secrets.key, algorithms=['HS256'])
            if type(value) is not dict: raise CookieError('Decoded cookie is not dict')

            if 'exp_date' not in value: raise CookieError('exp_date is not found')
            exp_date = value['exp_date']
            if type(exp_date) is not float: raise CookieError('exp_date is not float')
            if exp_date < datetime.utcnow().timestamp(): raise CookieError('Cookie expired')
            
            if 'user' not in value: raise CookieError('user is not found')
            user = value['user']
            if type(user) is not dict: raise CookieError('user is not dict')

            return Person(user)
        except Exception as e:
            # print(f'Token decode error: {e}')
            return None

    def _get_cookie(self):
        """ Get the decoded user information from cookie in the client's browser.
            if reauthorization using cookie in the client's browser is enabled

        ## Returns
        Person | None
            user information if it is avaliable and valid, otherwise `None`
        """
        if self.cookie_secrets is None: return None

        token = self.cookie_manager.get(self.cookie_secrets.name)
        time.sleep(0.1)
        return self._token_decode(self.cookie_secrets, token)

    def _set_cookie(self, user: Person):
        """ Assign the encoded user information to cookie in the client's browser
            if reauthorization using cookie in the client's browser is enabled

        ## Arguments
        user: Person
            User information to assign to cookie in the client's browser
        """
        if self.cookie_secrets is None: return

        token = self._token_encode(self.cookie_secrets, user)
        exp_date = datetime.now() + timedelta(days=self.cookie_secrets.expiry_days)
        self.cookie_manager.set(self.cookie_secrets.name, token, expires_at=exp_date)
        time.sleep(0.1)

    def _delete_cookie(self):
        """ Delete the cookie in the client's browser
            if reauthorization using cookie in the client's browser is enabled
        """
        if self.cookie_secrets is None: return

        self.cookie_manager.delete(self.cookie_secrets.name)
        time.sleep(0.1)


    def _createLoginForm(self,
                         func: Union[Callable[[Union[Connection, None], Person], Union[Literal[True], str]], None] = None,
                         config: Union[LoginFormConfig, None] = None):
        """ create the login form
        
        ## Arguments
        func: ((Connection | None, Person | None) -> (True | str)) | None
            * Function to perform addtional authentication check.
            * Function must return `True` if additional authentication is successful, otherwise must return error message
            * Passing `None` will ignore additional authentiation check.

        config: LoginFormConfig | None
            Optional config for login in form
        """
        config = config if config is not None else LoginFormConfig()
        
        form = getForm('Login', config.location)

        if config.title is not None: form.subheader(config.title)
        username = form.text_input(config.username.get_label('User Name'),
                                   placeholder=config.username.placeholder,
                                   help=config.username.help,
                                   label_visibility=config.username.get_label_visibility())

        password = form.text_input(config.password.get_label('Password'),
                                   type='password',
                                   placeholder=config.password.placeholder,
                                   help=config.password.help,
                                   label_visibility=config.password.get_label_visibility())
        
        btnCtn, statusCtn = form.columns([1, 3])

        submit = btnCtn.form_submit_button(config.sign_in.label, config.sign_in.help)
        if submit:
            with statusCtn:
                with st.spinner("Logging in..."):
                    result = self.ldap_auth.login(username, password, func, config.wrong_message)

                    if type(result) is str:
                        statusCtn.error(result, icon=config.error_icon)
                    elif type(result) is Person:
                        return result
                    else:
                        statusCtn.error(f'Unexpected Return: {result}', icon=config.error_icon)
    
    def _checkUser(self,
                   user: Union[Person, None],
                   connection: Union[Connection, None] = None,
                   func: Union[Callable[[Union[Connection, None], Person], Union[Literal[True], str]], None] = None):
        """ Check user information during reauthorization

        ## Arguments
        user : Person | None
            Optional user information to check
        connection: Connection | None
            Optional ldap connection
        func: ((Connection | None, Person | None) -> (True | str)) | None
            * Function to perform addtional authentication check.
            * Function must return `True` if additional authentication is successful, otherwise must return error message
            * Passing `None` will ignore additional authentiation check.

        ## Returns
        bool
            `True` if user is authorized to use.
            otherwise, `False`.
        """
        if type(user) is not Person: return False
        if func is None: return True
        result = func(connection, user)
        return result == True

    def login(self,
              func: Union[Callable[[Union[Connection, None], Person], Union[Literal[True], str]], None] = None,
              config: Union[LoginFormConfig, None] = None):
        """ Authentication using ldap. Reauthorize if it is valid and create login form if authorization fail.

        ## Arguments
        func: ((Connection | None, Person | None) -> (True | str)) | None
            * Function to perform addtional authentication check.
            * Function must return `True` if additional authentication is successful, otherwise must return error message
            * Passing `None` will ignore additional authentiation check.
        config: LoginFormConfig | None
            Optional config for login form

        ## Returns
        bool
            `False` until user authorization is completed.
            Once completed, `True` will be returned
        """
        # check user authentication if it is found in streamlit session_state
        self.user = self._getUser()
        if self._checkUser(self.user, None, func): return True

        # check user authentication if it is found in cookie
        self.user = self._get_cookie()
        if self._checkUser(self.user, None, func):
            self._setUser(self.user)
            return True

        # ask user to log in
        self.user = self._createLoginForm(func, config)
        if type(self.user) is Person:
            self._setUser(self.user)
            self._set_cookie(self.user)
            try: return True
            finally: st.rerun()
        return False


    def createLogoutForm(self, config: Union[LogoutFormConfig, None] = None):
        """ create the logout form
        
        ## Arguments
        config: LoginFormConfig | None
            Optional config for login out form
        """
        def logout():
            self._setUser(None)
            self._delete_cookie()

        if self.user is None: return

        config = config if config is not None else LogoutFormConfig()

        if config.show_welcome:
            form = getForm('Logout', config.location)
            form.markdown(f'Welcome {self.user.display_name}')
            form.form_submit_button(config.sign_out.label, help=config.sign_out.help, on_click=logout, use_container_width=True)
        else:
            ctn = getContainer(config.location)
            ctn.button(config.sign_out.label, help=config.sign_out.help, on_click=logout, use_container_width=True)
