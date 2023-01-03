import sys
import telegram
import configloader
import flask
import duckbot
from blockonomics import BlockonomicsPoll
import sqlalchemy

# Start the bitcoin callback listener
app = flask.Flask(__name__)

@app.route('/callback', methods=['GET'])
def callback():
    # Create a bot instance
    bot = duckbot.factory(configloader.user_cfg)(request=telegram.utils.request.Request(configloader.user_cfg["Telegram"]["con_pool_size"]))

    # Test the specified token
    try:
        bot.get_me()
    except telegram.error.Unauthorized:
        print("The token you have entered in the config file is invalid.\n"
              "Fix it, then restart this script.")
        sys.exit(1)

    # Fetch the callback parameters
    secret = flask.request.args.get("secret")
    status = int(flask.request.args.get("status"))
    address = flask.request.args.get("addr")

    # Check the secret
    if secret == configloader.user_cfg["Bitcoin"]["secret"]:
        # Fetch the current transaction by address
        engine = sqlalchemy.create_engine(configloader.user_cfg["Database"]["engine"])

        satoshi = float(flask.request.args.get("value"))
        txid = flask.request.args.get("txid")
        
        return BlockonomicsPoll(bot=bot, engine=engine).handle_update(
            address=address,
            status=status,
            satoshi=satoshi,
            txid=txid
        )
    else:
        return "Incorrect secret"

if __name__ == "__main__":
    # Run the flask app in the main process
    app.run()
