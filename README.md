# HISL Sensor GUI

## Generate `.exe` file

pyinstaller --onefile --noconsole --add-data "mysql_config.json:." HISL_Sensors_GUI.py