import streamlit as st
from streamlit_ldap_authenticator import Authenticate, Connection, LogoutFormConfig, UserInfos
from typing import Optional

# Declare the authentication object
auth = Authenticate(
    st.secrets['ldap'],
    st.secrets['session_state_names'],
    st.secrets['auth_cookie']
)

def __isReportTo(user: UserInfos, conn: Optional[Connection], email: str, max_level = 3, current_level = 1):
    if current_level > max_level: return False
    
    manager = user['manager']
    
    if type(manager) is str and type(conn) is Connection:
        manager = auth.ldap_auth.getInfoByDistinguishedName(conn, manager)
        user['manager'] = manager

    if type(manager) is not dict: return False
    if manager['mail'] == email: return True
    return __isReportTo(manager, conn, email, max_level, current_level + 1)

def checkUserInOrganization(conn: Optional[Connection], user: UserInfos):
    email = 'vbalamurugan@illumina.com'
    return True if __isReportTo(user, conn, email) else f'You are not reported to {email}. Not authorize to use this page.'

def checkUserByTitle(conn: Optional[Connection], user: UserInfos):
    title = "Engineer"
    if user['title'].__contains__(title): return True
    return f"You are not a {title}. Not authorize to use this page."

def checkUserInList(conn: Optional[Connection], user: UserInfos):
    allowUsers = [ "nchen1@illumina.com" ]
    if user['userPrincipalName'] in allowUsers: return True
    return f"You are not in the authorized list. Not allowed to use this page"

# Login Process
user = auth.login(checkUserInList)
if user is not None:
    auth.createLogoutForm(LogoutFormConfig(message=f"Welcome {user['displayName']}"))
    
    # Your page application can be written below
    st.write("# Welcome to my App! 👋")
    st.write(st.session_state)
    st.button('Test')
