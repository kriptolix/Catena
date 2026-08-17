# enums.py
from enum import Enum


class StatusEquipment(str, Enum):
    FUNCIONAL = "funcional"
    DEFEITUOSO = "defeituoso"
    DEVOLVIDO = "devolvido"


class HistoryType(str, Enum):
    CREATED = "created"
    UPDATED = "updated"
    STATUS_CHANGED = "status_changed"
    LOCATION_CHANGED = "location_changed"
    INVENTORY_COLLECTED = "inventory_collected"
    COMPONENT_CHANGED = "component_changed"    
    DEACTIVATED = "deactivated"
    REACTIVATED = "reactivated"
    DEFECT_REPORTED = "defect_reported"
    DEFECT_RESOLVED = "defect_resolved"
    ANNOTATION_ADDED = "annotation_added"  

class AuditAction(str, Enum): 
   
    LOGIN = "login" 
    LOGOUT = "logout" 
    LOGIN_FAILED = "login_failed" 
  
    USER_CREATED = "user_created" 
    USER_UPDATED = "user_updated" 
    USER_DEACTIVATED = "user_deactivated" 
    USER_REACTIVATED = "user_reactivated" 
    PASSWORD_CHANGED = "password_changed" 

    EQUIPMENT_CREATED = "equipment_created" 
    EQUIPMENT_UPDATED = "equipment_updated" 
    EQUIPMENT_DEACTIVATED = "equipment_deactivated" 
    EQUIPMENT_REACTIVATED = "equipment_reactivated" 
    EQUIPMENT_INVENTORIED = "equipment_inventoried" 

    SETTINGS_UPDATED = "settings_updated"