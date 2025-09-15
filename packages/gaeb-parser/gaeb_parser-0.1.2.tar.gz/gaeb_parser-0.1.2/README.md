# gaeb-parser
parses xml gaeb files and converts to table data

![Screenshot of the example import.](example_screenshot.jpg)

It uses [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) to parse the xml content of the *.x8X gaeb files.
Custom functions navigate through the tree object, collect the project data and translate the specifications data into table form.
The data ist the available as a [Pandas](https://pandas.pydata.org/) dataframe. The software only relies on the modules mentioned above.

## Use it:
`pip install gaeb-parser`

## Change it:

### Install required modules in venv

`python -m venv .venv`

`Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force`

`.venv/Scripts/activate.ps1`

`pip install -r requirements.txt`


### run tests
`Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force`

`.venv/Scripts/activate.ps1`

`pytest`

## To-Dos:
- some minor elements are not parsed yet, see console output
