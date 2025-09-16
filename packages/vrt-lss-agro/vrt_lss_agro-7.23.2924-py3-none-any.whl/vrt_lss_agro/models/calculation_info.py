# coding: utf-8

"""
    VRt.Agro [AG]

    Veeroute Agro API.  # Description  The service is designed to calculate the work plan of production facilities.  ## Objects overview  ![objects](../images/agro_objects.svg)  ### Field  - produces a certain crop of a certain moisture content - products from the field can only be moved to the Elevator or Factory  ### Elevator  - consists of Gates, Dryers, short-term and long-term storage areas - dries the grain (if the moisture content of the crop is more than acceptable) - stores dry grain in short-term storage places (warehouses), while unloading and loading grain is allowed within one day - stores dry grain in long-term storage places (sleeves, trenches, mounds) - when stored in one storage, only one type of culture can be located - sells surplus grain to the Market - production processes inside the facility: drying, loading / unloading to a storage location, storage  ### Factory  - consists of Gates, Dryers, Bunkers, Consumers - [if drying is present] dries the grain (if the moisture content of the crop is more than allowed) - stores dry grain in Bunkers (short-term storage tied to a specific crop) - maintains a minimum supply of grain for consumption in the Bunkers - Consumes grain from Bunkers - buys the missing grain from the Market - production processes inside the facility: drying, loading / unloading to a storage location, storage, consumption  ### Market  - buys grain from elevators - sells grain to factories  ## Project  The project reflects the planned sequence of operations on agricultural crops, the types of operations are described below.  ### HARVEST  Crop harvesting:  - between production facilities (Field and Elevator or Field) - the operation takes place within one day - on the Field there is a determination of grain moisture  |             | Object (target_key) | Subobject (target_detail_key) | |-------------|---------------------|-------------------------------| | Source      | Field               | -                             | | Destination | Elevator or Factory | Gate                          |  ### DRY  Drying culture:  - inside the production facility (Elevator or Field) - duration of the operation - days - during the drying process, the mass and type of humidity changes (WET -> DRY) - the source indicates the mass of raw culture - in the appointment, the resulting mass of dry culture is indicated  |             | Object (target_key) | Subobject (target_detail_key) | |-------------|---------------------|-------------------------------| | Source      | Elevator or Factory | Gate                          | | Destination | Elevator or Factory | Dryer                         |  ### LOAD  Loading culture from the Gate to the Storage Location (long-term, short-term, silo):  - between parts of one production facility (Elevator or Field) - the operation takes place within one day  |             | Object (target_key) | Subobject (target_detail_key)                    | |-------------|---------------------|--------------------------------------------------| | Source      | Elevator or Factory | Gate or Dryer                                    | | Destination | Elevator or Factory | Storage location (long-term, short-term, bunker) |  ### UNLOAD  Unloading the culture from the storage place to the gate:  - between parts of one production facility (Elevator) - the operation takes place within one day  |             | Object (target_key) | Subobject (target_detail_key)                    | |-------------|---------------------|--------------------------------------------------| | Source      | Elevator            | Storage location (long-term, short-term, bunker) | | Destination | Elevator            | Gate                                             |  ### STORE  Culture storage:  - the operation takes place within one day - storage location does not change  |             | Object (target_key) | Subobject (target_detail_key)                    | |-------------|---------------------|--------------------------------------------------| | Source      | Elevator or Factory | Storage location (long-term, short-term, bunker) | | Destination | Elevator or Factory | The same storage location                        |  ### RELOCATE  Transportation between production facilities:  - between production facilities (Elevator and Field) - the operation takes place within one day  |             | Object (target_key) | Subobject (target_detail_key) | |-------------|---------------------|-------------------------------| | Source      | Elevator            | Gate                          | | Destination | Factory             | Gate                          |  ### CONSUMPTION  Field crop consumption:  - between parts of one production facility (Field) - the operation takes place within one day - consumption comes from the Bunker - in addition, we can consume directly from the Gate or Dryer without laying in the Bunker  |             | Object (target_key) | Subobject (target_detail_key) | |-------------|---------------------|-------------------------------| | Source      | Factory             | Hopper or Gate or Dryer       | | Destination | Factory             | Consumer                      |  ### SELL  Sale of culture:  - between production facilities (Elevator and Market) - the operation takes place within one day  |             | Object (target_key) | Subobject (target_detail_key) | |-------------|---------------------|-------------------------------| | Source      | Elevator            | Gate                          | | Destination | Market              | Contract                      |  ### BUY  Buying culture:  - between production facilities (Market and Factory) - the operation takes place within one day  |             | Object (target_key) | Subobject (target_detail_key) | |-------------|---------------------|-------------------------------| | Source      | Market              | Contract                      | | Destination | Factory             | Gate                          |  ## Entity relationship diagram  ![erd](../uml/agro.svg) 

    The version of the OpenAPI document: 7.23.2924
    Contact: servicedesk@veeroute.com
    Generated by OpenAPI Generator (https://openapi-generator.tech)

    Do not edit the class manually.
"""  # noqa: E501


