"""
Initialize sample notification data for MongoDB
Creates 100 notifications across multiple channels
All dates stored as ISO string format
"""

import os
from datetime import datetime, timedelta
from pymongo import MongoClient
from dotenv import load_dotenv
import random

# Load environment variables
load_dotenv()

# MongoDB connection
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
DB_NAME = os.getenv('DB_NAME', 'notifications_db')

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# Sample data pools
CUSTOMER_NAMES = [
    "John Smith", "Emma Johnson", "Michael Brown", "Sarah Davis", "James Wilson",
    "Emily Martinez", "David Anderson", "Olivia Taylor", "Robert Thomas", "Sophia Moore",
    "William Jackson", "Isabella White", "Christopher Harris", "Mia Martin", "Daniel Thompson",
    "Charlotte Garcia", "Matthew Rodriguez", "Amelia Lewis", "Joseph Lee", "Harper Walker",
    "Andrew Hall", "Evelyn Allen", "Ryan Young", "Abigail King", "Nicholas Wright",
    "Ella Lopez", "Joshua Hill", "Avery Scott", "Brandon Green", "Sofia Adams",
    "Tyler Baker", "Scarlett Nelson", "Kevin Carter", "Grace Mitchell", "Jacob Perez",
    "Chloe Roberts", "Aaron Turner", "Lily Phillips", "Justin Campbell", "Zoey Parker",
    "Samuel Evans", "Nora Edwards", "Benjamin Collins", "Hannah Stewart", "Nathan Sanchez",
    "Aria Morris", "Dylan Rogers", "Layla Reed", "Caleb Cook", "Zoe Bailey"
]

EVENT_TYPES = [
    "ORDER_PLACED", "PAYMENT_RECEIVED", "ACCOUNT_CREATED", "ORDER_SHIPPED",
    "PASSWORD_RESET", "SUBSCRIPTION_RENEWED", "PAYMENT_FAILED", "ORDER_DELIVERED",
    "ACCOUNT_VERIFIED", "SUBSCRIPTION_CANCELLED", "REFUND_PROCESSED", "ITEM_RETURNED"
]

NOTIFICATION_TYPES = ["promotional", "transactional", "alert", "reminder", "system"]

EMAIL_PROVIDERS = ["SendGrid", "AWS SES", "Mailgun", "Postmark", "SparkPost"]
SMS_PROVIDERS = ["Twilio", "Vonage", "AWS SNS", "MessageBird", "Plivo"]
PUSH_PROVIDERS = ["Firebase", "OneSignal", "Pusher", "AWS SNS", "Urban Airship"]

def generate_tracking_id(index):
    """Generate unique tracking ID"""
    date_str = datetime.now().strftime("%Y%m%d")
    return f"EVT-{date_str}-{index:06d}"

def random_datetime(days_ago_max=30):
    """Generate random datetime within last N days as ISO string"""
    days_ago = random.randint(0, days_ago_max)
    hours_ago = random.randint(0, 23)
    minutes_ago = random.randint(0, 59)
    dt = datetime.now() - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
    return dt.isoformat()

def add_seconds_to_iso_string(iso_string, seconds):
    """Add seconds to an ISO datetime string"""
    if iso_string is None:
        return None
    dt = datetime.fromisoformat(iso_string)
    new_dt = dt + timedelta(seconds=seconds)
    return new_dt.isoformat()

def random_email(name):
    """Generate email from name"""
    name_parts = name.lower().split()
    domains = ["gmail.com", "yahoo.com", "outlook.com", "company.com", "email.com"]
    return f"{name_parts[0]}.{name_parts[1]}@{random.choice(domains)}"

def random_phone():
    """Generate random phone number"""
    return f"+1{random.randint(200, 999)}{random.randint(200, 999)}{random.randint(1000, 9999)}"

def clear_collections():
    """Clear existing notification data"""
    print("\n🗑️  Clearing existing notification data...")
    db.notification_events.delete_many({})
    db.email_notifications.delete_many({})
    db.sms_notifications.delete_many({})
    db.push_notifications.delete_many({})
    db.inapp_notifications.delete_many({})
    print("✓ Collections cleared")

