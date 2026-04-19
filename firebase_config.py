# firebase_config.py
import firebase_admin
from firebase_admin import credentials,firestore, db

# Use your service account key JSON file
# Download it from: Firebase Console → Project Settings → Service Accounts → Generate new private key
SERVICE_ACCOUNT_KEY = "recipe-genie.json"

# Initialize Firebase Admin SDK (only once!)

cred = credentials.Certificate(SERVICE_ACCOUNT_KEY)
firebase_admin.initialize_app(cred,{"databaseURL" : "https://recipegenie-cf868-default-rtdb.firebaseio.com"})

# Now you can safely use Firestore anywhere
datab = firestore.client()

database = db.reference()

# auth_client = auth