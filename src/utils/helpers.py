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
        
        # Remover duplicados manteniendo orden
        return list(dict.fromkeys(keywords))
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
        """Trunca texto a una longitud máxima"""
        if not text or len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix

class DataValidator:
    """Utilities for data validation"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Valida formato de email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Valida formato de teléfono"""
        pattern = r'^\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$'
        return bool(re.match(pattern, phone))
    
    @staticmethod
    def validate_zipcode(zipcode: str) -> bool:
        """Valida código postal estadounidense"""
        pattern = r'^\d{5}(-\d{4})?$'
        return bool(re.match(pattern, zipcode))
    
    @staticmethod
    def validate_price(price: Union[str, int, float]) -> bool:
        """Valida precio"""
        try:
            price_float = float(price)
            return price_float >= 0
        except (ValueError, TypeError):
            return False

class IDGenerator:
    """Utilidades para generación de IDs"""
    
    @staticmethod
    def generate_uuid() -> str:
        """Genera un UUID único"""
        return str(uuid.uuid4())
    
    @staticmethod
    def generate_short_id(length: int = 8) -> str:
        """Genera un ID corto"""
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
    """Utilidades para construir respuestas"""
    
    @staticmethod
    def success_response(data: Any = None, message: str = "Success") -> Dict[str, Any]:
        """Construye una respuesta de éxito"""
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
        """Construye una respuesta de error"""
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
        """Construye una respuesta paginada"""
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
    """Utilidades para configuración"""
    
    @staticmethod
    def get_env_var(key: str, default: Any = None, required: bool = False) -> Any:
        """Obtiene una variable de entorno con validación"""
        value = os.getenv(key, default)
        
        if required and value is None:
            raise ValueError(f"Variable de entorno requerida no encontrada: {key}")
        
        return value
    
    @staticmethod
    def get_bool_env(key: str, default: bool = False) -> bool:
        """Obtiene una variable de entorno como booleano"""
        value = os.getenv(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')
    
    @staticmethod
    def get_int_env(key: str, default: int = 0) -> int:
        """Obtiene una variable de entorno como entero"""
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            logger.warning(f"Variable de entorno {key} no es un entero válido, usando default: {default}")
            return default

class LoggerHelper:
    """Utilidades para logging"""
    
    @staticmethod
    def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
        """Configura un logger"""
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
        """Log de llamadas a funciones"""
        logger.debug(f"Función {func_name} llamada con args: {args}")
        if result is not None:
            logger.debug(f"Función {func_name} retornó: {result}")

# Funciones de utilidad específicas para el chatbot
def clean_text(text: str) -> str:
    """Limpia y normaliza texto"""
    return TextProcessor.clean_text(text)

def format_price(price: float) -> str:
    """Formatea un precio de manera legible"""
    if price is None:
        return "N/A"
    return f"${price:,.0f}"

def format_property_summary(property_data: Dict[str, Any]) -> str:
    """Crea un resumen legible de una propiedad"""
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
        summary += f"\n{property_type} | {bedrooms} hab, {bathrooms} baños"
        
        if living_area and living_area != 'N/A':
            summary += f" | {living_area:,.0f} sqft"
        
        return summary
        
    except Exception as e:
        logger.error(f"Error formateando resumen de propiedad: {e}")
        return "Información no disponible"

def extract_location_keywords(text: str) -> List[str]:
    """Extrae palabras clave relacionadas con ubicación"""
    location_keywords = []
    
    # Patrones comunes de ubicación
    patterns = [
        r'\b[A-Z][a-z]+\s+City\b',  # "Crescent City"
        r'\b[A-Z]{2}\b',  # Estados como "CA", "IL"
        r'\b\d{5}\b',  # Códigos postales
        r'\b[A-Z][a-z]+\b'  # Nombres de ciudades
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        location_keywords.extend(matches)
    
    return list(set(location_keywords))

def validate_search_query(query: str) -> bool:
    """Valida si una consulta de búsqueda es válida"""
    if not query or len(query.strip()) < 2:
        return False
    
    # Verificar que no sea solo caracteres especiales
    if not re.search(r'[a-zA-Z0-9]', query):
        return False
    
    return True

def create_search_filters(search_intent: Dict[str, Any]) -> Dict[str, Any]:
    """Crea filtros de búsqueda basados en la intención extraída"""
    filters = {}
    
    # Filtro por tipo de propiedad
    if search_intent.get('property_type'):
        filters['property_type'] = search_intent['property_type']
    
    # Filtro por ciudad
    if search_intent.get('location'):
        filters['city'] = search_intent['location']
    
    # Filtro por número de habitaciones
    if search_intent.get('bedrooms'):
        filters['bedrooms'] = search_intent['bedrooms']
    
    # Filtro por número de baños
    if search_intent.get('bathrooms'):
        filters['bathrooms'] = search_intent['bathrooms']
    
    return filters

# Instancias globales para uso fácil
text_processor = TextProcessor()
data_validator = DataValidator()
id_generator = IDGenerator()
file_handler = FileHandler()
response_builder = ResponseBuilder()
config_helper = ConfigHelper()
logger_helper = LoggerHelper()