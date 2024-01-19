import os

class Config:
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SECRET_KEY = "something_key_here"

class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv("DEVELOPMENT_DATABASE_URL")
    REDIS_URL = os.getenv("REDIS_URL")

class TestingConfig(Config):
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL")
    REDIS_URL = os.getenv("REDIS_URL")

class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv("STAGING_DATABASE_URL")

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv("PRODUCTION_DATABASE_URL")
    
config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "staging": StagingConfig,
    "production": ProductionConfig
}