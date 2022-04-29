# ai_engineering
Sky Global Reliability Technical Test for the AI Engineering Team 2nd stage interview.

A script to ingest time metrics data into a database and a API server to extract the data.

## Setup

Make sure PostgreSQL is installed. If PostgreSQL is not installed, I recommend using this link https://www.tutorialspoint.com/postgresql/postgresql_environment.html.


In a local directory or in a virtual environment, download the files from the git repo and cd into the folder.
```bash
git clone https://github.com/chrismalcolm/ai_engineering.git
cd ai_engineering
```

Download the requirements.
```bash
sudo apt-get install python-psycopg2
sudo apt-get install libpq-dev
pip3 install -r requirements.txt
```

Setup the database tables and user.
```bash
sudo -u postgres psql -f setup.sql
```

## Ingestion script

To run the ingestion script
```bash
python3 ingester.py
```

This will add new time metric data into the `metrics` table. The data added will be printed by the script. The timestamps of the data will cover the last five minutes.


## API Server

To run the API server
```bash
python3 server.py
```
The process will run in the terminal. To shutdown the API server, trigger a KeyboardInterrupt with `^C`

## API design

The backend API accepts POST requests made to the `/query` path, to access data from the PostgreSQL database. The request must have the `Content-Type:application/json` header as well as a JSON body. The response will be results in a JSON list, with ordered entries listed as JSON objects.

The parameters in the JSON body determine what data is returned and how. Below is the schema for the API

| Parameter | Type | Mandatory | Description |
| - | - | - | - |
| metadata | list | Yes | Determines which categories should be returned |
| criteria | Object | No | Keys are categories, values are Objects with "more than" or "less than" item pairs |
| order_by | string | No | Category to order the entries in |
| reverse | boolean | No | If ordering entries, set this value to 'false' of ascending order or 'true' for descending order, default is ascending |

### Example

```json
{
    "metadata": ["timestamp", "cpu_load"],
    "criteria": {
        "cpu_load": {
            "more than": 25,
            "less than": 50
        },
        "concurrency": {
            "less than": 300000
        }
    },
    "order_by":"cpu_load",
    "reverse": true
}
```

A request with this JSON body will return the timestamp and cpu_load of all entries satisfying the criteria. The criteria is that the 25 < cpu_load < 50 and the concurrency < 300000. The results will be ordered by cpu_load, in descending order.

```bash
curl -X POST localhost:8345/query -H "Content-Type:application/json" -d '{"metadata": ["timestamp", "cpu_load"], "order_by":"cpu_load", "reverse": true, "criteria":{"cpu_load": {"less than": 50, "more than": 25}, "concurrency": {"less than": 300000}}}'
```

Returns
```json
{
    "results":[
        {"cpu_load":47.321,"timestamp":1601549758},
        {"cpu_load":44.343,"timestamp":1601549900},
        {"cpu_load":41.012,"timestamp":1601550433},
        {"cpu_load":40.971,"timestamp":1601535110},
        {"cpu_load":29.949,"timestamp":1601534810},
        {"cpu_load":28.099,"timestamp":1601549818}
    ]
}
```
