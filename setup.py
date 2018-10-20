from setuptools import find_packages, setup

setup(
    name='gettor',
    version='1.0.0',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'flask', 'sqlalchemy', 'werkzeug', 'click', 'wtforms', 'requests', 'lxml', 'requests', 'flask_wtf',
        'flask_sqlalchemy'
    ],
)
