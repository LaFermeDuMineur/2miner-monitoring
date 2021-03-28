import requests
from datetime import datetime
from elasticsearch import Elasticsearch
import time
import pytz
import cli.app
import logging

factor = 0.000001
bounty_factor = 0.000000001


def write_pay(item, readable, es):
    for pay in item:
        bounty = {
            "Amount": pay['amount'] * bounty_factor,
            "pay_date": pay['timestamp'],
            "Date": readable
        }
        logging.debug(es.index(index='bounty', body=bounty))


def write_worker(item, readable, es):
    for miner in item:
        farm = {
            "Miner": miner,
            "Global_hashrate": item[miner]['hr'] * factor,
            "offline": item[miner]['offline'],
            "Date": readable
        }
        logging.debug(es.index(index='miner', body=farm))


def write_global(item, readable, es):
    global_info = {
        "Global_hashrate": item['currentHashrate'] * factor,
        "paiement": item['paymentsTotal'],
        "Date": readable,
        "workersOnline": item['workersOnline'],
        "workersOffline": item['workersOffline'],
        "workersTotal": item['workersTotal']
    }
    logging.debug(es.index(index='2miner', body=global_info))


def es_entry_point(walletid):
    # Connect to the elastic cluster
    es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
    logging.info(es.info())

    while True:
        r = requests.get('https://eth.2miners.com/api/accounts/{}'.format(walletid))
        logging.info('{} {}'.format(r.status_code, r.url))
        result = r.json()
        readable = datetime.fromtimestamp(result['updatedAt'] * 0.001, pytz.UTC).isoformat()
        write_global(result, readable, es)
        write_pay(result['payments'], readable, es)
        write_worker(result['workers'], readable, es)
        time.sleep(10)

def set_log_lvl(log_lvl):
    if log_lvl == 'INFO':
        return logging.INFO
    return logging.debug

@cli.app.CommandLineApp(name='2miner-monitoring')
def main(app):
    logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', level=set_log_lvl(app.params.log_level))
    es_entry_point(app.params.wallet)


# Build the options of the CLI
main.add_param("-w", "--wallet", type=str, help="wallet id", required=True)
main.add_param("-l", "--log_level", type=str, help="Log Level", default='INFO')

if __name__ == '__main__':
    main.run()
