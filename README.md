# Welcome to Streamlit LDAP Authenticator 🔑

[![PyPI][pypi_badge]][pypi_link]
[![GitHub][github_badge]][github_link]
[![GitHub license][license_badge]][license_link]
[![GitHub issues][issue_badge]][issue_link]
[![GitHub pull requests][pull_badge]][pull_link]

A fast and easy way to handle the user authentication using ldap in your Streamlit apps.

## What is Streamlit LDAP Authenticator?
`streamlit-ldap-authenticator` let you add login form and execute authentication before your streamlit page app started.
### Features
* Authentication using active directory.
* Each page app can have it's own additional user authorization.
* User login status will share across multi page app by making use of streamlit [Session State](https://docs.streamlit.io/library/api-reference/session-state)
* Can configure to remember user login by using cookie in the client's browser.


![LoginForm](/images/LoginForm.png)

![LogoutForm](/images/LogoutForm.png)

## Installation
Open a terminal and run:
``` terminal
pip install streamlit-ldap-authenticator
```


## Quickstart
### Simple log in example
Create a new file secrets.toml in .streamlit folder.\
You can learn more about secrets management [streamlit documentation](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management).

Require Configuration
* Active directory server path of your organization
* Your organization domain
* Avaliable attribute for your organization for person data in active directory. You can use [ADExplorer](https://learn.microsoft.com/en-us/sysinternals/downloads/adexplorer) to explore avaliable attribute for your organization.

If your organization email address is "@example.com", most likely
your configuration will be as below
``` ini
[ldap]
server_path = "ldap://ldap.example.com"
domain = "example"
search_base = "dc=example,dc=com"
attributes = ["sAMAccountName", "distinguishedName", "userPrincipalName", "displayName", "manager", "title"]
use_ssl = true

[session_state_names]
user = "login_user"
remember_me = "login_remember_me"

[auth_cookie]
name = "login_cookie"
key = "{any password for encryption}"
expiry_days = 1
auto_renewal = true
```
Create a new file simple_login.py with the following code:
``` python
import streamlit as st
from streamlit_ldap_authenticator import Authenticate, LogoutFormConfig

# Declare the authentication object
auth = Authenticate(
    st.secrets['ldap'],
    st.secrets['session_state_names'],
    st.secrets['auth_cookie']
)

# Login Process
user = auth.login()
if user is not None:  
    auth.createLogoutForm(LogoutFormConfig(message=f"Welcome {user['displayName']}"))
    
    # Your page application can be written below  
    st.write("# Welcome to my App! 👋")
    st.write(user)
```
Run the streamlit app!
``` terminal
streamlit run simple_login.py
```


## Configuration Objects
### LdapConfig
Configuration for your organization active directory
| Name        | Type      | Description
| ----------- | --------- | -----------
| server_path | str       | Active directory server path. E.g. 'ldap://ldap.example.com'
| domain      | str       | Your organization domain. E.g. 'Example'
| search_base | str       | Active directory base search. E.g. 'dc=example, dc=com'
| attributes  | List[str] | Attribute avaliable in your organization active directory. You can reference in [ADExplorer](https://learn.microsoft.com/en-us/sysinternals/downloads/adexplorer)
| use_ssl     | bool      | Determine whether to use basic SSL basic authentication


### SessionStateConfig
Configuration for streamlit [Session State](https://docs.streamlit.io/library/api-reference/session-state) key names
| Name        | Type | Description
| ----------- | ---- | -----------
| user        | str  | Key name to store user information
| remember_me | str  | Key name to store remember_me checkbox selection


### CookieConfig
Configuration to store user information to the cookie in client's browser. Thus even when user close the browser and reload the page, Reauthorization is possible with cookie.
| Name         | Type  | Description
| ------------ | ----- | -----------
| name         | str   | cookie name to store in client's browser
| key          | str   | encryption key to encrypt user information
| expiry_days  | float | expiry date for the cookie
| auto_renewal | bool  | Cookie will expire after defined days from the **last activity** when value is `True`. Cookie will expire after defined days from the **last login** when value is `False`.



## More Examples
### Addtional check with job title after ldap authentication completed
Create a new file title_login.py with the following code:
``` python
import streamlit as st
from streamlit_ldap_authenticator import Authenticate, Connection, LogoutFormConfig, UserInfos
from typing import Optional

# Declare the authentication object
auth = Authenticate(
    st.secrets['ldap'],
    st.secrets['session_state_names'],
    st.secrets['auth_cookie']
)

def checkUserByTitle(conn: Optional[Connection], user: UserInfos):
    title = "Engineer"
    if user['title'].__contains__(title): return True
    return f"You are not a {title}. Not authorize to use this page."

# Login Process
user = auth.login(checkUserByTitle)
if user is not None:
    auth.createLogoutForm(LogoutFormConfig(message=f"Welcome {user['displayName']}"))
    
    # Your page application can be written below
    st.write("# Welcome to my App! 👋")
    st.write(user)
```
Now run it to open the app!
``` terminal
streamlit run title_login.py
```


### Additional check with reporting structure after ldap authentication completed
Create a new file report_login.py with the following code:
``` python
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

# Login Process
user = auth.login(checkUserInOrganization)
if user is not None:
    auth.createLogoutForm(LogoutFormConfig(message=f"Welcome {user['displayName']}"))
    
    # Your page application can be written below
    st.write("# Welcome to my App! 👋")
    st.write(user)
```
Now run it to open the app!
``` terminal
streamlit run report_login.py
```


### Additional check against list of users after ldap authentication completed
Create a new file list_login.py with the following code:
``` python
import streamlit as st
from streamlit_ldap_authenticator import Authenticate, Connection, LogoutFormConfig, UserInfos
from typing import Optional

# Declare the authentication object
auth = Authenticate(
    st.secrets['ldap'],
    st.secrets['session_state_names'],
    st.secrets['auth_cookie']
)

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
    st.write(user)
```
Now run it to open the app!
``` terminal
streamlit run list_login.py
```

## Change Log
### Version 0.0.4
- Initial release
### Version 0.0.5
- default use_ssl for ldap connection to `True`
- Added use_ssl configuration in `LdapConfig`





[pypi_badge]: https://img.shields.io/pypi/v/streamlit-ldap-authenticator.svg
[pypi_link]: https://pypi.org/project/streamlit-ldap-authenticator/
[github_badge]: https://badgen.net/badge/icon/GitHub?icon=github&color=black&label
[github_link]: https://github.com/NathanChen198/streamlit-ldap-authenticator
[license_badge]: https://img.shields.io/badge/Licence-MIT-gr.svg
[license_link]: https://github.com/NathanChen198/streamlit-ldap-authenticator/blob/main/LICENSE
[issue_badge]: https://img.shields.io/github/issues/NathanChen198/streamlit-ldap-authenticator
[issue_link]: https://github.com/NathanChen198/streamlit-ldap-authenticator/issues
[pull_badge]: https://img.shields.io/github/issues-pr/NathanChen198/streamlit-ldap-authenticator
[pull_link]: https://github.com/NathanChen198/streamlit-ldap-authenticator/pulls