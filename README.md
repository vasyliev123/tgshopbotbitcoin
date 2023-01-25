# greed

A customizable Telegram shop bot that accepts bitcoin payments.

![](https://img.shields.io/badge/version-beta-blue.svg)

## Requirements, Installation & Usage

Please refer to the [main greed project fork](https://github.com/Steffo99/greed) for requirements, installation guide, and usage instructions before proceeding with the bitcoin setup below

## Integrating Bitcoin

1. Edit the `config/config.toml` file to set your Blockonomics *api_key* from [Blockonomics Merchants > Stores](https://www.blockonomics.co/merchants#/stores), and a *secret* of your choosing, you'll use this secret while setting up the Callback URL below.

2. Add a new store at [Blockonomics Merchants > Stores](https://www.blockonomics.co/merchants#/stores), and set your Callback URL to `https://www.blockonomics.co/api/test_callback?secret=YOUR_SECRET`, substituting in your chosen secret from step 1 in place of `YOUR_SECRET`

That's it! Restart your bot and start accepting bitcoin payments with your bot!

## Credits
This project is a fork of [greed project](https://github.com/Steffo99/greed) by @Steffo99. We would like to thank @Steffo99 for putting this in public domain. 
