# Author    : Nathan Chen
# Date      : 16-Feb-2024


from __future__ import annotations
import json
import re
from ldap3 import Server, Connection
from ldap3.abstract.entry import Entry
from ldap3.abstract.attribute import Attribute
from typing import List, Union, Callable, Literal
from .exceptions import AdAttributeError


class Person:
    """ User information from Active Directory

    ## Properties
    | Property     |   | Type |   | Description |
    | :----------- | - | :--: | - | :---------- |
    | user_name    | : | str  | : | User name of the user |
    | employee_id  | : | str  | : | Employee number of the user |
    | display_name | : | str  | : | Display name of the user |
    | given_name   | : | str  | : | Given name of the user |
    | title        | : | str  | : | Job title of the user |
    | mail         | : | str  | : | Email address of the user |
    | dn           | : | str  | : | Distinguish name of the user in Active Directory |
    | manager_dn   | : | str  | : | Manager's distinguish name in Active Directory |
    | reports_dn   | : | str  | : | List of direct reports' distinguish name in Active Directory |
    | manager      | : | str or `None`  | : | will be `None` until `updateManager()` is executed |
    | reports      | : | List[str] or `None`  | : | will be `None` until `updateReports()` is executed |
    """
    user_name: str
    employee_id: str
    display_name: str
    given_name: str
    title: str
    mail: str
    dn: str
    manager_dn: str
    reports_dn: str
    manager: Union['Person', None] = None
    reports: Union[List['Person'], None] = None


    def __init__(self, entry: Union[dict, Entry]):
        """ Create a new instance of `Person`

        ## Arguments
        entry: dict | Entry
            * Dictionary of `Person` object or
            * `Entry` object contains a single LDAP entry
        """
        if type(entry) is dict:
            for key, value in entry.items():
                if key == 'manager': self.__setattr__(key, Person(value))
                else: self.__setattr__(key, value)
        elif type(entry) is Entry:
            self._setattr('user_name', entry, 'sAMAccountName')
            self._setattr('employee_id', entry, 'employeeNumber')
            self._setattr('display_name', entry, 'displayName')
            self._setattr('given_name', entry, 'givenName')
            self._setattr('title', entry, 'title')
            self._setattr('mail', entry, 'mail')
            self._setattr('dn', entry, 'distinguishedName')
            self._setattr('manager_dn', entry, 'manager')
            self._setattr('report_dn', entry, 'directReports')
        else:
            raise AdAttributeError(f"Invalid type")

    def _setattr(self, att_name: str, entry: Entry, entry_name: str):
        if entry_name not in entry: raise AdAttributeError(f"'{entry_name}' is not found in entry")
        attribute = entry[entry_name]
        if type(attribute) is not Attribute: raise AdAttributeError(f"'{entry_name}' is not `{Attribute}` type")
        value = attribute.value

        if value is not []: self.__setattr__(att_name, value)
        elif len(value) == 1: self.__setattr__(att_name, value[0])
        else: self.__setattr__(att_name, value)


    def updateManager(self, conn: Connection):
        """Update manager property with `Person` object

        ## Arguments
        conn: Connection
            Main ldap connection object
        """
        self.manager = getPersonByDn(conn, self.manager_dn)
    
    def _getReportByDn(self, conn: Connection, report_dn: str):
        user = getPersonByDn(conn, report_dn)
        if user is None: return None
        user.manager = self
        return user

    def updateReports(self, conn: Connection, level: int = 1):
        """Update the user organization structure

        # Arguments
        conn: Connection
            Main ldap connection object
        level: int
            number of organization level below.
        """
        if level < 1: return

        reports = [self._getReportByDn(conn, report_dn) for report_dn in self.reports_dn]
        self.reports = [r for r in reports if r is not None]
        
        nextLevel = level - 1
        if nextLevel < 1: return

        if self.reports is not None:
            for report in self.reports:
                report.updateReports(conn, nextLevel)


    def _hasReport(self, checkFunc):
        """Check whether member is found in user organization
        """
        if self.reports is None: return False
        for report in self.reports:
            if checkFunc(report): return True
            if report.reports is not None and report._hasReport(checkFunc): return True
        return False

    def hasReportByDn(self, dn: str):
        """ Check whether member is found in organization by distinguish name

        ## Arguments
        dn: str
            distinguish name

        ## Returns
        bool
            `True` if memeber is found in the organization.
            otherwise, `False`
        """
        return self._hasReport(lambda report: report.dn == dn)
    
    def hasReportByUserName(self, user_name: str):
        """ Check whether member is found in organization by user_name

        ## Arguments
        user_name: str
            user_name without domain name

        ## Returns
        bool
            `True` if memeber is found in the organization.
            otherwise, `False`
        """
        return self._hasReport(lambda report: report.user_name == user_name)
    
    def hasReportByMail(self, mail: str):
        """ Check whether member is found in organization by mail

        ## Arguments
        mail: str
            email address

        ## Returns
        bool
            `True` if memeber is found in the organization.
            otherwise, `False`
        """
        return self._hasReport(lambda report: report.mail == mail)


    def _isReportTo(self, conn: Connection, manager: 'Person', maxLevel: int = 3, currentLevel: int = 1) -> bool:
        """Check whether in the organization of `manager`

        ## Arguments
        conn: Connection
            Main ldap connection object
        manager: Person
            Manager in `Person` object
        maxLevel: int
            Max level to look up relative to user
        currentLevel: current level of checking relative to user
        
        ## Returns
        bool
            `True` if in the organization of `manager`.
            otherwise `False`
        """
        if currentLevel > maxLevel: return False
        
        if self.manager is None and self.manager_dn is not None and conn is not None:
            self.manager = getPersonByDn(conn, self.manager_dn)

        if self.manager is None: return False
        if self.manager_dn == manager.dn: return True
        return self.manager._isReportTo(conn, manager, maxLevel, currentLevel + 1)
    
    def isReportTo(self, conn: Connection, manager: 'Person', maxLevel = 3) -> bool:
        """Check whether in the organization of `manager`

        ## Arguments
        conn: Connection
            Main ldap connection object
        manager: Person
            Manager in `Person` object
        maxLevel: int
            Max level to look up relative to user
        
        ## Returns
        bool
            `True` if in the organization of `manager`.
            otherwise `False`
        """
        return self._isReportTo(conn, manager, maxLevel)
    
    def isReportToByEmail(self, mail: str) -> bool:
        """ Check whether in the organization of manager using email

        ## Arguments
        mail: str
            email address
        
        ## Returns
        bool
            `True` if in the organization of `manager`.
            otherwise, `False`
        """
        if self.manager is None: return False
        if self.manager.mail == mail: return True
        return self.manager.isReportToByEmail(mail)
    
    def isReportToByUserName(self, user_name: str) -> bool:
        """ Check whether in the organization of manager using username

        ## Arguments
        user_name: str
            user_name without domain name
        
        ## Returns
        bool
            `True` if in the organization of `manager`.
            otherwise, `False`
        """
        if self.manager is None: return False
        if self.manager.user_name == user_name: return True
        return self.manager.isReportToByUserName(user_name)


    def toDict(self):
        """ Convert to `dict` object.

        ## Return
        dict[str, Any]
            dict equavilent of `Person` object
            Will not populate `reports` as it might contain circular reference
        """
        dict = self.__dict__.copy()
        if self.manager is not None: dict['manager'] = self.manager.toDict()
        if self.reports is not None: dict['reports'] = None
        return dict
    
    def toJson(self):
        j = '{'
        j += f'"user_name":{json.dumps(self.user_name)}'
        j += f',"employee_id":{json.dumps(self.employee_id)}'
        j += f',"display_name":{json.dumps(self.display_name)}'
        j += f',"given_name":{json.dumps(self.given_name)}'
        j += f',"title":{json.dumps(self.title)}'
        j += f',"mail":{json.dumps(self.mail)}'
        j += f',"dn":{json.dumps(self.dn)}'
        j += f',"manager_dn":{json.dumps(self.manager_dn)}'
        j += f',"reports_dn":{json.dumps(self.reports_dn)}'
        if self.manager is not None: j += f',"manager":{self.manager.toJson()}'
        if self.reports is not None and len(self.reports) > 0:
            reportStr = ','.join([r.toJson() for r in self.reports])
            j += f',"reports":[{reportStr}]'
        j += '}'
        
        return j


