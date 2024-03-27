# Author    : Nathan Chen
# Date      : 27-Mar-2024





from ldap3 import Server, Connection
from ldap3.abstract.entry import Entry
from typing import Union, Callable, Literal, Optional, List, Dict
from .exceptions import AdAttributeError
from .configs import LdapConfig, AttrDict, UserInfoValue, UserInfos





class LdapAuthenticate:
    """ Authentication using active directory

    ## Properties
    config: LdapConfig
        Config for authentication using active directory
    """
    config: LdapConfig

    def __init__(self, config: Union[LdapConfig, AttrDict]) -> None:
        """ Create an instance of `LdapAuthenticate` object

        ## Arguments
        config: LdapConfig | dict | streamlit.runtime.secrets.AttrDict
            Config for authentication using active directory
        """
        self.config = LdapConfig.getInstance(config)

    def login(self, username: str, password: str,
              getInfo: Callable[[Connection], Optional[UserInfos]],
              additionalCheck: Optional[Callable[[Optional[Connection], UserInfos], Union[Literal[True], str]]] = None) -> Union[UserInfos, str]:
        """ Login to active directory

        ## Arguments
        userName: str
            user name to login to active directory
        password: str
            password to login to active directory
        getInfo: (conneciton: Connection) -> UserInfos | None
            Function to retrieve user information from active directory
        additionalCheck: ((connection: Connection | None, user: UserInfos) -> (True | str)) | None
            * Function to perform addtional authentication check.
            * Function must return `True` if additional authentication is successful, otherwise must return error message
            * Passing `None` will ignore additional authentication check.

        ## Returns:
        UserInfos | str
            User information if authentication is successful.
            otherwise, authentication fail message
        """

        server = Server(self.config.server_path, use_ssl=self.config.use_ssl, get_info='ALL')
        conn = Connection(server, username, password, auto_bind=False, auto_referrals=False, raise_exceptions=False)
        try:
            conn.bind()
            if conn.result['result'] != 0: return 'Wrong username or password'
            user = getInfo(conn)
            if user is None: return f"No information found in active directory for '{username}'"
            if additionalCheck is None: return user

            result = additionalCheck(conn, user)
            if result == True: return user
            else : return result
        except Exception as e:
            return str(e).replace(self.config.server_path, 'server')
        finally:
            if conn.bound: conn.unbind()

    def getInfos(self, conn: Connection, filters: Union[str, Dict[str, str]]) -> List[UserInfos]:
        """ Get list of entries information from active directory

        ## Arguments
        conn: Connection
            Active directory connection
        filters: str | Dict[str, str]
            * sr: filter string
            * Dict[str, str]: Filter key value pairs

        ## Returns
        UserInfos | None
            User information if avaliable. otherwise, `None`
        """
        conn.search(search_base=self.config.search_base,
                    search_filter=self.__toFilterStr(filters),
                    search_scope='SUBTREE',
                    attributes=self.config.attributes)
        return self.__toInfos(conn.entries)

    def getInfo(self, conn: Connection, filters: Union[str, Dict[str, str]]) -> Optional[UserInfos]:
        """ Get entry information from active directory
        
        ## Arguments
        conn: Connection
            Active directory connection
        filters: str | Dict[str, str]
            * str: filter string
            * Dict[str, str]: Filter key value pairs
        
        ## Returns
        UserInfos | None
            User information if avaliable. otherwise, `None`
        """
        infos = self.getInfos(conn, filters)
        if len(infos) < 1: return None
        return infos[0]
    
    def getInfoBySamAccountName(self, conn: Connection, name: str) -> Optional[UserInfos]:
        """ Get information from active directory

        ## Arguments
        conn: Connection
            Active directory connection
        name: str
            Active directory SaAccountName

        ## Returns
        UserInfos | None
            User information if avaliable. otherwise, `None`
        """
        return self.getInfo(conn, {'sAMAccountName': name})
    
    def getInfoByUserPrincipalName(self, conn: Connection, name: str) -> Optional[UserInfos]:
        """ Get information from active directory

        ## Arguments
        conn: Connection
            Active directory connection
        name: str
            Active directory UserPrincipalName

        ## Returns
        UserInfos | None
            User information if avaliable. otherwise, `None`
        """
        return self.getInfo(conn, {'userPrincipalName': name})
    
    def getInfoByDistinguishedName(self, conn: Connection, name: str) -> Optional[UserInfos]:
        """ Get information from active directory

        ## Arguments
        conn: Connection
            Active directory connection
        name: str
            Active directory DistinguishedName

        ## Returns
        UserInfos | None
            User information if avaliable. otherwise, `None`
        """
        return self.getInfo(conn, {'distinguishedName': name})


    def __toValue(self, attribute) -> UserInfoValue:
        """ Convert the attribute value

        ## Arguments
        attribute: any
            Active directory attribute

        ## Returns
            * List[str]: when there is more than one item in attribute value
            * str: when there is only single item in attribute value
            * None: when there is no item in attribute value
        """
        if type(attribute) is not list: raise AdAttributeError(f"'{attribute}' is not `List` type")
        length = len(attribute)
        if length < 1: return None
        elif length == 1: return str(attribute[0])
        else: return attribute

    def __toInfo(self, entry) -> Optional[UserInfos]:
        if type(entry) is not Entry: return None
        info = { str(k):self.__toValue(v) for k,v in entry.entry_attributes_as_dict.items() }
        return info

    def __toInfos(self, entries) -> List[UserInfos]:
        """ Convert entries to user information list
        """
        if type(entries) is not list: raise TypeError("Expect 'entries' to be list type")
        infos = [self.__toInfo(e) for e in entries]
        infos = [i for i in infos if i is not None]
        return infos
    
    def __toFilterStr(self, filters: Union[str, Dict[str, str]]) -> str:
        if type(filters) is str: return filters
        elif type(filters) is dict:
            search_filters = [f"({k}={v})" for k,v in filters.items()]
            return f"(&{''.join(search_filters)})"
        else: raise TypeError("Expect 'filters' argument to be either str or Dict[str, str] type")

