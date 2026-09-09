import csv
import os
from collections.abc import Iterator
from pathlib import Path
import threading
from .bet import Bet

_LOTTERY_WINNER_NUMBER = 7574


class Lottery:
    def __init__(self, storage_path) -> None:
        self.storage_path = storage_path
        self.agency_id = None
        self._lock = threading.Lock()

    def _resolve_storage_path(self) -> str:
        if not os.path.isabs(self.storage_path):
            base_dir = os.path.dirname(os.path.abspath(__file__))
            return os.path.join(base_dir, self.storage_path)
        return self.storage_path
    def has_won(self, bet: Bet) -> bool:
        return bet.number == _LOTTERY_WINNER_NUMBER

    def store_bets(self, bets: list[Bet]) -> None:
        storage_path = self._resolve_storage_path()
        Path(storage_path).parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with open(storage_path, "a+") as file:
                writer = csv.writer(file, quoting=csv.QUOTE_MINIMAL)
                for bet in bets:
                    writer.writerow(
                        [
                            bet.agency_id,
                            bet.first_name,
                            bet.last_name,
                            bet.document,
                            bet.birthdate,
                            bet.number,
                        ]
                    )

    def load_bets(self) -> Iterator[Bet]:
        storage_path = self._resolve_storage_path()
        with open(storage_path, "r") as file:
            reader = csv.reader(file, quoting=csv.QUOTE_MINIMAL)
            for row in reader:
                [agency_id, first_name, last_name, document, birthdate, number] = row
                yield Bet(
                    int(agency_id),
                    first_name,
                    last_name,
                    int(document),
                    birthdate,
                    int(number),
                )
