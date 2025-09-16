from quantification import (
    RMB,
    Stock,
    Portfolio,
    SingleTrader,
    StockBrokerCN
)


class AFactorTrader(SingleTrader):
    def __init__(
            self,
            api,
            start_date,
            end_date,
            stage,
            strategy,
            stocks: list[type[Stock]],
            volume: float,
            long_short: float = False,
            padding: int = 0
    ):
        if not long_short:
            super().__init__(
                api=api,
                base=volume,
                scale=volume,
                init_portfolio=Portfolio(RMB(volume)),
                start_date=start_date,
                end_date=end_date,
                padding=padding,
                stage=stage,
                strategy=strategy,
                brokers=[StockBrokerCN]
            )
        else:
            super().__init__(
                api=api,
                base=0,
                scale=2 * volume,
                init_portfolio=Portfolio(RMB(0)),
                start_date=start_date,
                end_date=end_date,
                padding=padding,
                stage=stage,
                strategy=strategy,
                brokers=[StockBrokerCN],
                allow_debt=True,
                allow_short=True,
                round_lot=False,
            )

        self.stocks = stocks


__all__ = ["AFactorTrader"]
