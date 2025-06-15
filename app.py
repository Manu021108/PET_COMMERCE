import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime
import uuid
from PIL import Image
import io
import base64

# Configure page
st.set_page_config(
    page_title="🐶 PawMarket - Dog Selling Platform",
    page_icon="🐶",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
def init_database():
    conn = sqlite3.connect('dogs.db')
    cursor = conn.cursor()
    
    # Create dogs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dogs (
            id TEXT PRIMARY KEY,
            breed TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            price REAL NOT NULL,
            availability TEXT NOT NULL,
            description TEXT,
            location TEXT,
            image_data TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    
    # Create inquiries table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inquiries (
            id TEXT PRIMARY KEY,
            dog_id TEXT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            message TEXT,
            created_at TEXT,
            FOREIGN KEY (dog_id) REFERENCES dogs (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Database functions
def get_all_dogs():
    conn = sqlite3.connect('dogs.db')
    df = pd.read_sql_query("SELECT * FROM dogs ORDER BY created_at DESC", conn)
    conn.close()
    return df

def add_dog(breed, age, gender, price, availability, description, location, image_data):
    conn = sqlite3.connect('dogs.db')
    cursor = conn.cursor()
    
    dog_id = str(uuid.uuid4())
    created_at = datetime.now().isoformat()
    
    cursor.execute('''
        INSERT INTO dogs (id, breed, age, gender, price, availability, description, location, image_data, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (dog_id, breed, age, gender, price, availability, description, location, image_data, created_at, created_at))
    
    conn.commit()
    conn.close()
    return dog_id

def update_dog(dog_id, breed, age, gender, price, availability, description, location, image_data=None):
    conn = sqlite3.connect('dogs.db')
    cursor = conn.cursor()
    
    updated_at = datetime.now().isoformat()
    
    if image_data:
        cursor.execute('''
            UPDATE dogs SET breed=?, age=?, gender=?, price=?, availability=?, description=?, location=?, image_data=?, updated_at=?
            WHERE id=?
        ''', (breed, age, gender, price, availability, description, location, image_data, updated_at, dog_id))
    else:
        cursor.execute('''
            UPDATE dogs SET breed=?, age=?, gender=?, price=?, availability=?, description=?, location=?, updated_at=?
            WHERE id=?
        ''', (breed, age, gender, price, availability, description, location, updated_at, dog_id))
    
    conn.commit()
    conn.close()

def delete_dog(dog_id):
    conn = sqlite3.connect('dogs.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM dogs WHERE id=?", (dog_id,))
    conn.commit()
    conn.close()

def add_inquiry(dog_id, name, email, phone, message):
    conn = sqlite3.connect('dogs.db')
    cursor = conn.cursor()
    
    inquiry_id = str(uuid.uuid4())
    created_at = datetime.now().isoformat()
    
    cursor.execute('''
        INSERT INTO inquiries (id, dog_id, name, email, phone, message, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (inquiry_id, dog_id, name, email, phone, message, created_at))
    
    conn.commit()
    conn.close()

def get_inquiries():
    conn = sqlite3.connect('dogs.db')
    df = pd.read_sql_query("SELECT * FROM inquiries ORDER BY created_at DESC", conn)
    conn.close()
    return df

# Image handling functions
def image_to_base64(image):
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return img_str

def base64_to_image(img_str):
    img_data = base64.b64decode(img_str)
    return Image.open(io.BytesIO(img_data))

# Initialize session state
if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False

# Initialize database
init_database()

# Main app navigation
def main():
    # Sidebar navigation
    st.sidebar.title("🐶 Navigation")
    page = st.sidebar.selectbox("Go to", ["🏠 Marketplace", "👤 Admin Login", "📊 Admin Dashboard"])
    
    if page == "🏠 Marketplace":
        marketplace_page()
    elif page == "👤 Admin Login":
        admin_login_page()
    elif page == "📊 Admin Dashboard":
        if st.session_state.admin_logged_in:
            admin_dashboard()
        else:
            st.error("Please log in first!")
            admin_login_page()

def marketplace_page():
    st.title("🐶 PawMarket - Find Your Perfect Companion")
    st.markdown("---")
    
    # Get all available dogs
    dogs_df = get_all_dogs()
    
    if dogs_df.empty:
        st.info("No dogs available at the moment. Please check back later!")
        return
    
    # Filters in sidebar
    st.sidebar.markdown("## 🔍 Filters")
    
    # Get unique values for filters
    breeds = ["All"] + sorted(dogs_df['breed'].unique().tolist())
    locations = ["All"] + sorted(dogs_df['location'].unique().tolist())
    
    selected_breed = st.sidebar.selectbox("Breed", breeds)
    selected_location = st.sidebar.selectbox("Location", locations)
    selected_availability = st.sidebar.selectbox("Availability", ["All", "Available", "Sold"])
    
    # Price range filter
    if not dogs_df.empty:
        min_price = int(dogs_df['price'].min())
        max_price = int(dogs_df['price'].max())
        price_range = st.sidebar.slider("Price Range ($)", min_price, max_price, (min_price, max_price))
    
    # Age filter
    max_age = int(dogs_df['age'].max()) if not dogs_df.empty else 10
    age_range = st.sidebar.slider("Age (months)", 0, max_age, (0, max_age))
    
    # Apply filters
    filtered_df = dogs_df.copy()
    
    if selected_breed != "All":
        filtered_df = filtered_df[filtered_df['breed'] == selected_breed]
    
    if selected_location != "All":
        filtered_df = filtered_df[filtered_df['location'] == selected_location]
    
    if selected_availability != "All":
        filtered_df = filtered_df[filtered_df['availability'] == selected_availability]
    
    filtered_df = filtered_df[
        (filtered_df['price'] >= price_range[0]) & 
        (filtered_df['price'] <= price_range[1]) &
        (filtered_df['age'] >= age_range[0]) & 
        (filtered_df['age'] <= age_range[1])
    ]
    
    # Display results
    st.subheader(f"🐕 {len(filtered_df)} Dogs Found")
    
    if filtered_df.empty:
        st.info("No dogs match your current filters. Try adjusting the criteria.")
        return
    
    # Display dogs in a grid
    cols = st.columns(3)
    
    for idx, (_, dog) in enumerate(filtered_df.iterrows()):
        col = cols[idx % 3]
        
        with col:
            # Create a card-like container
            with st.container():
                st.markdown(f"### {dog['breed']}")
                
                # Display image if available
                if dog['image_data']:
                    try:
                        img = base64_to_image(dog['image_data'])
                        st.image(img, use_column_width=True)
                    except:
                        st.image("https://via.placeholder.com/300x200?text=Dog+Image", use_column_width=True)
                else:
                    st.image("https://via.placeholder.com/300x200?text=Dog+Image", use_column_width=True)
                
                # Dog details
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Age:** {dog['age']} months")
                    st.write(f"**Gender:** {dog['gender']}")
                with col2:
                    st.write(f"**Price:** ${dog['price']:,.0f}")
                    availability_color = "🟢" if dog['availability'] == "Available" else "🔴"
                    st.write(f"**Status:** {availability_color} {dog['availability']}")
                
                st.write(f"**Location:** {dog['location']}")
                
                if dog['description']:
                    st.write(f"**Description:** {dog['description'][:100]}...")
                
                # Contact button
                if dog['availability'] == "Available":
                    if st.button(f"Contact Seller", key=f"contact_{dog['id']}"):
                        show_contact_form(dog['id'], dog['breed'])
                
                st.markdown("---")

def show_contact_form(dog_id, breed):
    st.subheader(f"Contact About {breed}")
    
    with st.form(key=f"contact_form_{dog_id}"):
        name = st.text_input("Your Name*")
        email = st.text_input("Your Email*")
        phone = st.text_input("Phone Number")
        message = st.text_area("Message", value=f"Hi, I'm interested in the {breed}. Please contact me with more details.")
        
        submit = st.form_submit_button("Send Inquiry")
        
        if submit:
            if name and email and message:
                add_inquiry(dog_id, name, email, phone, message)
                st.success("Your inquiry has been sent! The seller will contact you soon.")
                st.balloons()
            else:
                st.error("Please fill in all required fields (Name, Email, Message)")

def admin_login_page():
    st.title("🔐 Admin Login")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            # Simple authentication (in production, use proper authentication)
            if username == "admin" and password == "dogadmin123":
                st.session_state.admin_logged_in = True
                st.success("Logged in successfully!")
                st.rerun()  # <-- updated herest.experimental_rerun()
            else:
                st.error("Invalid credentials. Use username: 'admin', password: 'dogadmin123'")

def admin_dashboard():
    st.title("📊 Admin Dashboard")
    
    # Logout button
    if st.sidebar.button("Logout"):
        st.session_state.admin_logged_in = False
        st.experimental_rerun()
    
    # Dashboard tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Overview", "➕ Add Dog", "📝 Manage Listings", "📧 Inquiries"])
    
    with tab1:
        dashboard_overview()
    
    with tab2:
        add_dog_form()
    
    with tab3:
        manage_listings()
    
    with tab4:
        view_inquiries()

def dashboard_overview():
    st.subheader("📈 Dashboard Overview")
    
    dogs_df = get_all_dogs()
    inquiries_df = get_inquiries()
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_dogs = len(dogs_df)
        st.metric("Total Dogs", total_dogs)
    
    with col2:
        available = len(dogs_df[dogs_df['availability'] == 'Available']) if not dogs_df.empty else 0
        st.metric("Available", available)
    
    with col3:
        sold = len(dogs_df[dogs_df['availability'] == 'Sold']) if not dogs_df.empty else 0
        st.metric("Sold", sold)
    
    with col4:
        total_inquiries = len(inquiries_df)
        st.metric("Total Inquiries", total_inquiries)
    
    # Charts
    if not dogs_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Dogs by Breed")
            breed_counts = dogs_df['breed'].value_counts()
            st.bar_chart(breed_counts)
        
        with col2:
            st.subheader("Availability Status")
            status_counts = dogs_df['availability'].value_counts()
            st.pie_chart(status_counts)

def add_dog_form():
    st.subheader("➕ Add New Dog")
    
    with st.form("add_dog_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            breed = st.text_input("Breed*")
            age = st.number_input("Age (months)*", min_value=1, max_value=120, value=6)
            gender = st.selectbox("Gender*", ["Male", "Female"])
            price = st.number_input("Price ($)*", min_value=0.0, value=500.0, step=50.0)
        
        with col2:
            availability = st.selectbox("Availability*", ["Available", "Sold"])
            location = st.text_input("Location*")
            description = st.text_area("Description")
            image_file = st.file_uploader("Upload Image", type=['png', 'jpg', 'jpeg'])
        
        submit = st.form_submit_button("Add Dog")
        
        if submit:
            if breed and age and gender and price and location:
                image_data = None
                if image_file:
                    image = Image.open(image_file)
                    # Resize image to reasonable size
                    image.thumbnail((800, 600), Image.Resampling.LANCZOS)
                    image_data = image_to_base64(image)
                
                add_dog(breed, age, gender, price, availability, description, location, image_data)
                st.success(f"Successfully added {breed} to the listings!")
            else:
                st.error("Please fill in all required fields")

def manage_listings():
    st.subheader("📝 Manage Dog Listings")
    
    dogs_df = get_all_dogs()
    
    if dogs_df.empty:
        st.info("No dogs in the database yet.")
        return
    
    # Display current listings
    for idx, (_, dog) in enumerate(dogs_df.iterrows()):
        with st.expander(f"{dog['breed']} - ${dog['price']:,.0f} ({dog['availability']})"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Edit form
                with st.form(f"edit_form_{dog['id']}"):
                    edit_col1, edit_col2 = st.columns(2)
                    
                    with edit_col1:
                        new_breed = st.text_input("Breed", value=dog['breed'], key=f"breed_{dog['id']}")
                        new_age = st.number_input("Age (months)", min_value=1, max_value=120, 
                                                value=int(dog['age']), key=f"age_{dog['id']}")
                        new_gender = st.selectbox("Gender", ["Male", "Female"], 
                                                index=0 if dog['gender'] == "Male" else 1, key=f"gender_{dog['id']}")
                        new_price = st.number_input("Price ($)", min_value=0.0, 
                                                  value=float(dog['price']), step=50.0, key=f"price_{dog['id']}")
                    
                    with edit_col2:
                        new_availability = st.selectbox("Availability", ["Available", "Sold"],
                                                      index=0 if dog['availability'] == "Available" else 1, 
                                                      key=f"availability_{dog['id']}")
                        new_location = st.text_input("Location", value=dog['location'], key=f"location_{dog['id']}")
                        new_description = st.text_area("Description", value=dog['description'] or "", 
                                                     key=f"description_{dog['id']}")
                        new_image = st.file_uploader("Update Image", type=['png', 'jpg', 'jpeg'], 
                                                   key=f"image_{dog['id']}")
                    
                    col_update, col_delete = st.columns(2)
                    
                    with col_update:
                        update_submit = st.form_submit_button("Update", type="primary")
                    
                    with col_delete:
                        delete_submit = st.form_submit_button("Delete", type="secondary")
                    
                    if update_submit:
                        new_image_data = None
                        if new_image:
                            image = Image.open(new_image)
                            image.thumbnail((800, 600), Image.Resampling.LANCZOS)
                            new_image_data = image_to_base64(image)
                        
                        update_dog(dog['id'], new_breed, new_age, new_gender, new_price, 
                                 new_availability, new_description, new_location, new_image_data)
                        st.success("Dog updated successfully!")
                        st.experimental_rerun()
                    
                    if delete_submit:
                        delete_dog(dog['id'])
                        st.success("Dog deleted successfully!")
                        st.experimental_rerun()
            
            with col2:
                # Display current image
                if dog['image_data']:
                    try:
                        img = base64_to_image(dog['image_data'])
                        st.image(img, caption="Current Image", width=200)
                    except:
                        st.write("Image error")
                else:
                    st.write("No image")

def view_inquiries():
    st.subheader("📧 Customer Inquiries")
    
    inquiries_df = get_inquiries()
    dogs_df = get_all_dogs()
    
    if inquiries_df.empty:
        st.info("No inquiries yet.")
        return
    
    # Merge with dog data to show breed info
    if not dogs_df.empty:
        merged_df = inquiries_df.merge(dogs_df[['id', 'breed']], left_on='dog_id', right_on='id', how='left')
        merged_df = merged_df.drop('id_y', axis=1).rename(columns={'id_x': 'id'})
    else:
        merged_df = inquiries_df
        merged_df['breed'] = 'Unknown'
    
    # Display inquiries
    for idx, (_, inquiry) in enumerate(merged_df.iterrows()):
        with st.expander(f"Inquiry about {inquiry.get('breed', 'Unknown')} - {inquiry['name']}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Name:** {inquiry['name']}")
                st.write(f"**Email:** {inquiry['email']}")
                st.write(f"**Phone:** {inquiry['phone'] or 'Not provided'}")
                st.write(f"**Date:** {inquiry['created_at'][:16]}")
            
            with col2:
                st.write(f"**Dog Breed:** {inquiry.get('breed', 'Unknown')}")
                st.write("**Message:**")
                st.write(inquiry['message'])

if __name__ == "__main__":
    main()