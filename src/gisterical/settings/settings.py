import json
from pathlib import Path

from attrs import define


@define
class Settings:
    conn_str: str
    cities_data: str
    countries_data: str


def load_settings() -> Settings:
    with open(Path().resolve() / "src/gisterical/settings/settings.json", "r") as f:
        s = json.load(f)
        conn_str = f"postgresql+psycopg2://{s['user']}:{s['password']}@{s['hostname']}/{s['database_name']}"
        return Settings(conn_str=conn_str, cities_data=s['cities_data'], countries_data=s['countries_data'])
    

def update_settings():
    sett_dict = {}
    
    db_name = input('Enter database name: ')
    
    host = input('Enter hostname or Enter to keep default "localhost": ')
    if not host:
        host = 'localhost'
    
    user = input('Enter user name of database owner: ')
    password = input('Enter password of database owner: ')

    with open(Path().resolve() / "src/gisterical/settings/settings.json", "r") as f:
        s = json.load(f)
        
    sett_dict = {
        'cities_data': s['cities_data'],
        "countries_data": s["countries_data"],
        "database_name": db_name,
        "user": user,
        "password": password,
        "hostname": host,
    }
    
    with open(Path().resolve() / "src/gisterical/settings/settings.json", "w") as f:
        json.dump(sett_dict, f)
        

if __name__ == '__main__':
    update_settings()   

    