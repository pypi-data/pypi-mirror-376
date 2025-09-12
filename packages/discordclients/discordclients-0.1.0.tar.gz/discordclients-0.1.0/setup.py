from setuptools import setup, find_packages

setup(
    name='DiscordClients',
    version='0.1.0',
    description='Usage of DiscordAPI',
    author='Momwhyareyouhere',
    packages=find_packages(),
    install_requires=[
        'requests',
    ],
    python_requires='>=3.7',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
)
