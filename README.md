To set up this script:

1. Create a new Python virtualenv
2. `pip install -r requirements.txt`
3. `python kdmomatic.py`
4. Edit `config.json` (generated by running kdmomatic.py) to contain your FTP server and a Gmail API client ID and client secret obtained from the [Google Developer Console](https://console.developers.google.com/)
5. `python kdmomatic.py`
6. Follow the instructions output by kdmomatic.py

And now you can just run kdmomatic.py at regular intervals, for example using a cronjob.