def create_notification_event(index, customer_name):
    """Create a notification event"""
    tracking_id = generate_tracking_id(index)
    event_type = random.choice(EVENT_TYPES)
    notification_type = random.choice(NOTIFICATION_TYPES)
    
    # Determine which channels to use (1-4 channels)
    all_channels = ["email", "sms", "push", "in_app"]
    num_channels = random.randint(1, 4)
    channels = random.sample(all_channels, num_channels)
    
    created_at = random_datetime(30)
    processed_at = add_seconds_to_iso_string(created_at, random.randint(1, 300))
    
    event = {
        "event_tracking_id": tracking_id,
        "event_name": event_type,
        "customer_id": f"CUST-{index:05d}",
        "customer_name": customer_name,
        "customer_email": random_email(customer_name),
        "customer_phone": random_phone(),
        "notification_type": notification_type,
        "priority": random.randint(1, 5),
        "subject": f"{event_type.replace('_', ' ').title()} - {customer_name}",
        "message": f"Your {event_type.lower().replace('_', ' ')} has been processed successfully.",
        "channels": channels,
        "status": random.choice(["accepted", "processed"]),
        "created_at": created_at,
        "processed_at": processed_at,
        "metadata": {
            "source": "notification_system",
            "version": "2.0",
            "batch_id": f"BATCH-{index // 10}"
        }
    }
    
    return event, channels, created_at

def create_email_notification(tracking_id, customer_name, customer_email, created_at):
    """Create email notification"""
    sent_at = add_seconds_to_iso_string(created_at, random.randint(5, 60))
    status = random.choice(["pending", "processing", "sent", "delivered", "failed", "bounced", "read"])
    
    email = {
        "event_tracking_id": tracking_id,
        "recipient_email": customer_email,
        "recipient_name": customer_name,
        "subject": f"Notification for {customer_name}",
        "message_body": "This is your notification message.",
        "html_body": "<html><body><h1>Notification</h1><p>This is your notification message.</p></body></html>",
        "status": status,
        "sent_at": sent_at if status != "pending" else None,
        "delivered_at": add_seconds_to_iso_string(sent_at, random.randint(10, 120)) if status in ["delivered", "read"] else None,
        "opened_at": add_seconds_to_iso_string(sent_at, random.randint(300, 86400)) if status == "read" else None,
        "clicked_at": add_seconds_to_iso_string(sent_at, random.randint(600, 90000)) if status == "read" and random.random() > 0.5 else None,
        "email_provider": random.choice(EMAIL_PROVIDERS),
        "message_id": f"MSG-{tracking_id}-EMAIL",
        "retry_count": random.randint(0, 3) if status == "failed" else 0,
        "error_details": "SMTP connection failed" if status == "failed" else None
    }
    
    return email

def create_sms_notification(tracking_id, customer_name, customer_phone, created_at):
    """Create SMS notification"""
    sent_at = add_seconds_to_iso_string(created_at, random.randint(5, 60))
    status = random.choice(["pending", "processing", "sent", "delivered", "failed"])
    
    sms = {
        "event_tracking_id": tracking_id,
        "recipient_phone": customer_phone,
        "recipient_name": customer_name,
        "message_body": f"Hi {customer_name.split()[0]}, your notification is ready. Check your account for details.",
        "status": status,
        "sent_at": sent_at if status != "pending" else None,
        "delivered_at": add_seconds_to_iso_string(sent_at, random.randint(5, 30)) if status == "delivered" else None,
        "sms_provider": random.choice(SMS_PROVIDERS),
        "message_id": f"MSG-{tracking_id}-SMS",
        "retry_count": random.randint(0, 2) if status == "failed" else 0,
        "error_details": "Invalid phone number" if status == "failed" else None
    }
    
    return sms

def create_push_notification(tracking_id, customer_name, customer_id, created_at):
    """Create push notification"""
    sent_at = add_seconds_to_iso_string(created_at, random.randint(5, 60))
    status = random.choice(["pending", "processing", "sent", "delivered", "read"])
    
    push = {
        "event_tracking_id": tracking_id,
        "recipient_id": customer_id,
        "device_tokens": [f"TOKEN-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"],
        "title": "New Notification",
        "message_body": f"Hi {customer_name.split()[0]}, you have a new notification!",
        "status": status,
        "sent_at": sent_at if status != "pending" else None,
        "delivered_at": add_seconds_to_iso_string(sent_at, random.randint(1, 10)) if status in ["delivered", "read"] else None,
        "received_at": add_seconds_to_iso_string(sent_at, random.randint(2, 15)) if status in ["delivered", "read"] else None,
        "clicked_at": add_seconds_to_iso_string(sent_at, random.randint(60, 3600)) if status == "read" and random.random() > 0.6 else None,
        "push_provider": random.choice(PUSH_PROVIDERS),
        "notification_id": f"NOTIF-{tracking_id}-PUSH",
        "retry_count": random.randint(0, 2) if status == "failed" else 0,
        "error_details": "Device token expired" if status == "failed" else None
    }
    
    return push

