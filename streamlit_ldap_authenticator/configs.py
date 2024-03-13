# Author    : Nathan Chen
# Date      : 13-Mar-2024





import streamlit as st
from streamlit.type_util import LabelVisibility
from streamlit.runtime.secrets import AttrDict as _AttrDict
from typing import Type, Literal, Optional, Union, TypeVar, List, Dict, Any





# UI Config
FormLocation = Literal['main', 'sidebar']

def getForm(key: str, location: FormLocation):
    if location == 'main': return st.form(key)
    elif location == 'sidebar': return st.sidebar.form(key)
    else: raise ValueError("Location must be one of 'main' or 'sidebar'")

def getContainer(location: FormLocation):
    if location == 'main': return st.container()
    elif location == 'sidebar': return st.sidebar.container()
    else: raise ValueError("Location must be one of 'main' or 'sidebar'")

class InputConfig:
    """ Config for input

    ## Properties
    label: str
        Label of the input. if None, label of the input will `collapsed`

    help: str | None
        An optional tooltip that gets displayed next to the input.
    """
    label: str
    help: Optional[str]


    def __init__(self,
                 label: str,
                 help: Optional[str] = None):
        """ Create an instance
        
        ## Arguments
        label: str | None
            Label of the input. if None, label of the input will `collapsed`

        help: str | None
            An optional tooltip that gets displayed next to the input.
        """
        self.label = label
        self.help = help

class HidableLabelInputConfig(InputConfig):
    """ Config for input

    ## Properties
    label: str
        Label of the input. if None, label of the input will `collapsed`

    help: str | None
        An optional tooltip that gets displayed next to the input.

    label_visibility: 'visible', 'hidden' or 'collapsed'
        The visibility of the label.
        If 'hidden', the label doesn't show but there is still empty space for it (equivalent to label="").
        If 'collapsed', both the label and the space are removed.
    """
    label_visibility: LabelVisibility

    def __init__(self,
                 label: str,
                 help: Optional[str] = None,
                 label_visibility: LabelVisibility = 'visible'):
        """ Create an instance

        ## Arguments
        label: str
            Label of the input. if None, label of the input will `collapsed`

        help: str | None
            An optional tooltip that gets displayed next to the input.

        label_visibility: 'visible', 'hidden' or 'collapsed'
            The visibility of the label.
            If 'hidden', the label doesn't show but there is still empty space for it (equivalent to label="").
            If 'collapsed', both the label and the space are removed.
        """
        super().__init__(label, help)
        self.label_visibility = label_visibility

class TextInputConfig(HidableLabelInputConfig):
    """ Config for text input

    ## Properties
    label: str
        Label of the input. if None, label of the input will `collapsed`

    help: str | None
        An optional tooltip that gets displayed next to the input.

    label_visibility: 'visible', 'hidden' or 'collapsed'
        The visibility of the label.
        If 'hidden', the label doesn't show but there is still empty space for it (equivalent to label="").
        If 'collapsed', both the label and the space are removed.

    placeholder: str | None
        An optional string displayed when the text input is empty. If None, no text is displayed.
    """
    placeholder: Optional[str]

    def __init__(self,
                 label: str,
                 help: Optional[str] = None,
                 label_visibility: LabelVisibility = 'visible',
                 placeholder: Optional[str] = None):
        """ Create an instance of `TextInputConfig`

        ## Arguments
        label: str
            Label of the input. if None, label of the input will `collapsed`

        help: str | None
            An optional tooltip that gets displayed next to the input.

        label_visibility: 'visible', 'hidden' or 'collapsed'
            The visibility of the label.
            If 'hidden', the label doesn't show but there is still empty space for it (equivalent to label="").
            If 'collapsed', both the label and the space are removed.

        placeholder: str | None
            An optional string displayed when the text input is empty. If None, no text is displayed.
        """
        super().__init__(label, help, label_visibility)
        self.placeholder = placeholder


