"""
Common utilities and helpers
"""
import logging
import os
import json
import re
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import hashlib
import uuid

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

class TextProcessor:
    """Text processing utilities"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Cleans and normalizes text"""
        if not text:
            return ""
        
        # Remove extra spaces and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove problematic special characters
        text = re.sub(r'[^\w\s\-.,!?@#$%&*()+=:;"\'<>/\\]', '', text)
        
        return text
    
    @staticmethod
    def extract_keywords(text: str, min_length: int = 3) -> List[str]:
        """Extracts keywords from text"""
        if not text:
            return []
        
        # Clean text
        clean_text = TextProcessor.clean_text(text)
        
        # Split into words and filter
        words = clean_text.lower().split()
        keywords = [
            word for word in words 
            if len(word) >= min_length and word.isalpha()
        ]
        
        # Remove duplicates while maintaining order
        return list(dict.fromkeys(keywords))
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
        """Truncates text to a maximum length"""
        if not text or len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix

class DataValidator:
    """Utilities for data validation"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validates email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validates phone format"""
        pattern = r'^\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$'
        return bool(re.match(pattern, phone))
    
    @staticmethod
    def validate_zipcode(zipcode: str) -> bool:
        """Validates US zipcode"""
        pattern = r'^\d{5}(-\d{4})?$'
        return bool(re.match(pattern, zipcode))
    
    @staticmethod
    def validate_price(price: Union[str, int, float]) -> bool:
        """Validates price"""
        try:
            price_float = float(price)
            return price_float >= 0
        except (ValueError, TypeError):
            return False

class IDGenerator:
    """Utilities for ID generation"""
    
    @staticmethod
    def generate_uuid() -> str:
        """Generates a unique UUID"""
        return str(uuid.uuid4())
    
    @staticmethod
    def generate_short_id(length: int = 8) -> str:
        """Generates a short ID"""
        return hashlib.md5(str(uuid.uuid4()).encode()).hexdigest()[:length]
    
    @staticmethod
    def generate_conversation_id() -> str:
        """Generates a conversation ID"""
        return f"conv_{IDGenerator.generate_short_id(12)}"

class FileHandler:
    """Utilities for file handling"""
    
    @staticmethod
    def ensure_directory(path: str) -> bool:
        """Ensures that a directory exists"""
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Error creating directory {path}: {e}")
            return False
    
    @staticmethod
    def read_json_file(file_path: str) -> Optional[Dict[str, Any]]:
        """Reads a JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading JSON file {file_path}: {e}")
            return None
    
    @staticmethod
    def write_json_file(file_path: str, data: Dict[str, Any]) -> bool:
        """Writes a JSON file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error writing JSON file {file_path}: {e}")
            return False

class ResponseBuilder:
    """Utilities for building responses"""
    
    @staticmethod
    def success_response(data: Any = None, message: str = "Success") -> Dict[str, Any]:
        """Builds a success response"""
        response = {
            "success": True,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        if data is not None:
            response["data"] = data
        return response
    
    @staticmethod
    def error_response(message: str, error_code: str = "ERROR", details: Any = None) -> Dict[str, Any]:
        """Builds an error response"""
        response = {
            "success": False,
            "error": {
                "code": error_code,
                "message": message,
                "timestamp": datetime.now().isoformat()
            }
        }
        if details is not None:
            response["error"]["details"] = details
        return response
    
    @staticmethod
    def paginated_response(
        data: List[Any], 
        total: int, 
        page: int = 1, 
        per_page: int = 10
    ) -> Dict[str, Any]:
        """Builds a paginated response"""
        total_pages = (total + per_page - 1) // per_page
        
        return {
            "success": True,
            "data": data,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            },
            "timestamp": datetime.now().isoformat()
        }

