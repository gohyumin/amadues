# Flask Web Application with DynamoDB

This is a web application built using Flask (Python) and Amazon DynamoDB for the database.

## Project Structure
```
├── app.py                  # Main Flask application file
├── static/                 # Static files directory
│   ├── assets/            # Core assets
│   │   ├── css/          # CSS files
│   │   │   ├── auth.css  # Authentication styles
│   │   │   └── main.css  # Main application styles
│   │   ├── img/          # Image assets
│   │   │   ├── about/    # About section images
│   │   │   ├── features/ # Features section images
│   │   │   ├── misc/     # Miscellaneous images
│   │   │   ├── person/   # Person/Team member images
│   │   │   └── services/ # Services section images
│   │   ├── js/          # JavaScript files
│   │   │   └── main.js  # Main JavaScript functionality
│   │   ├── scss/        # SCSS source files
│   │   └── vendor/      # Third-party libraries
│   │       ├── aos/     # Animate On Scroll library
│   │       ├── bootstrap/# Bootstrap framework files
│   │       ├── bootstrap-icons/# Bootstrap icons
│   │       ├── php-email-form/# PHP email form validator
│   │       └── swiper/  # Swiper slider library
│   ├── css/            # Additional CSS
│   ├── forms/          # Form handling
│   │   └── contact.php # Contact form processor
│   ├── img/            # Additional images
│   └── js/             # Additional JavaScript
└── templates/          # Flask HTML templates
    ├── index.html      # Main landing page
    ├── register.html   # User registration page
    ├── service-details.html # Service details page
    └── starter-page.html   # Template starter page
```

## Prerequisites

Before running this application, make sure you have the following installed:
- Python 3.x
- pip (Python package installer)
- AWS Account and configured credentials

## Installation

1. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
.\venv\Scripts\activate  # For Windows
```

2. Install the required packages:
```bash
pip install flask
pip install boto3
pip install python-dotenv
```

## AWS Configuration

1. Make sure you have AWS credentials configured either through:
   - AWS CLI configuration
   - Environment variables
   - Or a .env file (recommended for development)

2. If using a .env file, create one with your AWS credentials:
```
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=your_region
```

## Running the Application

1. Start the Flask application:
```bash
python app.py
```

2. Open your web browser and navigate to:
```
http://localhost:5000
```

## Features

- Responsive web design using Bootstrap
- Dynamic content rendering with Flask templates
- Data persistence using Amazon DynamoDB
- Custom CSS and JavaScript implementations
- Form handling and validation
- Image assets management

## Additional Information

- The application uses AOS (Animate On Scroll) library for animations
- Bootstrap Icons for UI elements
- Swiper for carousel/slider functionality
- Custom PHP email form (in static/forms)

## Project Dependencies

- Flask - Web framework
- Boto3 - AWS SDK for Python
- Bootstrap - Frontend framework
- AOS - Animation library
- Swiper - Touch slider

## Development

To modify the application:
- HTML templates are in the `templates/` directory
- Static files (CSS, JS, images) are in the `static/` directory
- Main application logic is in `app.py`
- Database operations are handled through boto3 DynamoDB client