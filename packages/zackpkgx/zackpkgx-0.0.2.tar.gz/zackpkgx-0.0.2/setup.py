from setuptools import setup, find_packages

VERSION = '0.0.2'
DESCRIPTION = 'Library to print hello in my package'
LONG_DESCRIPTION = 'A package that allows to build simple streams video'

# Setting up
setup(
    name="zackpkgx",  # اسم جديد وفريد
    version=VERSION,
    author="ArabCodeX",
    author_email="dina252422@gmail.com",
    description=DESCRIPTION,
    long_description_content_type="text/markdown",
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    install_requires=[],
    keywords=['python', 'zack', 'hello'],
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Operating System :: Unix",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ]
)
