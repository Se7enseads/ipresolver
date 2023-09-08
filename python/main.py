""" Import relevant modules in the project. """
# pylint: disable=E0401
import socket
import re
from urllib.parse import urlparse
import dataclasses
import click
import inquirer

# Import SQLAlchemy components for database operations.
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError

# Import Pydantic for input validation.
from pydantic import BaseModel, field_validator, Field

# Import Tabulate for displaying data in a tabular format.
from tabulate import tabulate

# Create a SQLAlchemy database engine and establish a connection.
Base = declarative_base()
engine = create_engine('sqlite:///ip_addresses.db')
Base.metadata.create_all(engine)

# Create a database session.
Session = sessionmaker(bind=engine)
session = Session()

# Define color constants for console output.
SUCCESS_COLOR = 'green'
ERROR_COLOR = 'red'
WARNING_COLOR = 'yellow'

# Define a data class for the IPAddress table in the database.
@dataclasses.dataclass
class IPAddress(Base):
    """Class to handle the table for storing IP addresses."""

    __tablename__ = 'ip_addresses'

    id = Column(Integer, primary_key=True)
    hostname = Column(String)
    ip_address = Column(String)

    def __init__(self, hostname, ip_address):
        self.hostname = hostname
        self.ip_address = ip_address

# Define a Pydantic BaseModel for input validation.
@dataclasses.dataclass
class ResolveInput(BaseModel):
    """ Class to validate and handle user input for resolving IP addresses. """
    input_url: str = Field(min_length=6, max_length=20)

    @field_validator('input_url')
    @classmethod
    def validate_url(cls, value):
        """ Function to validate the entered URL. """
        if not is_valid_hostname(value):
            raise ValueError(
                "Invalid input. Please enter a valid hostname or URL.")
        return value

# Define a function to validate hostnames using regular expressions.
def is_valid_hostname(hostname):
    """ Function to validate the entered hostname. """
    hostname_pattern = r'^[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)+$'
    return re.match(hostname_pattern, hostname)

# Define a function to store resolved IP addresses in the database.
def store_ip_address(hostname, ip_address):
    """ Function to store resolved hostnames in the database. """

    ip_entry = IPAddress(hostname=hostname, ip_address=ip_address)

    session.add(ip_entry)
    session.commit()
    session.close()

# Define a function to retrieve all saved resolved hostnames from the database.
def get_ip_addresses():
    """ Function to retrieve all saved resolved hostnames from the database. """

    ip_addresses = session.query(IPAddress).all()

    session.close()
    return ip_addresses

# Define a function to display resolved hostnames stored in the database.
def display_ip_history():
    """ Function to display resolved hostnames stored in the database. """
    ip_addresses = get_ip_addresses()
    if ip_addresses:
        row_data = [(data.hostname, data.ip_address)
                    for data in ip_addresses]
        row_id = [data.id for data in ip_addresses]
        headers = ["Hostname", "IP Address"]
        print(f"\n\n{'*' * 40}")
        print(tabulate(row_data, headers, tablefmt="simple_grid", showindex=row_id))
        print(f"{'*' * 40}\n")

    else:
        print("No IP addresses in the database.")

# Define a function to resolve IP addresses and store them in the database.
def resolve_ip():
    """ Function to resolve the entered URL/hostname and store it in the database. """
    while True:
        try:
            input_data = click.prompt(
                click.style(
                    "Please enter a website address (URL) or type 'back' to quit", fg="blue"),
                default='',
                show_default=False,
            )

            if input_data == 'back':
                print(click.style("Operation aborted by the user.", fg=WARNING_COLOR))
                break

            # Use urlparse to extract the hostname from the URL.
            parsed_url = urlparse(input_data)
            hostname = parsed_url.hostname or input_data

            ip_address = socket.gethostbyname(hostname)
            store_ip_address(hostname, ip_address)
            print(f"\n\n{'*' * 40}")
            print(click.style(f'Hostname: {hostname}', fg=SUCCESS_COLOR))
            print(f'IP: {ip_address}')
            print(f"{'*' * 40}\n\n")
        except socket.gaierror:
            print(click.style(
                f'Error: Unable to resolve hostname {hostname}.', fg=ERROR_COLOR))

# Define a function to delete a record from the database using the ID.
def delete_record():
    """ Function to delete a record from the database using the ID. """
    record_id = click.prompt("Enter the ID of the record you want to delete")

    try:
        record_id = int(record_id)
    except ValueError:
        print(click.style(
            "Invalid ID. Please enter a valid numeric ID.", fg=WARNING_COLOR))
        return

    ip_addresses = get_ip_addresses()
    for ip_address in ip_addresses:
        if ip_address.id == record_id:
            session.delete(ip_address)
            session.commit()
            print(click.style(
                f"Record with ID {record_id} deleted successfully.", fg=SUCCESS_COLOR))
            return

    print(click.style(
        f"No record found with ID {record_id}.", fg=WARNING_COLOR))

# Define a function to clear all records from the database.
def clear_database():
    """ Function to clear all records from the database. """
    try:
        session.query(IPAddress).delete()
        session.commit()
        print(click.style("Database cleared successfully.", fg=SUCCESS_COLOR))
    except SQLAlchemyError as error:
        session.rollback()
        print(click.style(
            f"Error clearing the database: {str(error)}", fg=ERROR_COLOR))

# Define the main CLI function for interacting with IP address resolution and management.
@click.command()
@click.option('--resolve', is_flag=True, help="Resolve and store IP address for a URL.")
@click.option('--history', is_flag=True, help="Display the database history.")
@click.option('--delete', is_flag=True, help="Delete a record.")
@click.option('--clear', is_flag=True, help="Clear the database.")
def get_hostname_ip(resolve, history, delete, clear):
    """ Main function to interact with IP address resolution and management. """

    if resolve:
        resolve_ip()
    elif history:
        display_ip_history()
    elif delete:
        delete_record()
    elif clear:
        clear_database()

    else:
        # If no specific option is selected, present a menu for user interaction.
        questions = [
            inquirer.List('menu',
                          message="Select an option",
                          choices=[
                              "Resolve and Store IP Address",
                              "Display IP History",
                              "Delete a record",
                              "Exit"
                          ]),
        ]

        while True:
            answers = inquirer.prompt(questions)

            if answers['menu'] == "Exit":
                print(click.style("Operation aborted by the user.", fg=WARNING_COLOR))
                break

            if answers['menu'] == "Display IP History":
                display_ip_history()
                break

            if answers['menu'] == "Delete a record":
                display_ip_history()
                delete_record()
                break

            if answers['menu'] == "Resolve and Store IP Address":
                resolve_ip()

# Entry point of the script, execute the main function if the script is run.
if __name__ == "__main__":
    # pylint: disable=E1120
    get_hostname_ip()
