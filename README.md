Movie Review Web App

Welcome to the Movie Review Web App, a lask-based web application designed for movie enthusiasts to manage and review their favorite movies. This app leverages modern technologies and APIs to provide a seamless movie browsing and management experience.

Technologies Used

    Flask: This app is built using Flask, a micro web framework in Python. Flask allows for rapid development and easy integration with various components.
    Flask-Bootstrap 5: The app's frontend is enhanced with Bootstrap 5, a popular CSS framework. This ensures a clean and responsive user interface across different devices.
    Flask-SQLAlchemy: SQLAlchemy is used as an Object-Relational Mapping (ORM) tool to interact with the SQLite database. It simplifies database operations and provides an intuitive way to manage data.
    Flask-WTF: Flask-WTF simplifies the integration of web forms with Flask. It's used to create and validate forms for adding and editing movies.
    Flask-Login: Flask-Login is used for user authentication, session management, and protecting routes. It provides easy-to-use methods for handling user sessions securely.
    The Movie Database (TMDb) API: The app fetches movie information and trailers using the TMDb API. This API integration enhances the app's functionality by providing accurate and up-to-date movie data.
    SQLite Database: The app uses an SQLite database to store movie information, ratings, and reviews. SQLAlchemy helps manage the interaction between the app and the database.
    Python Requests Library: The Python Requests library is used to make HTTP requests to the TMDb API. It's responsible for fetching movie data and trailers.
    Environment Variables: API keys and tokens are stored as environment variables to keep sensitive information secure.

Features

    View a list of movies ordered by rating.
    Add new movies to the collection using TMDb API integration.
	User authentication to provide a personalized experience for each user. Users can register, log in, and log out to access their own collection of favorite movies and reviews.
    Edit the rating and review of existing movies.
    Delete movies from the collection.
    View detailed descriptions and trailers of individual movies.
    User authentication and management for a personalized experience.