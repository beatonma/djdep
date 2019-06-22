from setuptools import setup

setup(
    name='djdep',
    version='0.1',
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
