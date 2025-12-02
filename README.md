# SavePlate – A Food Waste Reduction Marketplace

## Overview

SavePlate is a Food Surplus Marketplace designed to reduce food waste while providing affordable food options to communities.

Businesses often discard edible surplus food due to operational, inventory, or aesthetic constraints. At the same time, many consumers are willing to purchase this food at discounted prices if they knew where to find it.  
SavePlate addresses this issue by connecting sellers, buyers, and charities through a streamlined marketplace.

The platform demonstrates the core workflows needed to efficiently manage listings, orders, donations, negotiations, and communications, making surplus food accessible while minimizing waste.


## Goal

The objective is to implement a functional platform that:

- Allows **sellers** to post surplus listings  
- Allows **buyers** to browse and purchase listings  
- Supports **donations** to charities  
- Includes a **support ticket system**  
- Sends **notifications** for orders, donations, and ticket updates  
- Enforces **role-based access**  


## Quickstart

1. Clone the repository:

```bash
git clone https://github.com/Hrudayk1/SavePlate.git
cd SavePlate
```

2. (Recommended) Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:

Install the required packages with pip:

```bash
pip install fastapi uvicorn sqlalchemy pydantic
```


4. Run the application :

Activate virtual environment (if created earlier):

```bash
source .venv/bin/activate
```

Start the server:

```bash
uvicorn main:app --reload
```

Open `http://127.0.0.1:8000/docs` to explore and test all API endpoints using Swagger UI. 
ReDoc is also available at `http://127.0.0.1:8000/redoc`.



## API Documentation
SavePlate provides interactive API documentation generated automatically by FastAPI.

- **Swagger UI:** http://127.0.0.1:8000/docs
- **ReDoc:** http://127.0.0.1:8000/redoc

Both interfaces allow you to explore all endpoints, send test requests, and view request/response schemas.

## Key Features 

### 1. Listing 

The listing module allows sellers to publish surplus food items with detailed information, safety attributes, pricing rules, and search filters.

#### Key Capabilities
- Sellers can **create/update/delete** surplus food listings.
- Listings include:
  - **Food safety tracking fields**  
    - Prepared date  
    - Expiry date  
    - Allergen information  
    - Food images for authenticity and safety verification
  - **Cuisine type:** helpful for filtering (e.g: Indian, Chinese, Bakery)
  - **Availability window:** buyers can see until when the food is safe and available. Listings are automatically marked as sold when the expiry date is reached or the availability window ends.


#### Search & Filters
- **City Filter** – Buyers can view listings specific to a selected city.
- **Cuisine Filter** – Buyers can refine results based on cuisine type.
- **Keyword Search** – Users can search by title, description, cuisine, or allergens. Returns all listings containing the keyword in any searchable field.


### 2. Dynamic Pricing (Automated Discounts)
Dynamic pricing can be toggled ON or OFF by the seller.

When dynamic pricing is ON, the system applies automated discounts based on the time remaining until expiry:

- If less than 24 hours remain → price is reduced by 50%
- If less than 12 hours remain → price is reduced by 75%

When the seller disables dynamic pricing, the listing freezes at the last computed dynamic price.

Dynamic pricing works independently of negotiations. Automated price updates do not affect the negotiated offer flow.


### 3. Ordering 
- Buyers place orders for available listings  
- Once an order is placed, the listing is marked as sold to prevent further purchases 
- Order history is maintained and can be filtered by user id. 
- Includes a payment workflow allowing orders to be marked as paid
- Notifications sent to both buyer and seller upon order creation


### 4. Negotiations
- Consumers can start a negotiation on any active listing by proposing a price  
- Sellers and buyers can **accept, reject, or counter-offer**  
- Back-and-forth counter workflow until one party accepts or rejects  
- Notifications automatically sent to the concerned party:
  - When a negotiation starts  
  - When a counter-offer is made  
  - When a negotiation is accepted or rejected  
- Listing is marked as sold and order is placed upon successful negotiation acceptance  
- API supports filtering negotiations by **buyer**, **seller**, or **status**


### 5. Donations 
- Businesses donate surplus food to registered charities  
- Users with account type **Charity** can create and manage charity organizations  
- Donation records are stored for tracking  
- Charities are automatically notified when a new donation is made  
- Helps reduce food waste while supporting social organizations  


