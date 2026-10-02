import shared_database
from sqlalchemy import text

def check_sync():
    with shared_database.sync_engine.connect() as conn:
        props = conn.execute(text("SELECT id, title, status, price, lat, lng FROM property.properties")).fetchall()
        print(f"Total in property.properties: {len(props)}")
        for p in props[:5]:
            print(f" - ID: {p[0]}, Title: {p[1]}, Status: {p[2]}, Price: {p[3]}, Lat/Lng: {p[4]},{p[5]}")

        idx = conn.execute(text("SELECT property_id, title, status, price, lat, lng FROM search.property_index")).fetchall()
        print(f"\nTotal in search.property_index: {len(idx)}")
        for i in idx[:5]:
            print(f" - ID: {i[0]}, Title: {i[1]}, Status: {i[2]}, Price: {i[3]}, Lat/Lng: {i[4]},{i[5]}")

        # Check if there's any mismatch or why only 1 listing shows up
        # Wait, let's see what status values are in properties
        status_counts = conn.execute(text("SELECT status, count(*) FROM property.properties GROUP BY status")).fetchall()
        print("\nProperty status counts:")
        for s in status_counts:
            print(f" - Status: {s[0]}, Count: {s[1]}")

        status_counts_idx = conn.execute(text("SELECT status, count(*) FROM search.property_index GROUP BY status")).fetchall()
        print("\nSearch index status counts:")
        for s in status_counts_idx:
            print(f" - Status: {s[0]}, Count: {s[1]}")

if __name__ == "__main__":
    check_sync()
