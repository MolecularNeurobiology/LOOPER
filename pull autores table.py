# %%
from fmrest import server
import pandas


def pull_the_table(credentials, database, layout):
    SERVER_IP = credentials["ip"]
    USER = credentials["user"]
    PASSWORD = credentials["password"]
    DATABASE = database
    LAYOUT = layout

    fms = server.Server(
        SERVER_IP,
        user=USER,
        password=PASSWORD,
        database=DATABASE,
        layout=LAYOUT,
        api_version="v2",
        verify_ssl=False,
    )

    records = []
    offset = 0
    limit = 100
    fms.login()

    while True:
        try:
            print(f"{offset}-{len(records)}")
            if offset == 0:
                current_records = fms.get_records()
            else:
                current_records = fms.get_records(offset=offset)
            records += [i for i in current_records]
            offset += limit
            if not current_records.is_complete:
                break

        except Exception as e:
            print(e)
            break

    fms.logout()

    return records


config = {
    "RIGNAME": "Change My Name",
    "ip": "https://10.140.180.26",
    "user": "Python",
    "password": "python",
    "DATABASE": "MICE",
    "LAYOUT": "Autoresuscitation",
    "Tank_Number": "unk",
    "Facemask_ID": "unk",
}


output_path = "fm_auto_dump.csv"

print("testing")
x = pull_the_table(config, config["DATABASE"], config["LAYOUT"])
# %%
y = {i["recordId"]: {k: i[k] for k in i.keys()} for i in x}

z = pandas.DataFrame.from_dict(y).transpose()
print(z)
print(z.columns)
z.to_csv(output_path)
print("done")
