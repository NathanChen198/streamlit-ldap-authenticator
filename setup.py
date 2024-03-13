# Author   : Nathan Chen
# Date     : 13-Mar-2024


from pathlib import Path
from setuptools import setup, find_packages

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='UTF-8')

setup(
    name='streamlit-ldap-authenticator',
    version='0.1.0',
    author='Nathan Chen',
    author_email='nathan.chen.198@gmail.com',
    description='Authenticate using ldap',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/NathanChen198/streamlit-ldap-authenticator',
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent"
    ],
    python_requires=">=3.8",
    install_requires=[
        # By definition, a Custom Component depends on Streamlit.
        # If your component has other Python dependencies, list
        # them here.
        "streamlit >= 0.63",
        "ldap3 >= 2.9.1",
        "streamlit-cookies-controller >= 0.0.3",
        "streamlit-rsa-auth-ui >= 0.0.3"
    ],
    extras_require={
        "devel": [
            "wheel",
            "pytest==7.4.0",
            "playwright==1.39.0",
            "requests==2.31.0",
            "pytest-playwright-snapshot==1.0",
            "pytest-rerunfailures==12.0",
        ]
    }
)