import streamlit as st
from __init__ import Authenticate, LdapConfig, Cookie_Secrets, Connection, Person, LogoutFormConfig, getPersonByMail
from typing import Union

def checkUserInOrganization(conn: Union[Connection, None], user: Person):
    email = 'vbalamurugan@illumina.com'
    if conn is None:
        return True if user.isReportToByEmail(email) else f"You are not reported to {email}. Not Authorize to use this resource."
    
    manager = getPersonByMail(conn, email)
    if manager is None: return f"You are not reported to {email}. Not Authorize to use this resource."
    if user.isReportTo(conn, manager): return True
    return f"You are not reported to {manager.display_name}({manager.employee_id}). Not Authorize to use this resources"

authenticator = Authenticate(LdapConfig(st.secrets['ldap']['server_path'], st.secrets['ldap']['domain']),
                     None,# st.secrets['session_state_names']['user'],
                     Cookie_Secrets(st.secrets['auth_cookie']['key'], st.secrets['auth_cookie']['name'], st.secrets['auth_cookie']['expiry_days']))
if authenticator.login(checkUserInOrganization):
    st.markdown("## Testing")
    st.write(st.session_state)
    authenticator.createLogoutForm(LogoutFormConfig(show_welcome=True))
    st.button('test')
