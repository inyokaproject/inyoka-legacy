CELERY_RESULT_BACKEND = 'amqp'
CELERY_IMPORTS = ['inyoka.core.tasks']
BROKER_HOST = 'localhost'
BROKER_PORT = 5672
BROKER_USER = 'inyoka'
BROKER_PASSWORD = 'default'
BROKER_VHOST = 'inyoka'
