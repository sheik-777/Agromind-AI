"""
Smart Irrigation Decision Engine.

Implements sensor-driven, explainable irrigation decisions based on:
- Soil moisture
- Crop type and growth stage
- Weather forecast (rain probability, temperature, humidity)
- Soil properties (pH, soil type)
- Recent irrigation history
- Field capacity and wilting point estimates
"""
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
from backend.services.weather_service import get_weather_for_field
from backend.models.models import SensorReading, Field, Device, IrrigationEvent
from backend.config.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import desc
import logging

logger = logging.getLogger(__name__)


class IrrigationDecision(str, Enum):
    IRRIGATE = "IRRIGATE"
    WAIT = "WAIT"
    MONITOR = "MONITOR"
    SKIP = "SKIP"


@dataclass
class IrrigationDecisionResult:
    decision: IrrigationDecision
    confidence: float  # 0.0 - 1.0
    reason: str
    important_factors: List[str]
    next_evaluation: datetime
    recommended_duration_minutes: Optional[int] = None
    recommended_volume_mm: Optional[float] = None
    risk_factors: List[str] = None
    expected_outcome: str = ""

    def __post_init__(self):
        if self.risk_factors is None:
            self.risk_factors = []


@dataclass
class FieldContext:
    """Aggregated field context for irrigation decision."""
    field_id: str
    crop: Optional[str]
    growth_stage: Optional[str]
    soil_type: Optional[str]
    field_capacity_pct: Optional[float]  # % at field capacity
    wilting_point_pct: Optional[float]  # % at wilting point
    current_moisture: float
    soil_ph: Optional[float]
    soil_type: Optional[str]
    last_irrigation: Optional[datetime]
    last_rainfall: Optional[datetime]
    rain_last_24h_mm: float
    device_online: bool
    last_telemetry: datetime
    available: bool = True  # Whether field has valid sensor data


