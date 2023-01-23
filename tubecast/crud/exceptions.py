class RecordNotFoundError(Exception):
    """
    Exception raised when a record is not found in the database.
    """


class RecordAlreadyExistsError(Exception):
    """
    Exception raised when attempting to create a record in the database that already exists.
    """


class InvalidRecordError(Exception):
    """
    Exception raised when a record is invalid
    (e.g. missing required fields, invalid field values).
    """


class DeleteError(Exception):
    """
    Exception raised when there is an error deleting a record from the database
    (e.g. record is referenced by other records).
    """