from __future__ import annotations
import pprint
import re  # noqa: F401
import json

from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator
from typing import Any, ClassVar, Dict, List, Optional
from typing_extensions import Annotated
from vrt_lss_agro.models.calculation_status import CalculationStatus
from typing import Optional, Set
from typing_extensions import Self

class CalculationInfo(BaseModel):
    """
    Calculation information.
    """ # noqa: E501
    status: CalculationStatus
    message: Optional[StrictStr] = Field(default=None, description="Message with additional information about the calculation status.")
    result_version: Annotated[int, Field(le=1000000, strict=True, ge=0)] = Field(description="Planning result version.")
    preparing_time: Annotated[str, Field(min_length=3, strict=True, max_length=16)] = Field(description="Time duration according to [ISO 8601 duration](https://en.wikipedia.org/wiki/ISO_8601#Durations).")
    business_validation_time: Annotated[str, Field(min_length=3, strict=True, max_length=16)] = Field(description="Time duration according to [ISO 8601 duration](https://en.wikipedia.org/wiki/ISO_8601#Durations).")
    math_validation_time: Annotated[str, Field(min_length=3, strict=True, max_length=16)] = Field(description="Time duration according to [ISO 8601 duration](https://en.wikipedia.org/wiki/ISO_8601#Durations).")
    waiting_time: Annotated[str, Field(min_length=3, strict=True, max_length=16)] = Field(description="Time duration according to [ISO 8601 duration](https://en.wikipedia.org/wiki/ISO_8601#Durations).")
    calculation_time: Annotated[str, Field(min_length=3, strict=True, max_length=16)] = Field(description="Time duration according to [ISO 8601 duration](https://en.wikipedia.org/wiki/ISO_8601#Durations).")
    additional_properties: Dict[str, Any] = {}
    __properties: ClassVar[List[str]] = ["status", "message", "result_version", "preparing_time", "business_validation_time", "math_validation_time", "waiting_time", "calculation_time"]

    @field_validator('preparing_time')
    def preparing_time_validate_regular_expression(cls, value):
        """Validates the regular expression"""
        if not re.match(r"^P(?!$)((\d+Y)|(\d+\.\d+Y$))?((\d+M)|(\d+\.\d+M$))?((\d+W)|(\d+\.\d+W$))?((\d+D)|(\d+\.\d+D$))?(T(?=\d)((\d+H)|(\d+\.\d+H$))?((\d+M)|(\d+\.\d+M$))?(\d+(\.\d+)?S)?)??$", value):
            raise ValueError(r"must validate the regular expression /^P(?!$)((\d+Y)|(\d+\.\d+Y$))?((\d+M)|(\d+\.\d+M$))?((\d+W)|(\d+\.\d+W$))?((\d+D)|(\d+\.\d+D$))?(T(?=\d)((\d+H)|(\d+\.\d+H$))?((\d+M)|(\d+\.\d+M$))?(\d+(\.\d+)?S)?)??$/")
        return value

    @field_validator('business_validation_time')
    def business_validation_time_validate_regular_expression(cls, value):
        """Validates the regular expression"""
        if not re.match(r"^P(?!$)((\d+Y)|(\d+\.\d+Y$))?((\d+M)|(\d+\.\d+M$))?((\d+W)|(\d+\.\d+W$))?((\d+D)|(\d+\.\d+D$))?(T(?=\d)((\d+H)|(\d+\.\d+H$))?((\d+M)|(\d+\.\d+M$))?(\d+(\.\d+)?S)?)??$", value):
            raise ValueError(r"must validate the regular expression /^P(?!$)((\d+Y)|(\d+\.\d+Y$))?((\d+M)|(\d+\.\d+M$))?((\d+W)|(\d+\.\d+W$))?((\d+D)|(\d+\.\d+D$))?(T(?=\d)((\d+H)|(\d+\.\d+H$))?((\d+M)|(\d+\.\d+M$))?(\d+(\.\d+)?S)?)??$/")
        return value

    @field_validator('math_validation_time')
    def math_validation_time_validate_regular_expression(cls, value):
        """Validates the regular expression"""
        if not re.match(r"^P(?!$)((\d+Y)|(\d+\.\d+Y$))?((\d+M)|(\d+\.\d+M$))?((\d+W)|(\d+\.\d+W$))?((\d+D)|(\d+\.\d+D$))?(T(?=\d)((\d+H)|(\d+\.\d+H$))?((\d+M)|(\d+\.\d+M$))?(\d+(\.\d+)?S)?)??$", value):
            raise ValueError(r"must validate the regular expression /^P(?!$)((\d+Y)|(\d+\.\d+Y$))?((\d+M)|(\d+\.\d+M$))?((\d+W)|(\d+\.\d+W$))?((\d+D)|(\d+\.\d+D$))?(T(?=\d)((\d+H)|(\d+\.\d+H$))?((\d+M)|(\d+\.\d+M$))?(\d+(\.\d+)?S)?)??$/")
        return value

    @field_validator('waiting_time')
    def waiting_time_validate_regular_expression(cls, value):
        """Validates the regular expression"""
        if not re.match(r"^P(?!$)((\d+Y)|(\d+\.\d+Y$))?((\d+M)|(\d+\.\d+M$))?((\d+W)|(\d+\.\d+W$))?((\d+D)|(\d+\.\d+D$))?(T(?=\d)((\d+H)|(\d+\.\d+H$))?((\d+M)|(\d+\.\d+M$))?(\d+(\.\d+)?S)?)??$", value):
            raise ValueError(r"must validate the regular expression /^P(?!$)((\d+Y)|(\d+\.\d+Y$))?((\d+M)|(\d+\.\d+M$))?((\d+W)|(\d+\.\d+W$))?((\d+D)|(\d+\.\d+D$))?(T(?=\d)((\d+H)|(\d+\.\d+H$))?((\d+M)|(\d+\.\d+M$))?(\d+(\.\d+)?S)?)??$/")
        return value

    @field_validator('calculation_time')
    def calculation_time_validate_regular_expression(cls, value):
        """Validates the regular expression"""
        if not re.match(r"^P(?!$)((\d+Y)|(\d+\.\d+Y$))?((\d+M)|(\d+\.\d+M$))?((\d+W)|(\d+\.\d+W$))?((\d+D)|(\d+\.\d+D$))?(T(?=\d)((\d+H)|(\d+\.\d+H$))?((\d+M)|(\d+\.\d+M$))?(\d+(\.\d+)?S)?)??$", value):
            raise ValueError(r"must validate the regular expression /^P(?!$)((\d+Y)|(\d+\.\d+Y$))?((\d+M)|(\d+\.\d+M$))?((\d+W)|(\d+\.\d+W$))?((\d+D)|(\d+\.\d+D$))?(T(?=\d)((\d+H)|(\d+\.\d+H$))?((\d+M)|(\d+\.\d+M$))?(\d+(\.\d+)?S)?)??$/")
        return value

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        protected_namespaces=(),
    )


    def to_str(self) -> str:
        """Returns the string representation of the model using alias"""
        return pprint.pformat(self.model_dump(by_alias=True))

    def to_json(self) -> str:
        """Returns the JSON representation of the model using alias"""
        # TODO: pydantic v2: use .model_dump_json(by_alias=True, exclude_unset=True) instead
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> Optional[Self]:
        """Create an instance of CalculationInfo from a JSON string"""
        return cls.from_dict(json.loads(json_str))

    def to_dict(self) -> Dict[str, Any]:
        """Return the dictionary representation of the model using alias.

        This has the following differences from calling pydantic's
        `self.model_dump(by_alias=True)`:

        * `None` is only added to the output dict for nullable fields that
          were set at model initialization. Other fields with value `None`
          are ignored.
        * Fields in `self.additional_properties` are added to the output dict.
        """
        excluded_fields: Set[str] = set([
            "additional_properties",
        ])

        _dict = self.model_dump(
            by_alias=True,
            exclude=excluded_fields,
            exclude_none=True,
        )
        # puts key-value pairs in additional_properties in the top level
        if self.additional_properties is not None:
            for _key, _value in self.additional_properties.items():
                _dict[_key] = _value

        # set to None if message (nullable) is None
        # and model_fields_set contains the field
        if self.message is None and "message" in self.model_fields_set:
            _dict['message'] = None

        return _dict

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of CalculationInfo from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate({
            "status": obj.get("status"),
            "message": obj.get("message"),
            "result_version": obj.get("result_version"),
            "preparing_time": obj.get("preparing_time") if obj.get("preparing_time") is not None else 'PT0S',
            "business_validation_time": obj.get("business_validation_time") if obj.get("business_validation_time") is not None else 'PT0S',
            "math_validation_time": obj.get("math_validation_time") if obj.get("math_validation_time") is not None else 'PT0S',
            "waiting_time": obj.get("waiting_time") if obj.get("waiting_time") is not None else 'PT0S',
            "calculation_time": obj.get("calculation_time") if obj.get("calculation_time") is not None else 'PT0S'
        })
        # store additional fields in additional_properties
        for _key in obj.keys():
            if _key not in cls.__properties:
                _obj.additional_properties[_key] = obj.get(_key)

        return _obj


