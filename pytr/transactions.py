import asyncio
from pytr.utils import preview
import json
from datetime import datetime, timedelta

class Transactions:
    def __init__(self, tr,output_path, last_days):
        self.tr = tr
        self.output_path = output_path
        self.last_days = last_days
        self.transactions = []

    async def loop(self):
        recv = 0
        await self.tr.timeline_transactions()
        while True:
            _subscription_id, subscription, response = await self.tr.recv()

            if subscription['type'] == 'timelineTransactions':
                self.transactions.extend(response["items"])

                # Transactions in the response are ordered from newest to oldest
                # If the oldest (= last) transaction is older than what we want, exit the loop
                t = self.transactions[-1]
                if datetime.fromisoformat(t['timestamp']) < datetime.now().astimezone() - timedelta(days=self.last_days):
                    return

                await self.tr.timeline_transactions(response["cursors"]["after"])

            else:
                print(f"unmatched subscription of type '{subscription['type']}':\n{preview(response)}")

            if recv == 1:
                return

    def output(self):
        transactions = [
            t
            for t in self.transactions
            if datetime.fromisoformat(t['timestamp']) > datetime.now().astimezone() - timedelta(days=self.last_days)
        ]

        with open(self.output_path, mode='w', encoding='utf-8') as output_file:
            json.dump(transactions, output_file)

    def get(self):
        asyncio.get_event_loop().run_until_complete(self.loop())
        self.output()