def create_inapp_notification(tracking_id, customer_name, customer_id, created_at):
    """Create in-app notification"""
    sent_at = add_seconds_to_iso_string(created_at, random.randint(1, 30))
    status = random.choice(["pending", "sent", "delivered", "read"])
    
    inapp = {
        "event_tracking_id": tracking_id,
        "recipient_id": customer_id,
        "recipient_name": customer_name,
        "title": "New Activity",
        "message_body": "You have new activity in your account. Tap to view details.",
        "status": status,
        "sent_at": sent_at if status != "pending" else None,
        "delivered_at": add_seconds_to_iso_string(sent_at, random.randint(1, 5)) if status in ["delivered", "read"] else None,
        "read_at": add_seconds_to_iso_string(sent_at, random.randint(60, 7200)) if status == "read" else None,
        "retry_count": 0,
        "error_details": None
    }
    
    return inapp

def create_indexes():
    """Create indexes on collections"""
    print("\n🔍 Creating indexes...")
    
    # Notification events indexes
    db.notification_events.create_index("event_tracking_id", unique=True)
    db.notification_events.create_index("event_name")
    db.notification_events.create_index("customer_id")
    db.notification_events.create_index("created_at")
    
    # Email notifications indexes
    db.email_notifications.create_index("event_tracking_id")
    db.email_notifications.create_index("recipient_email")
    db.email_notifications.create_index("status")
    
    # SMS notifications indexes
    db.sms_notifications.create_index("event_tracking_id")
    db.sms_notifications.create_index("recipient_phone")
    db.sms_notifications.create_index("status")
    
    # Push notifications indexes
    db.push_notifications.create_index("event_tracking_id")
    db.push_notifications.create_index("recipient_id")
    db.push_notifications.create_index("status")
    
    # In-app notifications indexes
    db.inapp_notifications.create_index("event_tracking_id")
    db.inapp_notifications.create_index("recipient_id")
    db.inapp_notifications.create_index("status")
    
    print("✓ Indexes created")

def main():
    """Main function to initialize sample data"""
    print("=" * 60)
    print("Initializing Sample Notification Data (String Dates)")
    print("=" * 60)
    
    # Clear existing data
    clear_collections()
    
    # Create 100 notifications
    print(f"\n📧 Creating 100 notification events...")
    
    events = []
    emails = []
    sms_list = []
    pushes = []
    inapps = []
    
    for i in range(1, 101):
        customer_name = random.choice(CUSTOMER_NAMES)
        event, channels, created_at = create_notification_event(i, customer_name)
        events.append(event)
        
        tracking_id = event["event_tracking_id"]
        customer_id = event["customer_id"]
        customer_email = event["customer_email"]
        customer_phone = event["customer_phone"]
        
        # Create channel-specific notifications
        if "email" in channels:
            emails.append(create_email_notification(tracking_id, customer_name, customer_email, created_at))
        
        if "sms" in channels:
            sms_list.append(create_sms_notification(tracking_id, customer_name, customer_phone, created_at))
        
        if "push" in channels:
            pushes.append(create_push_notification(tracking_id, customer_name, customer_id, created_at))
        
        if "in_app" in channels:
            inapps.append(create_inapp_notification(tracking_id, customer_name, customer_id, created_at))
    
    # Insert all data
    db.notification_events.insert_many(events)
    print(f"✓ Created {len(events)} notification events")
    
    if emails:
        db.email_notifications.insert_many(emails)
        print(f"✓ Created {len(emails)} email notifications")
    
    if sms_list:
        db.sms_notifications.insert_many(sms_list)
        print(f"✓ Created {len(sms_list)} SMS notifications")
    
    if pushes:
        db.push_notifications.insert_many(pushes)
        print(f"✓ Created {len(pushes)} push notifications")
    
    if inapps:
        db.inapp_notifications.insert_many(inapps)
        print(f"✓ Created {len(inapps)} in-app notifications")
    
    # Create indexes
    create_indexes()
    
    print("\n" + "=" * 60)
    print("✅ Sample data initialization complete!")
    print("=" * 60)
    print(f"\nDatabase: {DB_NAME}")
    print("Collections created:")
    print(f"  • notification_events: {db.notification_events.count_documents({})} documents")
    print(f"  • email_notifications: {db.email_notifications.count_documents({})} documents")
    print(f"  • sms_notifications: {db.sms_notifications.count_documents({})} documents")
    print(f"  • push_notifications: {db.push_notifications.count_documents({})} documents")
    print(f"  • inapp_notifications: {db.inapp_notifications.count_documents({})} documents")
    print("=" * 60)
    print("\n💡 All dates stored as ISO string format")

if __name__ == "__main__":
    main()
