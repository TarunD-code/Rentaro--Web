from auth_service.database import engine as auth_engine, Base as auth_base
from profile_service.database import engine as prof_engine, Base as prof_base
from property_service.database import engine as prop_engine, Base as prop_base
from agreements_service.database import engine as ag_engine, Base as ag_base
from notification_service.database import engine as notif_engine, Base as notif_base
from payment_service.database import engine as pay_engine, Base as pay_base

# Import models to register them with Base
import auth_service.models
import profile_service.models
import property_service.models
import agreements_service.models
import notification_service.models
import payment_service.models

def recreate():
    print("Recreating all databases...")
    auth_base.metadata.create_all(bind=auth_engine)
    prof_base.metadata.create_all(bind=prof_engine)
    prop_base.metadata.create_all(bind=prop_engine)
    ag_base.metadata.create_all(bind=ag_engine)
    notif_base.metadata.create_all(bind=notif_engine)
    pay_base.metadata.create_all(bind=pay_engine)
    print("All databases recreated successfully.")

if __name__ == "__main__":
    recreate()
