import requests
import configloader
import logging
import sqlalchemy
import datetime
from decimal import Decimal
import json

import database as db

log = logging.getLogger(__name__)

# Define all the database tables using the sqlalchemy declarative base
class Blockonomics:

    @staticmethod
    def fetch_new_btc_price():
        url = 'https://www.blockonomics.co/api/price'
        params = {'currency':configloader.user_cfg["Payments"]["currency"]}
        r = requests.get(url,params)
        if r.status_code == 200:
          price = r.json()['price']
          print ('Bitcoin price ' + str(price))
          return price
        else:
          print(r.status_code, r.text)

    @staticmethod
    def new_address(reset=False):
        api_key = configloader.user_cfg["Bitcoin"]["api_key"]
        secret = configloader.user_cfg["Bitcoin"]["secret"]
        url = 'https://www.blockonomics.co/api/new_address'
        if reset == True:
          url += '?match_callback='+secret+'&reset=1'
        else:
          url += "?match_callback=" + secret
        headers = {'Authorization': "Bearer " + api_key}
        print(url)
        r = requests.post(url, headers=headers)
        if r.status_code == 200:
          return r
        else:
          print(r.status_code, r.text)
          return r

class BlockonomicsPoll:

    def __init__(self, bot, engine) -> None:
        self.bot = bot

        log.debug(f"Opening new database session for Blockonomics Poll")
        self.session = sqlalchemy.orm.sessionmaker(bind=engine)()

    def __del__(self):
        self.session.close()

    def check_for_pending_transactions(self) -> None:

        pending_addresses = [o.address for o in self.session.query(db.BtcTransaction.address).filter(db.BtcTransaction.status != 2)]
        print("Checking for addresses ", pending_addresses)
        if not pending_addresses: return

        response = self._get_history_for_addresses(addresses=pending_addresses)
        print("Response: ", response)
        # Update Pending Transactions
        for transaction in response.get('pending', []):
            self.handle_update(
                address=transaction['addr'][0],
                status=transaction['status'],
                satoshi=transaction['value'],
                txid=transaction['txid']
            )

        # Update Confirmed Transactions
        for transaction in response.get('history', []):
            self.handle_update(
                address=transaction['addr'][0],
                status=2,
                satoshi=transaction['value'],
                txid=transaction['txid']
            )

    def _get_history_for_addresses(self, addresses: list) -> dict:
        
        api_key = configloader.user_cfg["Bitcoin"]["api_key"]

        url = "https://www.blockonomics.co/api/searchhistory"
        body = { "addr": ", ".join(addresses) }
        headers = { "Authorization": "Bearer %s" % api_key }

        print("URL: ", url)
        print("Body: ", body)
        print("Headers: ", headers)
        
        r = requests.post(
            url=url,
            data=json.dumps(body),
            headers=headers
        )

        if r.status_code == 200:
            return r.json()
        else:
          print(r.status_code, r.text)
          return {"pending": [], "history": []}

    def _satoshi_to_fiat(self, satoshi, transaction_price) -> float:
        """Convert satoshi to fiat"""

        received_btc = satoshi/1.0e8
        received_dec = round(Decimal(received_btc * transaction_price), int(configloader.user_cfg["Payments"]["currency_exp"]))
        return float(received_dec)

    def handle_update(self, address, status, satoshi, txid):
        """Handles Transaction Updates"""

        transaction = self.session.query(db.BtcTransaction).filter(db.BtcTransaction.address == address).one_or_none()
        if transaction and transaction.txid == "":
            
            # Check the status
            if transaction.status == -1:
                current_time = datetime.datetime.now()
                timeout = 30

                # If timeout has passed, use new btc price
                if current_time - datetime.timedelta(minutes = timeout) > datetime.datetime.strptime(transaction.timestamp, '%Y-%m-%d %H:%M:%S.%f'):
                    transaction.price = Blockonomics.fetch_new_btc_price()
                transaction.timestamp = current_time
                transaction.status = 0
                self.bot.send_message(transaction.user_id, "Payment recieved!\nYour account will be credited on confirmation.")
            
            if status == 2:
                received_float = self._satoshi_to_fiat(satoshi, transaction.price)

                print ("Recieved %(received_float)s %(currency)s on address %(address)s" % {
                    "received_float": received_float,
                    "currency": configloader.user_cfg["Payments"]["currency"],
                    "address": address
                })

                # Add the credit to the user account
                user = self.session.query(db.User).filter(db.User.user_id == transaction.user_id).one_or_none()
                user.credit += int(received_float * (10 ** int(configloader.user_cfg["Payments"]["currency_exp"])))

                # Add a transaction to list
                new_transaction = db.Transaction(
                    user=user,
                    value=int(received_float * (10 ** int(configloader.user_cfg["Payments"]["currency_exp"]))),
                    provider="Bitcoin",
                    notes = address
                )

                # Add and commit the transaction
                self.session.add(new_transaction)

                # Update the received_value for address in DB
                transaction.value += received_float
                transaction.txid = txid
                transaction.status = 2
                self.session.commit()

                self.bot.send_message(
                    transaction.user_id, 
                    "Payment confirmed!\nYour account has been credited with %(received_float)s %(currency)s." % {
                        "recevied_float": received_float,
                        "currency": configloader.user_cfg["Payments"]["currency"]
                    }
                )

                return "Success"
            else:
                self.session.commit()
                return "Not enough confirmations"
        else:
            self.session.commit()
            return "Transaction already proccessed"
        