### 6. Support Ticket 
- Any user can create a support ticket  
- A ticket can be created by entering an order ID or a donation ID and describing the issue
- When a ticket is created, all accounts of type Support are automatically notified  
- Support staff can communicate with the user through the chat feature  
- Only Support accounts can update the ticket status or mark it as resolved  


### 7. Chat
- Users can send direct messages to each other through the platform  
- Supports **one-to-one conversations** between any two users  
- All messages are stored with timestamps for history tracking  
- Receivers are notified whenever a new message arrives  
- Users can fetch the full conversation history with another user  
- Support staff can chat with users about tickets  
- Buyers and sellers can communicate regarding listings and negotiations  


### 8. Notifications
- Centralized notification system storing all events in the database  
- Notifications are generated for key activities, including:
  - Donations – charities notified of new donations  
  - Orders – buyers and sellers notified when an order is placed or updated  
  - Support tickets – support staff and users notified of ticket creation and updates  
  - Negotiations – both parties notified of new offers, counter-offers, acceptance, or rejection  
  - Chat messages – users notified when they receive a new message  
  - Payments – buyers and sellers notified when an order is marked as paid  
- Users can fetch all their notifications through a dedicated API endpoint  
- Notifications can be marked as read once acknowledged by the user  


### 9. Ratings
- Allows users to provide feedback and rate transactions on the platform  
- **Consumers** can rate completed orders with businesses  
- **Charity accounts** can rate businesses for donations received  
- Ratings are on a **1–5 scale**  
- Duplicate ratings for the same order or donation are prevented  
- **rating summary** includes average score and total ratings
- Helps maintain trust and accountability between buyers, sellers, and charities  


### 10. Role-Based Access Control
SavePlate enforces different permissions based on user roles to ensure secure and organized operations:

- **Business** – Can create, update, and manage listings, handle orders and negotiations  
- **Consumer** – Can browse listings, place orders, negotiate prices, and rate businesses  
- **Charity** – Can create and manage charity organizations, receive donations, and rate businesses  
- **Support** – Can view and manage support tickets, communicate with users, and mark issues as resolved  


## Tech Stack

- **FastAPI** – backend framework  
- **SQLAlchemy** – ORM  
- **SQLite** – configurable database  
- **Pydantic** – validation layer  
- **Uvicorn** – ASGI server  


## Database Notes

- The SQLite database (`saveplate.db`) is automatically created on the first run.
- All tables are generated using SQLAlchemy metadata during application startup.
- To reset all data, delete the `saveplate.db` file and restart the server.


## Project Structure

- **main.py**  
  Entry point of the application, initializes the FastAPI app and registers all route modules.

- **database.py**  
  Configures the SQLite database engine, session management, and connection utilities.

- **models.py**  
  Defines all database tables and relationships using SQLAlchemy ORM.

- **schemas.py**  
  Contains Pydantic models for request validation and API responses.

- **crud.py**  
  Reusable helper functions for common database operations.

- **routes/**  
  Directory containing all feature-specific route modules:
  - **listings.py** – Create, update, view and delete surplus food listings  
  - **orders.py** – Manage order creation, list orders, and status  
  - **donate.py** – Donation workflow for businesses and charities  
  - **negotiations.py** – Buyer–seller price negotiation system  
  - **chat.py** – User-to-user messaging  
  - **notifications.py** – Notification creation, status update, and retrieval  
  - **ratings.py** – Seller ratings from consumers and charities 
  - **support.py** – Support ticket submission and updates  
  - **charity.py** – Charity onboarding and list charity organisations 
  - **payment.py** – Payment marking and verification  
  - **users.py** – User account and role management  

- **saveplate.db**  
  SQLite database storing all application data.

- **README.md**  
  Documentation describing the system, features, and setup instructions.

- **.gitignore**  
  Specifies ignored files and folders for version control.


## Future Roadmap

- Develop a frontend (web or mobile) to connect with the backend APIs and provide a usable interface for all platform features.
- Add user authentication and authorization with secure login, password hashing, and token-based sessions.
- Add analytics dashboards for sellers and charities, showing metrics like sales, donations, and listing performance.
- Integrate AI-based recommendations to help consumers discover relevant surplus listings based on past behavior and preferences.
