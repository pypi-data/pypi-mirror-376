from setuptools import setup, find_packages

setup(
    name='SSIaquitaine',
    version='0.1.0',
    author='Mohamed Redha Abdessemed',
    author_email='mohamed.abdessemed@eurocybersecurite.fr',
    description='Un outil de gestion de projet pour un SSI (Système de Sécurité Informatique).',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/tuteur1/SSIaquitaine',
    project_urls={
        'Documentation': 'https://github.com/tuteur1/SSIaquitaine#readme',
        'Source': 'https://github.com/tuteur1/SSIaquitaine',
        'Issues': 'https://github.com/tuteur1/SSIaquitaine/issues',
    },
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Security',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Framework :: Setuptools Plugin',
    ],
    python_requires='>=3.9',
    install_requires=[
        'pytest',
    ],
    entry_points={
        'console_scripts': [
            'ssiaquitaine-welcome=ssiaquitaine.core:cli_welcome',
        ],
    },
)
