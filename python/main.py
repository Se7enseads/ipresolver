import socket
import re
import click
import inquirer

from urllib.parse import urlparse

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base

from tabulate import tabulate

Base = declarative_base()
engine = create_engine('sqlite:///ip_addresses.db')
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

SUCCESS_COLOR = 'green'
ERROR_COLOR = 'red'
WARNING_COLOR = 'yellow'

class IPAddress(Base):
    __tablename__ = 'ip_addresses'

    id = Column(Integer, primary_key=True)
    hostname = Column(String)
    ip_address = Column(String)


def is_valid_hostname(hostname):
    hostname_pattern = r'^[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)+$'
    return re.match(hostname_pattern, hostname)


def store_ip_address(engine, hostname, ip_address):

    ip_entry = IPAddress(hostname=hostname, ip_address=ip_address)

    session.add(ip_entry)
    session.commit()
    session.close()


def get_ip_addresses():

    ip_addresses = session.query(IPAddress).all()

    session.close()
    return ip_addresses


def display_ip_history():
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


def resolve_ip():
    while True:
        input_url = click.prompt(
            click.style("Please enter a website address (URL) or type 'back' to quit", fg="blue"), default='', show_default=False)

        if input_url == 'back':
            print(click.style("Operation aborted by the user.", fg=WARNING_COLOR))
            break

        try:
            parsed_url = urlparse(input_url)
            if parsed_url.netloc:
                hostname = parsed_url.netloc
            else:
                hostname = input_url

            if not is_valid_hostname(hostname):
                print(click.style("Invalid input. Please enter a valid hostname or URL.", fg=WARNING_COLOR))
                continue

            if len(hostname) <= 4:
                print(click.style("Hostname should be more than 4 characters.", fg=WARNING_COLOR))
                continue

            ip_address = socket.gethostbyname(hostname)
            store_ip_address(engine, hostname, ip_address)
            print(f"\n\n{'*' * 40}")
            print(click.style(f'Hostname: {hostname}', fg=SUCCESS_COLOR))
            print(f'IP: {ip_address}')
            print(f"{'*' * 40}\n\n")
        except socket.gaierror as error:
            print(click.style(
                f'Error: Unable to resolve hostname {hostname}.', fg=ERROR_COLOR))


def delete_record():
    record_id = click.prompt("Enter the ID of the record you want to delete")

    try:
        record_id = int(record_id)
    except ValueError:
        print(click.style("Invalid ID. Please enter a valid numeric ID.", fg=WARNING_COLOR))
        return

    ip_addresses = get_ip_addresses()
    for ip_address in ip_addresses:
        if ip_address.id == record_id:
            session.delete(ip_address)
            session.commit()
            print(click.style(
                f"Record with ID {record_id} deleted successfully.", fg=SUCCESS_COLOR))
            return

    print(click.style(f"No record found with ID {record_id}.", fg=WARNING_COLOR))


def clear_database():
    try:
        session.query(IPAddress).delete()
        session.commit()
        print(click.style("Database cleared successfully.", fg=SUCCESS_COLOR))
    except Exception as e:
        session.rollback()
        print(click.style(f"Error clearing the database: {str(e)}", fg=ERROR_COLOR))


@click.command()
@click.option('--resolve', is_flag=True, help="Resolve and store IP address for a URL.")
@click.option('--history', is_flag=True, help="Display the database history.")
@click.option('--delete', is_flag=True, help="Delete a record.")
@click.option('--clear', is_flag=True, help="Clear the database.")
def get_hostname_ip(resolve, history, delete, clear):

    if resolve:
        resolve_ip()
    elif history:
        display_ip_history()
    elif delete:
        delete_record()
    elif clear:
        clear_database()

    else:
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

            elif answers['menu'] == "Display IP History":
                display_ip_history()
                break

            elif answers['menu'] == "Delete a record":
                display_ip_history()
                delete_record()
                break

            elif answers['menu'] == "Resolve and Store IP Address":
                resolve_ip()


if __name__ == "__main__":
    get_hostname_ip()
