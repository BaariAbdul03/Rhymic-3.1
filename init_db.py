from app import app, db, scan_library

print("Initializing Database...")
with app.app_context():
    db.create_all()
    print("Database tables created successfully!")
    
    print("Scanning Library...")
    scan_library()
    print("Library scan complete!")
