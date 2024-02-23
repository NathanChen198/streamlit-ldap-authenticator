# Welcome to Streamlit LDAP3 Authenticator 🔑
A fast and easy way to handle the user authentication using ldap3 in your Streamlit apps.

## What is Streamlit LDAP3 Authenticator?
`streamlit-ldap3-authenticator` let you add login form and execute authentication before execute your streamlit page app.
* Easy to add login form before execute your streamlit page app.
* Each page can have it's own custom user authorization.
* Authentication using LDAP protocol to connect to active directory.
* You can add additional user level authentication requirement as well.
Avaliable reauthentication method
* steamlit session_state: only valid in the session. Will need to log in again if page is refresh.
* cookie in the client's browser: valid until cookie expired.


## Installation
Open a terminal and run:
``` terminal
pip install streamlit-ldap3-authenticator
```


## Quickstart
### Simple log in example
Create a new file secrets.toml in .streamlit folder.\
You can learn more about secrets management [streamlit documentation](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management).\
Configure the secrets as below
``` ini
[ldap]
server_path = "{your ldap server url}"
domain = "{your domain here}"

[session_state_names]
user = "user"

[auth_cookie]
name = "auth_cookie"
key = "{any cookie password}"
expiry_days = 1
```
Create a new file simple_login.py with the following code:
``` python
import streamlit as st
from streamlit_ldap3_authenticator import Authenticate, LdapConfig, Cookie_Secrets

auth = Authenticate(LdapConfig(st.secrets['ldap']['server_path'], st.secrets['ldap']['domain']),
                     st.secrets['session_state_names']['user'],
                     Cookie_Secrets(st.secrets['auth_cookie']['key'], st.secrets['auth_cookie']['name'], st.secrets['auth_cookie']['expiry_days']))
if auth.login():
    st.set_page_config(
        page_title='Welcome',
        page_icon='👋',
        initial_sidebar_state='expanded'
    )
    
    auth.createLogoutForm()
    st.write("# Welcome to my App! 👋")
```
Now run it to open the app!
``` terminal
streamlit run simple_login.py
```


## More Examples
### Addtional check with job title after ldap authentication completed
Create a new file title_login.py with the following code:
``` python
import streamlit as st
from typing import Union
from streamlit_ldap3_authenticator import Connection, Person, Authenticate, LdapConfig, Cookie_Secrets

def checkUserByTitle(_: Union[Connection, None], user: [Person, None]):
    title = 'Manager'
    if user.title.__contains__(title): return True
    return f"You are not a {title}. Not Authorize to use this page"

auth = Authenticate(LdapConfig(st.secrets['ldap']['server_path'], st.secrets['ldap']['domain']),
                     st.secrets['session_state_names']['user'],
                     Cookie_Secrets(st.secrets['auth_cookie']['key'], st.secrets['auth_cookie']['name'], st.secrets['auth_cookie']['expiry_days']))

if auth.login(checkUserByTitle):
    st.set_page_config(
        page_title='Welcome',
        page_icon='👋',
        initial_sidebar_state='expanded'
    )
    
    auth.createLogoutForm()
    st.write("# Welcome to my App! 👋")
```
Now run it to open the app!
``` terminal
streamlit run title_login.py
```


### Additional check with reporting structure after ldap authentication completed
Create a new file report_login.py with the following code:
``` python
import streamlit as st
from typing import Union
from streamlit_ldap3_authenticator import Connection, Person, Authenticate, LdapConfig, Cookie_Secrets, getPersonByMail

def checkUserInOrganization(conn: Union[Connection, None], user: Person):
    email = '{manager/director/vp email address here}'
    if conn is None:
        return True if user.isReportToByEmail(email) else f"You are not reported to {email}. Not Authorize to use this resource."
    
    manager = getPersonByMail(conn, email)
    if manager is None: return f"You are not reported to {email}. Not Authorize to use this resource."
    if user.isReportTo(conn, manager): return True
    return f"You are not reported to {manager.display_name}({manager.employee_id}). Not Authorize to use this resources"
   
auth = Authenticate(LdapConfig(st.secrets['ldap']['server_path'], st.secrets['ldap']['domain']),
                     st.secrets['session_state_names']['user'],
                     Cookie_Secrets(st.secrets['auth_cookie']['key'], st.secrets['auth_cookie']['name'], st.secrets['auth_cookie']['expiry_days']))

if auth.login(checkUserInOrganization):
    st.set_page_config(
        page_title='Welcome',
        page_icon='👋',
        initial_sidebar_state='expanded'
    )
    
    auth.createLogoutForm()
    st.write("# Welcome to my App! 👋")
```
Now run it to open the app!
``` terminal
streamlit run report_login.py
```


### Additional check against list of users after ldap authentication completed
Create a new file list_login.py with the following code:
``` python
import streamlit as st
from typing import Union
from streamlit_ldap3_authenticator import Connection, Person, Authenticate, LdapConfig, Cookie_Secrets

def checkUserInList(_: Union[Connection, None], user: Person):
    allowUsers = [ '{your email here}' ]
    if user.mail in allowUsers: return True
    return f"You are not in the authorized list. Not allowed to use this page"
   
auth = Authenticate(LdapConfig(st.secrets['ldap']['server_path'], st.secrets['ldap']['domain']),
                     st.secrets['session_state_names']['user'],
                     Cookie_Secrets(st.secrets['auth_cookie']['key'], st.secrets['auth_cookie']['name'], st.secrets['auth_cookie']['expiry_days']))

if auth.login(checkUserInList):
    st.set_page_config(
        page_title='Welcome',
        page_icon='👋',
        initial_sidebar_state='expanded'
    )
    
    auth.createLogoutForm()
    st.write("# Welcome to my App! 👋")
```
Now run it to open the app!
``` terminal
streamlit run list_login.py
```