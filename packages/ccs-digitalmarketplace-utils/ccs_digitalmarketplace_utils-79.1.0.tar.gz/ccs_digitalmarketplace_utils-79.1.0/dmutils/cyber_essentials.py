from datetime import datetime, timezone
from enum import Enum
from logging import Logger

from typing import Tuple, Union, Literal

from dmapiclient import DataInsightsAPIClient
from dmapiclient.errors import APIError
from dmapiclient.data_insights import IasmeCyberEssentialsAPIError
from dmutils.timing import logged_duration_for_external_request as log_external_request


class CyberEssentialsCertificateType(Enum):
    CYBER_ESSENTIALS = 'CE'
    CYBER_ESSENTIALS_PLUS = 'CE+'


def cyber_essentials_certificate_check(
    insights_api_client: DataInsightsAPIClient,
    certificate_number: str,
    certificate_type: CyberEssentialsCertificateType,
    logger: Logger
) -> Union[Tuple[Literal[False], str], Tuple[Literal[True], None]]:
    """
    Function to check if the cyber essentials certificate exists and that it is valid
    """
    try:
        with log_external_request(service="IASME Cubter essentials"):
            response = insights_api_client.get_cyber_essentials_certificate(
                certificate_number
            )["cyberEssentialsCertificateDetails"]

            if response['CertificateLevel'] != certificate_type.value:
                return False, 'certificate_not_right_level'

            if response['CertificationExpiryDate'] <= datetime.now(timezone.utc).strftime("%Y-%m-%d"):
                return False, 'certificate_expired'

            return True, None

    except IasmeCyberEssentialsAPIError:
        return False, 'certificate_not_found'
    except APIError as e:
        logger.error(
            "Error when getting a certificate",
            extra={
                "error": str(e),
            },
        )
        return False, 'api_error'
