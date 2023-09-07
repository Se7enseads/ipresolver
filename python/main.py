import socket
import re
import click
import inquirer

from urllib.parse import urlparse

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
engine = create_engine('sqlite:///ip_addresses.db')
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()


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


def resolve_ip():
    while True:
        input_url = click.prompt(
            "Please enter a website address (URL) or type 'back' to quit", default='', show_default=False)

        if input_url == 'back':
            print("Operation aborted by the user.")
            break

        try:
            parsed_url = urlparse(input_url)
            if parsed_url.netloc:
                hostname = parsed_url.netloc
            else:
                hostname = input_url

            if not is_valid_hostname(hostname):
                print("Invalid input. Please enter a valid hostname or URL.")
                continue

            if len(hostname) <= 4:
                print("Hostname should be more than 4 characters.")
                continue

            ip_address = socket.gethostbyname(hostname)
            store_ip_address(engine, hostname, ip_address)
            print(f"\n\n{'*' * 40}")
            print(click.style(f'Hostname: {hostname}', fg='green'))
            print(f'IP: {ip_address}')
            print(f"{'*' * 40}\n\n")
        except socket.gaierror as error:
            print(click.style(
                f'Error: Unable to resolve hostname {hostname}.', fg="red"))


@click.command()
@click.option('--resolve', is_flag=True, help="Resolve and store IP address for a URL.")
def get_hostname_ip(resolve):

    if resolve:
        resolve_ip()

    else:
        questions = [
            inquirer.List('menu',
                          message="Select an option",
                          choices=[
                              "Resolve and Store IP Address",
                              "Exit"
                          ]),
        ]

        while True:
            answers = inquirer.prompt(questions)

            if answers['menu'] == "Exit":
                print("Operation aborted by the user.")
                break

            elif answers['menu'] == "Resolve and Store IP Address":
                resolve_ip()


if __name__ == "__main__":
    get_hostname_ip()
