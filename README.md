# applitools
My application for Applitools Visual AI Rockstar Hackathon 2019

System requirements:
	- Python 3.6 or later (with an up-to-date version of pip) installed 
	- Chrome browser supporting headless mode installed
	- Chromedriver with appropriate version to the installed Chrome browser
	- Chromedriver executable location included in PATH environment variable

How to execute "Traditional Tests":
	1. `pip install -r requirements.txt`
	2. to switch System Under Test set `base_url` in `config.ini`
	3. `python -m pytest TraditionalTests.py`