class CheckboxConfig(HidableLabelInputConfig):
    def __init__(self,
                 label: str,
                 help: Optional[str] = None,
                 label_visibility: LabelVisibility = 'visible'):
        """ Create an instance

        ## Arguments
        label: str
            Label of the input. if None, label of the input will `collapsed`

        help: str | None
            An optional tooltip that gets displayed next to the input.

        label_visibility: 'visible', 'hidden' or 'collapsed'
            The visibility of the label.
            If 'hidden', the label doesn't show but there is still empty space for it (equivalent to label="").
            If 'collapsed', both the label and the space are removed.
        """
        super().__init__(label, help, label_visibility)

class ButtonConfig(InputConfig):
    def __init__(self,
                 label: str,
                 help: Optional[str] = None):
        """ Create an instance
        
        ## Arguments
        label: str | None
            Label of the input. if None, label of the input will `collapsed`

        help: str | None
            An optional tooltip that gets displayed next to the input.
        """
        super().__init__(label, help)




# Application Config
UserInfoValue = Union[List[str], str, None]
UserInfos = Dict[str, Any]
T = TypeVar('T')
AttrDict = Union[_AttrDict, dict]

class Config:
    @classmethod
    def _getAttrWithDefault(cls, dict: AttrDict, key: str, _type: Type, defaultValue: T): # type: ignore
        if key in dict:
            value = dict[key]
            value = value if type(value) is _type else defaultValue
        else: value = defaultValue
        return value
    
    @classmethod
    def _getAttr(cls, dict: AttrDict, key: str, _type: Type):
        if key not in dict: raise AttributeError(f"'{key}' is not found")

        value = dict[key]
        if type(value) is not _type: raise AttributeError(f"'{key}' is not {_type.__name__}")
        return value
        
class LdapConfig(Config):
    """ Config for authentication using active directory

    ## Properties
    server_path: str
        ldap server path. E.g. 'ldap://ldap.example.com:389'
    domain: str
        Your organization domain. E.g. 'Example'
    search_base: str
        Active Directory base search. E.g. 'dc=example,dc=com'
    attributes: List[str]
        Attribute avaliable in your organization active directory. You can reference in [ADExplorer](https://learn.microsoft.com/en-us/sysinternals/downloads/adexplorer)
    use_ssl: bool
        Determine whether to use basic SSL basic authentication. Default value is `True`
    """
    server_path: str
    domain: str
    search_base: str
    attributes: List[str]
    use_ssl: bool

    def __init__(self, server_path: str, domain: str, search_base: str, attributes: List[str], use_ssl: bool = True):
        """ Create an instance of `LdapConfig` object

        ## Arguments
        server_path: str
            ldap server path. E.g. 'ldap://ldap.example.com:389'
        domain: str
            Your organization domain. E.g. 'Example'
        search_base: str
            Active Directory base search. E.g. 'dc=example,dc=com'
        attributes: List[str]
            Attribute avaliable in your organization active directory. You can reference in [ADExplorer](https://learn.microsoft.com/en-us/sysinternals/downloads/adexplorer)
        """
        self.server_path = server_path
        self.domain = domain
        self.search_base = search_base
        self.attributes = attributes
        self.use_ssl = use_ssl

    @classmethod
    def from_dict(cls, dict: AttrDict) -> 'LdapConfig':
        server_path = cls._getAttr(dict, 'server_path', str)
        domain = cls._getAttr(dict, 'domain', str)
        search_base = cls._getAttr(dict, 'search_base', str)
        attributes = cls._getAttr(dict, 'attributes', list)
        use_ssl = cls._getAttrWithDefault(dict, 'use_ssl', bool, True)
        return LdapConfig(server_path, domain, search_base, attributes, use_ssl)

    @classmethod
    def getInstance(cls, value: Union['LdapConfig', AttrDict]) -> 'LdapConfig':
        if type(value) is LdapConfig: return value
        if type(value) is dict or type(value) is _AttrDict: return cls.from_dict(value)
        raise AttributeError(f"Unpected 'value' type")

