from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ✅ Get MongoDB URI & Database Name from .env
MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")

# ✅ Connect to MongoDB with a specific database name
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]  
users = db["users"] 
contacts = db["contacts"]

# Ensure Indexes (Prevents duplicate emails)
users.create_index("email", unique=True)

print(f"✅ Connected to MongoDB database: {DATABASE_NAME}")

# Close the connection
client.close()
