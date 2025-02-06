# src/main.py
import logging
import click
from queue_manager import AlarmQueue
from config import load_config, update_config
from database import DatabaseManager
from sms_sender import SMSSender
from logger import setup_logger
from db_init import init_database


def setup():
    """Initialize configuration and logging."""
    config = load_config()
    setup_logger(config['logging'].get('log_dir', 'logs'))

@click.group()
def cli():
    """SCADA SMS Notification System"""
    pass


@cli.command('send-alarm')
@click.argument('message')
@click.argument('group', type=int)
def send_alarm(message, group):
    """Send alarm notification to a group."""
    config = load_config()
    setup_logger(config['logging'].get('log_dir', 'logs'))
    logger = logging.getLogger(__name__)

    try:
        queue = AlarmQueue()
        alarm_id = queue.enqueue_alarm(message, group)
        if alarm_id:
            click.echo(f"Alarm queued successfully. ID: {alarm_id}")
            logger.info("Starting queue processing...")
            process_queue_internal()  # Call the internal function instead of the CLI command
    except Exception as err:
        logger.error(f"Failed to queue alarm: {err}")
        raise click.ClickException(str(err))

@cli.command('process-queue')  # Use hyphen in command name
def process_queue():
    """CLI command to process queued alarms."""
    config = load_config()  # Make sure we have config
    setup_logger(config['logging'].get('log_dir', 'logs'))  # Set up logging
    process_queue_internal()


def process_queue_internal():
    """Internal function to process queued alarms."""
    logger = logging.getLogger(__name__)
    logger.info("Process queue started")

    config = load_config()
    queue = AlarmQueue()

    try:
        logger.info("Initializing database connection...")
        db = DatabaseManager(
            username=config['database']['username'],
            password=config['database']['password'],
            server=config['database']['server'],
            database=config['database']['database']
        )

        logger.info("Initializing SMS sender...")
        sms = SMSSender(config['api']['hostname'])

        logger.info("Looking for alarms to process...")
        while True:
            alarm = queue.get_next_alarm()
            if not alarm:
                logger.info("No more alarms to process")
                break

            logger.info(f"Processing alarm: {alarm['id']}")

            try:
                # Process alarm
                recipients = db.get_sms_recipients(alarm['group_number'])

                if not recipients:
                    logger.warning(f"No SMS-enabled recipients found for group {alarm['group_number']}")
                    queue.mark_completed(alarm['id'])
                    continue

                # Send SMS to each recipient
                success = True
                for recipient in recipients:
                    try:
                        response = sms.send_sms(recipient['phone_number'], alarm['description'])
                        status = 'SUCCESS'
                    except Exception as err:
                        logger.error(f"Failed to send SMS to {recipient['phone_number']}: {err}")
                        response = str(err)
                        status = 'FAILED'
                        success = False

                    # Log to SQL audit
                    try:
                        db.log_sms_audit(
                            alarm['id'],
                            recipient['user_id'],
                            alarm['description'],
                            status,
                            str(response)
                        )
                    except Exception as audit_err:
                        logger.error(f"Audit logging failed: {audit_err}")
                        success = False

                if success:
                    queue.mark_completed(alarm['id'])
                    logger.info(f"Alarm {alarm['id']} processed successfully")
                else:
                    queue.mark_failed(alarm['id'], "Some messages failed to send or log")
                    logger.error(f"Alarm {alarm['id']} processing had some failures")

            except Exception as err:
                logger.error(f"Error processing alarm {alarm['id']}: {err}")
                queue.mark_failed(alarm['id'], str(err))

    except Exception as err:
        logger.error(f"Queue processing failed: {err}")
        raise click.ClickException(str(err))

@cli.command()
@click.argument('username')
@click.argument('password')
def set_db_credentials(username: str, password: str):
    """Update database credentials."""
    logger = logging.getLogger(__name__)
    try:
        update_config('database', 'username', username)
        update_config('database', 'password', password)
        click.echo("Database credentials updated successfully")
    except Exception as err:
        logger.error(f"Failed to update database credentials: {err}")
        raise click.ClickException(str(err))

@cli.command()
@click.argument('hostname')
def set_api_hostname(hostname: str):
    """Update API hostname."""
    logger = logging.getLogger(__name__)
    try:
        update_config('api', 'hostname', hostname)
        click.echo("API hostname updated successfully")
    except Exception as err:
        logger.error(f"Failed to update API hostname: {err}")
        raise click.ClickException(str(err))

@cli.command()
@click.argument('server')
@click.argument('database')
def set_db_connection(server: str, database: str):
    """Update database server and database name."""
    logger = logging.getLogger(__name__)
    try:
        update_config('database', 'server', server)
        update_config('database', 'database', database)
        click.echo("Database connection settings updated successfully")
    except Exception as err:
        logger.error(f"Failed to update database connection settings: {err}")
        raise click.ClickException(str(err))

@cli.command()
def init_db():
    """Initialize database tables and indexes."""
    logger = logging.getLogger(__name__)
    config = load_config()

    try:
        db = DatabaseManager(
            username=config['database']['username'],
            password=config['database']['password'],
            server=config['database']['server'],
            database=config['database']['database']
        )

        init_database(db)
        click.echo("Database initialized successfully")

    except Exception as err:
        logger.error(f"Database initialization failed: {err}")
        raise click.ClickException(str(err))

if __name__ == '__main__':
    cli(standalone_mode=True)