from pydantic import BaseModel
from typing import Optional
from enum import Enum
 
 
class RiskLevel(str, Enum):
    normal = "normal"
    warning = "warning"
    critical = "critical"
 
 
class VitalsData(BaseModel):
    heart_rate: Optional[float] = None          # bpm
    spo2: Optional[float] = None                # % oxygen saturation
    temperature: Optional[float] = None         # Celsius
    systolic_bp: Optional[float] = None         # mmHg
    diastolic_bp: Optional[float] = None        # mmHg
    glucose: Optional[float] = None             # mg/dL
    timestamp: Optional[str] = None
 
 
class VitalsRisk(BaseModel):
    overall_risk: RiskLevel = RiskLevel.normal
    heart_rate_risk: RiskLevel = RiskLevel.normal
    spo2_risk: RiskLevel = RiskLevel.normal
    temperature_risk: RiskLevel = RiskLevel.normal
    bp_risk: RiskLevel = RiskLevel.normal
    glucose_risk: RiskLevel = RiskLevel.normal
    flags: list[str] = []                        # human-readable risk messages
 
 
class IoMTReading(BaseModel):
    vitals: VitalsData
    risk: VitalsRisk
    summary: str                                 # e.g. "SpO2 critically low at 88%"
    recommendation: str                          # e.g. "Seek immediate medical attention"
 