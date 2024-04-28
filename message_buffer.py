import os
import pickle
from datetime import datetime

path_db = 'db.dat'


def load_all(filename):
    if not os.path.exists(filename):
        return []
    with open(filename, "rb") as f:
        while True:
            try:
                yield pickle.load(f)
            except EOFError:
                break


def write_dat(data):
    with open(path_db, 'ab') as wf:
        pickle.dump(data, wf)


def clear_dat():
    with open(path_db, 'rb+') as file:
        file.truncate(0)


class BaseMessageBuffer:
    def put(self, message: dict,
            updated_at: datetime | None = None):
        score = updated_at.timestamp() if updated_at else datetime.now().timestamp()
        self._put({"score": score, "values": message})

    def get(self) -> dict | None:

        message = self._get()
        if message:
            return message["values"]

    def _put(self, data: dict):
        write_dat(data)

    def _get(self) -> dict | None:
        queue = list(load_all(path_db))
        if not queue:
            return None
        queue.sort(key=lambda n: n["score"])
        data = queue.pop(0)

        clear_dat()
        for queue_elem in queue:

            self._put(queue_elem)

        return data
