# src/main.py
import logging
import click
import json
import datetime
from src.queue_manager import AlarmQueue
from src.config import load_config, update_config
from src.database import DatabaseManager
from src.sms_sender import SMSSender
from src.logger import setup_logger
from src.db_init import init_database


def setup():
    """Initialize configuration and logging."""
    config = load_config()
    setup_logger(config['logging'].get('log_dir', 'logs'))


def is_special_day():
    """
    Check if today is a special day (Saturday or Jewish holiday).
    """
    # Load config to initialize database connection
    config = load_config()

    # Create database manager
    db = DatabaseManager(
        username=config['database']['username'],
        password=config['database']['password'],
        server=config['database']['server'],
        database=config['database']['database']
    )

    # Use the database method to check if today is a sabbatical holiday
    return db.is_sabbatical_holiday()


@click.group()
def cli():
    """SCADA SMS Notification System"""
    pass


@cli.command('send-alarm')
@click.argument('message')
@click.argument('group_id', type=int)
@click.option('--special-day', is_flag=True, help="Force special day flag (otherwise auto-detected)")
def send_alarm(message, group_id, special_day):
    """Send alarm notification to a group."""
    config = load_config()
    setup_logger(config['logging'].get('log_dir', 'logs'))
    logger = logging.getLogger(__name__)

    # Determine if special day flag should be set
    special_day_flag = special_day or is_special_day()

    if special_day_flag:
        logger.info("Special day flag is active")

    try:
        queue = AlarmQueue()
        # Pass special day flag to the queue
        alarm_id = queue.enqueue_alarm(message, group_id, special_day_flag)
        if alarm_id:
            click.echo(f"Alarm queued successfully. ID: {alarm_id}")
            logger.info("Starting queue processing...")
            process_queue_internal()  # Call the internal function
    except Exception as err:
        logger.error(f"Failed to queue alarm: {err}")
        raise click.ClickException(str(err))


@cli.command('process-queue')
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
        sms = SMSSender(
            api_hostname=config['api']['hostname'],
            params_json=config['api']['params']
        )

        logger.info("Looking for alarms to process...")
        while True:
            alarm = queue.get_next_alarm()
            if not alarm:
                logger.info("No more alarms to process")
                break

            logger.info(f"Processing alarm: {alarm['id']}")

            try:
                # Check if this is a special day alarm
                is_special_day_alarm = alarm.get('special_day', False)

                # Get recipients based on special day flag
                recipients = db.get_sms_recipients(
                    alarm['group_id'],
                    is_special_day=is_special_day_alarm
                )
                logger.info(
                    f"About to get recipients for group {alarm['group_id']} with special_day flag: {is_special_day_alarm}")

                if not recipients:
                    logger.warning(
                        f"No SMS-enabled recipients found for group {alarm['group_id']}" +
                        (" on special day" if is_special_day_alarm else "")
                    )
                    queue.mark_completed(alarm['id'])
                    continue

                # Send SMS to each recipient
                success = True
                for recipient in recipients:
                    try:
                        response, message_status = sms.send_sms(
                            recipient['phone_number'],
                            alarm['description']
                        )
                        status = 'SUCCESS'
                    except Exception as err:
                        logger.error(f"Failed to send SMS to {recipient['phone_number']}: {err}")
                        response = str(err)
                        status = 'FAILED'
                        message_status = getattr(err, 'args', ['UNKNOWN_ERROR'])[0]
                        success = False

                    # Log to SQL audit with enhanced details
                    try:
                        db.log_sms_audit(
                            alarm_id=alarm['id'],
                            user_id=recipient['user_id'],
                            phone_number=recipient['phone_number'],
                            alarm_desc=alarm['description'],
                            status=status,
                            message_status=message_status,
                            response=str(response)
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
@click.argument('section')
@click.argument('key')
@click.argument('value')
def set_config(section: str, key: str, value: str):
    """Set a configuration value."""
    try:
        update_config(section, key, value)
        click.echo(f"{section}.{key} updated successfully")
    except Exception as err:
        raise click.ClickException(str(err))


@cli.command()
@click.argument('params_json')
def set_api_params(params_json: str):
    """Update API parameters JSON."""
    logger = logging.getLogger(__name__)
    try:
        # Try to handle both single and double quote formats
        if params_json.startswith("'"):
            params_json = params_json.replace("'", '"')
        parsed = json.loads(params_json)
        cleaned_json = json.dumps(parsed)
        update_config('api', 'params', cleaned_json)
        click.echo("API parameters updated successfully")
    except json.JSONDecodeError as e:
        logger.error(f"JSON Error. Input was: {repr(params_json)}")
        raise click.ClickException(f"Invalid JSON format: {e}")


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