class SessionStateConfig(Config):
    """ Config for streamlit session state key names

    ## Properties
    user: str
        session state key name to store the user information.

    remember_me: str
        session state key name to keep track remember_me checkbox value.
    """

    __default_user__ = "login_user"
    __default_remember_me__ = "login_remember_me"
    __default_auth_result__ = "login_result"

    user: str
    remember_me: str
    auth_result: str

    def __init__(self,
                 user: str = __default_user__,
                 remember_me: str = __default_remember_me__,
                 auth_result: str = __default_auth_result__):
        self.user = user
        self.remember_me = remember_me
        self.auth_result = auth_result

    @classmethod
    def from_dict(cls, dict: AttrDict) -> 'SessionStateConfig':
        user = cls._getAttrWithDefault(dict, 'user', str, cls.__default_user__)
        remember_me = cls._getAttrWithDefault(dict, 'remember_me', str, cls.__default_remember_me__)
        auth_result = cls._getAttrWithDefault(dict, 'auth_result', str, cls.__default_auth_result__)

        return SessionStateConfig(user, remember_me, auth_result)

    @classmethod
    def getInstance(cls, value: Union['SessionStateConfig', AttrDict, None]) -> 'SessionStateConfig':
        if type(value) is SessionStateConfig: return value
        if type(value) is dict or type(value) is _AttrDict: return cls.from_dict(value)
        return SessionStateConfig()

class CookieConfig(Config):
    """ Secrects to encode information to cookie in the client's browser

    ## Properties
    key: str
        key password to encode and decode information from cookie in the client's browser
    name: str
        name of the cookie to save in the client's browser
    expiry_days: float
        The number of days before the reauthentication cookie automatically expires on the client's browser.
    """
    __default_name__: str = "login_cookie"
    __default_expiry_days__: float = 1.0
    __default_auto_renewal__: bool = True

    
    key: str
    name: str
    expiry_days: float
    auto_renewal: bool

    def __init__(self, key: str,
                 name: str = __default_name__,
                 expiry_days: float = __default_expiry_days__,
                 auto_renewal: bool = __default_auto_renewal__):
        """ Create an instance of `CookieConfig` object
        """
        self.key = key
        self.name = name
        self.expiry_days = expiry_days
        self.auto_renewal = auto_renewal

    @classmethod
    def from_dict(cls, dict: AttrDict) -> 'CookieConfig':
        key = cls._getAttr(dict, 'key', str)
        name = cls._getAttrWithDefault(dict, 'name', str, cls.__default_name__)
        expiry_days = cls._getAttrWithDefault(dict, 'expiry_days', float, cls.__default_expiry_days__)
        auto_renewal = cls._getAttrWithDefault(dict, 'auto_renewal', bool, cls.__default_auto_renewal__)
        return CookieConfig(key, name, expiry_days, auto_renewal)

    @classmethod
    def getInstance(cls, value: Union['CookieConfig', AttrDict, None]) -> Optional['CookieConfig']:
        if type(value) is CookieConfig: return value
        if type(value) is dict or type(value) is _AttrDict: return cls.from_dict(value)
        return None

class EncryptorConfig(Config):
    """ Encryption key to encode and decode information between client and server

    ## Properties
    folderPath: str
        Location of the folder where both private key and public key is located
    keyName: str
        The name of the key
    """
    folderPath: str
    keyName: str

    def __init__(self, folderPath: str, keyName: str) -> None:
        self.folderPath = folderPath
        self.keyName = keyName

    @classmethod
    def from_dict(cls, dict: AttrDict) -> 'EncryptorConfig':
        folderPath = cls._getAttr(dict, 'folderPath', str)
        keyName = cls._getAttr(dict, 'keyName', str)
        return EncryptorConfig(folderPath, keyName)
    
    @classmethod
    def getInstance(cls, value: Union['EncryptorConfig', AttrDict, None]) -> Optional['EncryptorConfig']:
        if type(value) is EncryptorConfig: return value
        if type(value) is dict or type(value) is _AttrDict: return cls.from_dict(value)
        return None
