import unittest
from betfairlightweight import metadata


class MetadataTest(unittest.TestCase):
    def test_transaction_limit(self):
        assert metadata.transaction_limit == 5000

    def test_limits(self):
        assert metadata.order_limits == {
            "placeOrders": 200,
            "cancelOrders": 60,
            "updateOrders": 60,
            "replaceOrders": 60,
        }
        assert metadata.list_current_orders == {"marketIds": 250, "orders": 1000}
        assert metadata.list_market_catalogue == {
            "MARKET_DESCRIPTION": 1,
            "RUNNER_DESCRIPTION": 0,
            "EVENT": 0,
            "EVENT_TYPE": 0,
            "COMPETITION": 0,
            "RUNNER_METADATA": 1,
            "MARKET_START_TIME": 0,
        }

        assert metadata.list_market_book == {
            "": 2,
            "SP_AVAILABLE": 3,
            "EX_BEST_OFFERS": 5,
            "SP_TRADED": 7,
            "EX_ALL_OFFERS": 17,
            "EX_TRADED": 17,
        }

        assert metadata.list_market_profit_and_loss == {"": 4}

    def test_currency_parameters(self):
        self.assertEqual(
            metadata.currency_parameters,
            {
                "ARS": {
                    "min_bet_payout": 500,
                    "min_bet_size": 100,
                    "min_bsp_liability": 500,
                },
                "AUD": {
                    "min_bet_payout": 30,
                    "min_bet_size": 5,
                    "min_bsp_liability": 30,
                },
                "BRL": {
                    "min_bet_payout": 50,
                    "min_bet_size": 5,
                    "min_bsp_liability": 50,
                },
                "CAD": {
                    "min_bet_payout": 30,
                    "min_bet_size": 2,
                    "min_bsp_liability": 30,
                },
                "DKK": {
                    "min_bet_payout": 150,
                    "min_bet_size": 15,
                    "min_bsp_liability": 150,
                },
                "EUR": {
                    "min_bet_payout": 20,
                    "min_bet_size": 1,
                    "min_bsp_liability": 10,
                },
                "GBP": {
                    "min_bet_payout": 10,
                    "min_bet_size": 1,
                    "min_bsp_liability": 10,
                },
                "GEL": {
                    "min_bet_payout": 50,
                    "min_bet_size": 10,
                    "min_bsp_liability": 50,
                },
                "HKD": {
                    "min_bet_payout": 125,
                    "min_bet_size": 10,
                    "min_bsp_liability": 125,
                },
                "HUF": {
                    "min_bet_payout": 4000,
                    "min_bet_size": 400,
                    "min_bsp_liability": 4000,
                },
                "ISK": {
                    "min_bet_payout": 1750,
                    "min_bet_size": 350,
                    "min_bsp_liability": 1750,
                },
                "MXN": {
                    "min_bet_payout": 300,
                    "min_bet_size": 30,
                    "min_bsp_liability": 300,
                },
                "NOK": {
                    "min_bet_payout": 150,
                    "min_bet_size": 10,
                    "min_bsp_liability": 150,
                },
                "NZD": {
                    "min_bet_payout": 10,
                    "min_bet_size": 2,
                    "min_bsp_liability": 10,
                },
                "PEN": {
                    "min_bet_payout": 50,
                    "min_bet_size": 5,
                    "min_bsp_liability": 50,
                },
                "RON": {
                    "min_bet_payout": 50,
                    "min_bet_size": 5,
                    "min_bsp_liability": 50,
                },
                "SEK": {
                    "min_bet_payout": 150,
                    "min_bet_size": 15,
                    "min_bsp_liability": 150,
                },
                "SGD": {
                    "min_bet_payout": 30,
                    "min_bet_size": 2,
                    "min_bsp_liability": 30,
                },
                "USD": {
                    "min_bet_payout": 20,
                    "min_bet_size": 1,
                    "min_bsp_liability": 20,
                },
            },
        )
