from setuptools import setup, find_packages

setup(
    name="osmxmpp",
    version="1.0.1",

    author="osmiumnet",
    description="Python XMPP library",

    packages=find_packages(),
    install_requires=[
        "osmxml==1.0.1",
        "osmomemo==1.1.2",
    ],
    python_requires=">=3.10",
)