class ConfigHelper:
    """Utilities for configuration"""
    
    @staticmethod
    def get_env_var(key: str, default: Any = None, required: bool = False) -> Any:
        """Gets an environment variable with validation"""
        value = os.getenv(key, default)
        
        if required and value is None:
            raise ValueError(f"Required environment variable not found: {key}")
        
        return value
    
    @staticmethod
    def get_bool_env(key: str, default: bool = False) -> bool:
        """Gets an environment variable as boolean"""
        value = os.getenv(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')
    
    @staticmethod
    def get_int_env(key: str, default: int = 0) -> int:
        """Gets an environment variable as integer"""
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            logger.warning(f"Environment variable {key} is not a valid integer, using default: {default}")
            return default

class LoggerHelper:
    """Utilities for logging"""
    
    @staticmethod
    def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
        """Configures a logger"""
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    @staticmethod
    def log_function_call(func_name: str, args: Dict[str, Any] = None, result: Any = None):
        """Logs function calls"""
        logger.debug(f"Function {func_name} called with args: {args}")
        if result is not None:
            logger.debug(f"Function {func_name} returned: {result}")

# Chatbot-specific utility functions
def clean_text(text: str) -> str:
    """Cleans and normalizes text"""
    return TextProcessor.clean_text(text)

def format_price(price: float) -> str:
    """Formats a price in a readable way"""
    if price is None:
        return "N/A"
    return f"${price:,.0f}"

def format_property_summary(property_data: Dict[str, Any]) -> str:
    """Creates a readable property summary"""
    try:
        address = property_data.get('address', 'N/A')
        city = property_data.get('city', 'N/A')
        state = property_data.get('state', 'N/A')
        price = format_price(property_data.get('price'))
        bedrooms = property_data.get('bedrooms', 'N/A')
        bathrooms = property_data.get('bathrooms', 'N/A')
        living_area = property_data.get('living_area', 'N/A')
        property_type = property_data.get('property_type', 'N/A')
        
        summary = f"{address}, {city}, {state} - {price}"
        summary += f"\n{property_type} | {bedrooms} bed, {bathrooms} bath"
        
        if living_area and living_area != 'N/A':
            summary += f" | {living_area:,.0f} sqft"
        
        return summary
        
    except Exception as e:
        logger.error(f"Error formatting property summary: {e}")
        return "Information not available"

def extract_location_keywords(text: str) -> List[str]:
    """Extracts location-related keywords"""
    location_keywords = []
    
    # Common location patterns
    patterns = [
        r'\b[A-Z][a-z]+\s+City\b',  # "Crescent City"
        r'\b[A-Z]{2}\b',  # States like "CA", "IL"
        r'\b\d{5}\b',  # Zipcodes
        r'\b[A-Z][a-z]+\b'  # City names
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        location_keywords.extend(matches)
    
    return list(set(location_keywords))

def validate_search_query(query: str) -> bool:
    """Validates if a search query is valid"""
    if not query or len(query.strip()) < 2:
        return False
    
    # Verify it's not only special characters
    if not re.search(r'[a-zA-Z0-9]', query):
        return False
    
    return True

def create_search_filters(search_intent: Dict[str, Any]) -> Dict[str, Any]:
    """Creates search filters based on extracted intent"""
    filters = {}
    
    # Filter by property type
    if search_intent.get('property_type'):
        filters['property_type'] = search_intent['property_type']
    
    # Filter by city
    if search_intent.get('location'):
        filters['city'] = search_intent['location']
    
    # Filter by number of bedrooms
    if search_intent.get('bedrooms'):
        filters['bedrooms'] = search_intent['bedrooms']
    
    # Filter by number of bathrooms
    if search_intent.get('bathrooms'):
        filters['bathrooms'] = search_intent['bathrooms']
    
    return filters

# Global instances for easy use
text_processor = TextProcessor()
data_validator = DataValidator()
id_generator = IDGenerator()
file_handler = FileHandler()
response_builder = ResponseBuilder()
config_helper = ConfigHelper()
logger_helper = LoggerHelper()