from setuptools import setup , find_packages
import codecs
import os 

VERSION = '0.0.2'
DESCRIPTION = 'library to print hello in my package'
LONG_DESCRIPTION = 'A package that allows to build simple streams video'

# Setting up 
setup(
    name="Mo_Adly" , 
    version=VERSION , 
    author="MoAdly", 
    author_email="aboismaelh@gmail.com", 
    description=DESCRIPTION,
    long_description_content_type= "text/markdown", 
    long_description=LONG_DESCRIPTION, 
    packages=find_packages(),
    install_requires = [],
    keywords=['python' , 'MoAdly' , 'Hello'],
    classifiers=[
    "Development Status :: 5 - Production/Stable", 
    "Intended Audience :: Developers",
    "Programming Language :: Python :: 3", 
    "Operating System :: Unix",
    "Operating System :: MacOS :: MacOS X", 
    "Operating System :: Microsoft :: Windows", 
]
   
)