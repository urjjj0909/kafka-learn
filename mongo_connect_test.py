from pymongo import MongoClient, errors

try:
    # Instantiate a client instance.
    client = MongoClient(
        host=["mongodb://localhost:27018/"],
        serverSelectionTimeoutMS=3000,
    )

    db = client["database"]
    collection = db["test_db"] # create a collection called "test_db"
    print("MongoDB connection initialized.")

    # Print the version of MongoDB server if connection successful.
    print("Server version:", client.server_info()["version"])

    # Get the database_names from the MongoClient().
    database_names = client.list_database_names()

    # Get the collection_names from "database".
    collection_names = client["database"].list_collection_names()

except errors.ServerSelectionTimeoutError as err:

    # Set the client and DB name list to 'None' and `[]` if exception.
    client = None
    database_names = []
    collection_names = []

    # Catch pymongo.errors.ServerSelectionTimeoutError.
    print("pymongo ERROR:", err)

print("databases:", database_names)
print("collections:", collection_names)
