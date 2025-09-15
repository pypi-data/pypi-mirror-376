# Usage of the `hana_cloud_interface` package 

This package provides a simple interface to connect to SAP HANA Cloud databases and execute SQL queries. Below are some examples of how to use the package.


## example
the main function is very simple It takes a SQL command as a string and returns the data
```python
import hana_cloud_interface as hci

sql_command = """
SELECT top 10
    "data1"
    "data2"
FROM "table1"
"""
    
data = hci.hana_sql(sql_command)

```

## Configuration file
You need specify the location of your configuration file by setting the `config_file` attribute of the `hci` module. For example:

```python
hci.config_file = 'location of configuration file'
```
the configuration file is a .json file
```python
{
    "CLIENT_ID": "",
    "CLIENT_SECRET": "",
    "AUTH_URL": "",
    "TOKEN_URL": "",
    "protected_url": "",
    "REDIRECT_URI": "",
    "SCOPE": "",
	"HC_prod_URL": ""
}
```