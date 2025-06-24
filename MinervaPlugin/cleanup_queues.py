#!/usr/bin/env python3
"""
Script to clean up RabbitMQ queues that have conflicting TTL settings.
This resolves the PRECONDITION_FAILED error when queue arguments don't match.
"""

import pika
import logging
from config import RABBITMQ_SERVER, PING_QUEUE, COMMAND_QUEUE, MINERVA_STREAM_QUEUE

def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def delete_queue_if_exists(channel, queue_name, logger):
    """
    Delete a queue if it exists.
    
    Args:
        channel: RabbitMQ channel
        queue_name (str): Name of the queue to delete
        logger: Logger instance
    """
    try:
        # Try to delete the queue
        channel.queue_delete(queue=queue_name)
        logger.info(f"Successfully deleted queue: {queue_name}")
        return True
    except pika.exceptions.ChannelClosedByBroker as e:
        if "NOT_FOUND" in str(e):
            logger.info(f"Queue {queue_name} does not exist, skipping deletion")
            return True
        else:
            logger.error(f"Error deleting queue {queue_name}: {e}")
            return False
    except Exception as e:
        logger.error(f"Unexpected error deleting queue {queue_name}: {e}")
        return False

def cleanup_queues():
    """
    Clean up existing queues that might have conflicting TTL settings.
    """
    logger = setup_logging()
    
    try:
        # Connect to RabbitMQ
        logger.info(f"Connecting to RabbitMQ server: {RABBITMQ_SERVER}")
        connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_SERVER))
        channel = connection.channel()
        
        # List of queues that might have TTL conflicts
        queues_to_cleanup = [
            PING_QUEUE,
            COMMAND_QUEUE,
            MINERVA_STREAM_QUEUE
        ]
        
        logger.info("Starting queue cleanup...")
        
        for queue_name in queues_to_cleanup:
            logger.info(f"Processing queue: {queue_name}")
            
            # Create a new channel for each operation to handle potential channel closures
            try:
                channel = connection.channel()
                delete_queue_if_exists(channel, queue_name, logger)
            except pika.exceptions.ChannelClosedByBroker:
                # Channel was closed, create a new one
                logger.info(f"Channel closed while processing {queue_name}, creating new channel")
                channel = connection.channel()
        
        logger.info("Queue cleanup completed successfully")
        
        # Close connection
        connection.close()
        logger.info("Connection closed")
        
    except pika.exceptions.AMQPConnectionError as e:
        logger.error(f"Failed to connect to RabbitMQ: {e}")
        logger.error("Make sure RabbitMQ server is running and accessible")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during cleanup: {e}")
        return False
    
    return True

def main():
    """Main function to run the cleanup script."""
    print("RabbitMQ Queue Cleanup Script")
    print("=" * 40)
    print("This script will delete existing queues to resolve TTL conflicts.")
    print("The queues will be recreated automatically when the application starts.")
    print()
    
    response = input("Do you want to proceed with queue cleanup? (y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("Cleanup cancelled.")
        return
    
    print("\nStarting cleanup...")
    success = cleanup_queues()
    
    if success:
        print("\n✅ Cleanup completed successfully!")
        print("You can now restart your application.")
    else:
        print("\n❌ Cleanup failed. Please check the logs above.")
        print("Make sure RabbitMQ server is running and accessible.")

if __name__ == "__main__":
    main()
