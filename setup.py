from setuptools import setup
from djappdep.djappdep import __version__

setup(
    name='djdep',
    version=__version__,
    packages=['djappdep'],
    url='https://beatonma.org',
    license='',
    author='Michael Beaton',
    author_email='beatonma@gmail.com',
    description='Show relationships between project apps, ignoring 3rd party packages.',
    entry_points={
        'console_scripts': [
            'djdep = djappdep.djappdep:main',
        ]
    }
)
