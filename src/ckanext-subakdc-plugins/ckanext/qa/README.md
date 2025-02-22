# QA Plugin

The QA CKAN plugin defines several tasks that report on the quality of datasets in the data catalogue. It also defines actions that can be taken on the selected datasets in the reports

By default the results of each QA task are evaluated on a given package when the package if first created and then every time it is updated.

# Runing QA taska via the command line
To run all of the QA tasks on every package in the catalogue, run:

```
make qa.run
```

or to run just one task over all packages:

```
make ssh.ckan
ckan qa run {task_name}
```

The `{task_name}` must match one of the keys in the `tasks` dict in `__init__.py`

# Defining a new QA task
- Copy an existing qa file (e.g. qa_no_resources.py) to a new python file named `qa_{task_name}.py` in this directory
- Update `QA_PROPERTY_NAME` and add any actions you need into the `QA_ACTIONS` variable
- Rename classes and the `{task_name}_report_info variable` as per your new task's name
- Update the information in the `{task_name}_report_info` dict
- Update the `evaluate` and `should_show_in_report` methods (these are the conditions for setting the qa property on the model and whether a dataset should appear in the report respectively). Also update the `generate` method if you want to display different dataset fields in the report.

For the report template:
- Copy an existing report in `template/report` (e.g. qa_no_resources.html) to a new file and name it `qa_{task_name}.html`
- Update this new file as required

Finally:
- Import and add your new task to the `tasks` list in `__init__.py`
- Import and add you task report to `reports` list in `__init__.py`

Note:
Redis will cache job commands so if you change code you need to run:  
`make restart.redis`  

# Cold start
The first time you run reporting you will need to run `make qa.init` to create the database tables.