# Geomancer

Geomancer is a project with a simple goal: to create a prototype tool that will help journalists easily mash up data based on shared geography. It’s such a common task for data-savvy journalists that it’s easy to underestimate the difficulty. But on deadline, it can become daunting. It requires locating the right data set to provide context, getting it into shape and into place to join it with the data in hand and then merging the two data sets — all before the reporter can even get started with the analysis.

We aim to take some of that complexity out of the way by providing an intuitive interface to discover available data sets for a given geography and supplement the data in hand with the relevant values. We’ll know it’s working when it appears too easy.

Read more: [AP wins Knight grant to build data journalism tool](http://www.ap.org/content/press-release/2013/ap-wins-knight-grant-to-build-data-journalism-tool)

### Setup

**Install OS level dependencies:** 

* Python 2.7
* Redis

**Install app requirements**

```bash
$ pip install -r requirements.txt
$ cp geo/app_config.py.example geo/app_config.py
```

### Running Geomancer

There are three components that should be running simultaneously for the app to work: Redis, the Flask app, and the worker process that appends to the spreadsheets. For debugging purposes, it is useful to run these three processes in separate terminal sessions. 

``` bash 
$ redis-server # This command may differ depending on your OS
$ python runworker.py # starts the worker for processing files
$ python runserver.py # starts the web server
```

Open your browser and navigate to `http://localhost:5000`

## DataMade Team

* [Eric van Zanten](https://github.com/evz)
* [Cathy Deng](https://github.com/cathydeng)
* [Derek Eder](https://github.com/derekeder)

## Errors / Bugs

If something is not behaving intuitively, it is a bug, and should be reported.
Report it here: https://github.com/associatedpress/geomancer/issues

## Note on Patches/Pull Requests
 
* Fork the project.
* Make your feature addition or bug fix.
* Commit, do not mess with rakefile, version, or history.
* Send me a pull request. Bonus points for topic branches.

## Copyright

Copyright (c) 2014 Associated Press. Released under the [MIT License](https://github.com/associatedpress/geomancer/blob/master/LICENSE).
