from setuptools import setup


setup(
    name='django-minibadge',
    version='0.0.1',
    description='Minimal django app for managing and hosting badges.',
    long_description=open('README.md').read(),
    author='Rob Young',
    author_email='rob@roryoung.co.uk',
    url='http://github.com/robyoung/django-minibadge',
    license='BSD',
    packages=['minibadge'],
    package_data={'minibadge': ['templates/minibadge/*.html']},
    include_package_data=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