class LdapConfig:
    """ Config for Ldap authentication

    ## Properties
    server_path: str
        ldap server path. E.g. ldap://ldap.example.com:389
    domain: str
        domain
    """
    server_path: str
    domain: str

    def __init__(self, server_path: str, domain: str):
        """ Create an instance of `LdapConfig` object
        """
        self.server_path = server_path
        self.domain = domain


class LdapAuthenticate:
    """ Authentication using Ldap

    ## Properties
    config: LdapConfig
        Config for Ldap authentication
    """
    config: LdapConfig

    def __init__(self, config: LdapConfig) -> None:
        """ Create an instance of `LdapAuthenticate` object

        ## Arguments
        config: LdapConfig
            Config for Ldap authentication
        """
        self.config = config
        self.regex = re.compile(fr'^(.*)\\(.*)$', re.IGNORECASE)

    def login(self, username: str, password: str,
              func: Union[Callable[[Union[Connection, None], Person], Union[Literal[True], str]], None] = None,
              wrongMessage: str = "Wrong userName or Password."):
        """ Login to ldap server

        ## Arguments
        userName: str
            user name to login to ldap server
        password: str
            password to login to ldap server
        func: ((Connection | None, Person | None) -> (True | str)) | None
            * Function to perform addtional authentication check.
            * Function must return `True` if additional authentication is successful, otherwise must return error message
            * Passing `None` will ignore additional authentiation check.
        wrongMessage: str
            Wrong username or password message.

        ## Returns:
        Person | str
            User information if authentication is successful.
            otherwise, authentication fail error message
        """

        match = self.regex.match(username)
        domain = self.config.domain if match is None else match.groups()[0]
        username = username if match is None else match.groups()[1]

        server = Server(self.config.server_path, use_ssl=False, get_info='ALL')
        conn = Connection(server, f'{domain}\\{username}', password, auto_bind=False, auto_referrals=False, raise_exceptions=False)
        try:
            conn.bind()
            if conn.result['result'] != 0: return wrongMessage
            user = getPersonByUserName(conn, username)
            if user is None: return wrongMessage
            if func is None: return user

            result = func(conn, user)
            if result == True: return user
            else : return result
        except Exception as e:
            print("Login error occured:", e)
            return wrongMessage
        finally:
            if conn.bound: conn.unbind()



