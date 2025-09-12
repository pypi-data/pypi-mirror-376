import duckdb
import pandas as pd
import random
import string
import requests
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Type, Union
from faker import Faker
from dataclasses import dataclass, field
import uuid
import json
from enum import Enum

# Import the Pydantic models
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from enum import Enum

# Import litellm for question generation
import litellm
from litellm import completion

# Training-related Pydantic models
class TrainingQuestion(BaseModel):
    question: str

class CountAnswer(BaseModel):
    count: int

class MostCommonAnswer(BaseModel):
    item: str

class PatientStatsAnswer(BaseModel):
    average_age: float
    total_patients: int
    gender_distribution: Dict[str, int]

class TrainingExample(BaseModel):
    question: str
    answer: Union[CountAnswer, MostCommonAnswer, PatientStatsAnswer]
    plugin_name: str

# Medical data Pydantic models
class ConditionStatusEnumT(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    RESOLVED = "resolved"
    REMISSION = "remission"
    RECURRENCE = "recurrence"

class ConditionT(BaseModel):
    id: str
    name: str
    description: str
    status: ConditionStatusEnumT
    date: Optional[datetime]
    origin_ids: List[str]
    recorder_name: str

class MedicationStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    DISCONTINUED = "discontinued"

class MedicationHistoryT(BaseModel):
    id: str
    name: str
    rxcode: str
    reason: str
    note: str
    status: MedicationStatus
    period_start: Optional[datetime]
    period_end: Optional[datetime]
    dosage_and_route_instructions: str
    requester_name: str

class ObservationType(str, Enum):
    VITAL = "vital-signs"
    LAB = "laboratory"
    SOCIAL_HISTORY = "social-history"

class ObservationStatus(str, Enum):
    REGISTERED = "registered"
    PRELIMINARY = "preliminary"
    FINAL = "final"
    AMENDED = "amended"
    CORRECTED = "corrected"

class VitalSignT(BaseModel):
    id: str
    name: str
    value: float
    unit: str
    date: datetime
    status: ObservationStatus
    reference_range_high: Optional[float] = None
    reference_range_low: Optional[float] = None
    reference_range_unit: Optional[str] = None
    notes: Optional[str] = None

class LabT(BaseModel):
    id: str
    name: str
    value: str
    date: datetime
    status: ObservationStatus
    notes: Optional[str] = None
    reference_range_high: Optional[float] = None
    reference_range_low: Optional[float] = None
    reference_range_unit: Optional[str] = None

class SocialHistoryT(BaseModel):
    id: str
    name: str
    value: str
    date: datetime
    status: ObservationStatus
    notes: Optional[str] = None

class ProcedureStatusEnum(Enum):
    COMPLETED = "completed"
    IN_PROGRESS = "in-progress"
    STOPPED = "stopped"
    CANCELLED = "cancelled"

class ProcedureT(BaseModel):
    id: str
    name: str
    info: str
    status: ProcedureStatusEnum
    date: Optional[datetime]
    origin_ids: List[str]
    performer_names: str

@dataclass
class PluginGroundTruth:
    """Ground truth data specific to a plugin"""
    record_count: int
    most_common_value: Optional[str] = None
    unique_values: List[str] = field(default_factory=list)
    custom_metrics: Dict[str, Any] = field(default_factory=dict)

@dataclass
class GroundTruth:
    """Stores ground truth facts about the generated data for testing"""
    total_records: int
    plugin_ground_truths: Dict[str, PluginGroundTruth]
    schema_perturbations: Dict[str, List[str]]

def generate_fixed(instructions: str, response_model: Type[BaseModel]) -> Optional[BaseModel]:
    """
    Generate structured content using litellm with response format
    
    Args:
        instructions: Instructions for generating the content
        response_model: Pydantic model class to structure the response
        
    Returns:
        Instance of response_model or None if generation fails
    """
    try:
        response = completion(
            model="gpt-4o-mini",  # Use a compatible model
            messages=[
                {
                    "role": "system", 
                    "content": "You are a helpful assistant that generates natural, conversational questions for medical database training."
                },
                {
                    "role": "user", 
                    "content": instructions
                }
            ],
            response_format=response_model
        )
        
        content = response.choices[0].message.content
        if isinstance(content, str):
            return response_model.model_validate_json(content)
        elif isinstance(content, dict):
            return response_model.model_validate(content)
        else:
            return response_model.model_validate(content)
    except Exception as e:
        print(f"Error generating structured content: {e}")
        return None

class DatabasePlugin(ABC):
    """
    Abstract base class for database plugins.
    Each plugin handles one or more related tables.
    """
    
    def __init__(self, fake: Faker, use_apis: bool = True, seed: Optional[int] = None):
        self.fake = fake
        self.use_apis = use_apis
        self.seed = seed
        self._cache = {}
        
    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name identifier"""
        pass
    
    @property
    @abstractmethod
    def table_names(self) -> List[str]:
        """List of table names this plugin manages"""
        pass
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize any external data sources (APIs, etc.)"""
        pass
    
    @abstractmethod
    def generate_data(self, patients_df: pd.DataFrame, context: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
        """
        Generate fake data for this plugin's tables
        
        Args:
            patients_df: DataFrame of patient data for reference
            context: Dictionary containing data from other plugins
            
        Returns:
            Dictionary mapping table names to DataFrames
        """
        pass
    
    @abstractmethod
    def apply_perturbations(self, dataframes: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """
        Apply schema perturbations to the plugin's DataFrames
        
        Args:
            dataframes: Dictionary mapping table names to DataFrames
            
        Returns:
            Dictionary mapping table names to perturbed DataFrames
        """
        pass
    
    @abstractmethod
    def get_ground_truth(self, dataframes: Dict[str, pd.DataFrame]) -> PluginGroundTruth:
        """
        Calculate ground truth metrics for this plugin's data
        
        Args:
            dataframes: Dictionary mapping table names to DataFrames
            
        Returns:
            PluginGroundTruth object with metrics
        """
        pass
    
    @abstractmethod
    def get_training_example(self, ground_truth: PluginGroundTruth) -> Optional[TrainingExample]:
        """
        Generate a training example based on this plugin's ground truth data
        
        Args:
            ground_truth: PluginGroundTruth object with metrics for this plugin
            
        Returns:
            TrainingExample object or None if no example can be generated
        """
        pass
    
    def _apply_common_perturbations(self, df: pd.DataFrame, table_name: str) -> Tuple[pd.DataFrame, List[str]]:
        """Apply common schema perturbations that work for any table"""
        perturbations = []
        df_copy = df.copy()
        
        # 1. Column renaming (30% chance)
        if random.random() < 0.3:
            columns_to_rename = random.sample(list(df_copy.columns), random.randint(1, min(3, len(df_copy.columns))))
            rename_map = {}
            for col in columns_to_rename:
                new_name = col + "_" + random.choice(["v2", "new", "updated", "alt", "mod"])
                rename_map[col] = new_name
            df_copy = df_copy.rename(columns=rename_map)
            perturbations.append(f"Renamed columns: {rename_map}")
        
        # 2. Column dropping (20% chance)
        if random.random() < 0.2 and len(df_copy.columns) > 3:
            columns_to_drop = random.sample(list(df_copy.columns), random.randint(1, min(2, len(df_copy.columns)-2)))
            df_copy = df_copy.drop(columns=columns_to_drop)
            perturbations.append(f"Dropped columns: {columns_to_drop}")
        
        # 3. Add noise columns (25% chance)
        if random.random() < 0.25:
            num_noise_cols = random.randint(1, 3)
            for i in range(num_noise_cols):
                col_name = f"noise_{table_name}_{i}"
                df_copy[col_name] = [self.fake.word() for _ in range(len(df_copy))]
            perturbations.append(f"Added {num_noise_cols} noise columns")
        
        # 4. Data type perturbations (15% chance)
        if random.random() < 0.15:
            numeric_cols = df_copy.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                col_to_change = random.choice(numeric_cols)
                df_copy[col_to_change] = df_copy[col_to_change].astype(str)
                perturbations.append(f"Changed {col_to_change} from numeric to string")
        
        # 5. Add missing values (20% chance)
        if random.random() < 0.2:
            col_to_null = random.choice(list(df_copy.columns))
            null_indices = random.sample(range(len(df_copy)), random.randint(1, min(10, len(df_copy)//4)))
            df_copy.loc[null_indices, col_to_null] = None
            perturbations.append(f"Added nulls to {col_to_null}")
        
        return df_copy, perturbations

class PatientPlugin(DatabasePlugin):
    """Plugin for managing patient demographic data"""
    
    @property
    def name(self) -> str:
        return "patients"
    
    @property
    def table_names(self) -> List[str]:
        return ["patients"]
    
    def initialize(self) -> None:
        """No external APIs needed for patient data"""
        pass
    
    def generate_data(self, patients_df: pd.DataFrame, context: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
        """Generate patient demographic data"""
        # If patients_df is provided, use it; otherwise generate new
        if patients_df is not None and not patients_df.empty:
            return {"patients": patients_df}
        
        # Generate new patient data
        num_patients = context.get("num_patients", 100)
        patients = []
        for _ in range(num_patients):
            birth_date = self.fake.date_of_birth(minimum_age=18, maximum_age=90)
            age = (datetime.now().date() - birth_date).days // 365
            
            patients.append({
                "patient_id": str(uuid.uuid4()),
                "first_name": self.fake.first_name(),
                "last_name": self.fake.last_name(),
                "birth_date": birth_date,
                "age": age,
                "gender": random.choice(["M", "F", "Other"]),
                "address": self.fake.address().replace('\n', ', '),
                "phone": self.fake.phone_number(),
                "email": self.fake.email()
            })
        
        return {"patients": pd.DataFrame(patients)}
    
    def apply_perturbations(self, dataframes: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Apply perturbations to patient data"""
        result = {}
        all_perturbations = []
        
        for table_name, df in dataframes.items():
            perturbed_df, perturbations = self._apply_common_perturbations(df, table_name)
            result[table_name] = perturbed_df
            all_perturbations.extend(perturbations)
        
        self._perturbations = all_perturbations
        return result
    
    def get_ground_truth(self, dataframes: Dict[str, pd.DataFrame]) -> PluginGroundTruth:
        """Calculate ground truth for patient data"""
        patients_df = dataframes["patients"]
        
        avg_age = patients_df["age"].mean() if "age" in patients_df.columns else 0
        gender_counts = patients_df["gender"].value_counts().to_dict() if "gender" in patients_df.columns else {}
        
        return PluginGroundTruth(
            record_count=len(patients_df),
            most_common_value=patients_df["gender"].mode().iloc[0] if "gender" in patients_df.columns and not patients_df.empty else None,
            custom_metrics={
                "average_age": avg_age,
                "gender_distribution": gender_counts
            }
        )
    
    def get_training_example(self, ground_truth: PluginGroundTruth) -> Optional[TrainingExample]:
        """Generate patient-related training examples"""
        if ground_truth.record_count == 0:
            return None
        
        # Choose between different question types
        question_types = ["count", "demographics"]
        if ground_truth.custom_metrics:
            question_types.append("stats")
        
        question_type = random.choice(question_types)
        
        if question_type == "count":
            instructions = f"""Generate a natural, conversational question asking about the total number of 
            patients in a medical database. The person should sound like a healthcare administrator 
            who needs patient statistics but can't remember. 
            The actual count is {ground_truth.record_count} patients."""
            
            question_obj = generate_fixed(instructions, TrainingQuestion)
            if question_obj:
                answer = CountAnswer(count=ground_truth.record_count)
                return TrainingExample(
                    question=question_obj.question,
                    answer=answer,
                    plugin_name=self.name
                )
        
        elif question_type == "stats":
            avg_age = ground_truth.custom_metrics.get("average_age", 0)
            gender_dist = ground_truth.custom_metrics.get("gender_distribution", {})
            
            instructions = f"""Generate a natural, conversational question asking about patient 
            demographics in a medical database. The person should sound like they're preparing 
            a report but having memory issues. 
            The actual data includes {ground_truth.record_count} patients with average age {avg_age:.1f}."""
            
            question_obj = generate_fixed(instructions, TrainingQuestion)
            if question_obj:
                answer = PatientStatsAnswer(
                    average_age=avg_age,
                    total_patients=ground_truth.record_count,
                    gender_distribution=gender_dist
                )
                return TrainingExample(
                    question=question_obj.question,
                    answer=answer,
                    plugin_name=self.name
                )
        
        return None

class ConditionPlugin(DatabasePlugin):
    """Plugin for managing medical conditions data"""
    
    @property
    def name(self) -> str:
        return "conditions"
    
    @property
    def table_names(self) -> List[str]:
        return ["conditions"]
    
    def initialize(self) -> None:
        """Initialize conditions from API or fallback"""
        self._conditions_cache = []
        if self.use_apis:
            self._conditions_cache = self._get_conditions_from_api()
        
        if not self._conditions_cache:
            self._conditions_cache = [
                "Diabetes Mellitus Type 2", "Hypertension", "Asthma", "Depression",
                "Obesity", "Coronary Artery Disease", "COPD", "Arthritis", "Anxiety",
                "Hyperlipidemia", "Sleep Apnea", "Atrial Fibrillation"
            ]
    
    def _get_conditions_from_api(self, count=100) -> List[str]:
        """Get conditions from Clinical Tables API"""
        try:
            url = "https://clinicaltables.nlm.nih.gov/api/conditions/v3/search"
            params = {'terms': '', 'maxList': count}
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if len(data) > 3 and data[3]:
                    conditions_list = [condition for condition in data[3] if len(condition) < 100]
                    conditions = []
                    for condition_list in conditions_list:
                      conditions.extend(condition_list)
                    return conditions[:count]
        except Exception as e:
            print(f"Error fetching conditions from API: {e}")
        return []
    
    def generate_data(self, patients_df: pd.DataFrame, context: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
        """Generate conditions data"""
        conditions = []
        patient_ids = patients_df["patient_id"].tolist()
        
        for patient_id in patient_ids:
            num_conditions = random.randint(0, 3)
            patient_conditions = random.sample(self._conditions_cache, min(num_conditions, len(self._conditions_cache)))
            
            for condition_name in patient_conditions:
                condition = ConditionT(
                    id=str(uuid.uuid4()),
                    name=condition_name,
                    description=f"Patient diagnosed with {condition_name}",
                    status=random.choice(list(ConditionStatusEnumT)),
                    date=self.fake.date_between(start_date="-5y", end_date="today"),
                    origin_ids=[patient_id],
                    recorder_name=self.fake.name()
                )
                conditions.append(condition.model_dump())
        
        return {"conditions": pd.DataFrame(conditions)}
    
    def apply_perturbations(self, dataframes: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Apply perturbations to conditions data"""
        result = {}
        all_perturbations = []
        
        for table_name, df in dataframes.items():
            perturbed_df, perturbations = self._apply_common_perturbations(df, table_name)
            
            # Domain-specific perturbation: change status enum values
            if random.random() < 0.2 and "status" in perturbed_df.columns:
                perturbed_df["status"] = perturbed_df["status"].replace({
                    "active": "current",
                    "inactive": "dormant",
                    "resolved": "cured"
                })
                perturbations.append("Modified condition status values")
            
            result[table_name] = perturbed_df
            all_perturbations.extend(perturbations)
        
        self._perturbations = all_perturbations
        return result
    
    def get_ground_truth(self, dataframes: Dict[str, pd.DataFrame]) -> PluginGroundTruth:
        """Calculate ground truth for conditions data"""
        conditions_df = dataframes["conditions"]
        
        if conditions_df.empty:
            return PluginGroundTruth(record_count=0)
        
        most_common = conditions_df["name"].mode().iloc[0] if "name" in conditions_df.columns else None
        unique_conditions = conditions_df["name"].unique().tolist() if "name" in conditions_df.columns else []
        diabetes_count = len(conditions_df[conditions_df["name"].str.contains("Diabetes", na=False)]) if "name" in conditions_df.columns else 0
        
        return PluginGroundTruth(
            record_count=len(conditions_df),
            most_common_value=most_common,
            unique_values=unique_conditions,
            custom_metrics={"diabetes_patients": diabetes_count}
        )
    
    def get_training_example(self, ground_truth: PluginGroundTruth) -> Optional[TrainingExample]:
        """Generate condition-related training examples"""
        if ground_truth.record_count == 0:
            return None
        
        # Choose between count, most common, and diabetes-specific questions
        question_types = ["count"]
        if ground_truth.most_common_value:
            question_types.append("most_common")
        if ground_truth.custom_metrics.get("diabetes_patients", 0) > 0:
            question_types.append("diabetes")
        
        question_type = random.choice(question_types)
        
        if question_type == "count":
            instructions = f"""Generate a natural, conversational question asking about the total number of 
            medical conditions in a patient database. The person should sound like a healthcare worker 
            who needs condition statistics but can't remember. 
            The actual count is {ground_truth.record_count} condition records."""
            
            question_obj = generate_fixed(instructions, TrainingQuestion)
            if question_obj:
                answer = CountAnswer(count=ground_truth.record_count)
                return TrainingExample(
                    question=question_obj.question,
                    answer=answer,
                    plugin_name=self.name
                )
        
        elif question_type == "most_common":
            instructions = f"""Generate a natural, conversational question asking about the most common 
            medical condition in a patient database. The person should sound like they're working on a 
            health trends report but having memory issues. 
            The actual most common condition is '{ground_truth.most_common_value}'."""
            
            question_obj = generate_fixed(instructions, TrainingQuestion)
            if question_obj:
                answer = MostCommonAnswer(item=ground_truth.most_common_value)
                return TrainingExample(
                    question=question_obj.question,
                    answer=answer,
                    plugin_name=self.name
                )
        
        elif question_type == "diabetes":
            diabetes_count = ground_truth.custom_metrics.get("diabetes_patients", 0)
            instructions = f"""Generate a natural, conversational question asking about the number of 
            diabetic patients in a medical database. The person should sound like they're working on 
            a diabetes care program but having memory issues. 
            The actual count is {diabetes_count} diabetic patients."""
            
            question_obj = generate_fixed(instructions, TrainingQuestion)
            if question_obj:
                answer = CountAnswer(count=diabetes_count)
                return TrainingExample(
                    question=question_obj.question,
                    answer=answer,
                    plugin_name=self.name
                )
        
        return None

class MedicationPlugin(DatabasePlugin):
    """Plugin for managing medication data"""
    
    @property
    def name(self) -> str:
        return "medications"
    
    @property
    def table_names(self) -> List[str]:
        return ["medications"]
    
    def initialize(self) -> None:
        """Initialize medications from API or fallback"""
        self._medications_cache = []
        if self.use_apis:
            self._medications_cache = self._get_medications_from_api()
        
        if not self._medications_cache:
            self._medications_cache = [
                "Metformin", "Lisinopril", "Atorvastatin", "Amlodipine", "Albuterol",
                "Sertraline", "Losartan", "Gabapentin", "Levothyroxine", "Omeprazole",
                "Hydrochlorothiazide", "Metoprolol"
            ]
    
    def _get_medications_from_api(self, count=100) -> List[str]:
        """Get medications from RxNorm API"""
        try:
            all_drugs = []
            letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'l', 'm', 'p', 's', 't']
            
            for letter in letters:
                if len(all_drugs) >= count:
                    break
                
                try:
                    url = "https://rxnav.nlm.nih.gov/REST/drugs.json"
                    params = {'name': letter}
                    
                    response = requests.get(url, params=params, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        if 'drugGroup' in data and 'conceptGroup' in data['drugGroup']:
                            for group in data['drugGroup']['conceptGroup']:
                                if 'conceptProperties' in group:
                                    for drug in group['conceptProperties']:
                                        drug_name = drug['name']
                                        if len(drug_name) < 50 and drug_name not in all_drugs:
                                            all_drugs.append(drug_name)
                                        if len(all_drugs) >= count:
                                            break
                    time.sleep(0.1)
                except Exception:
                    continue
            
            return all_drugs[:count]
        except Exception as e:
            print(f"Error fetching medications from API: {e}")
        return []
    
    def generate_data(self, patients_df: pd.DataFrame, context: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
        """Generate medication data"""
        medications = []
        patient_ids = patients_df["patient_id"].tolist()
        
        for patient_id in patient_ids:
            num_meds = random.randint(0, 4)
            patient_meds = random.sample(self._medications_cache, min(num_meds, len(self._medications_cache)))
            
            for med_name in patient_meds:
                start_date = self.fake.date_between(start_date="-2y", end_date="today")
                
                medication = MedicationHistoryT(
                    id=str(uuid.uuid4()),
                    name=med_name,
                    rxcode=f"RX{random.randint(1000, 9999)}",
                    reason=random.choice(self._medications_cache),
                    note=f"Prescribed {med_name} for treatment",
                    status=random.choice(list(MedicationStatus)),
                    period_start=start_date,
                    period_end=self.fake.date_between(start_date=start_date, end_date="+1y") if random.random() > 0.3 else None,
                    dosage_and_route_instructions=f"{random.randint(1, 4)} tablet(s) {random.choice(['once', 'twice', 'three times'])} daily",
                    requester_name=self.fake.name()
                )
                medications.append(medication.model_dump())
        
        return {"medications": pd.DataFrame(medications)}
    
    def apply_perturbations(self, dataframes: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Apply perturbations to medication data"""
        result = {}
        all_perturbations = []
        
        for table_name, df in dataframes.items():
            perturbed_df, perturbations = self._apply_common_perturbations(df, table_name)
            
            # Domain-specific: rename rxcode to different variations
            if random.random() < 0.3 and "rxcode" in perturbed_df.columns:
                new_col_name = random.choice(["rx_code", "prescription_code", "med_code", "drug_code"])
                perturbed_df = perturbed_df.rename(columns={"rxcode": new_col_name})
                perturbations.append(f"Renamed rxcode to {new_col_name}")
            
            result[table_name] = perturbed_df
            all_perturbations.extend(perturbations)
        
        self._perturbations = all_perturbations
        return result
    
    def get_ground_truth(self, dataframes: Dict[str, pd.DataFrame]) -> PluginGroundTruth:
        """Calculate ground truth for medication data"""
        medications_df = dataframes["medications"]
        
        if medications_df.empty:
            return PluginGroundTruth(record_count=0)
        
        most_common = medications_df["name"].mode().iloc[0] if "name" in medications_df.columns else None
        active_count = len(medications_df[medications_df["status"] == "active"]) if "status" in medications_df.columns else 0
        
        return PluginGroundTruth(
            record_count=len(medications_df),
            most_common_value=most_common,
            custom_metrics={"active_medications": active_count}
        )
    
    def get_training_example(self, ground_truth: PluginGroundTruth) -> Optional[TrainingExample]:
        """Generate medication-related training examples"""
        if ground_truth.record_count == 0:
            return None
        
        # Choose between count, most common, and active medication questions
        question_types = ["count"]
        if ground_truth.most_common_value:
            question_types.append("most_common")
        if ground_truth.custom_metrics.get("active_medications", 0) > 0:
            question_types.append("active")
        
        question_type = random.choice(question_types)
        
        if question_type == "count":
            instructions = f"""Generate a natural, conversational question asking about the total number of 
            medication records in a medical database. The person should sound like a pharmacy coordinator 
            who needs medication statistics but can't remember. 
            The actual count is {ground_truth.record_count} medication records."""
            
            question_obj = generate_fixed(instructions, TrainingQuestion)
            if question_obj:
                answer = CountAnswer(count=ground_truth.record_count)
                return TrainingExample(
                    question=question_obj.question,
                    answer=answer,
                    plugin_name=self.name
                )
        
        elif question_type == "most_common":
            instructions = f"""Generate a natural, conversational question asking about the most commonly 
            prescribed medication in a patient database. The person should sound like they're working on 
            medication usage analysis but having memory issues. 
            The actual most common medication is '{ground_truth.most_common_value}'."""
            
            question_obj = generate_fixed(instructions, TrainingQuestion)
            if question_obj:
                answer = MostCommonAnswer(item=ground_truth.most_common_value)
                return TrainingExample(
                    question=question_obj.question,
                    answer=answer,
                    plugin_name=self.name
                )
        
        elif question_type == "active":
            active_count = ground_truth.custom_metrics.get("active_medications", 0)
            instructions = f"""Generate a natural, conversational question asking about the number of 
            active medication prescriptions in a medical database. The person should sound like they're 
            doing inventory planning but having memory issues. 
            The actual count is {active_count} active medications."""
            
            question_obj = generate_fixed(instructions, TrainingQuestion)
            if question_obj:
                answer = CountAnswer(count=active_count)
                return TrainingExample(
                    question=question_obj.question,
                    answer=answer,
                    plugin_name=self.name
                )
        
        return None

class VitalSignPlugin(DatabasePlugin):
    """Plugin for managing vital signs data"""
    
    @property
    def name(self) -> str:
        return "vitals"
    
    @property
    def table_names(self) -> List[str]:
        return ["vitals"]
    
    def initialize(self) -> None:
        """Initialize vital sign definitions"""
        self.vital_signs = [
            ("Systolic Blood Pressure", "mmHg", 90, 180),
            ("Diastolic Blood Pressure", "mmHg", 60, 120),
            ("Heart Rate", "bpm", 60, 100),
            ("Body Temperature", "°F", 97.0, 99.5),
            ("Respiratory Rate", "breaths/min", 12, 20),
            ("Weight", "lbs", 100, 300),
            ("Height", "inches", 60, 78),
            ("BMI", "kg/m²", 18.5, 35.0)
        ]
    
    def generate_data(self, patients_df: pd.DataFrame, context: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
        """Generate vital signs data"""
        vitals = []
        patient_ids = patients_df["patient_id"].tolist()
        
        for patient_id in patient_ids:
            num_vitals = random.randint(5, 15)
            
            for _ in range(num_vitals):
                vital_name, unit, min_val, max_val = random.choice(self.vital_signs)
                value = round(random.uniform(min_val, max_val), 1)
                
                vital = VitalSignT(
                    id=str(uuid.uuid4()),
                    name=vital_name,
                    value=value,
                    unit=unit,
                    date=self.fake.date_between(start_date="-1y", end_date="today"),
                    status=random.choice(list(ObservationStatus)),
                    reference_range_low=min_val,
                    reference_range_high=max_val,
                    reference_range_unit=unit,
                    notes=f"Measured during routine visit" if random.random() > 0.7 else None
                )
                vitals.append(vital.model_dump())
        
        return {"vitals": pd.DataFrame(vitals)}
    
    def apply_perturbations(self, dataframes: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Apply perturbations to vital signs data"""
        result = {}
        all_perturbations = []
        
        for table_name, df in dataframes.items():
            perturbed_df, perturbations = self._apply_common_perturbations(df, table_name)
            
            # Domain-specific: modify unit representations
            if random.random() < 0.25 and "unit" in perturbed_df.columns:
                unit_replacements = {
                    "mmHg": "mm Hg",
                    "bpm": "beats/min",
                    "°F": "fahrenheit",
                    "kg/m²": "kg/m2"
                }
                for old_unit, new_unit in unit_replacements.items():
                    perturbed_df["unit"] = perturbed_df["unit"].replace(old_unit, new_unit)
                perturbations.append("Modified unit representations")
            
            result[table_name] = perturbed_df
            all_perturbations.extend(perturbations)
        
        self._perturbations = all_perturbations
        return result
    
    def get_ground_truth(self, dataframes: Dict[str, pd.DataFrame]) -> PluginGroundTruth:
        """Calculate ground truth for vital signs data"""
        vitals_df = dataframes["vitals"]
        
        if vitals_df.empty:
            return PluginGroundTruth(record_count=0)
        
        avg_value = vitals_df["value"].mean() if "value" in vitals_df.columns else 0
        unique_vital_types = vitals_df["name"].unique().tolist() if "name" in vitals_df.columns else []
        
        return PluginGroundTruth(
            record_count=len(vitals_df),
            unique_values=unique_vital_types,
            custom_metrics={"average_vital_value": avg_value}
        )
    
    def get_training_example(self, ground_truth: PluginGroundTruth) -> Optional[TrainingExample]:
        """Generate vital signs-related training examples"""
        if ground_truth.record_count == 0:
            return None
        
        instructions = f"""Generate a natural, conversational question asking about the total number of 
        vital sign measurements in a medical database. The person should sound like a nurse or clinical 
        coordinator who needs vital signs statistics but can't remember. 
        The actual count is {ground_truth.record_count} vital sign records."""
        
        question_obj = generate_fixed(instructions, TrainingQuestion)
        if question_obj:
            answer = CountAnswer(count=ground_truth.record_count)
            return TrainingExample(
                question=question_obj.question,
                answer=answer,
                plugin_name=self.name
            )
        
        return None

class LabPlugin(DatabasePlugin):
    """Plugin for managing laboratory results data"""
    
    @property
    def name(self) -> str:
        return "labs"
    
    @property
    def table_names(self) -> List[str]:
        return ["labs"]
    
    def initialize(self) -> None:
        """Initialize lab test definitions"""
        self.lab_tests = [
            "Hemoglobin A1C", "Total Cholesterol", "HDL Cholesterol", "LDL Cholesterol",
            "Triglycerides", "Glucose", "Creatinine", "BUN", "TSH", "Vitamin D"
        ]
    
    def generate_data(self, patients_df: pd.DataFrame, context: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
        """Generate lab results data"""
        labs = []
        patient_ids = patients_df["patient_id"].tolist()
        
        for patient_id in patient_ids:
            num_labs = random.randint(3, 8)
            patient_labs = random.sample(self.lab_tests, min(num_labs, len(self.lab_tests)))
            
            for lab_name in patient_labs:
                lab = LabT(
                    id=str(uuid.uuid4()),
                    name=lab_name,
                    value=f"{random.uniform(1.0, 200.0):.1f}",
                    date=self.fake.date_between(start_date="-1y", end_date="today"),
                    status=random.choice(list(ObservationStatus)),
                    notes=f"Lab test for {lab_name}" if random.random() > 0.5 else None,
                    reference_range_low=random.uniform(1.0, 50.0),
                    reference_range_high=random.uniform(50.0, 200.0),
                    reference_range_unit="mg/dL"
                )
                labs.append(lab.model_dump())
        
        return {"labs": pd.DataFrame(labs)}
    
    def apply_perturbations(self, dataframes: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Apply perturbations to lab data"""
        result = {}
        all_perturbations = []
        
        for table_name, df in dataframes.items():
            perturbed_df, perturbations = self._apply_common_perturbations(df, table_name)
            
            # Domain-specific: split reference ranges into separate columns
            if random.random() < 0.3 and "reference_range_low" in perturbed_df.columns and "reference_range_high" in perturbed_df.columns:
                perturbed_df["reference_range"] = perturbed_df["reference_range_low"].astype(str) + "-" + perturbed_df["reference_range_high"].astype(str)
                perturbed_df = perturbed_df.drop(columns=["reference_range_low", "reference_range_high"])
                perturbations.append("Combined reference ranges into single column")
            
            result[table_name] = perturbed_df
            all_perturbations.extend(perturbations)
        
        self._perturbations = all_perturbations
        return result
    
    def get_ground_truth(self, dataframes: Dict[str, pd.DataFrame]) -> PluginGroundTruth:
        """Calculate ground truth for lab data"""
        labs_df = dataframes["labs"]
        
        if labs_df.empty:
            return PluginGroundTruth(record_count=0)
        
        unique_lab_types = labs_df["name"].unique().tolist() if "name" in labs_df.columns else []
        
        return PluginGroundTruth(
            record_count=len(labs_df),
            unique_values=unique_lab_types
        )
    
    def get_training_example(self, ground_truth: PluginGroundTruth) -> Optional[TrainingExample]:
        """Generate lab-related training examples"""
        if ground_truth.record_count == 0:
            return None
        
        instructions = f"""Generate a natural, conversational question asking about the total number of 
        laboratory test results in a medical database. The person should sound like a lab technician 
        or clinical coordinator who needs lab statistics but can't remember. 
        The actual count is {ground_truth.record_count} lab test records."""
        
        question_obj = generate_fixed(instructions, TrainingQuestion)
        if question_obj:
            answer = CountAnswer(count=ground_truth.record_count)
            return TrainingExample(
                question=question_obj.question,
                answer=answer,
                plugin_name=self.name
            )
        
        return None

class ProcedurePlugin(DatabasePlugin):
    """Plugin for managing procedures data"""
    
    @property
    def name(self) -> str:
        return "procedures"
    
    @property
    def table_names(self) -> List[str]:
        return ["procedures"]
    
    def initialize(self) -> None:
        """Initialize procedures from API or fallback"""
        self._procedures_cache = []
        if self.use_apis:
            self._procedures_cache = self._get_procedures_from_api()
        
        if not self._procedures_cache:
            self._procedures_cache = [
                "Annual Physical Exam", "Colonoscopy", "Mammography", "Echocardiogram",
                "Stress Test", "CT Scan", "MRI", "Blood Draw", "Vaccination", "EKG"
            ]
    
    def _get_procedures_from_api(self, count=100) -> List[str]:
        """Get procedures from ICD-10-CM/PCS API"""
        try:
            all_procedures = []
            procedure_terms = ['surgery', 'biopsy', 'examination', 'injection', 'removal', 
                             'therapy', 'treatment', 'procedure', 'operation', 'test']
            
            url = "https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search"
            
            for term in procedure_terms:
                if len(all_procedures) >= count:
                    break
                
                try:
                    params = {'terms': term, 'maxList': 20}
                    response = requests.get(url, params=params, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        if len(data) > 3 and data[3]:
                            procedures = [proc for proc in data[3] if len(proc) < 100]
                            all_procedures.extend(procedures)
                    time.sleep(0.1)
                except Exception:
                    continue
            
            unique_procedures = list(set(all_procedures))
            return unique_procedures[:count]
        except Exception as e:
            print(f"Error fetching procedures from API: {e}")
        return []
    
    def generate_data(self, patients_df: pd.DataFrame, context: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
        """Generate procedures data"""
        procedures = []
        patient_ids = patients_df["patient_id"].tolist()
        
        for patient_id in patient_ids:
            num_procedures = random.randint(1, 5)
            patient_procedures = random.sample(self._procedures_cache, min(num_procedures, len(self._procedures_cache)))
            
            for proc_name in patient_procedures:
                procedure = ProcedureT(
                    id=str(uuid.uuid4()),
                    name=proc_name,
                    info=f"Performed {proc_name} for patient care",
                    status=random.choice(list(ProcedureStatusEnum)),
                    date=self.fake.date_between(start_date="-1y", end_date="today"),
                    origin_ids=[patient_id],
                    performer_names=self.fake.name()
                )
                procedures.append(procedure.model_dump())
        
        return {"procedures": pd.DataFrame(procedures)}
    
    def apply_perturbations(self, dataframes: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Apply perturbations to procedures data"""
        result = {}
        all_perturbations = []
        
        for table_name, df in dataframes.items():
            perturbed_df, perturbations = self._apply_common_perturbations(df, table_name)
            
            # Domain-specific: modify performer_names to performer
            if random.random() < 0.3 and "performer_names" in perturbed_df.columns:
                perturbed_df = perturbed_df.rename(columns={"performer_names": "performer"})
                perturbations.append("Renamed performer_names to performer")
            
            result[table_name] = perturbed_df
            all_perturbations.extend(perturbations)
        
        self._perturbations = all_perturbations
        return result
    
    def get_ground_truth(self, dataframes: Dict[str, pd.DataFrame]) -> PluginGroundTruth:
        """Calculate ground truth for procedures data"""
        procedures_df = dataframes["procedures"]
        
        if procedures_df.empty:
            return PluginGroundTruth(record_count=0)
        
        most_common = procedures_df["name"].mode().iloc[0] if "name" in procedures_df.columns else None
        unique_procedures = procedures_df["name"].unique().tolist() if "name" in procedures_df.columns else []
        
        return PluginGroundTruth(
            record_count=len(procedures_df),
            most_common_value=most_common,
            unique_values=unique_procedures
        )
    
    def get_training_example(self, ground_truth: PluginGroundTruth) -> Optional[TrainingExample]:
        """Generate procedure-related training examples"""
        if ground_truth.record_count == 0:
            return None
        
        # Choose between count and most common procedure questions
        question_types = ["count"]
        if ground_truth.most_common_value:
            question_types.append("most_common")
        
        question_type = random.choice(question_types)
        
        if question_type == "count":
            instructions = f"""Generate a natural, conversational question asking about the total number of 
            medical procedures in a patient database. The person should sound like a clinical coordinator 
            who needs procedure statistics but can't remember. 
            The actual count is {ground_truth.record_count} procedure records."""
            
            question_obj = generate_fixed(instructions, TrainingQuestion)
            if question_obj:
                answer = CountAnswer(count=ground_truth.record_count)
                return TrainingExample(
                    question=question_obj.question,
                    answer=answer,
                    plugin_name=self.name
                )
        
        elif question_type == "most_common":
            instructions = f"""Generate a natural, conversational question asking about the most commonly 
            performed medical procedure in a patient database. The person should sound like they're 
            analyzing procedure patterns but having memory issues. 
            The actual most common procedure is '{ground_truth.most_common_value}'."""
            
            question_obj = generate_fixed(instructions, TrainingQuestion)
            if question_obj:
                answer = MostCommonAnswer(item=ground_truth.most_common_value)
                return TrainingExample(
                    question=question_obj.question,
                    answer=answer,
                    plugin_name=self.name
                )
        
        return None

class PluginRegistry:
    """Registry for managing database plugins"""
    
    def __init__(self):
        self.plugins: Dict[str, DatabasePlugin] = {}
        self.plugin_order: List[str] = []
    
    def register(self, plugin: DatabasePlugin) -> None:
        """Register a plugin"""
        self.plugins[plugin.name] = plugin
        if plugin.name not in self.plugin_order:
            self.plugin_order.append(plugin.name)
    
    def get_plugin(self, name: str) -> Optional[DatabasePlugin]:
        """Get a plugin by name"""
        return self.plugins.get(name)
    
    def get_all_plugins(self) -> List[DatabasePlugin]:
        """Get all plugins in registration order"""
        return [self.plugins[name] for name in self.plugin_order if name in self.plugins]
    
    def get_all_table_names(self) -> List[str]:
        """Get all table names managed by all plugins"""
        table_names = []
        for plugin in self.get_all_plugins():
            table_names.extend(plugin.table_names)
        return table_names

class MedicalDatabaseGym:
    """
    Plugin-based medical database gym for training RL models.
    Each plugin handles a specific domain of medical data.
    """
    
    def __init__(self, db_path: str = ":memory:", seed: Optional[int] = None, use_apis: bool = True):
        self.fake = Faker()
        if seed:
            Faker.seed(seed)
            random.seed(seed)
        
        self.conn = duckdb.connect(db_path)
        self.use_apis = use_apis
        self.seed = seed
        
        # Initialize plugin registry
        self.registry = PluginRegistry()
        self._initialize_default_plugins()
        
        self.ground_truth: Optional[GroundTruth] = None
        self.schema_perturbations: Dict[str, List[str]] = {}
    
    def _initialize_default_plugins(self):
        """Initialize default medical plugins"""
        plugins = [
            PatientPlugin(self.fake, self.use_apis, self.seed),
            ConditionPlugin(self.fake, self.use_apis, self.seed),
            MedicationPlugin(self.fake, self.use_apis, self.seed),
            VitalSignPlugin(self.fake, self.use_apis, self.seed),
            LabPlugin(self.fake, self.use_apis, self.seed),
            ProcedurePlugin(self.fake, self.use_apis, self.seed)
        ]
        
        for plugin in plugins:
            self.registry.register(plugin)
            if self.use_apis:
                print(f"Initializing {plugin.name} plugin...")
                plugin.initialize()
    
    def register_plugin(self, plugin: DatabasePlugin) -> None:
        """Register a custom plugin"""
        plugin.fake = self.fake  # Ensure plugin uses same faker instance
        self.registry.register(plugin)
        plugin.initialize()
    
    def create_database(self, num_patients: int = 100, apply_perturbations: bool = True) -> GroundTruth:
        """Create the complete database using all registered plugins"""
        
        # Generate patient data first (base data)
        patient_plugin = self.registry.get_plugin("patients")
        context = {"num_patients": num_patients}
        patient_data = patient_plugin.generate_data(None, context)
        patients_df = patient_data["patients"]
        
        # Generate data for all other plugins
        all_dataframes = {"patients": patients_df}
        plugin_ground_truths = {}
        
        for plugin in self.registry.get_all_plugins():
            if plugin.name == "patients":
                continue  # Already generated
                
            plugin_data = plugin.generate_data(patients_df, context)
            all_dataframes.update(plugin_data)
        
        # Apply perturbations if requested
        if apply_perturbations:
            self.schema_perturbations = {}
            for plugin in self.registry.get_all_plugins():
                plugin_tables = {name: df for name, df in all_dataframes.items() if name in plugin.table_names}
                perturbed_tables = plugin.apply_perturbations(plugin_tables)
                all_dataframes.update(perturbed_tables)
                
                # Collect perturbations
                if hasattr(plugin, '_perturbations'):
                    for table_name in plugin.table_names:
                        if table_name in perturbed_tables:
                            self.schema_perturbations[table_name] = plugin._perturbations
        
        # Create tables in DuckDB
        for table_name, df in all_dataframes.items():
            # Drop both table and view if they exist
            self.conn.execute(f"DROP VIEW IF EXISTS {table_name}")
            self.conn.execute(f"DROP TABLE IF EXISTS {table_name}")
            self.conn.register(table_name, df)
            self.conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM {table_name}")
        
        # Calculate ground truth for each plugin
        for plugin in self.registry.get_all_plugins():
            plugin_tables = {name: df for name, df in all_dataframes.items() if name in plugin.table_names}
            plugin_ground_truths[plugin.name] = plugin.get_ground_truth(plugin_tables)
        
        # Calculate overall ground truth
        total_records = sum(len(df) for df in all_dataframes.values())
        
        self.ground_truth = GroundTruth(
            total_records=total_records,
            plugin_ground_truths=plugin_ground_truths,
            schema_perturbations=self.schema_perturbations
        )
        
        return self.ground_truth
    
    def get_connection(self) -> duckdb.DuckDBPyConnection:
        """Get the DuckDB connection for querying"""
        return self.conn
    
    def get_schema_info(self) -> Dict[str, List[str]]:
        """Get information about current table schemas"""
        schema_info = {}
        tables = self.conn.execute("SHOW TABLES").fetchall()
        
        for table in tables:
            table_name = table[0]
            columns = self.conn.execute(f"PRAGMA table_info('{table_name}')").fetchall()
            schema_info[table_name] = [col[1] for col in columns]
        
        return schema_info
    
    def reset(self, num_patients: int = None, apply_perturbations: bool = True) -> GroundTruth:
        """Reset the database with new random data"""
        if num_patients is None:
            num_patients = random.randint(50, 200)
        
        return self.create_database(num_patients, apply_perturbations)
    
    def get_ground_truth(self) -> Optional[GroundTruth]:
        """Get the ground truth facts about the current database"""
        return self.ground_truth
    
    def list_plugins(self) -> List[str]:
        """List all registered plugins"""
        return list(self.registry.plugins.keys())
    
    def get_plugin(self, name: str) -> Optional[DatabasePlugin]:
        """Get a specific plugin"""
        return self.registry.get_plugin(name)
    
    def get_training_example(self) -> Optional[TrainingExample]:
        """
        Generate a training example using plugin-based approach.
        
        Returns:
            TrainingExample object or None if no example can be generated
        """
        if not self.ground_truth:
            raise ValueError("No ground truth available. Call create_database() first.")
        
        # Get all plugins that can generate training examples
        available_plugins = []
        for plugin in self.registry.get_all_plugins():
            plugin_gt = self.ground_truth.plugin_ground_truths.get(plugin.name)
            if plugin_gt and plugin_gt.record_count > 0:
                available_plugins.append((plugin, plugin_gt))
        
        if not available_plugins:
            return None
        
        # Try to generate a training example from a random plugin
        attempts = 0
        max_attempts = len(available_plugins) * 3
        
        while attempts < max_attempts:
            plugin, plugin_gt = random.choice(available_plugins)
            try:
                training_example = plugin.get_training_example(plugin_gt)
                if training_example:
                    return training_example
            except Exception as e:
                print(f"Error generating training example from {plugin.name}: {e}")
            
            attempts += 1
        
        return None
    
    def close(self):
        """Close the database connection"""
        self.conn.close()

# Example custom plugin for allergies
class AllergyPlugin(DatabasePlugin):
    @property
    def name(self) -> str:
        return "allergies"
    
    @property
    def table_names(self) -> List[str]:
        return ["allergies"]
    
    def initialize(self) -> None:
        self.allergens = ["Peanuts", "Shellfish", "Dairy", "Eggs", "Soy", "Wheat", "Tree nuts"]
    
    def generate_data(self, patients_df: pd.DataFrame, context: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
        allergies = []
        for patient_id in patients_df["patient_id"].tolist():
            if random.random() < 0.3:  # 30% chance of having allergies
                num_allergies = random.randint(1, 2)
                patient_allergens = random.sample(self.allergens, num_allergies)
                for allergen in patient_allergens:
                    allergies.append({
                        "id": str(uuid.uuid4()),
                        "patient_id": patient_id,
                        "allergen": allergen,
                        "severity": random.choice(["mild", "moderate", "severe"]),
                        "date_discovered": self.fake.date_between(start_date="-10y", end_date="today")
                    })
        return {"allergies": pd.DataFrame(allergies)}
    
    def apply_perturbations(self, dataframes: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        result = {}
        all_perturbations = []
        for table_name, df in dataframes.items():
            perturbed_df, perturbations = self._apply_common_perturbations(df, table_name)
            result[table_name] = perturbed_df
            all_perturbations.extend(perturbations)
        self._perturbations = all_perturbations
        return result
    
    def get_ground_truth(self, dataframes: Dict[str, pd.DataFrame]) -> PluginGroundTruth:
        allergies_df = dataframes["allergies"]
        if allergies_df.empty:
            return PluginGroundTruth(record_count=0)
        
        most_common = allergies_df["allergen"].mode().iloc[0] if "allergen" in allergies_df.columns else None
        return PluginGroundTruth(
            record_count=len(allergies_df),
            most_common_value=most_common
        )
    
    def get_training_example(self, ground_truth: PluginGroundTruth) -> Optional[TrainingExample]:
        """Generate allergy-related training questions"""
        if ground_truth.record_count == 0:
            return None
        
        # Choose between count and most common allergen questions
        question_types = ["count"]
        if ground_truth.most_common_value:
            question_types.append("most_common")
        
        question_type = random.choice(question_types)
        
        if question_type == "count":
            instructions = f"""Generate a natural, conversational question asking about the total number of 
            allergy records in a medical database. The person should sound like a healthcare worker 
            who needs allergy statistics but can't remember. 
            The actual count is {ground_truth.record_count} allergy records."""
            
            question_obj = generate_fixed(instructions, TrainingQuestion)
            if question_obj:
                answer = CountAnswer(count=ground_truth.record_count)
                return TrainingExample(
                    question=question_obj.question,
                    answer=answer,
                    plugin_name=self.name
                )
        
        elif question_type == "most_common":
            instructions = f"""Generate a natural, conversational question asking about the most common 
            allergen in a patient database. The person should sound like they're working on an allergy 
            management program but having memory issues. 
            The actual most common allergen is '{ground_truth.most_common_value}'."""
            
            question_obj = generate_fixed(instructions, TrainingQuestion)
            if question_obj:
                answer = MostCommonAnswer(item=ground_truth.most_common_value)
                return TrainingExample(
                    question=question_obj.question,
                    answer=answer,
                    plugin_name=self.name
                )
        
        return None

# Example usage
if __name__ == "__main__":
    # Create the gym with default plugins
    print("Creating Plugin-Based Medical Database Gym...")
    gym = MedicalDatabaseGym(seed=42, use_apis=True)
    
    print(f"Registered plugins: {gym.list_plugins()}")
    
    # Generate a database
    print("Generating database with realistic medical data...")
    ground_truth = gym.create_database(num_patients=100, apply_perturbations=True)
    
    # Get connection for querying
    conn = gym.get_connection()
    
    # Show schema info
    print("\nSchema info:")
    schema_info = gym.get_schema_info()
    for table, columns in schema_info.items():
        print(f"{table}: {columns}")
    
    # Show ground truth
    print(f"\nGround truth:")
    print(f"Total records: {ground_truth.total_records}")
    for plugin_name, plugin_gt in ground_truth.plugin_ground_truths.items():
        print(f"{plugin_name}: {plugin_gt.record_count} records")
        if plugin_gt.most_common_value:
            print(f"  Most common: {plugin_gt.most_common_value}")
        if plugin_gt.custom_metrics:
            print(f"  Custom metrics: {plugin_gt.custom_metrics}")
    
    # Generate training examples using new plugin-based approach
    print(f"\n=== TRAINING EXAMPLES ===")
    for i in range(5):
        try:
            training_example = gym.get_training_example()
            if training_example:
                print(f"\nExample {i+1}:")
                print(f"Plugin: {training_example.plugin_name}")
                print(f"Question: {training_example.question}")
                print(f"Answer Type: {type(training_example.answer).__name__}")
                print(f"Answer: {training_example.answer.model_dump()}")
            else:
                print(f"Example {i+1}: No training example generated")
        except Exception as e:
            print(f"Error generating example {i+1}: {e}")
    
    # Show how an RL agent would use this
    print(f"\n=== RL TRAINING SIMULATION ===")
    training_example = gym.get_training_example()
    if training_example:
        print(f"Question for agent: {training_example.question}")
        print(f"Expected answer schema: {type(training_example.answer).__name__}")
        print(f"Ground truth answer: {training_example.answer.model_dump()}")
        print(f"Plugin source: {training_example.plugin_name}")
        
        print(f"\nAgent would now:")
        print(f"1. Parse the question: '{training_example.question}'")
        print(f"2. Generate SQL queries to find the answer")
        print(f"3. Return a {type(training_example.answer).__name__} model")
        print(f"4. Compare against ground truth for reward calculation")
    
    # Show schema perturbations
    print(f"\nSchema perturbations applied:")
    for table, perturbations in ground_truth.schema_perturbations.items():
        if perturbations:
            print(f"{table}: {perturbations}")
    
    # Register and use the custom allergy plugin
    print("\nAdding custom Allergy plugin...")
    gym.register_plugin(AllergyPlugin(gym.fake, gym.use_apis, gym.seed))
    
    # Regenerate database with new plugin
    new_ground_truth = gym.reset(num_patients=50)
    print(f"New plugins: {gym.list_plugins()}")
    if 'allergies' in new_ground_truth.plugin_ground_truths:
        print(f"Allergies plugin data: {new_ground_truth.plugin_ground_truths['allergies']}")
    
    # Test training examples with new plugin
    print(f"\nTraining example with extended plugin system:")
    try:
        training_example = gym.get_training_example()
        if training_example:
            print(f"Plugin source: {training_example.plugin_name}")
            print(f"Question: {training_example.question}")
            print(f"Answer: {training_example.answer.model_dump()}")
        else:
            print("No training example generated")
    except Exception as e:
        print(f"Error: {e}")
    
    gym.close()