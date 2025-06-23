# import libraries
import fm_tools
import pandas


# constants
fm_connect_dict = {
    "RIGNAME": "VM SCRIPT RUNNER",
    "SERVER_IP" : "https://10.140.180.26",
    "USER" : "Python",
    "PASSWORD" : "python",
    "DATABASE" : "MICE",
    "LAYOUT" : "Autoresuscitation",
    "Tank_Number" : "unk",
    "Facemask_ID" : "unk"
}

credentials = {
    "ip" : "https://10.140.180.26",
    "user" : "Python",
    "password" : "python",
}
email_keys = ["ToGeneral", "ToEngineers", "ToChris", "From", "CC"]

# collect email list
email_form = fm_tools.pull_the_table(credentials=credentials, database="MICE",layout="Error_List",table_keys=email_keys)
email_list = list(set([[i for i in v["ToGeneral"].split()]+[i for i in v["ToEngineers"].split()]+[i for i in v["ToChris"].split()]+[i for i in v["From"].split()]+[i for i in v["CC"].split()] for k,v in email_form.items()][0]))
print(email_list)

# collect error reports
error_dict = fm_tools.pull_the_table(credentials=credentials, database="MICE",layout="Rigs_Error_Log",table_keys=None)
error_df = pandas.DataFrame(error_dict).transpose()
print(error_df)
print('columns are >>>')
print(error_df.columns)


# summary sheets (recommend filter for last month)

# "all errors" list of all records sort by "error_type", "Component", "error_status"

# "facemask" filter df.Component=="Facemask", aggregate by day > "Component" (count) (make graphs if possible, try other aggregates if possible) 

# "rig" filter by date range, aggregate by "Plethysmography::Rig'" > "Component" (count)


