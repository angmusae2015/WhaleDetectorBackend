from typing import TYPE_CHECKING
import json

if TYPE_CHECKING:
    from database.database import Database


class ValueNotFoundInDatabaseError(Exception):
    def __init__(self):
        super().__init__('Could not find value with given primary key in database.')


class DatabaseObject:
    def __init__(self, db: 'Database', primary_key):
        self.db = db
        self.id = primary_key
        self.table_name = self.__class__.__name__

        if not self.is_exists():
            raise ValueNotFoundInDatabaseError

    
    def is_exists(self) -> bool:
        return self.db.is_exists(self.table_name, self.id)


    def get_result_set(self) -> dict:
        return self.db.get_by_primary_key(self.table_name, self.id)

    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())
