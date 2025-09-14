from setuptools import setup, find_packages

setup(
    name='pyglitch',
    version='0.1.1',
    author='GuestRoblox Studios!',
    author_email='maria.gomes23.1949@gmail.com',
    description='A library for image file manipulation, focused on data corruption and glitch effects.',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/RoVerify/pyglitch',
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
    install_requires=[

    ],
)