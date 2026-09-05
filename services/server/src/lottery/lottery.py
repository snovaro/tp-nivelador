import csv
import os
from collections.abc import Iterator
from .bet import Bet

_LOTTERY_WINNER_NUMBER = 7574


class Lottery:
    def __init__(self, storage_path) -> None:
        self.storage_path = storage_path
        self.agency_id = None

    def set_agency_id(self, agency_id: int) -> None:
        self.agency_id = agency_id

    def _resolve_storage_path(self) -> str:
        if self.storage_path is None:
            return None

        if self.agency_id is None:
            return self.storage_path

        directory = os.path.dirname(self.storage_path)
        filename = os.path.basename(self.storage_path)
        agency_storage_filename = f"{self.agency_id}_{filename}"
        if directory:
            return os.path.join(directory, agency_storage_filename)
        return agency_storage_filename

    def has_won(self, bet: Bet) -> bool:
        return bet.number == _LOTTERY_WINNER_NUMBER

    def store_bets(self, bets: list[Bet]) -> None:
        storage_path = self._resolve_storage_path()
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
