import pytest
from cyborgdb_service.utils.environment_check import validate_connection_string


class TestValidateConnectionString:
    """Test connection string validation without database dependencies"""
    
    def test_valid_redis_connection_string(self):
        """Test valid Redis connection strings"""
        # Basic valid format
        success, msg = validate_connection_string('host:localhost,port:6379,db:0', 'redis')
        assert success is True
        assert "valid" in msg.lower()
        
        # With password
        success, msg = validate_connection_string('host:localhost,port:6379,db:0,password:secret', 'redis')
        assert success is True
        
        # Different port
        success, msg = validate_connection_string('host:redis.example.com,port:6380,db:1', 'redis')
        assert success is True
    
    def test_invalid_redis_connection_string(self):
        """Test invalid Redis connection strings"""
        # URI format not supported
        success, msg = validate_connection_string('redis://localhost:6379', 'redis')
        assert success is False
        assert "URI format not supported" in msg
        
        # Missing required fields
        success, msg = validate_connection_string('host:localhost', 'redis')
        assert success is False
        assert "required" in msg.lower()
        
        # Invalid port number
        success, msg = validate_connection_string('host:localhost,port:99999,db:0', 'redis')
        assert success is False
        assert "Invalid port" in msg
        
        # Non-numeric port
        success, msg = validate_connection_string('host:localhost,port:abc,db:0', 'redis')
        assert success is False
        assert "must be a number" in msg
        
        # Negative db number
        success, msg = validate_connection_string('host:localhost,port:6379,db:-1', 'redis')
        assert success is False
        assert "non-negative" in msg
    
    def test_valid_postgres_connection_string(self):
        """Test valid PostgreSQL connection strings"""
        # Basic valid format
        success, msg = validate_connection_string(
            'host=localhost port=5432 dbname=mydb user=myuser password=mypass',
            'postgres'
        )
        assert success is True
        assert "valid" in msg.lower()
        
        # Without password
        success, msg = validate_connection_string(
            'host=localhost port=5432 dbname=testdb user=testuser',
            'postgres'
        )
        assert success is True
        
        # With additional parameters
        success, msg = validate_connection_string(
            'host=db.example.com port=5433 dbname=prod user=admin sslmode=require',
            'postgres'
        )
        assert success is True
    
    def test_invalid_postgres_connection_string(self):
        """Test invalid PostgreSQL connection strings"""
        # Missing required field - host
        success, msg = validate_connection_string(
            'port=5432 dbname=mydb user=myuser',
            'postgres'
        )
        assert success is False
        assert "host" in msg.lower()
        
        # Missing required field - port
        success, msg = validate_connection_string(
            'host=localhost dbname=mydb user=myuser',
            'postgres'
        )
        assert success is False
        assert "port" in msg.lower()
        
        # Missing required field - dbname
        success, msg = validate_connection_string(
            'host=localhost port=5432 user=myuser',
            'postgres'
        )
        assert success is False
        assert "dbname" in msg.lower()
        
        # Invalid port number
        success, msg = validate_connection_string(
            'host=localhost port=70000 dbname=mydb user=myuser',
            'postgres'
        )
        assert success is False
        assert "Invalid port" in msg
    
    def test_unsupported_database_type(self):
        """Test unsupported database type"""
        success, msg = validate_connection_string(
            'some_connection_string',
            'mysql'
        )
        assert success is False
        assert "Unsupported database type" in msg
    
    def test_case_insensitive_database_type(self):
        """Test that database type is case insensitive"""
        # Test REDIS in uppercase
        success, msg = validate_connection_string('host:localhost,port:6379,db:0', 'REDIS')
        assert success is True
        
        # Test Postgres with mixed case
        success, msg = validate_connection_string(
            'host=localhost port=5432 dbname=mydb',
            'Postgres'
        )
        assert success is True
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        # Port at minimum boundary
        success, msg = validate_connection_string('host:localhost,port:1,db:0', 'redis')
        assert success is True
        
        # Port at maximum boundary
        success, msg = validate_connection_string('host:localhost,port:65535,db:0', 'redis')
        assert success is True
        
        # Port just below minimum
        success, msg = validate_connection_string('host:localhost,port:0,db:0', 'redis')
        assert success is False
        
        # Port just above maximum
        success, msg = validate_connection_string('host:localhost,port:65536,db:0', 'redis')
        assert success is False
        
        # Empty connection string
        success, msg = validate_connection_string('', 'redis')
        assert success is False
        
        # Whitespace handling
        success, msg = validate_connection_string('host: localhost , port: 6379 , db: 0', 'redis')
        assert success is True