class IrrigationEngine:
    """
    Smart irrigation decision engine.
    
    Decision logic:
    1. Check if soil moisture is below management allowed depletion (MAD)
    2. Check weather forecast for rain probability
    3. Check crop growth stage water requirements
    4. Check recent irrigation history
    5. Consider soil type and field capacity
    6. Generate decision with confidence and explanation
    """
    
    # Crop-specific parameters
    CROP_PARAMS = {
        "wheat": {
            "root_depth_cm": 90,
            "kc_ini": 0.3, "kc_mid": 1.15, "kc_end": 0.25,
            "mad_pct": 0.50,  # Management Allowed Depletion
            "growth_stages": {
                "initial": {"days": 20, "kc": 0.3},
                "development": {"days": 40, "kc": 0.7},
                "mid": {"days": 50, "kc": 1.15},
                "late": {"days": 30, "kc": 0.25}
            }
        },
        "rice": {
            "root_depth_cm": 45,
            "kc_ini": 1.05, "kc_mid": 1.2, "kc_end": 0.9,
            "mad_pct": 0.20,  # Rice needs more water
            "growth_stages": {
                "initial": {"days": 30, "kc": 1.05},
                "development": {"days": 30, "kc": 1.1},
                "mid": {"days": 60, "kc": 1.2},
                "late": {"days": 30, "kc": 0.9}
            }
        },
        "rice_paddy": {
            "root_depth_cm": 30,
            "kc_ini": 1.05, "kc_mid": 1.2, "kc_end": 0.9,
            "mad_pct": 0.10,  # Keep flooded
            "growth_stages": {
                "initial": {"days": 30, "kc": 1.05},
                "development": {"days": 30, "kc": 1.1},
                "mid": {"days": 60, "kc": 1.2},
                "late": {"days": 30, "kc": 0.9}
            }
        },
        "tomato": {
            "root_depth_cm": 60,
            "kc_ini": 0.6, "kc_mid": 1.15, "kc_end": 0.7,
            "mad_pct": 0.40,
            "growth_stages": {
                "initial": {"days": 30, "kc": 0.6},
                "development": {"days": 40, "kc": 0.9},
                "mid": {"days": 50, "kc": 1.15},
                "late": {"days": 30, "kc": 0.7}
            }
        },
        "cotton": {
            "root_depth_cm": 120,
            "kc_ini": 0.35, "kc_mid": 1.15, "kc_end": 0.6,
            "mad_pct": 0.50,
            "growth_stages": {
                "initial": {"days": 30, "kc": 0.35},
                "development": {"days": 50, "kc": 0.75},
                "mid": {"days": 55, "kc": 1.15},
                "late": {"days": 45, "kc": 0.6}
            }
        },
        "cotton_crop": {
            "root_depth_cm": 120,
            "kc_ini": 0.35, "kc_mid": 1.15, "kc_end": 0.6,
            "mad_pct": 0.50,
            "growth_stages": {
                "initial": {"days": 30, "kc": 0.35},
                "development": {"days": 50, "kc": 0.75},
                "mid": {"days": 55, "kc": 1.15},
                "late": {"days": 45, "kc": 0.6}
            }
        },
        "maize": {
            "root_depth_cm": 100,
            "kc_ini": 0.3, "kc_mid": 1.2, "kc_end": 0.35,
            "mad_pct": 0.50,
            "growth_stages": {
                "initial": {"days": 20, "kc": 0.3},
                "development": {"days": 35, "kc": 0.7},
                "mid": {"days": 40, "kc": 1.2},
                "late": {"days": 30, "kc": 0.35}
            }
        },
        "soybean": {
            "root_depth_cm": 60,
            "kc_ini": 0.4, "kc_mid": 1.15, "kc_end": 0.5,
            "mad_pct": 0.50,
            "growth_stages": {
                "initial": {"days": 20, "kc": 0.4},
                "development": {"days": 40, "kc": 0.8},
                "mid": {"days": 50, "kc": 1.15},
                "late": {"days": 30, "kc": 0.5}
            }
        },
        "cotton_crop": {
            "root_depth_cm": 100,
            "kc_ini": 0.35, "kc_mid": 1.15, "kc_end": 0.6,
            "mad_pct": 0.50,
            "growth_stages": {
                "initial": {"days": 30, "kc": 0.35},
                "development": {"days": 50, "kc": 0.75},
                "mid": {"days": 55, "kc": 1.15},
                "late": {"days": 45, "kc": 0.6}
            }
        },
        "sugarcane": {
            "root_depth_cm": 150,
            "kc_ini": 0.4, "kc_mid": 1.25, "kc_end": 0.75,
            "mad_pct": 0.40,
            "growth_stages": {
                "initial": {"days": 30, "kc": 0.4},
                "development": {"days": 60, "kc": 1.0},
                "mid": {"days": 120, "kc": 1.25},
                "late": {"days": 40, "kc": 0.75}
            }
        },
        "potato": {
            "root_depth_cm": 45,
            "kc_ini": 0.5, "kc_mid": 1.15, "kc_end": 0.75,
            "mad_pct": 0.35,
            "growth_stages": {
                "initial": {"days": 25, "kc": 0.5},
                "development": {"days": 30, "kc": 0.8},
                "mid": {"days": 45, "kc": 1.15},
                "late": {"days": 30, "kc": 0.75}
            }
        },
        "onion": {
            "root_depth_cm": 30,
            "kc_ini": 0.7, "kc_mid": 1.05, "kc_end": 0.75,
            "mad_pct": 0.30,
            "growth_stages": {
                "initial": {"days": 20, "kc": 0.7},
                "development": {"days": 30, "kc": 0.9},
                "mid": {"days": 40, "kc": 1.05},
                "late": {"days": 25, "kc": 0.75}
            }
        },
        "chickpea": {
            "root_depth_cm": 60,
            "kc_ini": 0.4, "kc_mid": 1.0, "kc_end": 0.35,
            "mad_pct": 0.50,
            "growth_stages": {
                "initial": {"days": 25, "kc": 0.4},
                "development": {"days": 40, "kc": 0.8},
                "mid": {"days": 45, "kc": 1.0},
                "late": {"days": 30, "kc": 0.35}
            }
        },
        "groundnut": {
            "root_depth_cm": 50,
            "kc_ini": 0.4, "kc_mid": 1.15, "kc_end": 0.6,
            "mad_pct": 0.50,
            "growth_stages": {
                "initial": {"days": 25, "kc": 0.4},
                "development": {"days": 40, "kc": 0.8},
                "mid": {"days": 50, "kc": 1.15},
                "late": {"days": 30, "kc": 0.6}
            }
        }
    }
    
    # Soil type adjustments
    SOIL_ADJUSTMENTS = {
        "sandy": {"fc_pct": 15, "wp_pct": 5, "mad_factor": 0.8},
        "sandy_loam": {"fc_pct": 20, "wp_pct": 8, "mad_factor": 0.9},
        "loamy": {"fc_pct": 25, "wp_pct": 10, "mad_factor": 1.0},
        "clay_loam": {"fc_pct": 30, "wp_pct": 15, "mad_factor": 1.1},
        "clay": {"fc_pct": 35, "wp_pct": 20, "mad_factor": 1.2},
        "clay_loam": {"fc_pct": 30, "wp_pct": 14, "mad_factor": 1.1},
        "silty": {"fc_pct": 28, "wp_pct": 12, "mad_factor": 1.0},
        "red_laterite": {"fc_pct": 25, "wp_pct": 12, "mad_factor": 1.0},
        "black": {"fc_pct": 35, "wp_pct": 18, "mad_factor": 1.1},
        "red_laterite": {"fc_pct": 25, "wp_pct": 12, "mad_factor": 1.0},
        "rocky/dry": {"fc_pct": 15, "wp_pct": 5, "mad_factor": 0.8},
        "rock/bark": {"fc_pct": 10, "wp_pct": 3, "mad_factor": 0.7},
        "bark/peat": {"fc_pct": 40, "wp_pct": 20, "mad_factor": 1.2},
        "peaty": {"fc_pct": 50, "wp_pct": 25, "mad_factor": 1.3},
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_crop_params(self, crop: Optional[str]) -> Dict[str, Any]:
        """Get crop parameters, with defaults for unknown crops."""
        if crop and crop.lower() in self.CROP_PARAMS:
            return self.CROP_PARAMS[crop.lower()]
        # Default parameters for unknown crops
        return {
            "root_depth_cm": 60,
            "kc_ini": 0.5, "kc_mid": 1.0, "kc_end": 0.6,
            "mad_pct": 0.50,
            "growth_stages": {
                "initial": {"days": 30, "kc": 0.5},
                "development": {"days": 40, "kc": 0.8},
                "mid": {"days": 50, "kc": 1.0},
                "late": {"days": 30, "kc": 0.6}
            }
        }
    
    def get_soil_adjustment(self, soil_type: Optional[str]) -> Dict[str, float]:
        """Get soil adjustments for field capacity, wilting point, MAD factor."""
        if soil_type and soil_type.lower() in self.SOIL_ADJUSTMENTS:
            return self.SOIL_ADJUSTMENTS[soil_type.lower()]
        return {"fc_pct": 25, "wp_pct": 10, "mad_factor": 1.0}
    
    def calculate_mad_threshold(self, crop: Optional[str], soil_type: Optional[str]) -> float:
        """Calculate Management Allowed Depletion (MAD) threshold as % of field capacity."""
        crop_params = self.get_crop_params(None)  # Default
        if crop:
            crop_params = self.get_crop_params(crop)
        
        soil_adj = self.get_soil_adjustment(None)
        
        base_mad = crop_params.get("mad_pct", 0.50)
        mad_factor = soil_adj.get("mad_factor", 1.0)
        
        return base_mad * mad_factor
    
    def estimate_field_capacity(self, soil_type: Optional[str]) -> float:
        """Estimate field capacity (%) based on soil type."""
        return self.get_soil_adjustment(soil_type).get("fc_pct", 25)
    
    def estimate_wilting_point(self, soil_type: Optional[str]) -> float:
        """Estimate wilting point (%) based on soil type."""
        return self.get_soil_adjustment(soil_type).get("wp_pct", 10)
    
    def get_crop_kc(self, crop: Optional[str], growth_stage: Optional[str]) -> float:
        """Get crop coefficient (Kc) for given crop and growth stage."""
        crop_params = self.get_crop_params(crop)
        stages = crop_params.get("growth_stages", {})
        
        if growth_stage and growth_stage.lower() in stages:
            return stages[growth_stage.lower()]["kc"]
        
        # Default to mid-season Kc if stage unknown
        return crop_params.get("kc_mid", 1.0)
    
    def get_field_context(self, field_id: str, db: Session) -> Optional[FieldContext]:
        """Gather all context needed for irrigation decision."""
        from backend.models.models import Field, Device, SensorReading
        from sqlalchemy import desc
        from datetime import datetime, timedelta
        
        field = db.query(Field).filter(Field.id == field_id).first()
        if not field:
            return None
        
        # Get latest sensor reading
        reading = db.query(SensorReading).filter(
            SensorReading.field_id == field_id
        ).order_by(desc(SensorReading.recorded_at)).first()
        
        # Get device info
        device = db.query(Device).filter(Device.field_id == field.id).first()
        
        # Get last irrigation event
        last_irrigation = db.query(IrrigationEvent).filter(
            IrrigationEvent.field_id == field_id
        ).order_by(desc(IrrigationEvent.started_at)).first()
        
        # Calculate rain in last 24h
        since_24h = datetime.utcnow() - timedelta(hours=24)
        # Would need rainfall data - placeholder for now
        rain_24h = 0.0
        
        current_moisture = reading.soil_moisture if reading else 0
        soil_ph = reading.soil_ph if reading else None
        soil_temp = reading.soil_temp if reading else None
        
        return FieldContext(
            field_id=field.id,
            crop=field.crop,
            growth_stage=None,  # Would need crop calendar
            soil_type=None,  # Would need from field profile
            field_capacity_pct=None,
            wilting_point_pct=None,
            current_moisture=current_moisture,
            soil_ph=soil_ph,
            last_irrigation=last_irrigation.started_at if last_irrigation else None,
            last_rainfall=None,
            rain_last_24h_mm=0.0,
            device_online=device.online if device else False,
            last_telemetry=reading.recorded_at if reading else datetime.utcnow()
        )
    
    async def make_decision(self, field_id: str, db: Session) -> IrrigationDecisionResult:
        """
        Main decision function - returns irrigation decision with reasoning.
        """
        ctx = self.get_field_context(field_id, db)
        if not ctx or not ctx.available:
            return IrrigationDecisionResult(
                decision=IrrigationDecision.MONITOR,
                confidence=0.0,
                reason="No field data available",
                important_factors=["No sensor data available"],
                next_evaluation=datetime.utcnow() + timedelta(hours=1)
            )
        
        # Get crop parameters
        crop_params = self.get_crop_params(ctx.crop)
        soil_adj = self.get_soil_adjustment(ctx.soil_type)
        
        # Estimate field capacity and wilting point
        fc = ctx.field_capacity_pct or self.estimate_field_capacity(ctx.soil_type)
        wp = ctx.wilting_point_pct or self.estimate_wilting_point(ctx.soil_type)
        
        # Calculate MAD threshold
        mad_pct = crop_params.get("mad_pct", 0.5) * soil_adj.get("mad_factor", 1.0)
        mad_threshold = wp + (fc - wp) * mad_pct
        
        # Current soil moisture
        current_moisture = ctx.current_moisture
        
        # Get weather forecast
        weather = await get_weather_for_field(
            latitude=20.5937,  # Would come from field location
            longitude=78.9629,
            soil_moisture=ctx.current_moisture
        )
        
        # Decision factors
        factors = []
        risk_factors = []
        decision = IrrigationDecision.MONITOR
        confidence = 0.5
        reason = ""
        
        # 1. Check soil moisture against MAD threshold
        available_water_pct = ((current_moisture - wp) / (fc - wp)) * 100 if fc > wp else 0
        mad_threshold = wp + (fc - wp) * crop_params.get("mad_pct", 0.5)
        
        if current_moisture <= mad_threshold:
            decision = IrrigationDecision.IRRIGATE
            confidence = 0.9
            factors.append(f"Soil moisture ({current_moisture:.0f}%) below MAD threshold ({mad_threshold:.0f}%)")
            reason = f"Soil moisture ({current_moisture:.0f}%) has dropped below the Management Allowed Depletion threshold ({mad_threshold:.0f}%). Irrigation recommended."
        elif current_moisture <= wp + (fc - wp) * 0.7:
            decision = IrrigationDecision.MONITOR
            confidence = 0.7
            factors.append(f"Soil moisture ({current_moisture:.0f}%) approaching MAD threshold")
            reason = f"Soil moisture ({current_moisture:.0f}%) is approaching the depletion threshold. Monitor closely."
        else:
            decision = IrrigationDecision.WAIT
            confidence = 0.8
            factors.append(f"Soil moisture ({current_moisture:.0f}%) is adequate")
            reason = f"Soil moisture ({current_moisture:.0f}%) is within optimal range."
        
        # 2. Check weather forecast for rain
        if weather:
            daily_rain_probs = weather.get("daily", {}).get("precipitation_probability_max", [])
            max_rain_prob = max(daily_rain_probs) if daily_rain_probs else 0
            if max_rain_prob > 70:
                if decision == IrrigationDecision.IRRIGATE:
                    decision = IrrigationDecision.WAIT
                    confidence = 0.8
                    factors.append(f"High rain probability ({max_rain_prob}%) forecast")
                    reason = f"High rain probability ({max_rain_prob}%) expected. Delay irrigation and reassess after rainfall."
                elif decision == IrrigationDecision.MONITOR:
                    decision = IrrigationDecision.WAIT
                    confidence = 0.7
                    factors.append(f"Rain likely ({max_rain_prob}%) - delaying decision")
                    reason = f"Rain probability is {max_rain_prob}%. Wait for forecast to clarify."
                else:
                    factors.append(f"Rain probability: {max_rain_prob}%")
            
            # Check rain in next 24h
            next_day_rain = daily_rain_probs[0] if daily_rain_probs else 0
            if next_day_rain > 50:
                factors.append(f"Rain likely tomorrow ({next_day_rain}%)")
                if decision == IrrigationDecision.IRRIGATE:
                    decision = IrrigationDecision.WAIT
                    reason = "Rain expected tomorrow - delaying irrigation"
        
        # 3. Check recent irrigation
        if ctx.last_irrigation:
            hours_since = (datetime.utcnow() - ctx.last_irrigation).total_seconds() / 3600
            if hours_since < 12:
                decision = IrrigationDecision.WAIT
                confidence = max(confidence, 0.9)
                factors.append(f"Recent irrigation {hours_since:.1f}h ago")
                reason = f"Field was irrigated {hours_since:.1f} hours ago. Wait before re-irrigating."
        
        # 4. Check device status
        if not ctx.device_online:
            risk_factors.append("Device offline - telemetry may be stale")
            confidence *= 0.7
        
        # Determine next evaluation time
        if decision == IrrigationDecision.IRRIGATE:
            next_eval = datetime.utcnow() + timedelta(hours=4)
        elif decision == IrrigationDecision.MONITOR:
            next_eval = datetime.utcnow() + timedelta(hours=2)
        elif decision == IrrigationDecision.WAIT:
            next_eval = datetime.utcnow() + timedelta(hours=6)
        else:
            next_eval = datetime.utcnow() + timedelta(hours=12)
        
        # Calculate recommended duration/volume (simplified)
        recommended_duration = None
        recommended_volume = None
        if decision == IrrigationDecision.IRRIGATE:
            # Simple estimate: refill to 80% of FC
            target_moisture = wp + (fc - wp) * 0.8
            deficit = target_moisture - current_moisture
            if deficit > 0:
                # Rough estimate: 1% moisture = ~10mm water for 1m root zone
                # Adjust for root depth
                root_depth = 60  # cm, default
                recommended_volume_mm = deficit * 10 * (crop_params.get("root_depth_cm", 60) / 100)
                recommended_volume = round(recommended_volume_mm, 1)
                recommended_duration = max(30, int(recommended_volume_mm * 2))  # Rough: 2 min per mm
        
        return IrrigationDecisionResult(
            decision=decision,
            confidence=round(confidence, 2),
            reason=reason,
            important_factors=factors,
            next_evaluation=next_eval,
            recommended_duration_minutes=recommended_duration,
            recommended_volume_mm=recommended_volume,
            risk_factors=risk_factors,
            expected_outcome=f"Target soil moisture: {target_moisture:.0f}%" if decision == IrrigationDecision.IRRIGATE else "Monitor soil moisture trend"
        )


# Singleton
_irrigation_engine = None

def get_irrigation_engine(db: Session) -> IrrigationEngine:
    global _irrigation_engine
    if _irrigation_engine is None:
        _irrigation_engine = IrrigationEngine(db)
    return _irrigation_engine


if __name__ == "__main__":
    # Quick test
    engine = IrrigationEngine(None)
    print("Crop params for tomato:", engine.get_crop_params("tomato"))
    print("Crop params for unknown:", engine.get_crop_params("unknown"))
    print("Soil adjustment for clay:", engine.get_soil_adjustment("clay"))
    print("MAD threshold for tomato on clay:", 
          engine.calculate_mad_threshold("tomato", "clay"))
    print("Field capacity for loam:", engine.estimate_field_capacity("loam"))
    print("Kc for tomato mid-season:", engine.get_crop_kc("tomato", "mid"))