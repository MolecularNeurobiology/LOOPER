"""
FMP19 Connector
"""

# %% import libraries
#from fmrest import dataAPI
from fmrest import server
# %% define functions

SERVER_IP = "https://3.141.29.47"
USER = "AWS_admin"
PASSWORD = "testmicemakemoney"
DATABASE = "MICE"
LAYOUT = "Autoresuscitation"

table_keys = [
    'PlyUID',
    'RUID',
    'Project Number'
]

DATABASE_PM = "Project_Management"
LAYOUT_PM = "Project_Management"

table_keys_pm = [
    'Project Identification Number',
    'Project_ID_Title'
]
credentials = {
    'ip':SERVER_IP,
    'user':USER,
    'password':PASSWORD
}

# %%= fmrest.

def pull_the_table(
    credentials,
    database,
    layout,
    table_keys
):
    SERVER_IP = credentials['ip']
    USER = credentials['user']
    PASSWORD = credentials['password']
    DATABASE = database
    LAYOUT = layout

    fms =  server.Server(
        SERVER_IP,
        user=USER,
        password=PASSWORD,
        database=DATABASE,
        layout=LAYOUT,
        api_version="v2",
        verify_ssl=False
    )

    records = []
    offset = 0
    limit = 100
    fms.login()

    while True:
        try:
            print(f'{offset}-{len(records)}')
            if offset == 0:
                current_records = fms.get_records() 
            else:
                current_records = fms.get_records(offset=offset)
            records+=[i for i in current_records]
            offset += limit
            if not current_records.is_complete: break

        except Exception as e:
            print(e)
            break
        
    fms.logout()


    record_dict = {
        i['recordId']:{
            k:i[k] for k in table_keys 
        } for i in records
    }
    return record_dict

# %%
def pull_specific_record(credentials,database,layout,search_args,table_keys):
    SERVER_IP = credentials['ip']
    USER = credentials['user']
    PASSWORD = credentials['password']
    DATABASE = database
    LAYOUT = layout

    fms =  server.Server(
        SERVER_IP,
        user=USER,
        password=PASSWORD,
        database=DATABASE,
        layout=LAYOUT,
        api_version="v2",
        verify_ssl=False
    )

    fms.login()

    records = fms.find([search_args])

    fms.logout()
    record_dict = {
        i['recordId']:{
            k:i[k] for k in table_keys 
        } for i in records
    }


    return record_dict

# %%

projects = pull_the_table(credentials,DATABASE_PM,LAYOUT_PM,table_keys_pm)
ruids = pull_the_table(credentials,DATABASE,LAYOUT,table_keys)
# %%
pm_for_r2222 = pull_specific_record(
    credentials,
    DATABASE,
    LAYOUT,
    {'RUID':'R2222'},
    table_keys
)

# %%


# %% define main()
def main():
    pass

# %% run main
if __name__ == "__main__":
    main()