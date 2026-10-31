# E-commerce Backend API

A RESTful E-commerce Backend API built using Django REST Framework and PostgreSQL.

This project provides backend functionality for an e-commerce application, including user registration, email and phone verification, JWT authentication, product management, shopping cart operations, order processing, and online payment integration using Razorpay.

The API includes interactive documentation through Swagger UI and ReDoc.

## Features

* User registration and authentication
* Email OTP verification
* Phone OTP verification using Twilio
* JWT access and refresh tokens
* Product and category management
* Product search and ordering
* Shopping cart management
* Order creation and management
* Product stock validation
* Razorpay payment integration (Test Mode)
* Payment signature verification
* Automatic stock updates after successful payment
* API documentation using Swagger UI and ReDoc

## Technologies Used

### Backend

* Python
* Django
* Django REST Framework

### Database

* PostgreSQL

### Authentication

* JWT Authentication (Simple JWT)
* Email OTP Verification
* Twilio Verify API

### Payment Gateway

* Razorpay (Test Mode)

### API Documentation

* drf-spectacular
* Swagger UI
* ReDoc

### Development Tools

* Visual Studio Code
* Postman
* Git and GitHub
* Python Virtual Environment

## Project Structure

```text
ecommerce-backend/
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── ...
│
├── users/
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
│
├── products/
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
│
├── cart/
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
│
├── orders/
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
│
├── manage.py
├── requirements.txt
├── .env
└── README.md

## Installation and Setup

### 1. Clone the repository


git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd ecommerce-backend
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it:

**Windows:**

```powershell
venv\Scripts\activate
```

**Linux/macOS:**

```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root and configure the required environment variables.

See the Environment Variables section below.

### 5. Configure PostgreSQL

Create a PostgreSQL database and configure its credentials in your `.env` file.

### 6. Apply migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Create a superuser

```bash
python manage.py createsuperuser
```

### 8. Run the development server

```bash
python manage.py runserver
```

The API will be available at:

`http://127.0.0.1:8000/`


## Environment Variables

Create a `.env` file in the project root and configure the following variables:

```env
SECRET_KEY=your-django-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=your-database-name
DB_USER=your-database-user
DB_PASSWORD=your-database-password
DB_HOST=localhost
DB_PORT=5432

RAZORPAY_KEY_ID=your-razorpay-key-id
RAZORPAY_KEY_SECRET=your-razorpay-key-secret

EMAIL_HOST=your-email-host
EMAIL_PORT=your-email-port
EMAIL_HOST_USER=your-email
EMAIL_HOST_PASSWORD=your-email-password

TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_VERIFY_SERVICE_SID=your-twilio-verify-service-sid
```

**Important:**

* Never commit your `.env` file to GitHub.
* Keep API keys, passwords, and secret keys private.
* Set `DEBUG=False` in production.
* Configure production environment variables through your hosting provider.


## API Endpoints

### Authentication — Users

| Method | Endpoint                       | Description          |
| ------ | ------------------------------ | -------------------- |
| POST   | `/api/users/register/`         | Register a new user  |
| POST   | `/api/users/email-otp/send/`   | Send email OTP       |
| POST   | `/api/users/email-otp/verify/` | Verify email OTP     |
| POST   | `/api/users/phone-otp/send/`   | Send phone OTP       |
| POST   | `/api/users/phone-otp/verify/` | Verify phone OTP     |
| POST   | `/api/token/`                  | Obtain JWT tokens    |
| POST   | `/api/token/refresh/`          | Refresh access token |

### Products

| Method    | Endpoint              | Description      |
| --------- | --------------------- | ---------------- |
| GET       | `/api/products/`      | List products    |
| POST      | `/api/products/`      | Create a product |
| GET       | `/api/products/{id}/` | Retrieve product |
| PUT/PATCH | `/api/products/{id}/` | Update product   |
| DELETE    | `/api/products/{id}/` | Delete product   |

### Cart

| Method    | Endpoint                       | Description         |
| --------- | ------------------------------ | ------------------- |
| GET       | `/api/cart/`                   | Retrieve user cart  |
| POST      | `/api/cart/items/`             | Add product to cart |
| DELETE    | `/api/cart/items/{id}/`        | Remove cart item    |
| PUT/PATCH | `/api/cart/items/{id}/update/` | Update cart item    |

### Orders and Payments

| Method | Endpoint                                 | Description           |
| ------ | ---------------------------------------- | --------------------- |
| POST   | `/api/orders/checkout/`                  | Create checkout order |
| POST   | `/api/orders/{order_id}/payment/`        | Create Razorpay order |
| POST   | `/api/orders/{order_id}/verify-payment/` | Verify payment        |


## Authentication

This project uses JSON Web Token (JWT) authentication through Simple JWT.

### Authentication Flow

1. Register a new user.
2. Verify the email using OTP.
3. Verify the phone number using Twilio OTP.
4. Obtain JWT access and refresh tokens.
5. Include the access token in protected API requests.

Authorization header:

```http
Authorization: Bearer <access_token>
```

## Payment Integration

This project integrates Razorpay for online payment processing.

### Payment Flow

1. Customer adds products to the cart.
2. Customer initiates checkout.
3. Backend creates an order.
4. Backend creates a Razorpay payment order.
5. Customer completes payment using Razorpay Checkout.
6. Backend verifies the payment signature.
7. Backend checks payment details and stock availability.
8. Order and inventory are updated after successful verification.

**Note:** Payment integration is currently configured for Razorpay Test Mode.

## API Documentation

Interactive API documentation is available through:

* **Swagger UI:** `/api/swagger/`
* **ReDoc:** `/api/redo

## Future Improvements

* Automated API testing
* Razorpay webhook integration
* Actual refund processing
* Enhanced logging and monitoring
* Production deployment and optimization

## Author

Thanveerul Irfan

Developed as a Django REST Framework portfolio project.