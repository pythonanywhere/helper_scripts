# Legacy scripts 

We still provide separate scripts for specific actions that are now all integrated 
into unified `pa` cli tool. We will keep them available for people who rely on them in 
their workflow, but we plan to drop them when we release 1.0.

There are scripts provided for dealing with web apps: 

* [pa_autoconfigure_django.py](https://github.com/pythonanywhere/helper_scripts/blob/master/scripts/pa_autoconfigure_django.py)
* [pa_create_webapp_with_virtualenv.py](https://github.com/pythonanywhere/helper_scripts/blob/master/scripts/pa_create_webapp_with_virtualenv.py)
* [pa_delete_webapp_logs.py](https://github.com/pythonanywhere/helper_scripts/blob/master/scripts/pa_delete_webapp_logs.py)
* [pa_install_webapp_letsencrypt_ssl.py](https://github.com/pythonanywhere/helper_scripts/blob/master/scripts/pa_install_webapp_letsencrypt_ssl.py)
* [pa_install_webapp_ssl.py](https://github.com/pythonanywhere/helper_scripts/blob/master/scripts/pa_install_webapp_ssl.py)
* [pa_reload_webapp.py](https://github.com/pythonanywhere/helper_scripts/blob/master/scripts/pa_reload_webapp.py)
* [pa_start_django_webapp_with_virtualenv.py](https://github.com/pythonanywhere/helper_scripts/blob/master/scripts/pa_start_django_webapp_with_virtualenv.py)

and scheduled tasks:

* [pa_create_scheduled_task.py](https://github.com/pythonanywhere/helper_scripts/blob/master/scripts/pa_create_scheduled_task.py)
* [pa_delete_scheduled_task.py](https://github.com/pythonanywhere/helper_scripts/blob/master/scripts/pa_delete_scheduled_task.py)
* [pa_get_scheduled_tasks_list.py](https://github.com/pythonanywhere/helper_scripts/blob/master/scripts/pa_get_scheduled_tasks_list.py)
* [pa_get_scheduled_task_specs.py](https://github.com/pythonanywhere/helper_scripts/blob/master/scripts/pa_get_scheduled_task_specs.py)
* [pa_update_scheduled_task.py](https://github.com/pythonanywhere/helper_scripts/blob/master/scripts/pa_update_scheduled_task.py)

Run any of them with `--help` flag to get information about usage.   

See the [blog post](https://blog.pythonanywhere.com/155/) about how it all started.
