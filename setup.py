from setuptools import setup, find_packages

setup(
    name='django-oauth-tokens',
    version=__import__('oauth_tokens').__version__,
    description='Application for getting, refreshing and storing OAuth access_tokens for Django standalone applications',
    long_description=open('README.md').read(),
    author='ramusus',
    author_email='ramusus@gmail.com',
    url='https://github.com/ramusus/django-oauth-tokens',
    download_url='http://pypi.python.org/pypi/django-oauth-tokens',
    license='BSD',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,  # because we're including media that Django needs
    install_requires=[
        'django',
        'requests',
        'requests_oauthlib',
        'beautifulsoup4',
        'django-taggit',
        'django-annoying',
        'distributedlock',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
