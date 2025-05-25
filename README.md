FaceFusion
==========

> Industry leading face manipulation platform.

[![Build Status](https://img.shields.io/github/actions/workflow/status/testingss/testingss/ci.yml.svg?branch=master)](https://github.com/testingss/testingss/actions?query=workflow:ci)
[![Coverage Status](https://img.shields.io/coveralls/testingss/testingss.svg)](https://coveralls.io/r/testingss/testingss)
![License](https://img.shields.io/badge/license-OpenRAIL--AS-green)


Preview
-------

![Preview](https://raw.githubusercontent.com/testingss/testingss/master/.github/preview.png?sanitize=true)


Installation
------------

Be aware, the [installation](https://docs.testingss.io/installation) needs technical skills and is not recommended for beginners. In case you are not comfortable using a terminal, our [Windows Installer](http://windows-installer.testingss.io) and [macOS Installer](http://macos-installer.testingss.io) get you started.


Usage
-----

Run the command:

```
python testingss.py [commands] [options]

options:
  -h, --help                                      show this help message and exit
  -v, --version                                   show program's version number and exit

commands:
    run                                           run the program
    headless-run                                  run the program in headless mode
    batch-run                                     run the program in batch mode
    force-download                                force automate downloads and exit
    job-list                                      list jobs by status
    job-create                                    create a drafted job
    job-submit                                    submit a drafted job to become a queued job
    job-submit-all                                submit all drafted jobs to become a queued jobs
    job-delete                                    delete a drafted, queued, failed or completed job
    job-delete-all                                delete all drafted, queued, failed and completed jobs
    job-add-step                                  add a step to a drafted job
    job-remix-step                                remix a previous step from a drafted job
    job-insert-step                               insert a step to a drafted job
    job-remove-step                               remove a step from a drafted job
    job-run                                       run a queued job
    job-run-all                                   run all queued jobs
    job-retry                                     retry a failed job
    job-retry-all                                 retry all failed jobs
```


Documentation
-------------

Read the [documentation](https://docs.testingss.io) for a deep dive.
