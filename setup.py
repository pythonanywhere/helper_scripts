from pathlib import Path
from setuptools import setup

here = Path(__file__).parent

# Get the long description from the README file
with (here / "README.md").open(encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="pythonanywhere",
    version="0.15.3",
    description="PythonAnywhere helper tools for users",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pythonanywhere/helper_scripts/",
    author="PythonAnywhere LLP",
    author_email="developers@pythonanywhere.com",
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.8",
    ],
    keywords="pythonanywhere api cloud web hosting",
    packages=[
        "cli",
        "pythonanywhere",
    ],
    install_requires=[
        "docopt",
        "packaging",
        "python-dateutil",
        "pythonanywhere_core==0.2.2",
        "requests",
        "schema",
        "snakesay",
        "tabulate",
        "typer",
    ],
    extras_require={},
    python_requires=">=3.8",
    package_data={},
    data_files=[],
    entry_points={
        "console_scripts": [
            "pa=cli.pa:app",
        ]
    },
    scripts=[
        "scripts/pa_autoconfigure_django.py",
        "scripts/pa_create_scheduled_task.py",
        "scripts/pa_create_webapp_with_virtualenv.py",
        "scripts/pa_delete_scheduled_task.py",
        "scripts/pa_delete_webapp_logs.py",
        "scripts/pa_get_scheduled_task_specs.py",
        "scripts/pa_get_scheduled_tasks_list.py",
        "scripts/pa_install_webapp_letsencrypt_ssl.py",
        "scripts/pa_install_webapp_ssl.py",
        "scripts/pa_reload_webapp.py",
        "scripts/pa_start_django_webapp_with_virtualenv.py",
        "scripts/pa_update_scheduled_task.py",
    ],
)