def _getPerson(entries):
    if entries is None: return None
    elif len(entries) < 1: return None
    entry = entries[0]
    if type(entry) is not Entry: return None
    return Person(entry)

def _getAttributes():
    return ['sAMAccountName', 'employeeNumber', 'displayName', 'givenName', 'title', 'mail', 'distinguishedName', 'manager', 'directReports']

def getPersonByUserName(conn: Connection, userName: str):
    """Get User Information from Active Directory
    
    ## Arguments
    conn: Connection
        Connection to bind to ldap server
    userName: str
        user name to login to ldap server

    ## Returns
    Person | None
        User information if user is found in Active Directory,
        otherwise `None` will be returned
    """
    conn.search(search_base='dc=illumina,dc=com',
                search_filter=f'(&(objectclass=person)(sAMAccountName={userName}))',
                search_scope='SUBTREE',
                attributes=_getAttributes())
    return _getPerson(conn.entries)

def getPersonByDn(conn: Connection, dn: str):
    """Get User Information from Active Directory
    
    ## Arguments
    conn: Connection
        Connection to bind to ldap server
    dn: str
        Distinguish name of the user in ldap server

    ## Returns
    Person | None
        User information if user is found in Active Directory,
        otherwise `None` will be returned
    """
    conn.search(search_base=dn,
                search_filter=f'(&(objectclass=person))',
                search_scope='SUBTREE',
                attributes=_getAttributes())
    return _getPerson(conn.entries)

def getPersonByMail(conn: Connection, mail: str):
    """Get User Information from Active Directory
    
    ## Arguments
    conn: Connection
        Connection to bind to ldap server
    mail: str
        email address of the user

    ## Returns
    Person | None
        User information if user is found in Active Directory,
        otherwise `None` will be returned
    """
    conn.search(search_base='dc=illumina,dc=com',
                search_filter=f'(&(objectclass=person)(mail={mail}))',
                search_scope='SUBTREE',
                attributes=_getAttributes())
    return _getPerson(conn.entries)

