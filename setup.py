from pathlib import Path
from setuptools import setup

here = Path(__file__).parent

# Get the long description from the README file
with (here / 'README.md').open(encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='pythonanywhere',
    version='0.6',
    description='PythonAnywhere helper tools for users',
    long_description=long_description,
    url='https://github.com/pythonanywhere/helper_scripts/',
    author='PythonAnywhere LLP',
    author_email='developers@pythonanywhere.com',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.5',
    ],

    keywords='pythonanywhere api cloud web hosting',
    # packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    packages=['pythonanywhere'],
    install_requires=[
        'docopt',
        'requests',
    ],
    extras_require={},
    python_requires='>=3.5',
    package_data={},
    data_files=[],
    entry_points={},
    scripts=[
        'scripts/pa_install_webapp_letsencrypt_ssl.py',
        'scripts/pa_install_webapp_ssl.py',
        'scripts/pa_start_django_webapp_with_virtualenv.py',
        'scripts/pa_autoconfigure_django.py',
        'pythonanywhere/snakesay.py',
    ]
)
