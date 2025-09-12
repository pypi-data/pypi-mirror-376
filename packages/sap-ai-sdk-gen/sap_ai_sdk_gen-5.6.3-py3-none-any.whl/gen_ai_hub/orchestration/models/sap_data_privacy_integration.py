from enum import Enum
from typing import List

from gen_ai_hub.orchestration.models.data_masking import DataMaskingProvider, DataMaskingProviderName


class MaskingMethod(str, Enum):
    """
    Enumerates the supported masking methods.

    This enum defines the two main methods for masking sensitive information: anonymization and pseudonymization.
    Anonymization irreversibly removes sensitive data, while pseudonymization allows the original data to be recovered.

    Values:
        ANONYMIZATION: Irreversibly replaces sensitive data with placeholders (e.g., MASKED_ENTITY).
        PSEUDONYMIZATION: Replaces sensitive data with reversible placeholders (e.g., MASKED_ENTITY_ID).
    """
    ANONYMIZATION = "anonymization"
    PSEUDONYMIZATION = "pseudonymization"


class ProfileEntity(str, Enum):
    """
    Enumerates the entity categories that can be masked by the SAP Data Privacy Integration service.

    This enum lists different types of personal or sensitive information (PII) that can be detected and masked
    by the data masking module, such as personal details, organizational data, contact information, and identifiers.

    Values:
        PERSON: Represents personal names.
        ORG: Represents organizational names.
        UNIVERSITY: Represents educational institutions.
        LOCATION: Represents geographical locations.
        EMAIL: Represents email addresses.
        PHONE: Represents phone numbers.
        ADDRESS: Represents physical addresses.
        SAP_IDS_INTERNAL: Represents internal SAP identifiers.
        SAP_IDS_PUBLIC: Represents public SAP identifiers.
        URL: Represents URLs.
        USERNAME_PASSWORD: Represents usernames and passwords.
        NATIONAL_ID: Represents national identification numbers.
        IBAN: Represents International Bank Account Numbers.
        SSN: Represents Social Security Numbers.
        CREDIT_CARD_NUMBER: Represents credit card numbers.
        PASSPORT: Represents passport numbers.
        DRIVING_LICENSE: Represents driving license numbers.
        NATIONALITY: Represents nationality information.
        RELIGIOUS_GROUP: Represents religious group affiliation.
        POLITICAL_GROUP: Represents political group affiliation.
        PRONOUNS_GENDER: Represents pronouns and gender identity.
        GENDER: Represents gender information.
        SEXUAL_ORIENTATION: Represents sexual orientation.
        TRADE_UNION: Represents trade union membership.
        SENSITIVE_DATA: Represents any other sensitive information.
    """

    PERSON = "profile-person"
    ORG = "profile-org"
    UNIVERSITY = "profile-university"
    LOCATION = "profile-location"
    EMAIL = "profile-email"
    PHONE = "profile-phone"
    ADDRESS = "profile-address"
    SAP_IDS_INTERNAL = "profile-sapids-internal"
    SAP_IDS_PUBLIC = "profile-sapids-public"
    URL = "profile-url"
    USERNAME_PASSWORD = "profile-username-password"
    NATIONAL_ID = "profile-nationalid"
    IBAN = "profile-iban"
    SSN = "profile-ssn"
    CREDIT_CARD_NUMBER = "profile-credit-card-number"
    PASSPORT = "profile-passport"
    DRIVING_LICENSE = "profile-driverlicense"
    NATIONALITY = "profile-nationality"
    RELIGIOUS_GROUP = "profile-religious-group"
    POLITICAL_GROUP = "profile-political-group"
    PRONOUNS_GENDER = "profile-pronouns-gender"
    GENDER = "profile-gender"
    SEXUAL_ORIENTATION = "profile-sexual-orientation"
    TRADE_UNION = "profile-trade-union"
    SENSITIVE_DATA = "profile-sensitive-data"


class SAPDataPrivacyIntegration(DataMaskingProvider):
    """
    SAP Data Privacy Integration provider for data masking.

    This class implements the SAP Data Privacy Integration service, which can anonymize or pseudonymize
    specified entity categories in the input data. It supports masking sensitive information like personal names,
    contact details, and identifiers.

    Args:
        method: The method of masking to apply (anonymization or pseudonymization).
        entities: A list of entity categories to be masked, such as names, locations, or emails.
        allowlist: A list of strings that should not be masked.
        mask_grounding_input: A flag indicating whether to mask input to the grounding module.
    """

    def __init__(
            self,
            method: MaskingMethod,
            entities: List[ProfileEntity],
            allowlist: List[str] = None,
            mask_grounding_input: bool = False,
    ):
        self.method = method
        self.entities = entities
        self.allowlist = allowlist or []
        self.mask_grounding_input = mask_grounding_input

    def to_dict(self):
        result = {
            "type": DataMaskingProviderName.SAP_DATA_PRIVACY_INTEGRATION,
            "method": self.method,
            "entities": [
                {
                    "type": entity
                } for entity in self.entities
            ],
            "mask_grounding_input": {
                "enabled": self.mask_grounding_input
            }
        }

        if self.allowlist:
            result["allowlist"] = self.allowlist

        return result
