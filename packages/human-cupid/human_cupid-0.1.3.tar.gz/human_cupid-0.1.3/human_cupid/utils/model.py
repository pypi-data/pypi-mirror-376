from enum import Enum
from typing import get_args, get_origin
from pydantic import BaseModel, ValidationError, model_validator


class Model(BaseModel):
    @model_validator(mode="before")
    @classmethod
    def self_heal(cls, data):
        def heal_enum(enum_class, value):
            if isinstance(value, enum_class):
                return value
            
            if not isinstance(value, str):
                value = str(value)

            try:
                return enum_class(value)
            except ValueError:
                pass

            # Try case-insensitive match
            for enum_item in enum_class.__members__.values():
                if enum_item.value.lower() == value.lower():
                    return enum_item
            
            # Try to extract enum value from descriptions like "high - very confident"
            for enum_item in enum_class.__members__.values():
                if value.lower().startswith(enum_item.value.lower()):
                    return enum_item
            
            raise ValidationError(f"Value '{value}' is not a valid member of enum {enum_class.__name__}")

        def process_value(field_type, value):
            if get_origin(field_type) is list and get_args(field_type) == (str,):
                if isinstance(value, str):
                   return [value]
                return value
             
            if isinstance(value, dict) and hasattr(field_type, "model_fields"):
                return field_type.self_heal(value)
            
            if isinstance(field_type, type) and issubclass(field_type, Enum):
                return heal_enum(field_type, value)

            return value
        
        if isinstance(data, dict):
            for field_name, value in list(data.items()):
                field = cls.model_fields.get(field_name)
                if field is None:
                    continue
                data[field_name] = process_value(field.annotation, value)

        return data
