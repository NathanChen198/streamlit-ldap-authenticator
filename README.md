# Welcome to Streamlit LDAP Authenticator 🔑

[![PyPI][pypi_badge]][pypi_link]
[![Download][pypi_download_badge]][pypi_link]
[![GitHub][github_badge]][github_link]
[![GitHub license][license_badge]][license_link]
[![GitHub issues][issue_badge]][issue_link]
[![GitHub pull requests][pull_badge]][pull_link]

A fast and easy way to handle the user authentication using ldap in your Streamlit apps.

## What is Streamlit LDAP Authenticator?

`streamlit-ldap-authenticator` let you add login form and execute authentication before your streamlit page app started.

### Features

- Authentication using active directory.
- Each page app can have it's own additional user authorization.
- User login status will share across multi page app by making use of streamlit [Session State](https://docs.streamlit.io/library/api-reference/session-state)
- Can configure to remember user login by using cookie in the client's browser.

![LoginForm](/images/LoginForm.png)

![LogoutForm](/images/LogoutForm.png)

## Installation

Open a terminal and run:

```terminal
pip install streamlit-ldap-authenticator
```

## Quickstart

### Simple log in example

Create a new file secrets.toml in .streamlit folder.\
You can learn more about secrets management [streamlit documentation](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management).

Require Configuration

- Active directory server path of your organization
- Your organization domain
- Avaliable attribute for your organization for person data in active directory. You can use [ADExplorer](https://learn.microsoft.com/en-us/sysinternals/downloads/adexplorer) to explore avaliable attribute for your organization.

If your organization email address is "@example.com", most likely
your configuration will be as below

```ini
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
delay_sec = 0.1
```

Create a new file simple_login.py with the following code:

```python
import streamlit as st
from streamlit_ldap_authenticator import Authenticate

# Declare the authentication object
auth = Authenticate(
    st.secrets['ldap'],
    st.secrets['session_state_names'],
    st.secrets['auth_cookie']
)

# Login Process
user = auth.login()
if user is not None:
    auth.createLogoutForm({'message': f"Welcome {user['displayName']}"})

    # Your page application can be written below
    st.write("# Welcome to my App! 👋")
    st.write(user)
```

Run the streamlit app!

```terminal
streamlit run simple_login.py
```

## Add Encryption module

This is recommended if you are using http protocol as http protocol doesn't encrypt when exchanging information between server and client. So anyone in the network can see the user password if it is not encrypted.

### Gnerate RSA Key Pair

Create a new file generateKeys.py

```python
from streamlit_rsa_auth_ui import Encryptor

encryptor = Encryptor.generateNew(2048)
encryptor.save('rsa', 'authkey')
```

Run `generateKeys.py` python script

```terminal
python generateKeys.py
```

this will create a private key and public key pair

- private key with the file name `authkey`
- public key with the file name `authkey.pub`

```md
├── rsa
│ ├── authkey
│ │ authkey.pub
```

### Add Configuration

add to the secrets.toml

```ini
[encryptor]
folderPath = "rsa"
keyName = "authkey"
```

### Change the authentication declaration code

```python
# Declare the authentication object
auth = Authenticate(
    st.secrets['ldap'],
    st.secrets['session_state_names'],
    st.secrets['auth_cookie'],
    st.secrets['encryptor']
)
```

## Configuration Objects

### LdapConfig

Configuration for your organization active directory
| Name | Type | Description
| ----------- | --------- | -----------
| server_path | str | Active directory server path. E.g. 'ldap://ldap.example.com'
| domain | str | Your organization domain. E.g. 'Example'
| search_base | str | Active directory base search. E.g. 'dc=example, dc=com'
| attributes | List[str] | Attribute avaliable in your organization active directory. You can reference in [ADExplorer](https://learn.microsoft.com/en-us/sysinternals/downloads/adexplorer)
| use_ssl | bool | Determine whether to use basic SSL basic authentication

### SessionStateConfig

Configuration for streamlit [Session State](https://docs.streamlit.io/library/api-reference/session-state) key names
| Name | Type | Description
| ----------- | ---- | -----------
| user | str | Key name to store user information
| remember_me | str | Key name to store remember_me checkbox selection

### CookieConfig

Configuration to store user information to the cookie in client's browser. Thus even when user close the browser and reload the page, Reauthorization is possible with cookie.
| Name | Type | Description
| ------------ | ----- | -----------
| name | str | cookie name to store in client's browser
| key | str | encryption key to encrypt user information
| expiry_days | float | expiry date for the cookie
| auto_renewal | bool | Cookie will expire after defined days from the **last activity** when value is `True`. Cookie will expire after defined days from the **last login** when value is `False`.
| delay_sec | float | Delay in sec after set or delete cookie

### EncryptorConfig

Configuration for encryption key location to encrypt user information at the client browser before send back to server.
| Name | Type | Description
| ---------- | ---- | -----------
| folderPath | str | Folder location where the encryption key is stored. (Make sure the key location is private)
| keyName | str | The name of the key

### TitleConfig

| Name  | Type                                                                | Description                                                                                                                           |
| ----- | ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| text  | str \| None                                                         | Optional title text                                                                                                                   |
| size  | 'smaller' \| 'small' \| 'medium' \| 'large' \| 'extraLarge' \| None | Optional title size                                                                                                                   |
| align | 'left' \| 'center' \| 'right' \| None                               | Optional text alignment                                                                                                               |
| args  | dict \| None                                                        | Optional additional title properties can be reference in [Ant Design Title](https://ant.design/components/typography#typographytitle) |

### RequiredRule

| Name        | Type         | Description                                               |
| ----------- | ------------ | --------------------------------------------------------- |
| required    | bool         | `True` if the item is required                            |
| message     | str \| None  | Optional error message if violate the required rule       |
| warningOnly | bool \| None | Warning only if `True` and will not block the form submit |

### PatternRule

| Name        | Type         | Description                                               |
| ----------- | ------------ | --------------------------------------------------------- |
| pattern     | str          | Regex pattern                                             |
| message     | str \| None  | Optional error message if violate the pattern rule        |
| warningOnly | bool \| None | Warning only if `True` and will not block the form submit |

### TextInputConfig

| Name        | Type                                     | Description                                                                                                          |
| ----------- | ---------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| placeholder | str \| None                              | Optional placeholder for text input                                                                                  |
| label       | str \| None                              | Optional label will be display left of text input in wide screen size and top of text input in small screen size     |
| width       | str \| None                              | Optional width of the input [Reference](https://www.w3schools.com/cssref/pr_dim_width.php)                           |
| required    | RequiredRule \| bool \| dict \| None     | Optional required rule                                                                                               |
| patterns    | List[PatternRule \| str \| dict] \| None | Optional pattern rules                                                                                               |
| args        | dict \| None                             | optional additional input properties can be reference in [Ant Design Input](https://ant.design/components/input#api) |

### CheckboxConfig

| Name     | Type                                 | Description                                                                                                                |
| -------- | ------------------------------------ | -------------------------------------------------------------------------------------------------------------------------- |
| label    | str \| None                          | label will be display right of checkbox                                                                                    |
| width    | str \| None                          | Optional width of the checkbox [Reference](https://www.w3schools.com/cssref/pr_dim_width.php)                              |
| required | RequiredRule \| bool \| dict \| None | Optional required rule                                                                                                     |
| args     | dict \| None                         | optional additional input properties can be reference in [Ant Design Checkbox](https://ant.design/components/checkbox#api) |

### ButtonConfig

| Name  | Type         | Description                                                                                                             |
| ----- | ------------ | ----------------------------------------------------------------------------------------------------------------------- |
| label | str \| None  | Optional button label                                                                                                   |
| width | str \| None  | Optional width of the button [Reference](https://www.w3schools.com/cssref/pr_dim_width.php)                             |
| args  | dict \| None | Optional additional button properties can be reference in [Ant Design Button](https://ant.design/components/button#api) |

### SigninFormConfig

| Name        | Type                                   | Description                                                                                                      |
| ----------- | -------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| formType    | 'default' \| 'inline' \| None          | Will be 'default' if None                                                                                        |
| labelSpan   | int \| None                            | Label Layout                                                                                                     |
| wrapperSpan | int \| None                            | Layout of the input control                                                                                      |
| maxWidth    | int \| None                            | Max form width                                                                                                   |
| align       | 'left' \| 'center' \| 'right' \| None  | Horizontal form alignment                                                                                        |
| title       | TitleConfig \| str \| dict \| None     | Config for title control of the form                                                                             |
| submit      | ButtonConfig \| str \| dict \| None    | Config for submit button of the form                                                                             |
| username    | TextInputConfig \| str \| dict \| None | Config for username input of the form                                                                            |
| password    | TextInputConfig \| str \| dict \| None | Config for password input of the form                                                                            |
| remember    | CheckboxConfig \| str \| dict \| None  | Config for remember checkbox of the form                                                                         |
| args        | dict \| None                           | Optional addtional form properties can be reference in [Ant Design Form](https://ant.design/components/form#api) |

### SignoutFormConfig

| Name     | Type                                  | Description                                                                                                      |
| -------- | ------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| formType | 'default' \| 'inline' \| None         | Will be 'default' if None                                                                                        |
| maxWidth | int \| None                           | Max form width                                                                                                   |
| align    | 'left' \| 'center' \| 'right' \| None | Horizontal form alignment                                                                                        |
| title    | TitleConfig \| str \| dict \| None    | Config for title control of the form                                                                             |
| submit   | ButtonConfig \| str \| dict \| None   | Config for submit button of the form                                                                             |
| args     | dict \| None                          | Optional addtional form properties can be reference in [Ant Design Form](https://ant.design/components/form#api) |

## Callback Extension

Addtional task can be executed upon successful login or logout\
Login Process is as follow

- Reauthenticate from Session state, if unsuccessful
- Reauthenticate form cookie, if unsuccessful
- Ask user input
- Login to Active Directory
- Execute `additionalCheck` argument function
- Execute `callback` argument function
- Save user info in Session state
- Save encrypted user info in cookie

Logout Process is as follow
When user click `Sign out` button

- Execute `callback` argument function. If `'cancel'` is return, will not continue
- Delete user info from Session state
- Delete encrypted user info in cookie

Create a new file simple_login_callback.py with the following code:

```Python
import streamlit as st
from streamlit_rsa_auth_ui import SignoutEvent
from streamlit_ldap_authenticator import Authenticate, UserInfos
from typing import Optional, Union, Literal

# Declare the authentication object
auth = Authenticate(
    st.secrets['ldap'],
    st.secrets['session_state_names'],
    st.secrets['auth_cookie']
)

def login(user: Union[UserInfos, str]) -> Optional[str]:
    st.session_state.TestSs = {"login_successful": True}

def logout(event: SignoutEvent) -> Optional[Literal['cancel']]:
    if 'TestSs' in st.session_state:
        del st.session_state.TestSs
    if 'TestSs' in st.session_state:
        return 'cancel'

# Login Process
user = auth.login(callback=login)
if user is not None:
    auth.createLogoutForm({'message': f"Welcome {user['displayName']}"}, callback=logout)

    # Your page application can be written below
    st.write("# Welcome to my App! 👋")
    st.write(user)
```

## More Examples

### Addtional check with job title after ldap authentication completed

Create a new file title_login.py with the following code:

```python
import streamlit as st
from streamlit_ldap_authenticator import Authenticate, Connection, UserInfos
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
    auth.createLogoutForm({'message':f"Welcome {user['displayName']}"})

    # Your page application can be written below
    st.write("# Welcome to my App! 👋")
    st.write(user)
```

Now run it to open the app!

```terminal
streamlit run title_login.py
```

### Additional check with reporting structure after ldap authentication completed

Create a new file report_login.py with the following code:

```python
import streamlit as st
from streamlit_ldap_authenticator import Authenticate, Connection, UserInfos
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
    auth.createLogoutForm({'message':f"Welcome {user['displayName']}"})

    # Your page application can be written below
    st.write("# Welcome to my App! 👋")
    st.write(user)
```

Now run it to open the app!

```terminal
streamlit run report_login.py
```

### Additional check against list of users after ldap authentication completed

Create a new file list_login.py with the following code:

```python
import streamlit as st
from streamlit_ldap_authenticator import Authenticate, Connection, UserInfos
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
    auth.createLogoutForm({'message':f"Welcome {user['displayName']}"})

    # Your page application can be written below
    st.write("# Welcome to my App! 👋")
    st.write(user)
```

Now run it to open the app!

```terminal
streamlit run list_login.py
```

## Change Log

### Version 0.0.4

- Initial release

### Version 0.0.5

- default use_ssl for ldap connection to `True`
- Added use_ssl configuration in `LdapConfig`

### Version 0.0.6

- fix page application not working when auto renewal for cookie config is configured.

### Version 0.1.0

- Add encryption module
- Change user interface
- More customizable form config
- Remove LoginFormConfig and LogoutFormConfig

### Version 0.1.1

- Add pyjwt in the install requirement

### Version 0.2.0

- Add callback argument in login and logout

### Version 0.2.1

- Fix cannot login if encryptor module is provided.
- Fix cookie auto renewal not working when no additionalCheck parameter is provided.

### Version 0.2.2

- Fix misleading error message of "Wrong username or password" when there is an exception occured during ldap connection

### Version 0.2.3

- Enhance security by clearing password from Connection object after bind.

### Version 0.2.4

- Fix 'no attribute in signinevent' when cookie option is disabled.

### Version 0.2.5

- Add Optional delay_sec in cookie config for set and del cookie.

[pypi_badge]: https://img.shields.io/pypi/v/streamlit-ldap-authenticator.svg
[pypi_link]: https://pypi.org/project/streamlit-ldap-authenticator
[pypi_download_badge]: https://static.pepy.tech/badge/streamlit-ldap-authenticator
[github_badge]: https://badgen.net/badge/icon/GitHub?icon=github&color=black&label
[github_link]: https://github.com/NathanChen198/streamlit-ldap-authenticator
[license_badge]: https://img.shields.io/badge/Licence-MIT-gr.svg
[license_link]: https://github.com/NathanChen198/streamlit-ldap-authenticator/blob/main/LICENSE
[issue_badge]: https://img.shields.io/github/issues/NathanChen198/streamlit-ldap-authenticator
[issue_link]: https://github.com/NathanChen198/streamlit-ldap-authenticator/issues
[pull_badge]: https://img.shields.io/github/issues-pr/NathanChen198/streamlit-ldap-authenticator
[pull_link]: https://github.com/NathanChen198/streamlit-ldap-authenticator/pulls
